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
from . import xtnsapi as _xtnsapi


class Detection( __.immut.DataclassObject ):
    ''' Base detection result with common fields across all processors. '''

    confidence: float
    processor: str  # TODO: Processor object
    timestamp: float
    metadata: dict[ str, __.typx.Any ] = __.dcls.field(
        default_factory = dict[ str, __.typx.Any ] )


DetectionsByProcessor: __.typx.TypeAlias = __.cabc.Mapping[ str, Detection ]


class DetectionsCacheEntry( __.immut.DataclassObject ):
    ''' Cache entry for source detection results. '''

    detections: __.cabc.Mapping[ str, Detection ]
    timestamp: float
    ttl: int

    @property
    def best_detection( self ) -> __.Absential[ Detection ]:
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
    ) -> __.Absential[ Detection ]:
        ''' Returns the best detection for source, if unexpired. '''
        if source not in self._entries: return __.absent
        cache_entry = self._entries[ source ]
        current_time = __.time.time( )
        if cache_entry.is_expired( current_time ):
            del self._entries[ source ]
            return __.absent
        return cache_entry.best_detection

    def add_entry(
        self, source: str, results: __.cabc.Mapping[ str, Detection ],
    ) -> __.typx.Self:
        ''' Adds or updates cache entry with fresh results. '''
        self._entries[ source ] = DetectionsCacheEntry(
            detections = results,
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


_detections_cache = DetectionsCache( )


async def determine_processor_optimal(
    source: str, /, *,
    cache: DetectionsCache = _detections_cache,
    processors: _xtnsapi.ProcessorsRegistry = _xtnsapi.processors,
) -> __.Absential[ Detection ]:
    ''' Determines which processor can best handle the source. '''
    detection = cache.access_best_detection( source )
    if not __.is_absent( detection ): return detection
    detections = await _execute_processors( source, processors )
    cache.add_entry( source, detections )
    return _select_processor_optimal( detections, processors )


async def _execute_processors(
    source: str, processors: _xtnsapi.ProcessorsRegistry
) -> dict[ str, Detection ]:
    ''' Runs all processors on the source. '''
    results: dict[ str, Detection ] = { }
    current_time = __.time.time( )
    for processor in processors.values( ):
        try: detection = await processor.detect( source )
        except Exception as exc:  # noqa: PERF203
            # Log error but continue with other processors
            results[ processor.name ] = Detection(
                confidence = 0.0,
                metadata = { 'error': str( exc ) },
                processor = processor.name,
                timestamp = current_time,
            )
        else:
            results[ processor.name ] = Detection(
                confidence = detection.confidence,
                metadata = detection.specifics,
                processor = processor.name,
                timestamp = current_time,
            )
    return results


def _select_processor_optimal(
    detections: DetectionsByProcessor, processors: _xtnsapi.ProcessorsRegistry
) -> __.Absential[ Detection ]:
    ''' Selects best processor based on confidence and registration order. '''
    if not detections: return __.absent
    detections_ = [
        result for result in detections.values( )
        if result.confidence > 0.0 ]
    if not detections_: return __.absent
    processor_names = list( processors.keys( ) )
    def sort_key( result: Detection ) -> tuple[ float, int ]:
        confidence = result.confidence
        processor_name = result.processor
        registration_order = processor_names.index( processor_name )
        return ( -confidence, registration_order )
    detections_.sort( key = sort_key )
    return detections_[ 0 ]
