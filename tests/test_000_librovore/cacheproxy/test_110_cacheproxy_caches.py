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


''' Tests for cache entries, caches, and URL retrieval. '''

# ruff: noqa: E501

from unittest.mock import Mock, patch
from urllib.parse import ParseResult as Url

import appcore.generics as _generics
import httpx as _httpx
import pytest

import librovore.cacheproxy as module

from librovore import __
from librovore import exceptions as _exceptions

from .shared import (
    _HEADERS_TEXT_HTML,
    _HEADERS_TEXT_PLAIN,
    _URL_EMPTY_SCHEME,
    _URL_FILE_MISSING,
    _URL_FILE_TEST,
    _URL_FTP_TEST,
    _URL_HTTP_MISSING,
    _URL_HTTP_TEST,
)

#
# Series 000: Entry Classes
#




@patch.object( module.__.time, 'time', return_value = 1000.0 )
def test_010_cache_entry_fresh_not_extant( mock_time ):
    ''' Fresh entries are not extant. '''
    entry = module.CacheEntry( timestamp = 950.0, ttl = 100.0 )
    assert not entry.invalid


@patch.object( module.__.time, 'time', return_value = 1000.0 )
def test_011_cache_entry_expired_is_extant( mock_time ):
    ''' Expired entries are extant. '''
    entry = module.CacheEntry( timestamp = 800.0, ttl = 100.0 )
    assert entry.invalid


@patch.object( module.__.time, 'time', return_value = 1000.0 )
def test_012_cache_entry_boundary_condition( mock_time ):
    ''' Expiration boundary is handled correctly. '''
    # Exactly at boundary - not expired (uses > not >=)
    entry_exact = module.CacheEntry( timestamp = 900.0, ttl = 100.0 )
    assert not entry_exact.invalid
    # Just past boundary - expired
    mock_time.return_value = 1000.1
    entry_past = module.CacheEntry( timestamp = 900.0, ttl = 100.0 )
    assert entry_past.invalid


def test_015_content_cache_entry_memory_usage( ):
    ''' Memory usage calculation includes overhead. '''
    response = _generics.Value( b'test content' )
    headers = _httpx.Headers( { 'content-type': 'text/plain' } )
    entry = module.ContentCacheEntry(
        response = response,
        headers = headers,
        timestamp = 1000.0,
        ttl = 300.0,
        size_bytes = 12 )
    assert entry.memory_usage == 112  # 12 + 100 overhead


def test_016_probe_cache_entry_basic_construction( ):
    ''' Probe entries construct with required fields. '''
    response = _generics.Value( True )
    entry = module.ProbeCacheEntry(
        response = response,
        timestamp = 1000.0,
        ttl = 300.0 )
    assert entry.response == response
    assert entry.timestamp == 1000.0
    assert entry.ttl == 300.0


# Series 100: ContentCache Tests
#


def test_100_content_cache_initialization( test_delay_fn, robots_cache ):
    ''' Content cache initializes with constructor parameters. '''
    cache = module.ContentCache(
        robots_cache = robots_cache,
        memory_max = 1024,
        error_ttl = 45.0,
        success_ttl = 600.0,
        delay_function = test_delay_fn )
    assert cache.memory_max == 1024
    assert cache.error_ttl == 45.0
    assert cache.success_ttl == 600.0
    assert cache.delay_function == test_delay_fn
    assert cache._memory_total == 0
    assert len( cache._cache ) == 0
    assert len( cache._recency ) == 0


@pytest.mark.asyncio
async def test_110_content_cache_access_missing_returns_absent(
        content_cache ):
    ''' Missing URLs return absent from cache access. '''
    result = await content_cache.access( _URL_HTTP_MISSING.geturl( ) )
    assert __.is_absent( result )


