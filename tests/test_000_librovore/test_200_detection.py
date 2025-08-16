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


''' Detection module tests for processor selection and caching system. '''


from dataclasses import dataclass
from unittest.mock import Mock, patch

import pytest

import librovore.detection as module
import librovore.processors as _processors

from librovore import __


@dataclass( frozen = True )
class MockDetection:
    ''' Mock Detection implementation for testing. '''
    processor: _processors.Processor
    confidence: float
    timestamp: float = 1000.0


@dataclass
class MockProcessor:
    ''' Mock Processor implementation for testing. '''
    name: str
    detect_result: MockDetection = None
    detect_exception: Exception = None

    async def detect( self, auxdata, source: str ) -> MockDetection:
        ''' Mock detect that returns configured result or raises exception. '''
        if self.detect_exception:
            raise self.detect_exception
        return self.detect_result or MockDetection( self, 0.5 )


@pytest.fixture
def mock_detections( ):
    ''' Fixture providing various detection scenarios. '''
    mock_processor_a = MockProcessor( 'processor_a' )
    mock_processor_b = MockProcessor( 'processor_b' )
    mock_processor_c = MockProcessor( 'processor_c' )
    return {
        'empty': { },
        'single_valid': {
            'processor_a': MockDetection( mock_processor_a, 0.8 )
        },
        'single_zero': {
            'processor_a': MockDetection( mock_processor_a, 0.0 )
        },
        'multiple_valid': {
            'processor_a': MockDetection( mock_processor_a, 0.3 ),
            'processor_b': MockDetection( mock_processor_b, 0.7 ),
            'processor_c': MockDetection( mock_processor_c, 0.5 )
        },
        'tied_confidence': {
            'processor_a': MockDetection( mock_processor_a, 0.8 ),
            'processor_b': MockDetection( mock_processor_b, 0.8 )
        }
    }


@pytest.fixture
def mock_auxdata( ):
    ''' Fixture providing mock auxdata/globals object. '''
    return Mock( )


@pytest.fixture
def mock_registry( ):
    ''' Fixture providing mock processor registry. '''
    processor_a = MockProcessor( 'processor_a' )
    processor_b = MockProcessor( 'processor_b' )
    processor_c = MockProcessor( 'processor_c' )
    registry = { }
    registry[ 'processor_a' ] = processor_a
    registry[ 'processor_b' ] = processor_b
    registry[ 'processor_c' ] = processor_c
    return registry


#
# Series 100: DetectionsCacheEntry Tests
#


def test_100_cache_entry_best_detection_empty_returns_absent( ):
    ''' Cache entry with no detections returns absent. '''
    entry = module.DetectionsCacheEntry(
        detections = { }, timestamp = 1000.0, ttl = 3600 )
    result = entry.detection_optimal
    assert __.is_absent( result )


def test_110_cache_entry_best_detection_zero_confidence_returns_absent(
    mock_detections
):
    ''' Cache entry with only zero confidence detection returns absent. '''
    entry = module.DetectionsCacheEntry(
        detections = mock_detections[ 'single_zero' ],
        timestamp = 1000.0,
        ttl = 3600 )
    result = entry.detection_optimal
    assert __.is_absent( result )


def test_120_cache_entry_best_detection_highest_confidence_wins(
    mock_detections
):
    ''' Cache entry returns detection with highest confidence. '''
    entry = module.DetectionsCacheEntry(
        detections = mock_detections[ 'multiple_valid' ],
        timestamp = 1000.0,
        ttl = 3600 )
    result = entry.detection_optimal
    assert not __.is_absent( result )
    assert result.confidence == 0.7
    assert result.processor.name == 'processor_b'


def test_130_cache_entry_best_detection_tied_confidence_deterministic(
    mock_detections
):
    ''' Cache entry handles tied confidence deterministically. '''
    entry = module.DetectionsCacheEntry(
        detections = mock_detections[ 'tied_confidence' ],
        timestamp = 1000.0,
        ttl = 3600 )
    result = entry.detection_optimal
    assert not __.is_absent( result )
    assert result.confidence == 0.8


def test_140_cache_entry_is_expired_fresh_entry_returns_false( ):
    ''' Cache entry that is fresh returns false for expiration check. '''
    entry = module.DetectionsCacheEntry(
        detections = { },
        timestamp = 1000.0,
        ttl = 3600 )
    result = entry.invalid( 1500.0 )  # 500 seconds later, well within TTL
    assert result is False


def test_150_cache_entry_is_expired_expired_entry_returns_true( ):
    ''' Cache entry that is expired returns true for expiration check. '''
    entry = module.DetectionsCacheEntry(
        detections = { },
        timestamp = 1000.0,
        ttl = 3600 )
    result = entry.invalid( 5000.0 )  # 4000 seconds later, beyond TTL
    assert result is True


