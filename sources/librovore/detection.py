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
from . import interfaces as _interfaces
from . import xtnsapi as _xtnsapi


StructureStructureDetectionsByProcessor: __.typx.TypeAlias = (
    __.cabc.Mapping[ str, _interfaces.StructureDetection ] )
InventoryStructureDetectionsByProcessor: __.typx.TypeAlias = (
    __.cabc.Mapping[ str, _interfaces.InventoryDetection ] )


class DetectionsCacheEntry( __.immut.DataclassObject ):
    ''' Cache entry for source detection results. '''

    detections: __.cabc.Mapping[ str, _interfaces.StructureDetection ]
    timestamp: float
    ttl: int

    @property
    def best_detection( self ) -> __.Absential[ _interfaces.Detection ]:
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
    ) -> __.Absential[ StructureStructureDetectionsByProcessor ]:
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
    ) -> __.Absential[ _interfaces.Detection ]:
        ''' Returns the best detection for source, if unexpired. '''
        if source not in self._entries: return __.absent
        cache_entry = self._entries[ source ]
        current_time = __.time.time( )
        if cache_entry.is_expired( current_time ):
            del self._entries[ source ]
            return __.absent
        return cache_entry.best_detection

    def add_entry(
        self, source: str, 
        detections: __.cabc.Mapping[ str, _interfaces.StructureDetection ]
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
    ) -> __.Absential[ StructureStructureDetectionsByProcessor ]:
        ''' Removes specific source from cache, if present. '''
        entry = self._entries.pop( source, None )
        if entry: return entry.detections
        return __.absent


_detections_cache = DetectionsCache( )


async def detect_inventory(
    source: str, /, *,
    processor_name: __.Absential[ str ] = __.absent
) -> _interfaces.InventoryDetection:
    ''' Detects and returns best inventory processor for source. '''
    if not __.is_absent( processor_name ):
        if processor_name in _xtnsapi.inventory_processors:
            processor = _xtnsapi.inventory_processors[ processor_name ]
            return await processor.detect( source )
        raise __.ProcessorInavailability( processor_name )
    # Auto-detect best inventory processor  
    for processor in _xtnsapi.inventory_processors.values( ):
        try:
            detection = await processor.detect( source )
            if detection.confidence > 0.0:
                return detection
        except Exception:
            continue
    raise __.ProcessorInavailability( source )


async def detect_structure(
    source: str, /, *,
    processor_name: __.Absential[ str ] = __.absent  
) -> _interfaces.StructureDetection:
    ''' Detects and returns best structure processor for source. '''
    if not __.is_absent( processor_name ):
        if processor_name in _xtnsapi.structure_processors:
            processor = _xtnsapi.structure_processors[ processor_name ]
            return await processor.detect( source )
        raise __.ProcessorInavailability( processor_name )
    # Auto-detect best structure processor
    best_detection = None
    best_confidence = 0.0
    for processor in _xtnsapi.structure_processors.values( ):
        try:
            detection = await processor.detect( source )
            if detection.confidence > best_confidence:
                best_confidence = detection.confidence
                best_detection = detection
        except Exception:
            continue
    if best_detection is None:
        raise __.ProcessorInavailability( source )
    return best_detection


async def access_detections(
    source: str, /, *,
    cache: DetectionsCache = _detections_cache,
    processors: _xtnsapi.ProcessorsRegistry = _xtnsapi.processors,
) -> tuple[ StructureDetectionsByProcessor, __.Absential[ _interfaces.Detection ] ]:
    ''' Gets cached detections, triggering fresh detection if needed. '''
    detections = cache.access_entry( source )
    if __.is_absent( detections ):
        await _execute_processors_and_cache( source, cache, processors )
        detections = cache.access_entry( source )
        # After fresh execution, detections should never be absent
        if __.is_absent( detections ):
            # Fallback: create empty detections mapping
            detections = __.immut.Dictionary[ str, _interfaces.Detection ]( )
    best_detection = cache.access_best_detection( source )
    return detections, best_detection


async def determine_processor_optimal(
    source: str, /, *,
    cache: DetectionsCache = _detections_cache,
    processors: _xtnsapi.ProcessorsRegistry = _xtnsapi.processors,
) -> __.Absential[ _interfaces.Detection ]:
    ''' Determines which processor can best handle the source. '''
    detection = cache.access_best_detection( source )
    if not __.is_absent( detection ): return detection
    detections = await _execute_processors( source, processors )
    cache.add_entry( source, detections )
    return _select_processor_optimal( detections, processors )


async def _execute_processors(
    source: str, processors: _xtnsapi.ProcessorsRegistry
) -> dict[ str, _interfaces.Detection ]:
    ''' Runs all processors on the source. '''
    results: dict[ str, _interfaces.Detection ] = { }
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
    processors: _xtnsapi.ProcessorsRegistry,
) -> None:
    ''' Executes all processors and caches results. '''
    detections = await _execute_processors( source, processors )
    cache.add_entry( source, detections )


def _select_processor_optimal(
    detections: StructureDetectionsByProcessor, processors: _xtnsapi.ProcessorsRegistry
) -> __.Absential[ _interfaces.Detection ]:
    ''' Selects best processor based on confidence and registration order. '''
    if not detections: return __.absent
    detections_ = [
        result for result in detections.values( )
        if result.confidence > 0.0 ]
    if not detections_: return __.absent
    processor_names = list( processors.keys( ) )
    def sort_key( result: _interfaces.Detection ) -> tuple[ float, int ]:
        confidence = result.confidence
        processor_name = result.processor.name
        registration_order = processor_names.index( processor_name )
        return ( -confidence, registration_order )
    detections_.sort( key = sort_key )
    return detections_[ 0 ]