@pytest.mark.asyncio
async def test_111_content_cache_access_fresh_returns_content( content_cache ):
    ''' Fresh entries return content and headers from cache access. '''
    test_content = b'test content'
    response = _generics.Value( test_content )
    with patch.object( module.__.time, 'time', return_value = 1000.0 ):
        await content_cache.store(
            _URL_HTTP_TEST.geturl( ), response, _HEADERS_TEXT_PLAIN, 300.0 )
    with patch.object( module.__.time, 'time', return_value = 1100.0 ):
        result = await content_cache.access( _URL_HTTP_TEST.geturl( ) )
    assert not __.is_absent( result )
    content, headers = result
    assert content == test_content
    assert headers == _HEADERS_TEXT_PLAIN


@pytest.mark.asyncio
async def test_112_content_cache_access_expired_returns_absent(
        content_cache
):
    ''' Expired entries are removed and return absent from cache access. '''
    test_content = b'test content'
    response = _generics.Value( test_content )
    url_key = _URL_HTTP_TEST.geturl( )
    with patch.object( module.__.time, 'time', return_value = 1000.0 ):
        await content_cache.store(
            url_key, response, _HEADERS_TEXT_PLAIN, 300.0 )
    with patch.object( module.__.time, 'time', return_value = 2000.0 ):
        result = await content_cache.access( url_key )
    assert __.is_absent( result )
    assert url_key not in content_cache._cache


def test_120_content_cache_determine_ttl_success( test_delay_fn, robots_cache ):
    ''' Successful responses get appropriate TTL. '''
    cache = module.ContentCache(
        robots_cache = robots_cache, success_ttl = 123.0,
        delay_function = test_delay_fn )
    response = _generics.Value( b'content' )
    ttl = cache.determine_ttl( response )
    assert ttl == 123.0


def test_121_content_cache_determine_ttl_error( test_delay_fn, robots_cache ):
    ''' Error responses get appropriate TTL. '''
    cache = module.ContentCache(
        robots_cache = robots_cache, error_ttl = 45.0,
        delay_function = test_delay_fn )
    response = _generics.Error( Exception( 'test error' ) )
    ttl = cache.determine_ttl( response )
    assert ttl == 45.0


@pytest.mark.asyncio
async def test_130_content_cache_store_tracks_memory( content_cache ):
    ''' Storing entries updates memory tracking correctly. '''
    test_content = b'test content 12 bytes'
    response = _generics.Value( test_content )
    headers = _httpx.Headers( )
    url_key = _URL_HTTP_TEST.geturl( )
    with patch.object( module.__.time, 'time', return_value = 1000.0 ):
        await content_cache.store( url_key, response, headers, 300.0 )
    assert content_cache._memory_total == 121  # 21 bytes + 100 overhead
    assert url_key in content_cache._cache
    assert list( content_cache._recency ) == [ url_key ]


@pytest.mark.asyncio
async def test_131_content_cache_store_replaces_existing( content_cache ):
    ''' Storing replaces existing entries and updates memory. '''
    content1 = b'first'
    response1 = _generics.Value( content1 )
    headers1 = _httpx.Headers( )
    url_key = _URL_HTTP_TEST.geturl( )
    with patch.object( module.__.time, 'time', return_value = 1000.0 ):
        await content_cache.store( url_key, response1, headers1, 300.0 )
    # Store second entry with same URL
    content2 = b'second content longer'
    response2 = _generics.Value( content2 )
    with patch.object( module.__.time, 'time', return_value = 1100.0 ):
        await content_cache.store(
            url_key, response2, _HEADERS_TEXT_HTML, 300.0 )
    assert len( content_cache._cache ) == 1
    entry = content_cache._cache[ url_key ]
    assert entry.response.extract( ) == content2
    assert entry.headers == _HEADERS_TEXT_HTML
    assert content_cache._memory_total == 121  # 21 bytes + 100 overhead


@pytest.mark.asyncio
async def test_132_content_cache_eviction_by_memory( test_delay_fn ):
    ''' LRU entries are evicted when memory limit exceeded. '''
    cache = module.ContentCache(
        memory_max = 300, delay_function = test_delay_fn )
    # Store multiple entries that will exceed memory limit
    for i in range( 5 ):
        content = b'x' * 50  # 50 bytes each + 100 overhead = 150 each
        response = _generics.Value( content )
        headers = _httpx.Headers( )
        url = f'http://example.com/test{i}'
        with patch.object( module.__.time, 'time', return_value = 1000.0 + i ):
            await cache.store( url, response, headers, 300.0 )
    # Should have evicted oldest entries to stay under 300 bytes
    assert cache._memory_total <= 300
    assert len( cache._cache ) == 2  # Only last 2 entries fit
    assert 'http://example.com/test3' in cache._cache
    assert 'http://example.com/test4' in cache._cache
    assert 'http://example.com/test0' not in cache._cache


