# vim: set filetype=python fileencoding=utf-8:
# -*- coding: utf-8 -*-

#============================================================================#
#                                                                            #
#  Licensed under the Apache License, Version 2.0 (the "License");           #
#  you may not use this file except in compliance with the License.          #
#  You may obtain a copy of the License at                                   #
#                                                                            #
#      http://www.apache.org/licenses/LICENSE-2.0                            #
#                                                                            #
#  Unless required by applicable law or agreed to in writing, software       #
#  distributed under the License is distributed on an "AS IS" BASIS,         #
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  #
#  See the License for the specific language governing permissions and       #
#  limitations under the License.                                            #
#                                                                            #
#============================================================================#


''' Core business logic shared between CLI and MCP server. '''


from . import __
from . import exceptions as _exceptions
from . import interfaces as _interfaces
from . import xtnsapi as _xtnsapi


DocumentationResult: __.typx.TypeAlias = __.cabc.Mapping[ str, __.typx.Any ]
DomainFilter: __.typx.TypeAlias = __.typx.Annotated[
    __.Absential[ str ], __.ddoc.Fname( 'domain filter argument' ) ]
FuzzyThreshold: __.typx.TypeAlias = __.typx.Annotated[
    int, __.ddoc.Fname( 'fuzzy threshold argument' ) ]
RoleFilter: __.typx.TypeAlias = __.typx.Annotated[
    __.Absential[ str ], __.ddoc.Fname( 'role filter argument' ) ]
TermFilter: __.typx.TypeAlias = __.typx.Annotated[
    __.Absential[ str ], __.ddoc.Fname( 'term filter argument' ) ]
MatchModeArgument: __.typx.TypeAlias = __.typx.Annotated[
    _interfaces.MatchMode, __.ddoc.Fname( 'match mode argument' ) ]
PriorityFilter: __.typx.TypeAlias = __.typx.Annotated[
    __.Absential[ str ], __.ddoc.Fname( 'priority filter argument' ) ]
SearchResult: __.typx.TypeAlias = __.cabc.Mapping[ str, __.typx.Any ]
SectionFilter: __.typx.TypeAlias = __.typx.Annotated[
    __.Absential[ list[ str ] ], __.ddoc.Fname( 'section filter argument' ) ]
SourceArgument: __.typx.TypeAlias = __.typx.Annotated[
    str, __.ddoc.Fname( 'source argument' ) ]


async def query_documentation(
    source: SourceArgument,
    query: str, /, *,
    filters: _interfaces.Filters | None = None,
    max_results: int = 10,
    include_snippets: bool = True
) -> __.typx.Annotated[
    dict[ str, __.typx.Any ], __.ddoc.Fname( 'documentation return' ) ]:
    ''' Queries documentation content with relevance ranking. '''
    if filters is None:
        filters = _interfaces.Filters( )
    processor = await _select_processor_for_source( source )

    # Get raw query results from processor
    raw_results = await processor.query_documentation(
        source, query,
        filters = filters,
        max_results = max_results,
        include_snippets = include_snippets )

    # Transform to explore-style format
    return _build_query_result_structure(
        source, query, raw_results, max_results, filters )


async def summarize_inventory(
    source: SourceArgument,
    query: str = "", /, *,
    filters: _interfaces.Filters | None = None,
) -> __.typx.Annotated[
    str, __.ddoc.Fname( 'inventory summary return' ) ]:
    ''' Provides human-readable summary of inventory. '''
    if filters is None:
        filters = _interfaces.Filters( )
    # Use explore with no documentation to get inventory data
    explore_result = await explore(
        source, query, filters = filters,
        max_objects = 1000,  # Large number to get all matches
        include_documentation = False
    )
    # Convert explore result back to extract_inventory format for formatting
    inventory_data: dict[ str, __.typx.Any ] = {
        'project': explore_result[ 'project' ],
        'version': explore_result[ 'version' ],
        'object_count': explore_result[ 'search_metadata' ][ 'total_matches' ],
        'objects': _group_documents_by_domain( explore_result[ 'documents' ] ),
        'filters': explore_result[ 'search_metadata' ][ 'filters' ]
    }
    return _format_inventory_summary( inventory_data )


