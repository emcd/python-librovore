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
from . import detection as _detection
from . import exceptions as _exceptions
from . import interfaces as _interfaces
from . import search as _search
from . import xtnsapi as _xtnsapi # TODO: Replace with 'registries' module.


DocumentationResult: __.typx.TypeAlias = __.cabc.Mapping[ str, __.typx.Any ]
SearchResult: __.typx.TypeAlias = __.cabc.Mapping[ str, __.typx.Any ]
SourceArgument: __.typx.TypeAlias = __.typx.Annotated[
    str, __.ddoc.Fname( 'source argument' ) ]


_search_behaviors_default = _interfaces.SearchBehaviors( )
_filters_default = __.immut.Dictionary[ str, __.typx.Any ]( )


async def detect(
    source: SourceArgument,
    all_detections: bool = False,
) -> dict[ str, __.typx.Any ]:
    ''' Detects which processor(s) can handle a documentation source. '''
    start_time = __.time.perf_counter( )
    detections, detection_optimal = (
        await _detection.access_detections( source ) )
    end_time = __.time.perf_counter( )
    detection_time_ms = int( ( end_time - start_time ) * 1000 )
    detections_list = list( detections.values( ) )
    if not all_detections and not __.is_absent( detection_optimal ):
        detections_list = [ detection_optimal ]
    response = _interfaces.DetectionToolResponse(
        source = source,
        detections = detections_list,
        detection_best = (
            detection_optimal
            if not __.is_absent( detection_optimal ) else None ),
        time_detection_ms = detection_time_ms )
    return _serialize_dataclass( response )


async def query_content(  # noqa: PLR0913
    source: SourceArgument,
    query: str, /, *,
    search_behaviors: _interfaces.SearchBehaviors = _search_behaviors_default,
    filters: __.cabc.Mapping[ str, __.typx.Any ] = _filters_default,
    include_snippets: bool = True,
    results_max: int = 10,
) -> __.typx.Annotated[
    dict[ str, __.typx.Any ],
    __.ddoc.Fname( 'content query return' ) ]:
    ''' Searches documentation content with relevance ranking. '''
    processor = await _determine_processor_optimal( source )
    filtered_objects = await processor.extract_filtered_inventory(
        source, filters = filters,
        details = _interfaces.InventoryQueryDetails.Name )
    search_results = _search.filter_by_name(
        filtered_objects, query,
        match_mode = search_behaviors.match_mode,
        fuzzy_threshold = search_behaviors.fuzzy_threshold )
    candidate_objects = [
        result.object for result in search_results[ : results_max * 3 ] ]
    if not candidate_objects:
        filter_metadata: dict[ str, __.typx.Any ] = { }
        _populate_filter_metadata( filter_metadata, search_behaviors, filters )
        return {
            'source': source,
            'query': query,
            'search_metadata': {
                'result_count': 0,
                'max_results': results_max,
                'filters': filter_metadata,
            },
            'documents': [ ],
        }
    raw_results = await processor.extract_documentation_for_objects(
        source, candidate_objects, include_snippets = include_snippets )
    sorted_results = sorted(
        raw_results,
        key = lambda x: x.get( 'relevance_score', 0.0 ),
        reverse = True )
    limited_results = list( sorted_results[ : results_max ] )
    filter_metadata: dict[ str, __.typx.Any ] = { }
    _populate_filter_metadata( filter_metadata, search_behaviors, filters )
    search_metadata: dict[ str, __.typx.Any ] = {
        'result_count': len( limited_results ),
        'max_results': results_max,
        'filters': filter_metadata,
    }
    documents = [
        {
            'name': result[ 'object_name' ],
            'type': result[ 'object_type' ],
            'domain': result[ 'domain' ],
            'priority': result[ 'priority' ],
            'url': result[ 'url' ],
            'signature': result[ 'signature' ],
            'description': result[ 'description' ],
            'content_snippet': result[ 'content_snippet' ],
            'relevance_score': result[ 'relevance_score' ],
            'match_reasons': result[ 'match_reasons' ]
        }
        for result in limited_results ]
    return {
        'source': source,
        'query': query,
        'search_metadata': search_metadata,
        'documents': documents,
    }