@pytest.mark.asyncio
async def test_133_content_cache_record_access_updates_lru( test_delay_fn ):
    ''' Accessing entries moves URLs to end of recency queue. '''
    cache = module.ContentCache( delay_function = test_delay_fn )
    # Store multiple entries
    for i in range( 3 ):
        content = b'test'
        response = _generics.Value( content )
        headers = _httpx.Headers( )
        url = f'http://example.com/test{i}'
        with patch.object( module.__.time, 'time', return_value = 1000.0 + i ):
            await cache.store( url, response, headers, 300.0 )
    # Access middle entry
    with patch.object( module.__.time, 'time', return_value = 1100.0 ):
        await cache.access( 'http://example.com/test1' )
    # Should have moved test1 to end
    assert list( cache._recency ) == [
        'http://example.com/test0',
        'http://example.com/test2',
        'http://example.com/test1'
    ]


#
# Series 150: ProbeCache Tests
#


def test_150_probe_cache_initialization( test_delay_fn ):
    ''' Probe cache initializes with constructor parameters. '''
    cache = module.ProbeCache(
        entries_max = 500,
        error_ttl = 45.0,
        success_ttl = 600.0,
        delay_function = test_delay_fn )
    assert cache.entries_max == 500
    assert cache.error_ttl == 45.0
    assert cache.success_ttl == 600.0
    assert cache.delay_function == test_delay_fn
    assert len( cache._cache ) == 0
    assert len( cache._recency ) == 0


@pytest.mark.asyncio
async def test_160_probe_cache_access_missing_returns_absent( probe_cache ):
    ''' Missing URLs return absent from probe cache access. '''
    result = await probe_cache.access( _URL_HTTP_MISSING.geturl( ) )
    assert __.is_absent( result )


@pytest.mark.asyncio
async def test_161_probe_cache_access_fresh_returns_result( probe_cache ):
    ''' Fresh entries return probe results from cache access. '''
    response = _generics.Value( True )
    url_key = _URL_HTTP_TEST.geturl( )
    with patch.object( module.__.time, 'time', return_value = 1000.0 ):
        await probe_cache.store( url_key, response, 300.0 )
    with patch.object( module.__.time, 'time', return_value = 1100.0 ):
        result = await probe_cache.access( url_key )
    assert not __.is_absent( result )
    assert result is True


@pytest.mark.asyncio
async def test_162_probe_cache_access_expired_returns_absent( probe_cache ):
    ''' Expired entries are removed and return absent from probe cache. '''
    response = _generics.Value( False )
    url_key = _URL_HTTP_TEST.geturl( )
    with patch.object( module.__.time, 'time', return_value = 1000.0 ):
        await probe_cache.store( url_key, response, 300.0 )
    with patch.object( module.__.time, 'time', return_value = 2000.0 ):
        result = await probe_cache.access( url_key )
    assert __.is_absent( result )
    assert url_key not in probe_cache._cache


def test_170_probe_cache_determine_ttl_success( test_delay_fn ):
    ''' Successful probe responses get appropriate TTL. '''
    cache = module.ProbeCache(
        success_ttl = 456.0, delay_function = test_delay_fn )
    response = _generics.Value( True )
    ttl = cache.determine_ttl( response )
    assert ttl == 456.0


def test_171_probe_cache_determine_ttl_error( test_delay_fn ):
    ''' Error probe responses get appropriate TTL. '''
    cache = module.ProbeCache(
        error_ttl = 78.0, delay_function = test_delay_fn )
    response = _generics.Error( Exception( 'test error' ) )
    ttl = cache.determine_ttl( response )
    assert ttl == 78.0


