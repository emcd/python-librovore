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
from . import xtnsapi as _xtnsapi


DetectionsByProcessor: __.typx.TypeAlias = (
    __.cabc.Mapping[ str, _interfaces.BaseDetection ] )


class DetectionsCacheEntry( __.immut.DataclassObject ):
    ''' Cache entry for source detection results. '''

    detections: __.cabc.Mapping[ str, _interfaces.BaseDetection ]
    timestamp: float
    ttl: int

    @property
    def best_detection( self ) -> __.Absential[ _interfaces.BaseDetection ]:
        ''' Returns the detection with highest confidence. '''
        if not self.detections: return __.absent
        best_result = max(
            self.detections.values( ),
            key=lambda x: x.confidence )
        return (
            best_result if best_result.confidence > 0.0 else __.absent )

    def is_expired( self, current_time: float ) -> bool:
        ''' Checks if cache entry has expired. '''
        return current_time - self.timestamp > self.ttl


class DetectionsCache( __.immut.DataclassObject ):
    ''' Cache for source detection results with TTL support. '''

    ttl: int = 3600
    _entries: dict[ str, DetectionsCacheEntry ] = (
        __.dcls.field( default_factory = dict[ str, DetectionsCacheEntry ] ) )

    def access_entry(
        self, source: str
    ) -> __.Absential[ DetectionsByProcessor ]:
        ''' Returns all detections for source, if unexpired. '''
        if source not in self._entries: return __.absent
        cache_entry = self._entries[ source ]
        current_time = __.time.time( )
        if cache_entry.is_expired( current_time ):
            del self._entries[ source ]
            return __.absent
        return cache_entry.detections

    def access_best_detection(
        self, source: str
    ) -> __.Absential[ _interfaces.BaseDetection ]:
        ''' Returns the best detection for source, if unexpired. '''
        if source not in self._entries: return __.absent
        cache_entry = self._entries[ source ]
        current_time = __.time.time( )
        if cache_entry.is_expired( current_time ):
            del self._entries[ source ]
            return __.absent
        return cache_entry.best_detection

    def add_entry(
        self, source: str, detections: DetectionsByProcessor
    ) -> __.typx.Self:
        ''' Adds or updates cache entry with fresh results. '''
        self._entries[ source ] = DetectionsCacheEntry(
            detections = detections,
            timestamp = __.time.time( ),
            ttl = self.ttl,
        )
        return self

    def clear( self ) -> __.typx.Self:
        ''' Clears all cached entries. '''
        self._entries.clear( )
        return self

    def remove_entry(
        self, source: str
    ) -> __.Absential[ DetectionsByProcessor ]:
        ''' Removes specific source from cache, if present. '''
        entry = self._entries.pop( source, None )
        if entry: return entry.detections
        return __.absent


# Separate caches for each processor type
_inventory_detections_cache = DetectionsCache( )
_structure_detections_cache = DetectionsCache( )


async def access_detections(
    source: str, /, *,
    cache: DetectionsCache,
    processors: __.cabc.Mapping[ str, _interfaces.Processor ],
) -> tuple[ DetectionsByProcessor, __.Absential[ _interfaces.BaseDetection ] ]:
    ''' Gets cached detections, triggering fresh detection if needed. '''
    detections = cache.access_entry( source )
    if __.is_absent( detections ):
        await _execute_processors_and_cache( source, cache, processors )
        detections = cache.access_entry( source )
        # After fresh execution, detections should never be absent
        if __.is_absent( detections ):
            # Fallback: create empty detections mapping
            detections = __.immut.Dictionary[
                str, _interfaces.BaseDetection ]( )
    best_detection = cache.access_best_detection( source )
    return detections, best_detection


async def determine_processor_optimal(
    source: str, /, *,
    cache: DetectionsCache,
    processors: __.cabc.Mapping[ str, _interfaces.Processor ],
) -> __.Absential[ _interfaces.BaseDetection ]:
    ''' Determines which processor can best handle the source. '''
    detection = cache.access_best_detection( source )
    if not __.is_absent( detection ): return detection
    detections = await _execute_processors( source, processors )
    cache.add_entry( source, detections )
    return _select_processor_optimal( detections, processors )


async def detect_inventory(
    source: str, /, *,
    processor_name: __.Absential[ str ] = __.absent,
) -> _interfaces.InventoryDetection:
    ''' Detects inventory processors for source through cache system. '''
    processors = _xtnsapi.inventory_processors
    if not __.is_absent( processor_name ):
        if processor_name not in processors:
            raise _exceptions.ProcessorInavailability( processor_name )
        processor = processors[ processor_name ]
        detection = await processor.detect( source )
        return __.typx.cast( _interfaces.InventoryDetection, detection )
    # Use inventory-specific cache and processors
    detection = await determine_processor_optimal(
        source, cache = _inventory_detections_cache, processors = processors )
    if __.is_absent( detection ):
        raise _exceptions.ProcessorInavailability( 'inventory' )
    return __.typx.cast( _interfaces.InventoryDetection, detection )


async def detect_structure(
    source: str, /, *,
    processor_name: __.Absential[ str ] = __.absent,
) -> _interfaces.StructureDetection:
    ''' Detects structure processors for source through cache system. '''
    processors = _xtnsapi.structure_processors
    if not __.is_absent( processor_name ):
        if processor_name not in processors:
            raise _exceptions.ProcessorInavailability( processor_name )
        processor = processors[ processor_name ]
        detection = await processor.detect( source )
        return __.typx.cast( _interfaces.StructureDetection, detection )
    # Use structure-specific cache and processors
    detection = await determine_processor_optimal(
        source, cache = _structure_detections_cache, processors = processors )
    if __.is_absent( detection ):
        raise _exceptions.ProcessorInavailability( 'structure' )
    return __.typx.cast( _interfaces.StructureDetection, detection )


async def _execute_processors(
    source: str, processors: __.cabc.Mapping[ str, _interfaces.Processor ]
) -> dict[ str, _interfaces.BaseDetection ]:
    ''' Runs all processors on the source. '''
    results: dict[ str, _interfaces.BaseDetection ] = { }
    # TODO: Parallel async fanout.
    for processor in processors.values( ):
        try: detection = await processor.detect( source )
        except Exception:  # noqa: PERF203,S112
            # Skip processor on detection failure
            continue
        else: results[ processor.name ] = detection
    return results


async def _execute_processors_and_cache(
    source: str,
    cache: DetectionsCache,
    processors: __.cabc.Mapping[ str, _interfaces.Processor ],
) -> None:
    ''' Executes all processors and caches results. '''
    detections = await _execute_processors( source, processors )
    cache.add_entry( source, detections )


def _select_processor_optimal(
    detections: DetectionsByProcessor,
    processors: __.cabc.Mapping[ str, _interfaces.Processor ]
) -> __.Absential[ _interfaces.BaseDetection ]:
    ''' Selects best processor based on confidence and registration order. '''
    if not detections: return __.absent
    detections_ = [
        result for result in detections.values( )
        if result.confidence > 0.0 ]
    if not detections_: return __.absent
    processor_names = list( processors.keys( ) )
    def sort_key( result: _interfaces.BaseDetection ) -> tuple[ float, int ]:
        confidence = result.confidence
        processor_name = result.processor.name
        registration_order = processor_names.index( processor_name )
        return ( -confidence, registration_order )
    detections_.sort( key = sort_key )
    return detections_[ 0 ]