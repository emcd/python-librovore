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


''' Documentation source detection system for plugin architecture. '''


from . import __
from . import exceptions as _exceptions
from . import interfaces as _interfaces
from . import processors as _processors
from . import state as _state
from . import urlpatterns as _urlpatterns
from . import urls as _urls


CONFIDENCE_THRESHOLD_MINIMUM = 0.5


class DetectionsCacheEntry( __.immut.DataclassObject ):
    ''' Cache entry for source detection results. '''

    detections: __.cabc.Mapping[ str, _processors.Detection ]
    timestamp: float
    ttl: int

    @property
    def detection_optimal( self ) -> __.Absential[ _processors.Detection ]:
        ''' Returns the detection with highest confidence. '''
        if not self.detections: return __.absent
        optimum = max(
            self.detections.values( ), key=lambda x: x.confidence )
        return (
            optimum
            if optimum.confidence >= CONFIDENCE_THRESHOLD_MINIMUM
            else __.absent )

    def invalid( self, current_time: float ) -> bool:
        ''' Checks if cache entry has expired. '''
        return current_time - self.timestamp > self.ttl


class DetectionsCache( __.immut.DataclassObject ):
    ''' Cache for source detection results with TTL support. '''

    ttl: int = 3600
    _entries: dict[ str, DetectionsCacheEntry ] = (
        __.dcls.field( default_factory = dict[ str, DetectionsCacheEntry ] ) )

    def access_detections(
        self, source: str
    ) -> __.Absential[ _processors.DetectionsByProcessor ]:
        ''' Returns all detections for source, if unexpired. '''
        if source not in self._entries: return __.absent
        entry = self._entries[ source ]
        current_time = __.time.time( )
        if entry.invalid( current_time ):
            del self._entries[ source ]
            return __.absent
        return entry.detections

    def access_detection_optimal(
        self, source: str
    ) -> __.Absential[ _processors.Detection ]:
        ''' Returns the best detection for source, if unexpired. '''
        if source not in self._entries: return __.absent
        entry = self._entries[ source ]
        current_time = __.time.time( )
        if entry.invalid( current_time ):
            del self._entries[ source ]
            return __.absent
        return entry.detection_optimal

    def add_entry(
        self, source: str, detections: _processors.DetectionsByProcessor
    ) -> __.typx.Self:
        ''' Adds or updates cache entry with fresh results. '''
        self._entries[ source ] = DetectionsCacheEntry(
            detections = detections,
            timestamp = __.time.time( ),
            ttl = self.ttl )
        return self

    def clear( self ) -> __.typx.Self:
        ''' Clears all cached entries. '''
        self._entries.clear( )
        return self



_inventory_detections_cache = DetectionsCache( )
_structure_detections_cache = DetectionsCache( )

_url_redirects_cache: dict[ str, str ] = { }


def resolve_source_url( url: str ) -> str:
    ''' Resolves source URL through redirect cache, returns working URL. '''
    return _url_redirects_cache.get( url, url )


async def access_detections(
    auxdata: _state.Globals,
    source: str, /, *,
    genus: _interfaces.ProcessorGenera
) -> tuple[
    _processors.DetectionsByProcessor,
    __.Absential[ _processors.Detection ]
]:
    ''' Accesses detections via appropriate cache. '''
    source_ = _url_redirects_cache.get( source, source )
    match genus:
        case _interfaces.ProcessorGenera.Inventory:
            cache = _inventory_detections_cache
            processors = _processors.inventory_processors
        case _interfaces.ProcessorGenera.Structure:
            cache = _structure_detections_cache
            processors = _processors.structure_processors
    return await access_detections_ll(
        auxdata, source_, cache = cache, processors = processors )


async def access_detections_ll(
    auxdata: _state.Globals,
    source: str, /, *,
    cache: DetectionsCache,
    processors: __.cabc.Mapping[ str, _processors.Processor ],
) -> tuple[
    _processors.DetectionsByProcessor,
    __.Absential[ _processors.Detection ]
]:
    ''' Accesses detections via appropriate cache.

        Detections are performed to fill cache, if necessary.

        Low-level function accepting arbitrary cache and processors list.
    '''
    detections = cache.access_detections( source )
    if __.is_absent( detections ):
        await _execute_processors_and_cache(
            auxdata, source, cache, processors )
        detections = cache.access_detections( source )
        if __.is_absent( detections ):
            detections = __.immut.Dictionary[
                str, _processors.Detection ]( )
    optimum = cache.access_detection_optimal( source )
    return detections, optimum


async def collect_filter_inventories(
    auxdata: _state.Globals,
    location: str, /, *,
    confidence_limit: float = 0.5,
) -> __.immut.Dictionary[ str, _processors.InventoryDetection ]:
    ''' Collects all inventory sources above confidence threshold.

        Returns dictionary mapping processor names to their detections
        for multi-source inventory coordination.
    '''
    location_ = _url_redirects_cache.get( location, location )
    detections, _ = await access_detections(
        auxdata, location_, genus = _interfaces.ProcessorGenera.Inventory )
    detections_ = {
        processor_name: __.typx.cast(
            _processors.InventoryDetection, detection )
        for processor_name, detection in detections.items( )
        if detection.confidence >= confidence_limit }
    return __.immut.Dictionary( detections_ )