def test_160_cache_entry_is_expired_boundary_condition( ):
    ''' Cache entry handles expiration boundary correctly. '''
    entry = module.DetectionsCacheEntry(
        detections = { },
        timestamp = 1000.0,
        ttl = 3600 )
    # Exactly at expiration boundary - not expired yet (uses > not >=)
    result_exact = entry.invalid( 4600.0 )  # 1000 + 3600
    assert result_exact is False
    # Just after expiration boundary
    result_after = entry.invalid( 4600.1 )
    assert result_after is True


#
# Series 200: DetectionsCache Tests
#


def test_200_cache_access_entry_missing_returns_absent( ):
    ''' Cache access for missing source returns absent. '''
    cache = module.DetectionsCache( )
    result = cache.access_detections( 'nonexistent_source' )
    assert __.is_absent( result )


def test_210_cache_access_entry_fresh_returns_detections( mock_detections ):
    ''' Cache access for fresh entry returns stored detections. '''
    cache = module.DetectionsCache( ttl = 3600 )
    detections = mock_detections[ 'single_valid' ]
    with patch.object( module.__.time, 'time', return_value = 1000.0 ):
        cache.add_entry( 'test_source', detections )
    with patch.object( module.__.time, 'time', return_value = 1500.0 ):
        result = cache.access_detections( 'test_source' )
    assert not __.is_absent( result )
    assert result == detections


def test_220_cache_access_entry_expired_cleans_and_returns_absent(
    mock_detections
):
    ''' Cache access for expired entry removes it and returns absent. '''
    cache = module.DetectionsCache( ttl = 3600 )
    detections = mock_detections[ 'single_valid' ]
    with patch.object( module.__.time, 'time', return_value = 1000.0 ):
        cache.add_entry( 'test_source', detections )
    with patch.object( module.__.time, 'time', return_value = 5000.0 ):
        result = cache.access_detections( 'test_source' )
    assert __.is_absent( result )
    assert 'test_source' not in cache._entries


def test_230_cache_access_best_detection_delegates_to_entry( mock_detections ):
    ''' Cache access_best_detection delegates to cache entry. '''
    cache = module.DetectionsCache( ttl = 3600 )
    detections = mock_detections[ 'multiple_valid' ]
    with patch.object( module.__.time, 'time', return_value = 1000.0 ):
        cache.add_entry( 'test_source', detections )
    with patch.object( module.__.time, 'time', return_value = 1500.0 ):
        result = cache.access_detection_optimal( 'test_source' )
    assert not __.is_absent( result )
    assert result.confidence == 0.7  # Highest from multiple_valid
    assert result.processor.name == 'processor_b'


def test_240_cache_add_entry_stores_with_timestamp( mock_detections ):
    ''' Cache add_entry stores detections with current timestamp. '''
    cache = module.DetectionsCache( ttl = 3600 )
    detections = mock_detections[ 'single_valid' ]
    with patch.object( module.__.time, 'time', return_value = 2000.0 ):
        cache.add_entry( 'test_source', detections )
    assert 'test_source' in cache._entries
    entry = cache._entries[ 'test_source' ]
    assert entry.detections == detections
    assert entry.timestamp == 2000.0
    assert entry.ttl == 3600


def test_250_cache_add_entry_overwrites_existing( mock_detections ):
    ''' Cache add_entry overwrites existing entry for same source. '''
    cache = module.DetectionsCache( ttl = 3600 )
    first_detections = mock_detections[ 'single_valid' ]
    second_detections = mock_detections[ 'multiple_valid' ]
    with patch.object( module.__.time, 'time', return_value = 1000.0 ):
        cache.add_entry( 'test_source', first_detections )
    with patch.object( module.__.time, 'time', return_value = 2000.0 ):
        cache.add_entry( 'test_source', second_detections )
    # Verify second entry overwrote first
    entry = cache._entries[ 'test_source' ]
    assert entry.detections == second_detections
    assert entry.timestamp == 2000.0


def test_260_cache_remove_entry_missing_returns_absent( ):
    ''' Cache remove_entry for missing source returns absent. '''
    cache = module.DetectionsCache( )
    result = cache.remove_entry( 'nonexistent_source' )
    assert __.is_absent( result )