async def query_inventory(  # noqa: PLR0913
    source: SourceArgument,
    query: str, /, *,
    search_behaviors: _interfaces.SearchBehaviors = _search_behaviors_default,
    filters: __.cabc.Mapping[ str, __.typx.Any ] = _filters_default,
    details: _interfaces.InventoryQueryDetails = (
        _interfaces.InventoryQueryDetails.Documentation ),
    results_max: int = 5,
) -> __.typx.Annotated[
    dict[ str, __.typx.Any ], __.ddoc.Fname( 'inventory query return' ) ]:
    ''' Searches object inventory by name.

        Returns configurable detail levels. Always includes object names
        plus requested detail flags (signatures, summaries, documentation).
    '''
    processor = await _determine_processor_optimal( source )
    filtered_objects = await processor.extract_filtered_inventory(
        source, filters = filters, details = details )
    search_results = _search.filter_by_name(
        filtered_objects, query,
        match_mode = search_behaviors.match_mode,
        fuzzy_threshold = search_behaviors.fuzzy_threshold )
    selected_objects = [
        result.object for result in search_results[ : results_max ] ]
    documents = [
        {
            'name': obj[ 'name' ],
            'role': obj[ 'role' ],
            'domain': obj.get( 'domain', '' ),
            'uri': obj[ 'uri' ],
            'dispname': obj[ 'dispname' ],
        }
        for obj in selected_objects ]
    filter_metadata: dict[ str, __.typx.Any ] = { }
    _populate_filter_metadata( filter_metadata, search_behaviors, filters )
    search_metadata: dict[ str, __.typx.Any ] = {
        'object_count': len( selected_objects ),
        'max_objects': results_max,
        'total_matches': len( filtered_objects ),
        'filters': filter_metadata,
    }
    return {
        'project': (
            filtered_objects[ 0 ].get( '_inventory_project', 'Unknown' )
            if filtered_objects else 'Unknown' ),
        'version': (
            filtered_objects[ 0 ].get( '_inventory_version', 'Unknown' )
            if filtered_objects else 'Unknown' ),
        'query': query,
        'documents': documents,
        'search_metadata': search_metadata,
        'object_count': len( selected_objects ),
        'source': source,
    }


async def summarize_inventory(
    source: SourceArgument,
    query: str = '', /, *,
    search_behaviors: _interfaces.SearchBehaviors = _search_behaviors_default,
    filters: __.cabc.Mapping[ str, __.typx.Any ] = _filters_default,
) -> __.typx.Annotated[
    str, __.ddoc.Fname( 'inventory summary return' ) ]:
    ''' Provides human-readable summary of inventory. '''
    inventory_result = await query_inventory(
        source, query, search_behaviors = search_behaviors, filters = filters,
        results_max = 1000,  # Large number to get all matches
        details = _interfaces.InventoryQueryDetails.Name )
    inventory_data: dict[ str, __.typx.Any ] = {
        'project': inventory_result[ 'project' ],
        'version': inventory_result[ 'version' ],
        'object_count': inventory_result[ 'search_metadata' ][
            'total_matches' ],
        'objects': _group_documents_by_domain(
            inventory_result[ 'documents' ] ),
        'filters': inventory_result[ 'search_metadata' ][ 'filters' ],
    }
    return _format_inventory_summary( inventory_data )


async def survey_processors(
    name: __.typx.Optional[ str ] = None
) -> dict[ str, __.typx.Any ]:
    ''' Lists processor capabilities, optionally filtered to one processor. '''
    if name is not None and name not in _xtnsapi.processors:
        raise _exceptions.ProcessorInavailability( name )
    processors_capabilities = {
        name_: _serialize_dataclass( processor.capabilities )
        for name_, processor in _xtnsapi.processors.items( )
        if name is None or name_ == name }
    return { 'processors': processors_capabilities }


async def _add_documentation_to_results(
    source: str,
    selected_objects: list[ dict[ str, __.typx.Any ] ],
    result: dict[ str, __.typx.Any ],
) -> None:
    ''' Extracts documentation for objects and adds to results. '''
    detection = await _detection.determine_processor_optimal( source )
    if __.is_absent( detection ):
        raise _exceptions.ProcessorInavailability( source )
    processor = detection.processor
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