@pytest.mark.asyncio
async def test_172_probe_cache_store_updates_recency( test_delay_fn ):
    ''' Storing probe entries updates recency tracking correctly. '''
    cache = module.ProbeCache( delay_function = test_delay_fn )
    response = _generics.Value( True )

    with patch.object( module.__.time, 'time', return_value = 1000.0 ):
        await cache.store( 'http://example.com/test', response, 300.0 )

    assert 'http://example.com/test' in cache._cache
    assert list( cache._recency ) == [ 'http://example.com/test' ]


@pytest.mark.asyncio
async def test_173_probe_cache_eviction_by_count( test_delay_fn ):
    ''' Oldest entries are evicted when count limit exceeded. '''
    cache = module.ProbeCache(
        entries_max = 3, delay_function = test_delay_fn )
    # Store more entries than limit
    for i in range( 5 ):
        response = _generics.Value( i % 2 == 0 )  # Alternating True/False
        url = f'http://example.com/test{i}'
        with patch.object( module.__.time, 'time', return_value = 1000.0 + i ):
            await cache.store( url, response, 300.0 )
    # Should have evicted oldest entries to stay under limit
    assert len( cache._cache ) == 3
    assert 'http://example.com/test2' in cache._cache
    assert 'http://example.com/test3' in cache._cache
    assert 'http://example.com/test4' in cache._cache
    assert 'http://example.com/test0' not in cache._cache
    assert 'http://example.com/test1' not in cache._cache


@pytest.mark.asyncio
async def test_174_probe_cache_record_access_updates_lru( test_delay_fn ):
    ''' Accessing probe entries moves URLs to end of recency queue. '''
    cache = module.ProbeCache( delay_function = test_delay_fn )
    for i in range( 3 ):
        response = _generics.Value( True )
        url = f'http://example.com/test{i}'
        with patch.object( module.__.time, 'time', return_value = 1000.0 + i ):
            await cache.store( url, response, 300.0 )
    with patch.object( module.__.time, 'time', return_value = 1100.0 ):
        await cache.access( 'http://example.com/test0' )
    # Should have moved test0 to end
    assert list( cache._recency ) == [
        'http://example.com/test1',
        'http://example.com/test2',
        'http://example.com/test0'
    ]


#
# Series 200: probe_url Function Tests
#


@pytest.mark.asyncio
async def test_200_probe_url_file_scheme_existing_file( fs, probe_cache, robots_cache ):
    ''' Existing file URLs return True when probed. '''
    fs.create_file( '/test/file.txt', contents = 'test content' )
    result = await module.probe_url( probe_cache, _URL_FILE_TEST )
    assert result is True


@pytest.mark.asyncio
async def test_201_probe_url_file_scheme_missing_file( fs, probe_cache, robots_cache ):
    ''' Missing file URLs return False when probed. '''
    result = await module.probe_url( probe_cache, _URL_FILE_MISSING )
    assert result is False


@pytest.mark.asyncio
async def test_202_probe_url_empty_scheme_existing_file( fs, probe_cache, robots_cache ):
    ''' Empty schemes are handled as file paths when probing. '''
    fs.create_file( '/test/file.txt', contents = 'test content' )
    result = await module.probe_url( probe_cache, _URL_EMPTY_SCHEME )
    assert result is True


@pytest.mark.asyncio
async def test_203_probe_url_unsupported_scheme_returns_false( probe_cache, robots_cache ):
    ''' Unsupported URL schemes return False when probed. '''
    result = await module.probe_url( probe_cache, _URL_FTP_TEST )
    assert result is False


@pytest.mark.asyncio
async def test_210_probe_url_http_cache_hit_returns_cached( robots_cache ):
    ''' Cache hits return cached probe results. '''
    mock_cache = Mock( spec = module.ProbeCache )
    mock_cache.access.return_value = True
    result = await module.probe_url(
        mock_cache, _URL_HTTP_TEST )
    assert result is True
    mock_cache.access.assert_called_once_with( _URL_HTTP_TEST.geturl( ) )