def _group_documents_by_domain(
    documents: list[ dict[ str, __.typx.Any ] ]
) -> dict[ str, list[ dict[ str, __.typx.Any ] ] ]:
    ''' Groups documents by domain for inventory format compatibility. '''
    groups: dict[ str, list[ dict[ str, __.typx.Any ] ] ] = { }
    for doc in documents:
        domain = doc.get( 'domain', '' )
        if domain not in groups:
            groups[ domain ] = [ ]
        # Convert document format back to inventory object format
        inventory_obj = {
            'name': doc[ 'name' ],
            'role': doc[ 'role' ],
            'domain': doc[ 'domain' ],
            'uri': doc[ 'uri' ],
            'dispname': doc[ 'dispname' ]
        }
        if 'fuzzy_score' in doc:
            inventory_obj[ 'fuzzy_score' ] = doc[ 'fuzzy_score' ]
        groups[ domain ].append( inventory_obj )
    return groups


async def explore(
    source: SourceArgument,
    query: str, /, *,
    filters: _interfaces.Filters | None = None,
    max_objects: int = 5,
    include_documentation: bool = True,
) -> __.typx.Annotated[
    dict[ str, __.typx.Any ], __.ddoc.Fname( 'explore return' ) ]:
    '''
    Explores objects related to a query by combining inventory search
    with documentation extraction.

    This function streamlines the common workflow of searching inventory
    for relevant objects and then extracting detailed documentation for
    each match. It handles errors gracefully by separating successful
    results from failed extractions.
    '''
    if filters is None:
        filters = _interfaces.Filters( )
    processor = await _select_processor_for_source( source )
    result_mapping = await processor.extract_inventory(
        source,
        term = query,
        filters = filters
    )
    # Convert to mutable dict and add additional fields
    inventory_data = dict( result_mapping )
    inventory_data[ 'source' ] = source
    domains_summary: dict[ str, int ] = {
        domain_name: len( objs )
        for domain_name, objs in inventory_data[ 'objects' ].items( )
    }
    inventory_data[ 'domains' ] = domains_summary
    selected_objects = _select_top_objects( inventory_data, max_objects )
    result = _build_explore_result_structure(
        inventory_data, query, selected_objects, max_objects, filters )
    if include_documentation:
        await _add_documentation_to_results( source, selected_objects, result )
    else:
        _add_object_metadata_to_results( selected_objects, result )
    return result


def _select_top_objects(
    inventory_data: dict[ str, __.typx.Any ],
    max_objects: int
) -> list[ dict[ str, __.typx.Any ] ]:
    ''' Selects top objects from inventory, sorted by fuzzy score. '''
    all_objects: list[ dict[ str, __.typx.Any ] ] = [ ]
    for domain_objects in inventory_data[ 'objects' ].values( ):
        all_objects.extend( domain_objects )
    all_objects.sort(
        key = lambda obj: obj.get( 'fuzzy_score', 0 ),
        reverse = True
    )
    return all_objects[ :max_objects ]


def _build_explore_result_structure(
    inventory_data: dict[ str, __.typx.Any ],
    query: str,
    selected_objects: list[ dict[ str, __.typx.Any ] ],
    max_objects: int,
    filters: _interfaces.Filters,
) -> dict[ str, __.typx.Any ]:
    ''' Builds the base result structure with metadata. '''
    filter_metadata: dict[ str, __.typx.Any ] = { }
    _populate_filter_metadata( filter_metadata, filters )

    search_metadata: dict[ str, __.typx.Any ] = {
        'object_count': len( selected_objects ),
        'max_objects': max_objects,
        'total_matches': inventory_data[ 'object_count' ],
        'filters': filter_metadata
    }

    result: dict[ str, __.typx.Any ] = {
        'project': inventory_data[ 'project' ],
        'version': inventory_data[ 'version' ],
        'query': query,
        'search_metadata': search_metadata,
        'documents': [ ]
    }
    return result


def _populate_filter_metadata(
    metadata: dict[ str, __.typx.Any ],
    filters: _interfaces.Filters
) -> None:
    ''' Populates filter metadata dictionary with non-empty filters. '''
    if filters.domain:
        metadata[ 'domain' ] = filters.domain
    if filters.role:
        metadata[ 'role' ] = filters.role
    if filters.priority:
        metadata[ 'priority' ] = filters.priority
    metadata[ 'match_mode' ] = filters.match_mode.value
    if filters.match_mode == _interfaces.MatchMode.Fuzzy:
        metadata[ 'fuzzy_threshold' ] = filters.fuzzy_threshold


async def _add_documentation_to_results(
    source: str,
    selected_objects: list[ dict[ str, __.typx.Any ] ],
    result: dict[ str, __.typx.Any ],
) -> None:
    ''' Extracts documentation for objects and adds to results. '''
    processor = await _select_processor_for_source( source )
    for obj in selected_objects:
        doc_result = await processor.extract_documentation(
            source, obj[ 'name' ] )
        document = _create_document_with_docs( obj, doc_result )
        result[ 'documents' ].append( document )