def _construct_explore_result_structure(  # noqa: PLR0913
    inventory_data: dict[ str, __.typx.Any ],
    query: str,
    selected_objects: list[ dict[ str, __.typx.Any ] ],
    results_max: int,
    search_behaviors: _interfaces.SearchBehaviors,
    filters: __.cabc.Mapping[ str, __.typx.Any ],
) -> dict[ str, __.typx.Any ]:
    ''' Builds the base result structure with metadata. '''
    filter_metadata: dict[ str, __.typx.Any ] = { }
    _populate_filter_metadata( filter_metadata, search_behaviors, filters )
    search_metadata: dict[ str, __.typx.Any ] = {
        'object_count': len( selected_objects ),
        'max_objects': results_max,
        'total_matches': inventory_data[ 'object_count' ],
        'filters': filter_metadata,
    }
    result: dict[ str, __.typx.Any ] = {
        'project': inventory_data[ 'project' ],
        'version': inventory_data[ 'version' ],
        'query': query,
        'search_metadata': search_metadata,
        'documents': [ ],
    }
    return result


def _construct_query_result_structure(  # noqa: PLR0913
    source: str,
    query: str,
    raw_results: list[ __.cabc.Mapping[ str, __.typx.Any ] ],
    results_max: int,
    search_behaviors: _interfaces.SearchBehaviors,
    filters: __.cabc.Mapping[ str, __.typx.Any ],
) -> dict[ str, __.typx.Any ]:
    ''' Builds query result structure in explore format. '''
    filter_metadata: dict[ str, __.typx.Any ] = { }
    _populate_filter_metadata( filter_metadata, search_behaviors, filters )
    search_metadata: dict[ str, __.typx.Any ] = {
        'result_count': len( raw_results ),
        'max_results': results_max,
        'filters': filter_metadata,
    }
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
        'documents': documents,
    }
    return result


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
        'dispname': obj[ 'dispname' ],
    }
    if 'fuzzy_score' in obj:
        document[ 'fuzzy_score' ] = obj[ 'fuzzy_score' ]
    return document


async def _determine_processor_optimal(
    source: SourceArgument
) -> _interfaces.Processor:
    detection = await _detection.determine_processor_optimal( source )
    if __.is_absent( detection ):
        raise _exceptions.ProcessorInavailability( source )
    return detection.processor


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


def _serialize_dataclass( obj: __.typx.Any ) -> __.typx.Any:
    ''' Recursively serializes dataclass objects to JSON-compatible format. '''
    if __.dcls.is_dataclass( obj ):
        result = { }  # type: ignore[var-annotated]
        for field in __.dcls.fields( obj ):
            if field.name.startswith( '_' ):
                continue  # Skip private/internal fields
            value = getattr( obj, field.name )
            result[ field.name ] = _serialize_dataclass( value )
        return result  # type: ignore[return-value]
    if isinstance( obj, list ):
        return [ _serialize_dataclass( item ) for item in obj ]  # type: ignore[misc]
    if isinstance( obj, ( frozenset, set ) ):
        return list( obj )  # type: ignore[arg-type]
    if obj is None or isinstance( obj, ( str, int, float, bool ) ):
        return obj
    # For other objects, try to convert to string
    return str( obj )


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


def _populate_filter_metadata(
    metadata: dict[ str, __.typx.Any ],
    search_behaviors: _interfaces.SearchBehaviors,
    filters: __.cabc.Mapping[ str, __.typx.Any ]
) -> None:
    ''' Populates filter metadata dictionary with non-empty filters. '''
    metadata.update( {
        key: value for key, value in filters.items( ) if value } )
    metadata[ 'match_mode' ] = search_behaviors.match_mode.value
    if search_behaviors.match_mode == _interfaces.MatchMode.Fuzzy:
        metadata[ 'fuzzy_threshold' ] = search_behaviors.fuzzy_threshold


def _select_top_objects(
    inventory_data: dict[ str, __.typx.Any ],
    results_max: int
) -> list[ dict[ str, __.typx.Any ] ]:
    ''' Selects top objects from inventory, sorted by fuzzy score. '''
    all_objects: list[ dict[ str, __.typx.Any ] ] = [ ]
    for domain_objects in inventory_data[ 'objects' ].values( ):
        all_objects.extend( domain_objects )
    all_objects.sort(
        key = lambda obj: obj.get( 'fuzzy_score', 0 ),
        reverse = True )
    return all_objects[ : results_max ]