def test_270_cache_remove_entry_existing_returns_detections( mock_detections ):
    ''' Cache remove_entry for existing source returns and removes. '''
    cache = module.DetectionsCache( ttl = 3600 )
    detections = mock_detections[ 'single_valid' ]
    with patch.object( module.__.time, 'time', return_value = 1000.0 ):
        cache.add_entry( 'test_source', detections )
    result = cache.remove_entry( 'test_source' )
    assert not __.is_absent( result )
    assert result == detections
    assert 'test_source' not in cache._entries


def test_280_cache_clear_empties_all_entries( mock_detections ):
    ''' Cache clear removes all stored entries. '''
    cache = module.DetectionsCache( ttl = 3600 )
    with patch.object( module.__.time, 'time', return_value = 1000.0 ):
        cache.add_entry( 'source1', mock_detections[ 'single_valid' ] )
        cache.add_entry( 'source2', mock_detections[ 'multiple_valid' ] )
    assert len( cache._entries ) == 2
    result = cache.clear( )
    assert result == cache  # Returns self for chaining
    assert len( cache._entries ) == 0


def test_290_cache_integration_add_access_expire_cycle( mock_detections ):
    ''' Cache integration test covering add, access, and expiration cycle. '''
    cache = module.DetectionsCache( ttl = 1800 )  # 30 minutes
    detections = mock_detections[ 'single_valid' ]
    with patch.object( module.__.time, 'time', return_value = 1000.0 ):
        cache.add_entry( 'test_source', detections )
    # Access while fresh
    with patch.object( module.__.time, 'time', return_value = 1900.0 ):
        result_fresh = cache.access_detection_optimal( 'test_source' )
        assert not __.is_absent( result_fresh )
    # Access after expiration
    with patch.object( module.__.time, 'time', return_value = 3000.0 ):
        result_expired = cache.access_detection_optimal( 'test_source' )
        assert __.is_absent( result_expired )
        assert 'test_source' not in cache._entries


#
# Series 300: determine_processor_optimal Tests
#


@pytest.mark.asyncio
async def test_300_determine_processor_cache_hit_returns_cached(
    mock_detections, mock_auxdata
):
    ''' Determine processor with cache hit returns cached result. '''
    cache = module.DetectionsCache( ttl = 3600 )
    detections = mock_detections[ 'single_valid' ]
    expected_detection = next( iter( detections.values( ) ) )
    with patch.object( module.__.time, 'time', return_value = 1000.0 ):
        cache.add_entry( 'test_source', detections )
    with patch.object( module.__.time, 'time', return_value = 1500.0 ):
        result = await module.determine_detection_optimal_ll(
            mock_auxdata,
            'test_source',
            cache = cache,
            processors = { }  # Empty registry to ensure cache hit
        )
    assert not __.is_absent( result )
    assert result == expected_detection


@pytest.mark.asyncio
async def test_310_determine_processor_cache_miss_executes_processors(
    mock_registry, mock_auxdata
):
    ''' Determine processor with cache miss executes all processors. '''
    cache = module.DetectionsCache( ttl = 3600 )
    mock_registry[ 'processor_a' ].detect_result = MockDetection(
        mock_registry[ 'processor_a' ], 0.3 )
    mock_registry[ 'processor_b' ].detect_result = MockDetection(
        mock_registry[ 'processor_b' ], 0.8 )
    mock_registry[ 'processor_c' ].detect_result = MockDetection(
        mock_registry[ 'processor_c' ], 0.5 )
    result = await module.determine_detection_optimal_ll(
        mock_auxdata, 'test_source', cache = cache,
        processors = mock_registry )
    assert not __.is_absent( result )
    assert result.confidence == 0.8
    assert result.processor.name == 'processor_b'


@pytest.mark.asyncio
async def test_320_determine_processor_empty_registry_returns_absent(
    mock_auxdata
):
    ''' Determine processor with empty registry returns absent. '''
    cache = module.DetectionsCache( ttl = 3600 )
    result = await module.determine_detection_optimal_ll(
        mock_auxdata, 'test_source', cache = cache, processors = { } )
    assert __.is_absent( result )


@pytest.mark.asyncio
async def test_330_determine_processor_zero_confidence_returns_absent(
    mock_registry, mock_auxdata
):
    ''' Determine processor with only zero confidence returns absent. '''
    cache = module.DetectionsCache( ttl = 3600 )
    for processor in mock_registry.values( ):
        processor.detect_result = MockDetection( processor, 0.0 )
    result = await module.determine_detection_optimal_ll(
        mock_auxdata, 'test_source', cache = cache,
        processors = mock_registry )
    assert __.is_absent( result )


