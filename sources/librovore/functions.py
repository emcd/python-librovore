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
from . import processors as _processors
from . import results as _results
from . import search as _search
from . import state as _state



_SUCCESS_RATE_MINIMUM = 0.1


LocationArgument: __.typx.TypeAlias = __.typx.Annotated[
    str, __.ddoc.Fname( 'location argument' ) ]


_search_behaviors_default = _interfaces.SearchBehaviors( )
_filters_default = __.immut.Dictionary[ str, __.typx.Any ]( )


async def detect(
    auxdata: _state.Globals,
    location: LocationArgument, /,
    genus: _interfaces.ProcessorGenera,
    processor_name: __.Absential[ str ] = __.absent,
) -> _results.DetectionsResult:
    ''' Detects relevant processors of particular genus for location. '''
    location = _normalize_location( location )
    start_time = __.time.perf_counter( )
    detections, detection_optimal = (
        await _detection.access_detections(
            auxdata, location, genus = genus ) )
    end_time = __.time.perf_counter( )
    detection_time_ms = int( ( end_time - start_time ) * 1000 )
    if __.is_absent( detection_optimal ):
        genus_name = (
            genus.name.lower( ) if hasattr( genus, 'name' ) else str( genus ) )
        raise _exceptions.ProcessorInavailability(
            location,
            genus = genus_name )
    # Convert detections mapping to tuple of results.Detection objects
    detections_tuple = tuple(
        _results.Detection(
            processor_name = detection.processor.name,
            confidence = detection.confidence,
            processor_type = genus.value,
            detection_metadata = __.immut.Dictionary( ),
        )
        for detection in detections.values( )
    )
    # Convert detection_optimal to results.Detection
    detection_optimal_result = _results.Detection(
        processor_name = detection_optimal.processor.name,
        confidence = detection_optimal.confidence,
        processor_type = genus.value,
        detection_metadata = __.immut.Dictionary( ),
    )
    return _results.DetectionsResult(
        source = location,
        detections = detections_tuple,
        detection_optimal = detection_optimal_result,
        time_detection_ms = detection_time_ms )


async def query_content(  # noqa: PLR0913
    auxdata: _state.Globals,
    location: LocationArgument,
    term: str, /, *,
    processor_name: __.Absential[ str ] = __.absent,
    search_behaviors: _interfaces.SearchBehaviors = _search_behaviors_default,
    filters: __.cabc.Mapping[ str, __.typx.Any ] = _filters_default,
    content_id: __.Absential[ str ] = __.absent,
    results_max: int = 10,
    lines_max: __.typx.Optional[ int ] = None,
) -> _results.ContentQueryResult:
    ''' Searches documentation content with relevance ranking. '''
    location = _normalize_location( location )
    start_time = __.time.perf_counter( )
    resolved_location = _detection.resolve_source_url( location )
    objects = await _collect_inventory_objects_multi_source(
        auxdata, location, resolved_location, processor_name, filters )
    if not __.is_absent( content_id ):
        candidates = _process_content_id_filter(
            content_id, resolved_location, objects )
    else:
        results = _search.filter_by_name(
            objects, term, search_behaviors = search_behaviors )
        candidates = [
            result.inventory_object
            for result in results[ : results_max * 3 ] ]
    locations = await _create_inventory_location_info(
        auxdata, location, resolved_location, len( objects ) )
    if not candidates:
        end_time = __.time.perf_counter( )
        search_time_ms = int( ( end_time - start_time ) * 1000 )
        return _results.ContentQueryResult(
            location = resolved_location,
            term = term,
            documents = tuple( ),
            search_metadata = _results.SearchMetadata(
                results_count = 0,
                results_max = results_max,
                search_time_ms = search_time_ms ),
            inventory_locations = locations )
    sdetection = await _detection.detect_structure(
        auxdata, resolved_location, processor_name = processor_name )
    structure_capabilities = sdetection.get_capabilities( )
    compatible_candidates = _filter_objects_by_structure_capabilities(
        candidates[ : results_max ], structure_capabilities )
    if not compatible_candidates:
        end_time = __.time.perf_counter( )
        search_time_ms = int( ( end_time - start_time ) * 1000 )
        return _results.ContentQueryResult(
            location = resolved_location,
            term = term,
            documents = ( ),
            search_metadata = _results.SearchMetadata(
                results_count = 0,
                results_max = results_max,
                search_time_ms = search_time_ms ),
            inventory_locations = locations )
    documents = await sdetection.extract_contents(
        auxdata, resolved_location, compatible_candidates )
    end_time = __.time.perf_counter( )
    search_time_ms = int( ( end_time - start_time ) * 1000 )
    return _results.ContentQueryResult(
        location = resolved_location,
        term = term,
        documents = tuple( documents ),
        search_metadata = _results.SearchMetadata(
            results_count = len( documents ),
            results_max = results_max,
            matches_total = len( candidates ),
            search_time_ms = search_time_ms ),
        inventory_locations = locations )


