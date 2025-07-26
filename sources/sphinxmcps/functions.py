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
    __.Absential[ str ],
    __.ddoc.Doc( '''
        Filter objects by Sphinx domain. Built-in domains:
        'py' (Python), 'std' (standard), 'c' (C), 'cpp' (C++),
        'js' (JavaScript), 'rst' (reStructuredText),
        'math' (Mathematics). Empty string shows all domains.
    ''' )
]
FuzzyThreshold: __.typx.TypeAlias = __.typx.Annotated[
    int,
    __.ddoc.Doc( ''' Fuzzy matching threshold (0-100, higher = stricter). ''' )
]
RoleFilter: __.typx.TypeAlias = __.typx.Annotated[
    __.Absential[ str ],
    __.ddoc.Doc( ''' Filter objects by role (e.g., 'function'). ''' )
]
TermFilter: __.typx.TypeAlias = __.typx.Annotated[
    __.Absential[ str ],
    __.ddoc.Doc( ''' Filter objects by name containing this text. ''' )
]
MatchModeArgument: __.typx.TypeAlias = __.typx.Annotated[
    _interfaces.MatchMode,
    __.ddoc.Doc( ''' Term matching mode: exact, regex, or fuzzy. ''' )
]
PriorityFilter: __.typx.TypeAlias = __.typx.Annotated[
    __.Absential[ str ],
    __.ddoc.Doc( ''' Filter objects by priority level (e.g., '1', '0'). ''' )
]
RegexFlag: __.typx.TypeAlias = __.typx.Annotated[
    bool, __.ddoc.Doc( ''' Use regex pattern matching for term filter. ''' )
]
SearchResult: __.typx.TypeAlias = __.cabc.Mapping[ str, __.typx.Any ]
SectionFilter: __.typx.TypeAlias = __.typx.Annotated[
    __.Absential[ list[ str ] ],
    __.ddoc.Doc( ''' Sections to include (signature, description). ''' )
]
SourceArgument: __.typx.TypeAlias = __.typx.Annotated[
    str, __.ddoc.Doc( ''' URL or file path to documentation source. ''' )
]


class Filters( __.immut.DataclassObject ):
    ''' Common filters for inventory and documentation search. '''

    domain: str = ""
    role: str = ""
    priority: str = ""
    match_mode: _interfaces.MatchMode = _interfaces.MatchMode.Fuzzy
    fuzzy_threshold: int = 50


async def extract_documentation(
    source: SourceArgument,
    object_name: str, /, *,
    include_sections: SectionFilter = __.absent,
) -> DocumentationResult:
    ''' Extracts documentation for a specific object from source. '''
    processor = await _select_processor_for_source( source )
    return await processor.extract_documentation(
        source, object_name, include_sections = include_sections )


async def query_documentation(  # noqa: PLR0913
    source: SourceArgument,
    query: str, /, *,
    domain: DomainFilter = __.absent,
    role: RoleFilter = __.absent,
    priority: PriorityFilter = __.absent,
    match_mode: _interfaces.MatchMode = _interfaces.MatchMode.Fuzzy,
    fuzzy_threshold: int = 50,
    max_results: int = 10,
    include_snippets: bool = True
) -> __.typx.Annotated[
    list[ __.cabc.Mapping[ str, __.typx.Any ] ],
    __.ddoc.Doc( ''' List of query results with relevance ranking. ''' )
]:
    ''' Queries documentation content with relevance ranking. '''
    processor = await _select_processor_for_source( source )
    return await processor.query_documentation(
        source, query, domain = domain, role = role, priority = priority,
        match_mode = match_mode, fuzzy_threshold = fuzzy_threshold,
        max_results = max_results, include_snippets = include_snippets )


async def extract_inventory( # noqa: PLR0913
    source: SourceArgument, /, *,
    domain: DomainFilter = __.absent,
    role: RoleFilter = __.absent,
    term: TermFilter = __.absent,
    priority: PriorityFilter = __.absent,
    match_mode: MatchModeArgument = _interfaces.MatchMode.Exact,
    fuzzy_threshold: FuzzyThreshold = 50,
) -> __.typx.Annotated[
    dict[ str, __.typx.Any ],
    __.ddoc.Doc(
        ''' Dictionary containing inventory metadata and filtered objects.

            Contains project info, version, source, object counts, domain
            summary, and the actual objects grouped by domain.
        ''' )
]:
    ''' Extracts inventory from source with optional filtering. '''
    processor = await _select_processor_for_source( source )
    result_mapping = await processor.extract_inventory(
        source, domain = domain, role = role, term = term,
        priority = priority, match_mode = match_mode,
        fuzzy_threshold = fuzzy_threshold )
    # Convert to mutable dict so we can add fields
    result = dict( result_mapping )
    result[ 'source' ] = source
    domains_summary: dict[ str, int ] = {
        domain_name: len( objs )
        for domain_name, objs in result[ 'objects' ].items( ) }
    result[ 'domains' ] = domains_summary
    return result


async def summarize_inventory( # noqa: PLR0913
    source: SourceArgument, /, *,
    domain: DomainFilter = __.absent,
    role: RoleFilter = __.absent,
    term: TermFilter = __.absent,
    priority: PriorityFilter = __.absent,
    match_mode: MatchModeArgument = _interfaces.MatchMode.Exact,
    fuzzy_threshold: FuzzyThreshold = 50,
) -> __.typx.Annotated[
    str,
    __.ddoc.Doc( ''' Human-readable summary of inventory contents. ''' )
]:
    ''' Provides human-readable summary of inventory. '''
    inventory_data = await extract_inventory(
        source, domain = domain, role = role, term = term,
        priority = priority, match_mode = match_mode,
        fuzzy_threshold = fuzzy_threshold )
    return _format_inventory_summary( inventory_data )


async def explore(
    source: SourceArgument,
    query: str, /, *,
    filters: Filters | None = None,
    max_objects: int = 5,
    include_documentation: bool = True,
) -> __.typx.Annotated[
    dict[ str, __.typx.Any ],
    __.ddoc.Doc( '''
        Combined inventory search and documentation extraction results.
        Contains search metadata, matching objects, successful documentation
        extractions, and any errors encountered.
    ''' )
]:
    '''
    Explores objects related to a query by combining inventory search
    with documentation extraction.

    This function streamlines the common workflow of searching inventory
    for relevant objects and then extracting detailed documentation for
    each match. It handles errors gracefully by separating successful
    results from failed extractions.
    '''
    if filters is None:
        filters = Filters( )
    inventory_data = await extract_inventory(
        source,
        domain = filters.domain if filters.domain else __.absent,
        role = filters.role if filters.role else __.absent,
        term = query,
        priority = filters.priority if filters.priority else __.absent,
        match_mode = filters.match_mode,
        fuzzy_threshold = filters.fuzzy_threshold
    )
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
    filters: Filters,
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
        'documents': [ ],
        'errors': [ ]
    }
    return result


def _populate_filter_metadata(
    metadata: dict[ str, __.typx.Any ],
    filters: Filters
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
    for obj in selected_objects:
        try:
            doc_result = await extract_documentation( source, obj[ 'name' ] )
            document = _create_document_with_docs( obj, doc_result )
            result[ 'documents' ].append( document )
        except Exception as exc:  # noqa: PERF203
            error_info: dict[ str, __.typx.Any ] = {
                'name': obj[ 'name' ],
                'domain': obj.get( 'domain', '' ),
                'error': f"Documentation extraction failed: {exc}"
            }
            result[ 'errors' ].append( error_info )


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