@pytest.mark.asyncio
async def test_340_determine_processor_highest_confidence_wins(
    mock_registry, mock_auxdata
):
    ''' Determine processor selects highest confidence result. '''
    cache = module.DetectionsCache( ttl = 3600 )
    mock_registry[ 'processor_a' ].detect_result = MockDetection(
        mock_registry[ 'processor_a' ], 0.2 )
    mock_registry[ 'processor_b' ].detect_result = MockDetection(
        mock_registry[ 'processor_b' ], 0.9 )
    mock_registry[ 'processor_c' ].detect_result = MockDetection(
        mock_registry[ 'processor_c' ], 0.6 )
    result = await module.determine_detection_optimal_ll(
        mock_auxdata, 'test_source', cache = cache,
        processors = mock_registry )
    assert not __.is_absent( result )
    assert result.confidence == 0.9
    assert result.processor.name == 'processor_b'


@pytest.mark.asyncio
async def test_350_determine_processor_confidence_tie_registration_order(
    mock_registry, mock_auxdata
):
    ''' Determine processor with tied confidence uses registration order. '''
    cache = module.DetectionsCache( ttl = 3600 )
    # Configure first two processors with same confidence
    mock_registry[ 'processor_a' ].detect_result = MockDetection(
        mock_registry[ 'processor_a' ], 0.8 )
    mock_registry[ 'processor_b' ].detect_result = MockDetection(
        mock_registry[ 'processor_b' ], 0.8 )
    mock_registry[ 'processor_c' ].detect_result = MockDetection(
        mock_registry[ 'processor_c' ], 0.3 )
    result = await module.determine_detection_optimal_ll(
        mock_auxdata, 'test_source', cache = cache,
        processors = mock_registry )
    assert not __.is_absent( result )
    assert result.confidence == 0.8
    # Should pick first processor in registration order
    assert result.processor.name == 'processor_a'


@pytest.mark.asyncio
async def test_360_determine_processor_stores_results_in_cache(
    mock_registry, mock_auxdata
):
    ''' Determine processor stores detection results in cache. '''
    cache = module.DetectionsCache( ttl = 3600 )
    mock_registry[ 'processor_a' ].detect_result = MockDetection(
        mock_registry[ 'processor_a' ], 0.5 )
    mock_registry[ 'processor_b' ].detect_result = MockDetection(
        mock_registry[ 'processor_b' ], 0.7 )
    # Disable processor_c to ensure only 2 results
    mock_registry[ 'processor_c' ].detect_exception = (
        RuntimeError( 'Disabled' ) )
    with patch.object( module.__.time, 'time', return_value = 1000.0 ):
        await module.determine_detection_optimal_ll(
            mock_auxdata, 'test_source', cache = cache,
            processors = mock_registry )
    assert 'test_source' in cache._entries
    cached_entry = cache._entries[ 'test_source' ]
    assert len( cached_entry.detections ) == 2
    assert 'processor_a' in cached_entry.detections
    assert 'processor_b' in cached_entry.detections


@pytest.mark.asyncio
async def test_370_determine_processor_dependency_injection(
    mock_registry, mock_auxdata
):
    ''' Determine processor accepts injected cache and processors deps. '''
    custom_cache = module.DetectionsCache( ttl = 1800 )
    mock_registry[ 'processor_a' ].detect_result = MockDetection(
        mock_registry[ 'processor_a' ], 0.6 )
    custom_processors = { 'processor_a': mock_registry[ 'processor_a' ] }
    result = await module.determine_detection_optimal_ll(
        mock_auxdata, 'test_source', cache = custom_cache,
        processors = custom_processors )
    assert not __.is_absent( result )
    assert result.confidence == 0.6
    assert 'test_source' in custom_cache._entries
    assert len( custom_cache._entries[ 'test_source' ].detections ) == 1


@pytest.mark.asyncio
async def test_380_determine_processor_handles_processor_exceptions(
    mock_registry, mock_auxdata
):
    ''' Determine processor gracefully handles exceptions from processors. '''
    cache = module.DetectionsCache( ttl = 3600 )
    # Configure processors: one throws exception, one succeeds
    mock_registry[ 'processor_a' ].detect_exception = (
        ValueError( 'Processor A failed' ) )
    mock_registry[ 'processor_b' ].detect_result = MockDetection(
        mock_registry[ 'processor_b' ], 0.7 )
    mock_registry[ 'processor_c' ].detect_exception = (
        RuntimeError( 'Processor C failed') )
    result = await module.determine_detection_optimal_ll(
        mock_auxdata, 'test_source', cache = cache,
        processors = mock_registry )
    assert not __.is_absent( result )
    assert result.confidence == 0.7
    assert result.processor.name == 'processor_b'
    cached_entry = cache._entries[ 'test_source' ]
    assert len( cached_entry.detections ) == 1
    assert 'processor_b' in cached_entry.detections