async def query_inventory(  # noqa: PLR0913
    auxdata: _state.Globals,
    location: LocationArgument,
    term: str, /, *,
    processor_name: __.Absential[ str ] = __.absent,
    search_behaviors: _interfaces.SearchBehaviors = _search_behaviors_default,
    filters: __.cabc.Mapping[ str, __.typx.Any ] = _filters_default,
    results_max: int = 5,
) -> _results.InventoryQueryResult:
    ''' Searches object inventory by name.

        Returns configurable detail levels. Always includes object names
        plus requested detail flags (signatures, summaries, documentation).
    '''
    location = _normalize_location( location )
    start_time = __.time.perf_counter( )
    detection = await _detection.detect_inventory(
        auxdata, location, processor_name = processor_name )
    # Resolve URL after detection to get working URL if redirect exists
    resolved_location = _detection.resolve_source_url( location )
    objects = await detection.filter_inventory(
        auxdata, resolved_location, filters = filters )
    results = _search.filter_by_name(
        objects, term, search_behaviors = search_behaviors )
    selections = [
        result.inventory_object for result in results[ : results_max ] ]
    end_time = __.time.perf_counter( )
    search_time_ms = int( ( end_time - start_time ) * 1000 )
    return _results.InventoryQueryResult(
        location = resolved_location,
        term = term,
        objects = tuple( selections ),
        search_metadata = _results.SearchMetadata(
            results_count = len( selections ),
            results_max = results_max,
            matches_total = len( objects ),
            search_time_ms = search_time_ms ),
        inventory_locations = tuple( [
            _results.InventoryLocationInfo(
                inventory_type = detection.processor.name,
                location_url = resolved_location,
                processor_name = detection.processor.name,
                confidence = detection.confidence,
                object_count = len( objects ) ) ] ) )



async def survey_processors(
    auxdata: _state.Globals, /,
    genus: _interfaces.ProcessorGenera,
    name: __.typx.Optional[ str ] = None,
) -> _results.ProcessorsSurveyResult:
    ''' Lists processor capabilities for specified genus, filtered by name. '''
    start_time = __.time.perf_counter( )
    match genus:
        case _interfaces.ProcessorGenera.Inventory:
            processors = dict( _processors.inventory_processors )
        case _interfaces.ProcessorGenera.Structure:
            processors = dict( _processors.structure_processors )
    if name is not None and name not in processors:
        raise _exceptions.ProcessorInavailability(
            name,
            genus = genus.value )
    processor_infos: list[ _results.ProcessorInfo ] = [ ]
    for name_, processor in processors.items( ):
        if name is None or name_ == name:
            processor_info = _results.ProcessorInfo(
                processor_name = name_,
                processor_type = genus.value,
                capabilities = processor.capabilities,
            )
            processor_infos.append( processor_info )
    end_time = __.time.perf_counter( )
    survey_time_ms = int( ( end_time - start_time ) * 1000 )
    return _results.ProcessorsSurveyResult(
        genus = genus,
        filter_name = name,
        processors = tuple( processor_infos ),
        survey_time_ms = survey_time_ms,
    )


async def _collect_inventory_objects_multi_source(
    auxdata: _state.Globals,
    location: str,
    resolved_location: str,
    processor_name: __.Absential[ str ],
    filters: __.cabc.Mapping[ str, __.typx.Any ],
) -> tuple[ _results.InventoryObject, ... ]:
    ''' Collects inventory objects using multi-source coordination.

        Optimized to pre-filter inventory sources by structure processor
        compatibility before making network requests.
    '''
    try:
        inventory_detections = (
            await _detection.collect_filter_inventories( auxdata, location ) )
    except Exception:
        idetection = await _detection.detect_inventory(
            auxdata, location, processor_name = processor_name )
        return await idetection.filter_inventory(
            auxdata, resolved_location, filters = filters )
    if not inventory_detections: return ( )
    sdetection = await _detection.detect_structure(
        auxdata, resolved_location, processor_name = processor_name )
    structure_capabilities = sdetection.get_capabilities( )
    compatible_detections = _filter_detections_by_structure_capabilities(
        inventory_detections, structure_capabilities )
    if not compatible_detections: return ( )
    return await _merge_primary_supplementary(
        auxdata, compatible_detections, location, filters = filters )