def _add_object_metadata_to_results(
    selected_objects: list[ dict[ str, __.typx.Any ] ],
    result: dict[ str, __.typx.Any ],
) -> None:
    ''' Adds object metadata without documentation to results. '''
    for obj in selected_objects:
        document = _create_document_metadata( obj )
        result[ 'documents' ].append( document )


def _create_document_with_docs(
    obj: dict[ str, __.typx.Any ],
    doc_result: __.cabc.Mapping[ str, __.typx.Any ],
) -> dict[ str, __.typx.Any ]:
    ''' Creates document structure with documentation content. '''
    document = _create_document_metadata( obj )
    document[ 'documentation' ] = doc_result
    return document


def _create_document_metadata(
    obj: dict[ str, __.typx.Any ]
) -> dict[ str, __.typx.Any ]:
    ''' Creates base document structure from object metadata. '''
    document = {
        'name': obj[ 'name' ],
        'role': obj[ 'role' ],
        'domain': obj.get( 'domain', '' ),
        'uri': obj[ 'uri' ],
        'dispname': obj[ 'dispname' ]
    }
    if 'fuzzy_score' in obj:
        document[ 'fuzzy_score' ] = obj[ 'fuzzy_score' ]
    return document


def _format_inventory_summary(
    inventory_data: dict[ str, __.typx.Any ]
) -> str:
    ''' Formats inventory data into human-readable summary. '''
    summary_lines: list[ str ] = [
        f"Project: {inventory_data[ 'project' ]}",
        f"Version: {inventory_data[ 'version' ]}",
        f"Objects: {inventory_data[ 'object_count' ]}",
    ]
    if 'filters' in inventory_data:
        filters = inventory_data[ 'filters' ]
        filter_strings: list[ str ] = [ ]
        for key, value in filters.items( ):
            filter_strings.append( f"{key}={value}" )
        if filter_strings:
            summary_lines.append( f"Filters: {', '.join( filter_strings )}" )
    if inventory_data[ 'objects' ]:
        summary_lines.append( "\nDomain breakdown:" )
        for domain_name, objects in inventory_data[ 'objects' ].items( ):
            summary_lines.append(
                f"  {domain_name}: {len( objects )} objects" )
    return '\n'.join( summary_lines )


def _build_query_result_structure(
    source: str,
    query: str,
    raw_results: list[ __.cabc.Mapping[ str, __.typx.Any ] ],
    max_results: int,
    filters: _interfaces.Filters,
) -> dict[ str, __.typx.Any ]:
    ''' Builds query result structure in explore format. '''
    filter_metadata: dict[ str, __.typx.Any ] = { }
    _populate_filter_metadata( filter_metadata, filters )

    search_metadata: dict[ str, __.typx.Any ] = {
        'result_count': len( raw_results ),
        'max_results': max_results,
        'filters': filter_metadata
    }

    # Transform raw results to document format
    documents: list[ dict[ str, __.typx.Any ] ] = [ ]
    for raw_result in raw_results:
        result_dict = dict( raw_result )
        document: dict[ str, __.typx.Any ] = {
            'name': result_dict[ 'object_name' ],
            'type': result_dict[ 'object_type' ],
            'domain': result_dict[ 'domain' ],
            'priority': result_dict[ 'priority' ],
            'url': result_dict[ 'url' ],
            'signature': result_dict[ 'signature' ],
            'description': result_dict[ 'description' ],
            'content_snippet': result_dict[ 'content_snippet' ],
            'relevance_score': result_dict[ 'relevance_score' ],
            'match_reasons': result_dict[ 'match_reasons' ]
        }
        documents.append( document )

    result: dict[ str, __.typx.Any ] = {
        'source': source,
        'query': query,
        'search_metadata': search_metadata,
        'documents': documents
    }
    return result


async def _select_processor_for_source(
    source: SourceArgument
) -> _interfaces.Processor:
    ''' Selects best processor for source via detection. '''
    best_processor: _interfaces.Processor | None = None
    best_confidence = 0.0
    for processor in _xtnsapi.processors.values( ):
        detection = await processor.detect( source )
        if detection.confidence > best_confidence:
            best_confidence = detection.confidence
            best_processor = processor
    if not best_processor:
        raise _exceptions.ProcessorNotFound( source )
    return best_processor