@pytest.mark.asyncio
async def test_211_probe_url_http_cache_miss_success(
        probe_cache, mock_client_factory
):
    ''' HTTP cache miss executes successful HEAD request. '''
    url_status = Url(
        scheme = 'http', netloc = 'example.com', path = '/status/200',
        params = '', query = '', fragment = '' )
    client_factory = mock_client_factory( status = 200 )
    result = await module.probe_url(
        probe_cache, url_status, client_factory = client_factory )
    assert result is True


@pytest.mark.asyncio
async def test_212_probe_url_http_cache_miss_failure( probe_cache, robots_cache ):
    ''' HTTP cache miss handles HEAD request exceptions with graceful robots.txt degradation. '''
    def handler( request ):
        raise _httpx.TimeoutException( 'Timeout' )
    mock_transport = _httpx.MockTransport( handler )
    def client_factory( ):
        return _httpx.AsyncClient( transport = mock_transport )
    # With graceful degradation, robots.txt timeout should not propagate
    # The actual HEAD request timeout should still be raised
    with pytest.raises( _httpx.TimeoutException ):
        await module.probe_url(
            probe_cache, _URL_HTTP_TEST,
            client_factory = client_factory )


@pytest.mark.asyncio
async def test_220_probe_url_dependency_injection_with_custom_cache(
        test_delay_fn, robots_cache
):
    ''' Injected cache dependencies are accepted and used for probing. '''
    custom_cache = module.ProbeCache(
        entries_max = 5, delay_function = test_delay_fn )
    url = Url(
        scheme = 'file', netloc = '', path = '/nonexistent',
        params = '', query = '', fragment = '' )
    result = await module.probe_url( custom_cache, url )
    assert result is False
    assert custom_cache.entries_max == 5


@pytest.mark.asyncio
async def test_221_probe_url_cache_configuration_affects_behavior(
        test_delay_fn, robots_cache
):
    ''' Custom cache configuration affects probing behavior. '''
    custom_cache = module.ProbeCache(
        entries_max = 2, success_ttl = 60.0, delay_function = test_delay_fn )
    url = Url(
        scheme = 'file', netloc = '', path = '/nonexistent',
        params = '', query = '', fragment = '' )
    result = await module.probe_url( custom_cache, url )
    assert result is False
    assert custom_cache.entries_max == 2
    assert custom_cache.success_ttl == 60.0


@pytest.mark.asyncio
async def test_222_probe_url_mutex_reuse_sequential_requests( robots_cache ):
    ''' Sequential probe requests to same URL reuse existing mutex. '''
    # Use file URL to avoid HTTP complexity
    url = _URL_FILE_TEST

    # Use separate caches to avoid cache hits
    cache1 = module.ProbeCache( )
    cache2 = module.ProbeCache( )

    # First request creates mutex
    result1 = await module.probe_url( cache1, url )
    assert result1 is False  # File doesn't exist

    # Second request reuses existing mutex (exercises false branch)
    result2 = await module.probe_url( cache2, url )
    assert result2 is False  # File doesn't exist

    # Both requests should have completed without HTTP calls


#
# Series 300: retrieve_url Function Tests
#


@pytest.mark.asyncio
async def test_300_retrieve_url_file_scheme_existing_file( fs, content_cache, robots_cache ):
    ''' Existing file URLs return content when retrieved. '''
    test_content = b'file content for testing'
    fs.create_file( '/test/data.txt', contents = test_content )
    url_data = Url(
        scheme = 'file', netloc = '', path = '/test/data.txt',
        params = '', query = '', fragment = '' )
    result = await module.retrieve_url( content_cache, url_data )
    assert result == test_content


@pytest.mark.asyncio
async def test_301_retrieve_url_file_scheme_missing_file( fs, content_cache, robots_cache ):
    ''' Missing files raise DocumentationInaccessibility when retrieved. '''
    with pytest.raises( _exceptions.DocumentationInaccessibility ):
        await module.retrieve_url( content_cache, _URL_FILE_MISSING )