async def _create_inventory_location_info(
    auxdata: _state.Globals,
    location: str,
    resolved_location: str,
    object_count: int,
) -> tuple[ _results.InventoryLocationInfo, ... ]:
    ''' Creates inventory location info for multi-source results. '''
    try:
        inventory_detections = (
            await _detection.collect_filter_inventories(
                auxdata, location ) )
    except Exception:
        idetection = await _detection.detect_inventory( auxdata, location )
        return tuple( [ _results.InventoryLocationInfo(
            inventory_type = idetection.processor.name,
            location_url = resolved_location,
            processor_name = idetection.processor.name,
            confidence = idetection.confidence,
            object_count = object_count ) ] )
    if not inventory_detections:
        return ( )
    primary_detection = _select_primary_detection( inventory_detections )
    return tuple( [ _results.InventoryLocationInfo(
        inventory_type = primary_detection.processor.name,
        location_url = resolved_location,
        processor_name = primary_detection.processor.name,
        confidence = primary_detection.confidence,
        object_count = object_count ) ] )


def _filter_detections_by_structure_capabilities(
    inventory_detections: __.cabc.Mapping[
        str, _processors.InventoryDetection ],
    structure_capabilities: _interfaces.StructureProcessorCapabilities,
) -> __.immut.Dictionary[ str, _processors.InventoryDetection ]:
    ''' Filters inventory detections by structure processor capabilities.

        Pre-filters inventory sources by compatibility before object collection
        to avoid unnecessary network requests and processing overhead.
    '''
    compatible_detections = {
        processor_name: detection
        for processor_name, detection in inventory_detections.items( )
        if structure_capabilities.supports_inventory_type(
            detection.processor.name ) }
    return __.immut.Dictionary( compatible_detections )


def _filter_objects_by_structure_capabilities(
    candidates: __.cabc.Sequence[ _results.InventoryObject ],
    structure_capabilities: _interfaces.StructureProcessorCapabilities,
) -> tuple[ _results.InventoryObject, ... ]:
    ''' Filters inventory objects by structure processor capabilities. '''
    compatible_objects = [
        obj for obj in candidates
        if structure_capabilities.supports_inventory_type(
            obj.inventory_type ) ]
    return tuple( compatible_objects )


async def _merge_primary_supplementary(
    auxdata: _state.Globals,
    inventory_detections: __.cabc.Mapping[
        str, _processors.InventoryDetection ],
    location: str,
    filters: __.cabc.Mapping[ str, __.typx.Any ] = _filters_default,
) -> tuple[ _results.InventoryObject, ... ]:
    ''' Merges inventory objects using PRIMARY_SUPPLEMENTARY strategy.

        Uses highest-confidence detection as primary source, adds supplementary
        objects from other qualified sources with preserved source attribution.
        No deduplication - complementary metadata is valuable.

        Note: inventory_detections should already be pre-filtered for
        compatibility with the structure processor to avoid unnecessary
        network requests.
    '''
    if not inventory_detections: return ( )
    objects_aggregate: list[ _results.InventoryObject ] = [ ]
    location_ = _detection.resolve_source_url( location )
    for detection in inventory_detections.values( ):
        objects = await detection.filter_inventory(
            auxdata, location_, filters = filters )
        objects_aggregate.extend( objects )
    return tuple( objects_aggregate )


def _normalize_location( location: str ) -> str:
    ''' Normalizes location URL by stripping index.html. '''
    if location.endswith( '/' ): return location[ : -1 ]
    if location.endswith( '/index.html' ): return location[ : -11 ]
    return location


def _process_content_id_filter(
    content_id: str,
    location: str,
    objects: __.cabc.Sequence[ _results.InventoryObject ],
) -> tuple[ _results.InventoryObject, ... ]:
    ''' Processes content ID for browse-then-extract workflow filtering. '''
    try: location_, name = _results.parse_content_id( content_id )
    except ValueError as exc:
        raise _exceptions.ContentIdInvalidity(
            content_id, f"Parsing failed: {exc}" ) from exc
    if location_ != location:
        raise _exceptions.ContentIdLocationMismatch( location_, location )
    objects_ = [ obj for obj in objects if obj.name == name ]
    if not objects_:
        raise _exceptions.ContentIdObjectAbsence( name, location )
    return tuple( objects_[ :1 ] )


def _select_primary_detection(
    inventory_detections: __.cabc.Mapping[
        str, _processors.InventoryDetection ],
) -> _processors.InventoryDetection:
    ''' Selects primary detection with highest confidence. '''
    detections_list = list( inventory_detections.values( ) )
    detections_list.sort( key = lambda d: -d.confidence )
    return detections_list[ 0 ]