async def detect(
    auxdata: _state.Globals,
    source: str, /,
    genus: _interfaces.ProcessorGenera, *,
    processor_name: __.Absential[ str ] = __.absent,
) -> _processors.Detection:
    ''' Detects processors for source through cache system. '''
    source_ = _url_redirects_cache.get( source, source )
    match genus:
        case _interfaces.ProcessorGenera.Inventory:
            cache = _inventory_detections_cache
            class_name = 'inventory'
            processors = _processors.inventory_processors
        case _interfaces.ProcessorGenera.Structure:
            cache = _structure_detections_cache
            class_name = 'structure'
            processors = _processors.structure_processors
    if not __.is_absent( processor_name ):
        if processor_name not in processors:
            raise _exceptions.ProcessorInavailability( processor_name )
        processor = processors[ processor_name ]
        return await processor.detect( auxdata, source_ )
    detection = await determine_detection_optimal_ll(
        auxdata, source_, cache = cache, processors = processors )
    if __.is_absent( detection ):
        raise _exceptions.ProcessorInavailability( class_name )
    return detection


async def detect_inventory(
    auxdata: _state.Globals,
    source: str, /, *,
    processor_name: __.Absential[ str ] = __.absent,
) -> _processors.InventoryDetection:
    ''' Detects inventory processors for source through cache system. '''
    detection = await detect(
        auxdata, source,
        genus = _interfaces.ProcessorGenera.Inventory,
        processor_name = processor_name )
    return __.typx.cast( _processors.InventoryDetection, detection )


async def detect_structure(
    auxdata: _state.Globals,
    source: str, /, *,
    processor_name: __.Absential[ str ] = __.absent,
) -> _processors.StructureDetection:
    ''' Detects structure processors for source through cache system. '''
    detection = await detect(
        auxdata, source,
        genus = _interfaces.ProcessorGenera.Structure,
        processor_name = processor_name )
    return __.typx.cast( _processors.StructureDetection, detection )


async def determine_detection_optimal_ll(
    auxdata: _state.Globals,
    source: str, /, *,
    cache: DetectionsCache,
    processors: __.cabc.Mapping[ str, _processors.Processor ],
) -> __.Absential[ _processors.Detection ]:
    ''' Determines which processor can best handle the source.

        Low-level function accepting arbitrary cache and processors list.
    '''
    detection = cache.access_detection_optimal( source )
    if not __.is_absent( detection ): return detection
    detections = await _execute_processors_with_patterns(
        auxdata, source, processors )
    cache.add_entry( source, detections )
    return _select_detection_optimal( detections, processors )


async def _execute_processors(
    auxdata: _state.Globals,
    source: str,
    processors: __.cabc.Mapping[ str, _processors.Processor ],
) -> dict[ str, _processors.Detection ]:
    ''' Runs all processors on the source. '''
    results: dict[ str, _processors.Detection ] = { }
    access_failures: list[ _exceptions.RobotsTxtAccessFailure ] = [ ]
    # TODO: Parallel async fanout.
    for processor in processors.values( ):
        try: detection = await processor.detect( auxdata, source )
        except _exceptions.RobotsTxtAccessFailure as exc:  # noqa: PERF203
            access_failures.append( exc )
            continue
        except Exception:  # noqa: S112
            continue
        else: results[ processor.name ] = detection
    # If all processors failed due to robots.txt access issues, raise error
    if not results and access_failures:
        raise access_failures[ 0 ] from None
    return results


async def _execute_processors_with_patterns(
    auxdata: _state.Globals,
    source: str,
    processors: __.cabc.Mapping[ str, _processors.Processor ],
) -> dict[ str, _processors.Detection ]:
    ''' Runs processors with URL pattern extension fallback. '''
    results = await _execute_processors( auxdata, source, processors )
    if any( detection.confidence >= CONFIDENCE_THRESHOLD_MINIMUM
           for detection in results.values( ) ):
        return results
    base_url = _urls.normalize_base_url( source )
    working_url = await _urlpatterns.probe_url_patterns(
        auxdata, base_url, '/objects.inv' )
    if not __.is_absent( working_url ):
        working_source = working_url.geturl( )
        pattern_results = await _execute_processors(
            auxdata, working_source, processors )
        if any( detection.confidence >= CONFIDENCE_THRESHOLD_MINIMUM
               for detection in pattern_results.values( ) ):
            _url_redirects_cache[ source ] = working_source
            return pattern_results
    return results


async def _execute_processors_and_cache(
    auxdata: _state.Globals,
    source: str,
    cache: DetectionsCache,
    processors: __.cabc.Mapping[ str, _processors.Processor ],
) -> None:
    ''' Executes processors with URL pattern extension and caches. '''
    detections = await _execute_processors_with_patterns(
        auxdata, source, processors )
    cache.add_entry( source, detections )


def _select_detection_optimal(
    detections: _processors.DetectionsByProcessor,
    processors: __.cabc.Mapping[ str, _processors.Processor ]
) -> __.Absential[ _processors.Detection ]:
    ''' Selects best processor based on confidence and registration order. '''
    if not detections: return __.absent
    detections_ = [
        result for result in detections.values( )
        if result.confidence >= CONFIDENCE_THRESHOLD_MINIMUM ]
    if not detections_: return __.absent
    processor_names = list( processors.keys( ) )
    def sort_key( result: _processors.Detection ) -> tuple[ float, int ]:
        confidence = result.confidence
        processor_name = result.processor.name
        registration_order = processor_names.index( processor_name )
        return ( -confidence, registration_order )
    detections_.sort( key = sort_key )
    return detections_[ 0 ]