@pytest.mark.asyncio
async def test_302_retrieve_url_empty_scheme_existing_file( fs, content_cache, robots_cache ):
    ''' Empty schemes are handled as file paths when retrieving. '''
    test_content = b'empty scheme content'
    fs.create_file( '/test/data.txt', contents = test_content )
    url = Url(
        scheme = '', netloc = '', path = '/test/data.txt',
        params = '', query = '', fragment = '' )
    result = await module.retrieve_url( content_cache, url )
    assert result == test_content


@pytest.mark.asyncio
async def test_303_retrieve_url_unsupported_scheme_raises_exception( content_cache, robots_cache ):
    ''' Unsupported schemes raise DocumentationInaccessibility. '''
    with pytest.raises( _exceptions.DocumentationInaccessibility ):
        await module.retrieve_url( content_cache, _URL_FTP_TEST )


@pytest.mark.asyncio
async def test_310_retrieve_url_http_cache_hit_returns_cached( robots_cache ):
    ''' Cache hits return cached content when retrieving. '''
    mock_cache = Mock( spec = module.ContentCache )
    test_content = b'cached content'
    mock_cache.access.return_value = ( test_content, _HEADERS_TEXT_PLAIN )
    result = await module.retrieve_url( mock_cache, _URL_HTTP_TEST )
    assert result == test_content
    mock_cache.access.assert_called_once_with( _URL_HTTP_TEST.geturl( ) )


@pytest.mark.asyncio
async def test_311_retrieve_url_http_cache_miss( robots_cache ):
    ''' HTTP cache miss for retrieval executes GET and caches result. '''
    cache = module.ContentCache( )
    test_content = b'HTTP response content for cache miss test'
    url = Url(
        scheme = 'http', netloc = 'cache-miss-test.example.com',
        path = '/unique-cache-miss-560',
        params = '', query = '', fragment = '' )
    def handler( request ):
        return _httpx.Response(
            200, content = test_content,
            headers = { 'content-type': 'application/octet-stream' } )
    mock_transport = _httpx.MockTransport( handler )
    def client_factory( ):
        return _httpx.AsyncClient( transport = mock_transport )
    result = await module.retrieve_url(
        cache, url, client_factory = client_factory )
    assert result == test_content
    cached_result = await cache.access( url.geturl( ) )
    assert not __.is_absent( cached_result )
    cached_content, _ = cached_result
    assert cached_content == test_content


@pytest.mark.asyncio
async def test_312_retrieve_url_file_permission_error_raises_exception( content_cache, robots_cache ):
    ''' File errors raise DocumentationInaccessibility when retrieving. '''
    url = Url(
        scheme = 'file', netloc = '', path = '/nonexistent/file.txt',
        params = '', query = '', fragment = '' )
    with pytest.raises( _exceptions.DocumentationInaccessibility ):
        await module.retrieve_url( content_cache, url )


@pytest.mark.asyncio
async def test_320_retrieve_url_dependency_injection_with_custom_cache( fs, robots_cache ):
    ''' Injected cache dependencies are accepted for retrieval. '''
    custom_cache = module.ContentCache( memory_max = 2048 )
    test_content = b'custom cache test content'
    fs.create_file( '/test/custom.txt', contents = test_content )
    url = Url(
        scheme = 'file', netloc = '', path = '/test/custom.txt',
        params = '', query = '', fragment = '' )
    result = await module.retrieve_url( custom_cache, url )
    assert result == test_content
    assert custom_cache.memory_max == 2048


@pytest.mark.asyncio
async def test_321_retrieve_url_mutex_reuse_sequential_requests( robots_cache ):
    ''' Sequential retrieve requests to same URL reuse existing mutex. '''
    # Use file URL to avoid HTTP complexity
    url = _URL_FILE_MISSING

    # Use separate caches to avoid cache hits
    cache1 = module.ContentCache( )
    cache2 = module.ContentCache( )

    # First request creates mutex - should raise exception for missing file
    with pytest.raises( _exceptions.DocumentationInaccessibility ):
        await module.retrieve_url( cache1, url )

    # Second request reuses existing mutex (exercises false branch)
    with pytest.raises( _exceptions.DocumentationInaccessibility ):
        await module.retrieve_url( cache2, url )

    # Both requests should have completed without HTTP calls
