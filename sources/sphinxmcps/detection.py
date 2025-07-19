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


DetectionCache: __.typx.TypeAlias = __.typx.Annotated[
    dict[ str, dict[ str, __.typx.Any ] ],
    __.typx.Doc( '''
        Cache mapping source URLs to detection results.

        Structure:
        {
            "https://example.com/": {
                'timestamp': float,
                'ttl': int,
                'results': {
                    'sphinx': DetectionResult,
                    'openapi': DetectionResult,
                }
            }
        }
    ''' ),
]
DetectionResult: __.typx.TypeAlias = __.typx.Annotated[
    dict[ str, __.typx.Any ],
    __.typx.Doc( '''
        Result of source detection containing confidence score and metadata.

        Structure:
        {
            'confidence': float,  # 0.0-1.0 confidence score
            'metadata': dict,     # Plugin-specific metadata
            'detector_name': str, # Name of the detector
            'timestamp': float,   # Detection timestamp
        }
    ''' ),
]


# Global detection cache
_detection_cache: DetectionCache = { }


async def detect_source(
    source: str, *, cache_ttl: int = 3600
) -> DetectionResult | None:
    ''' Detect which processor can best handle the source. '''
    from . import xtnsapi as _xtnsapi
    
    # Check cache first
    cached_result = _get_cached_result( source, cache_ttl )
    if cached_result is not None:
        return cached_result

    # Run detection on all processors
    results = await _run_processors( source, _xtnsapi.processors )

    # Cache results
    _cache_results( source, results, cache_ttl )

    # Select best processor
    return _select_best_processor( results, _xtnsapi.processors )


def _get_cached_result(
    source: str, cache_ttl: int
) -> DetectionResult | None:
    ''' Get cached detection result if valid. '''
    if source not in _detection_cache:
        return None

    cache_entry = _detection_cache[ source ]

    if __.time.time( ) - cache_entry[ 'timestamp' ] > cache_ttl:
        del _detection_cache[ source ]
        return None

    # Return best result from cache
    if not cache_entry[ 'results' ]:
        return None

    best_result = max(
        cache_entry[ 'results' ].values( ),
        key=lambda x: x[ 'confidence' ]
    )
    return best_result if best_result[ 'confidence' ] > 0.0 else None


async def _run_processors(
    source: str,
    processors: __.accret.ValidatorDictionary[ str, _interfaces.Processor ]
) -> dict[ str, DetectionResult ]:
    ''' Run all processors on the source. '''
    results: dict[ str, DetectionResult ] = { }
    current_time = __.time.time( )

    for processor in processors.values( ):
        try:
            detection = await processor.detect( source )
            
            results[ processor.name ] = {
                'confidence': detection.confidence,
                'metadata': detection.specifics,
                'detector_name': processor.name,
                'timestamp': current_time,
            }
        except Exception as exc:  # noqa: PERF203
            # Log error but continue with other processors
            results[ processor.name ] = {
                'confidence': 0.0,
                'metadata': { 'error': str( exc ) },
                'detector_name': processor.name,
                'timestamp': current_time,
            }

    return results


def _cache_results(
    source: str, results: dict[ str, DetectionResult ], cache_ttl: int
) -> None:
    ''' Cache detection results. '''
    _detection_cache[ source ] = {
        'timestamp': __.time.time( ),
        'ttl': cache_ttl,
        'results': results,
    }


def _select_best_processor(
    results: dict[ str, DetectionResult ],
    processors: __.accret.ValidatorDictionary[ str, _interfaces.Processor ]
) -> DetectionResult | None:
    ''' Select best processor based on confidence and registration order. '''
    if not results: return None
    # Filter out zero confidence results
    valid_results = [
        result for result in results.values( )
        if result[ 'confidence' ] > 0.0 ]
    if not valid_results: return None
    # Sort by confidence (descending), then by processor registration order
    processor_names = list( processors.keys( ) )

    def sort_key( result: DetectionResult ) -> tuple[ float, int ]:
        confidence = result[ 'confidence' ]
        processor_name = result[ 'detector_name' ]
        registration_order = processor_names.index( processor_name )
        return ( -confidence, registration_order )  # Negative for descending

    valid_results.sort( key=sort_key )
    return valid_results[ 0 ]


def clear_cache( ) -> None:
    ''' Clear the detection cache. '''
    _detection_cache.clear( )
