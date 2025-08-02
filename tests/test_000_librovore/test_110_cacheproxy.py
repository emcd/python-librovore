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


''' Comprehensive tests for HTTP caching infrastructure. '''


import asyncio

from unittest.mock import patch, Mock, AsyncMock
from urllib.parse import ParseResult as Url
import urllib.robotparser as _urllib_robotparser

import httpx as _httpx
import appcore.generics as _generics
import pytest

import librovore.cacheproxy as module
from librovore import __
from librovore import exceptions as _exceptions


_URL_HTTP_TEST = Url(
    scheme = 'http', netloc = 'example.com', path = '/test',
    params = '', query = '', fragment = '' )
_URL_HTTP_MISSING = Url(
    scheme = 'http', netloc = 'example.com', path = '/missing',
    params = '', query = '', fragment = '' )
_URL_FILE_TEST = Url(
    scheme = 'file', netloc = '', path = '/test/file.txt',
    params = '', query = '', fragment = '' )
_URL_FILE_MISSING = Url(
    scheme = 'file', netloc = '', path = '/test/missing.txt',
    params = '', query = '', fragment = '' )
_URL_FTP_TEST = Url(
    scheme = 'ftp', netloc = 'example.com', path = '/test',
    params = '', query = '', fragment = '' )
_URL_EMPTY_SCHEME = Url(
    scheme = '', netloc = '', path = '/test/file.txt',
    params = '', query = '', fragment = '' )

_HEADERS_TEXT_PLAIN = _httpx.Headers( { 'content-type': 'text/plain' } )
_HEADERS_TEXT_HTML = _httpx.Headers( { 'content-type': 'text/html' } )
_HEADERS_APP_JSON = _httpx.Headers( {
    'content-type': 'application/json; charset=utf-8' } )
_HEADERS_IMAGE_PNG = _httpx.Headers( { 'content-type': 'image/png' } )


@pytest.fixture
def test_delay_fn( ):
    ''' No-op delay function for fast tests. '''
    async def delay( seconds: float ) -> None:
        pass  # No-op for fast tests
    return delay


@pytest.fixture
def content_cache( test_delay_fn ):
    ''' Content cache with test configuration. '''
    return module.ContentCache(
        memory_max = 1024,
        error_ttl = 30.0,
        success_ttl = 300.0,
        delay_function = test_delay_fn )


@pytest.fixture
def probe_cache( test_delay_fn ):
    ''' Probe cache with test configuration. '''
    return module.ProbeCache(
        entries_max = 500,
        error_ttl = 30.0,
        success_ttl = 300.0,
        delay_function = test_delay_fn )


@pytest.fixture
def mock_client_factory( ):
    ''' Factory for creating mock HTTP clients with customizable responses. '''
    def _factory( status = 200, content = b'test content', headers = None ):
        if headers is None:
            headers = { 'content-type': 'text/plain' }
        def handler( request ):
            return _httpx.Response(
                status, content = content, headers = headers )
        mock_transport = _httpx.MockTransport( handler )
        def client_factory( ):
            return _httpx.AsyncClient( transport = mock_transport )
        return client_factory
    return _factory


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


def test_030_extract_charset_from_headers_with_charset( ):
    ''' Charset is extracted from Content-Type headers. '''
    headers = _httpx.Headers( {
        'content-type': 'text/html; charset=iso-8859-1',
    } )
    result = module._extract_charset_from_headers( headers, 'utf-8' )
    assert result == 'iso-8859-1'


def test_031_extract_charset_from_headers_with_quotes( ):
    ''' Quoted charset values are handled correctly. '''
    headers = _httpx.Headers( {
        'content-type': 'text/html; charset="utf-16"',
    } )
    result = module._extract_charset_from_headers( headers, 'utf-8' )
    assert result == 'utf-16'


def test_032_extract_charset_from_headers_no_charset( ):
    ''' Default charset is returned when none specified. '''
    headers = _httpx.Headers( { 'content-type': 'text/html' } )
    result = module._extract_charset_from_headers( headers, 'utf-8' )
    assert result == 'utf-8'


def test_033_extract_charset_from_headers_missing_header( ):
    ''' Default charset is returned when header is missing. '''
    headers = _httpx.Headers( )
    result = module._extract_charset_from_headers( headers, 'utf-8' )
    assert result == 'utf-8'


def test_034_extract_charset_from_headers_with_semicolon_no_charset( ):
    ''' Default charset returned when semicolon present but no charset. '''
    headers = _httpx.Headers( {
        'content-type': 'text/html; boundary=something'
    } )
    result = module._extract_charset_from_headers( headers, 'utf-8' )
    assert result == 'utf-8'


def test_035_extract_mimetype_from_headers_with_params( ):
    ''' Mimetype is extracted before parameters. '''
    headers = _httpx.Headers( {
        'content-type': 'application/json; charset=utf-8',
    } )
    result = module._extract_mimetype_from_headers( headers )
    assert result == 'application/json'


def test_036_extract_mimetype_from_headers_no_params( ):
    ''' Full mimetype value is returned without parameters. '''
    headers = _httpx.Headers( { 'content-type': 'text/plain' } )
    result = module._extract_mimetype_from_headers( headers )
    assert result == 'text/plain'


def test_037_extract_mimetype_from_headers_missing_header( ):
    ''' Empty string is returned when mimetype header is missing. '''
    headers = _httpx.Headers( )
    result = module._extract_mimetype_from_headers( headers )
    assert result == ''


def test_040_is_textual_mimetype_text_types( ):
    ''' Text mimetypes are identified as textual. '''
    assert module._is_textual_mimetype( 'text/plain' )
    assert module._is_textual_mimetype( 'text/html' )
    assert module._is_textual_mimetype( 'text/css' )


def test_041_is_textual_mimetype_application_types( ):
    ''' Textual application types are identified as textual. '''
    assert module._is_textual_mimetype( 'application/json' )
    assert module._is_textual_mimetype( 'application/xml' )
    assert module._is_textual_mimetype( 'application/javascript' )
    assert module._is_textual_mimetype( 'application/yaml' )


def test_042_is_textual_mimetype_non_textual( ):
    ''' Non-textual mimetypes are identified as non-textual. '''
    assert not module._is_textual_mimetype( 'image/png' )
    assert not module._is_textual_mimetype( 'application/pdf' )
    assert not module._is_textual_mimetype( 'video/mp4' )


def test_045_validate_textual_content_valid_mimetype( ):
    ''' Textual mimetypes pass content validation. '''
    headers = _httpx.Headers( { 'content-type': 'text/html' } )
    module._validate_textual_content( headers, 'http://example.com' )


def test_046_validate_textual_content_invalid_mimetype( ):
    ''' Non-textual content raises validation exception. '''
    headers = _httpx.Headers( { 'content-type': 'image/png' } )
    with pytest.raises( _exceptions.HttpContentTypeInvalidity ):
        module._validate_textual_content( headers, 'http://example.com' )


def test_047_validate_textual_content_missing_header( ):
    ''' Missing Content-Type headers pass validation. '''
    headers = _httpx.Headers( )
    module._validate_textual_content( headers, 'http://example.com' )


#
# Series 100: ContentCache Tests
#


def test_100_content_cache_initialization( test_delay_fn ):
    ''' Content cache initializes with constructor parameters. '''
    cache = module.ContentCache(
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


def test_120_content_cache_determine_ttl_success( test_delay_fn ):
    ''' Successful responses get appropriate TTL. '''
    cache = module.ContentCache(
        success_ttl = 123.0, delay_function = test_delay_fn )
    response = _generics.Value( b'content' )
    ttl = cache.determine_ttl( response )
    assert ttl == 123.0


def test_121_content_cache_determine_ttl_error( test_delay_fn ):
    ''' Error responses get appropriate TTL. '''
    cache = module.ContentCache(
        error_ttl = 45.0, delay_function = test_delay_fn )
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
async def test_200_probe_url_file_scheme_existing_file( fs ):
    ''' Existing file URLs return True when probed. '''
    fs.create_file( '/test/file.txt', contents = 'test content' )
    result = await module.probe_url( _URL_FILE_TEST )
    assert result is True


@pytest.mark.asyncio
async def test_201_probe_url_file_scheme_missing_file( fs ):
    ''' Missing file URLs return False when probed. '''
    result = await module.probe_url( _URL_FILE_MISSING )
    assert result is False


@pytest.mark.asyncio
async def test_202_probe_url_empty_scheme_existing_file( fs ):
    ''' Empty schemes are handled as file paths when probing. '''
    fs.create_file( '/test/file.txt', contents = 'test content' )
    result = await module.probe_url( _URL_EMPTY_SCHEME )
    assert result is True


@pytest.mark.asyncio
async def test_203_probe_url_unsupported_scheme_returns_false( ):
    ''' Unsupported URL schemes return False when probed. '''
    result = await module.probe_url( _URL_FTP_TEST )
    assert result is False


@pytest.mark.asyncio
async def test_210_probe_url_http_cache_hit_returns_cached( ):
    ''' Cache hits return cached probe results. '''
    mock_cache = Mock( spec = module.ProbeCache )
    mock_cache.access.return_value = True
    result = await module.probe_url( _URL_HTTP_TEST, cache = mock_cache )
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
        url_status, cache = probe_cache, client_factory = client_factory )
    assert result is True


@pytest.mark.asyncio
async def test_212_probe_url_http_cache_miss_failure( probe_cache ):
    ''' HTTP cache miss handles HEAD request exceptions. '''
    def handler( request ):
        raise _httpx.TimeoutException( 'Timeout' )
    mock_transport = _httpx.MockTransport( handler )
    def client_factory( ):
        return _httpx.AsyncClient( transport = mock_transport )
    with pytest.raises( _httpx.TimeoutException ):
        await module.probe_url(
            _URL_HTTP_TEST, cache = probe_cache,
            client_factory = client_factory )


@pytest.mark.asyncio
async def test_220_probe_url_dependency_injection_with_custom_cache(
        test_delay_fn
):
    ''' Injected cache dependencies are accepted and used for probing. '''
    custom_cache = module.ProbeCache(
        entries_max = 5, delay_function = test_delay_fn )
    url = Url(
        scheme = 'file', netloc = '', path = '/nonexistent',
        params = '', query = '', fragment = '' )
    result = await module.probe_url( url, cache = custom_cache )
    assert result is False
    assert custom_cache.entries_max == 5


@pytest.mark.asyncio
async def test_221_probe_url_cache_configuration_affects_behavior(
        test_delay_fn
):
    ''' Custom cache configuration affects probing behavior. '''
    custom_cache = module.ProbeCache(
        entries_max = 2, success_ttl = 60.0, delay_function = test_delay_fn )
    url = Url(
        scheme = 'file', netloc = '', path = '/nonexistent',
        params = '', query = '', fragment = '' )
    result = await module.probe_url( url, cache = custom_cache )
    assert result is False
    assert custom_cache.entries_max == 2
    assert custom_cache.success_ttl == 60.0


@pytest.mark.asyncio
async def test_222_probe_url_mutex_reuse_sequential_requests( ):
    ''' Sequential probe requests to same URL reuse existing mutex. '''
    url = _URL_HTTP_TEST
    call_count = 0
    def handler( request ):
        nonlocal call_count
        call_count += 1
        return _httpx.Response( 200 )
    mock_transport = _httpx.MockTransport( handler )
    def client_factory( ):
        return _httpx.AsyncClient( transport = mock_transport )

    # Use separate caches to avoid cache hits
    cache1 = module.ProbeCache( )
    cache2 = module.ProbeCache( )

    # First request creates mutex
    result1 = await module.probe_url(
        url, cache = cache1, client_factory = client_factory )
    assert result1 is True

    # Second request reuses existing mutex (exercises false branch)
    result2 = await module.probe_url(
        url, cache = cache2, client_factory = client_factory )
    assert result2 is True

    # Both requests should have completed
    assert call_count == 2


#
# Series 300: retrieve_url Function Tests
#


@pytest.mark.asyncio
async def test_300_retrieve_url_file_scheme_existing_file( fs ):
    ''' Existing file URLs return content when retrieved. '''
    test_content = b'file content for testing'
    fs.create_file( '/test/data.txt', contents = test_content )
    url_data = Url(
        scheme = 'file', netloc = '', path = '/test/data.txt',
        params = '', query = '', fragment = '' )
    result = await module.retrieve_url( url_data )
    assert result == test_content


@pytest.mark.asyncio
async def test_301_retrieve_url_file_scheme_missing_file( fs ):
    ''' Missing files raise DocumentationInaccessibility when retrieved. '''
    with pytest.raises( _exceptions.DocumentationInaccessibility ):
        await module.retrieve_url( _URL_FILE_MISSING )


@pytest.mark.asyncio
async def test_302_retrieve_url_empty_scheme_existing_file( fs ):
    ''' Empty schemes are handled as file paths when retrieving. '''
    test_content = b'empty scheme content'
    fs.create_file( '/test/data.txt', contents = test_content )
    url = Url(
        scheme = '', netloc = '', path = '/test/data.txt',
        params = '', query = '', fragment = '' )
    result = await module.retrieve_url( url )
    assert result == test_content


@pytest.mark.asyncio
async def test_303_retrieve_url_unsupported_scheme_raises_exception( ):
    ''' Unsupported schemes raise DocumentationInaccessibility. '''
    with pytest.raises( _exceptions.DocumentationInaccessibility ):
        await module.retrieve_url( _URL_FTP_TEST )


@pytest.mark.asyncio
async def test_310_retrieve_url_http_cache_hit_returns_cached( ):
    ''' Cache hits return cached content when retrieving. '''
    mock_cache = Mock( spec = module.ContentCache )
    test_content = b'cached content'
    mock_cache.access.return_value = ( test_content, _HEADERS_TEXT_PLAIN )
    result = await module.retrieve_url( _URL_HTTP_TEST, cache = mock_cache )
    assert result == test_content
    mock_cache.access.assert_called_once_with( _URL_HTTP_TEST.geturl( ) )


@pytest.mark.asyncio
async def test_311_retrieve_url_http_cache_miss( ):
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
        url, cache = cache, client_factory = client_factory )
    assert result == test_content
    cached_result = await cache.access( url.geturl( ) )
    assert not __.is_absent( cached_result )
    cached_content, _ = cached_result
    assert cached_content == test_content


@pytest.mark.asyncio
async def test_312_retrieve_url_file_permission_error_raises_exception( ):
    ''' File errors raise DocumentationInaccessibility when retrieving. '''
    url = Url(
        scheme = 'file', netloc = '', path = '/nonexistent/file.txt',
        params = '', query = '', fragment = '' )
    with pytest.raises( _exceptions.DocumentationInaccessibility ):
        await module.retrieve_url( url )


@pytest.mark.asyncio
async def test_320_retrieve_url_dependency_injection_with_custom_cache( fs ):
    ''' Injected cache dependencies are accepted for retrieval. '''
    custom_cache = module.ContentCache( memory_max = 2048 )
    test_content = b'custom cache test content'
    fs.create_file( '/test/custom.txt', contents = test_content )
    url = Url(
        scheme = 'file', netloc = '', path = '/test/custom.txt',
        params = '', query = '', fragment = '' )
    result = await module.retrieve_url( url, cache = custom_cache )
    assert result == test_content
    assert custom_cache.memory_max == 2048


@pytest.mark.asyncio
async def test_321_retrieve_url_mutex_reuse_sequential_requests( ):
    ''' Sequential retrieve requests to same URL reuse existing mutex. '''
    url = _URL_HTTP_TEST
    test_content = b'test content for mutex reuse'
    call_count = 0
    def handler( request ):
        nonlocal call_count
        call_count += 1
        return _httpx.Response( 200, content = test_content )
    mock_transport = _httpx.MockTransport( handler )
    def client_factory( ):
        return _httpx.AsyncClient( transport = mock_transport )

    # Use separate caches to avoid cache hits
    cache1 = module.ContentCache( )
    cache2 = module.ContentCache( )

    # First request creates mutex
    result1 = await module.retrieve_url(
        url, cache = cache1, client_factory = client_factory )
    assert result1 == test_content

    # Second request reuses existing mutex (exercises false branch)
    result2 = await module.retrieve_url(
        url, cache = cache2, client_factory = client_factory )
    assert result2 == test_content

    # Both requests should have completed
    assert call_count == 2


#
# Series 350: retrieve_url_as_text Function Tests
#


@pytest.mark.asyncio
async def test_351_retrieve_url_as_text_unsupported_scheme_raises_exception( ):
    ''' Unsupported schemes raise DocumentationInaccessibility for text. '''
    url_ftp_txt = Url(
        scheme = 'ftp', netloc = 'example.com', path = '/test.txt',
        params = '', query = '', fragment = '' )
    with pytest.raises( _exceptions.DocumentationInaccessibility ):
        await module.retrieve_url_as_text( url_ftp_txt )


@pytest.mark.asyncio
async def test_360_retrieve_url_as_text_file_scheme_utf8( fs ):
    ''' UTF-8 files return decoded content as text. '''
    test_content = 'UTF-8 text content with émojis 🚀'
    fs.create_file(
        '/test/utf8.txt', contents = test_content, encoding = 'utf-8' )
    url = Url(
        scheme = 'file', netloc = '', path = '/test/utf8.txt',
        params = '', query = '', fragment = '' )
    result = await module.retrieve_url_as_text( url )
    assert result == test_content


@pytest.mark.asyncio
async def test_361_retrieve_url_as_text_file_scheme_custom_charset( fs ):
    ''' Custom default charset is used for file text retrieval. '''
    test_content = 'ASCII content only'
    fs.create_file(
        '/test/ascii.txt', contents = test_content.encode( 'ascii' ) )
    url = Url(
        scheme = 'file', netloc = '', path = '/test/ascii.txt',
        params = '', query = '', fragment = '' )
    result = await module.retrieve_url_as_text(
        url, charset_default = 'ascii' )
    assert result == test_content


@pytest.mark.asyncio
async def test_362_retrieve_url_as_text_http_cache_hit_with_charset( ):
    ''' Cache hits extract charset from headers for text retrieval. '''
    mock_cache = Mock( spec = module.ContentCache )
    test_content = 'Cached text content'
    test_headers = _httpx.Headers( {
        'content-type': 'text/html; charset=iso-8859-1',
    } )
    mock_cache.access.return_value = (
        test_content.encode( 'iso-8859-1' ), test_headers )
    result = await module.retrieve_url_as_text(
        _URL_HTTP_TEST, cache = mock_cache )
    assert result == test_content
    mock_cache.access.assert_called_once_with( _URL_HTTP_TEST.geturl( ) )


@pytest.mark.asyncio
async def test_363_retrieve_url_as_text_http_validates_content_type( ):
    ''' Textual content type is validated for text retrieval. '''
    mock_cache = Mock( spec = module.ContentCache )
    mock_cache.access.return_value = ( b'binary data', _HEADERS_IMAGE_PNG )
    url_image = Url(
        scheme = 'http', netloc = 'example.com', path = '/image',
        params = '', query = '', fragment = '' )
    with pytest.raises( _exceptions.HttpContentTypeInvalidity ):
        await module.retrieve_url_as_text( url_image, cache = mock_cache )


@pytest.mark.asyncio
async def test_364_retrieve_url_as_text_http_default_charset_fallback( ):
    ''' Default charset is used as fallback when none specified. '''
    mock_cache = Mock( spec = module.ContentCache )
    test_content = 'Default charset content'
    test_headers = _httpx.Headers( { 'content-type': 'text/plain' } )
    mock_cache.access.return_value = (
        test_content.encode( 'utf-8' ), test_headers )
    url = Url(
        scheme = 'http', netloc = 'example.com', path = '/text',
        params = '', query = '', fragment = '' )
    result = await module.retrieve_url_as_text( url, cache = mock_cache )
    assert result == test_content


@pytest.mark.asyncio
async def test_365_retrieve_url_as_text_http_cache_miss( ):
    ''' HTTP cache miss for text retrieval executes GET and caches result. '''
    cache = module.ContentCache( )
    test_content = 'HTTP text response'
    url = Url(
        scheme = 'http', netloc = 'example.com', path = '/text',
        params = '', query = '', fragment = '' )
    def handler( request ):
        return _httpx.Response(
            200, content = test_content.encode( 'utf-8' ),
            headers = { 'content-type': 'text/plain; charset=utf-8' } )
    mock_transport = _httpx.MockTransport( handler )
    def client_factory( ):
        return _httpx.AsyncClient( transport = mock_transport )
    result = await module.retrieve_url_as_text(
        url, cache = cache, client_factory = client_factory )
    assert result == test_content
    cached_result = await cache.access( url.geturl( ) )
    assert not __.is_absent( cached_result )
    cached_content, cached_headers = cached_result
    assert cached_content.decode( 'utf-8' ) == test_content


@pytest.mark.asyncio
async def test_366_retrieve_url_as_text_http_cache_miss_custom_charset( ):
    ''' HTTP cache miss for text with custom charset decodes correctly. '''
    cache = module.ContentCache( )
    test_content = 'Custom charset content'
    url = Url(
        scheme = 'http', netloc = 'example.com', path = '/latin',
        params = '', query = '', fragment = '' )
    def handler( request ):
        return _httpx.Response(
            200, content = test_content.encode( 'iso-8859-1' ),
            headers = { 'content-type': 'text/plain; charset=iso-8859-1' } )
    mock_transport = _httpx.MockTransport( handler )
    def client_factory( ):
        return _httpx.AsyncClient( transport = mock_transport )
    result = await module.retrieve_url_as_text(
        url, cache = cache, client_factory = client_factory )
    assert result == test_content
    cached_result = await cache.access( url.geturl( ) )
    assert not __.is_absent( cached_result )
    cached_content, cached_headers = cached_result
    assert cached_content.decode( 'iso-8859-1' ) == test_content


@pytest.mark.asyncio
async def test_370_retrieve_url_as_text_dependency_injection( fs ):
    ''' Injected cache dependencies are accepted for text retrieval. '''
    custom_cache = module.ContentCache( memory_max = 1024 )
    test_content = 'Custom text content'
    fs.create_file( '/test/text.txt', contents = test_content )
    url = Url(
        scheme = 'file', netloc = '', path = '/test/text.txt',
        params = '', query = '', fragment = '' )
    result = await module.retrieve_url_as_text( url, cache = custom_cache )
    assert result == test_content
    assert custom_cache.memory_max == 1024


#
# Series 800: Edge Case Coverage Tests
#


def test_800_content_cache_calculate_response_size_exception( ):
    ''' Exception responses use conservative size estimate. '''
    cache = module.ContentCache( )
    error_response = _generics.Error( ValueError( 'Test error' ) )
    size = cache._calculate_response_size( error_response )
    assert size == 100  # Conservative estimate for exceptions


def test_801_content_cache_evict_empty_recency_queue( ):
    ''' Memory eviction handles empty recency queue gracefully. '''
    cache = module.ContentCache( memory_max = 1 )
    # Force memory total above limit but with empty recency queue
    cache._memory_total = 1000
    cache._recency.clear( )
    # Should not crash when trying to evict from empty queue
    cache._evict_by_memory( )
    assert cache._memory_total == 1000  # Unchanged since nothing to evict


def test_802_content_cache_remove_missing_entry( ):
    ''' Removing missing entry returns early without error. '''
    cache = module.ContentCache( )
    # Should not crash when removing non-existent entry
    cache._remove( 'http://nonexistent.com' )
    assert len( cache._cache ) == 0


def test_803_probe_cache_evict_empty_recency_queue( ):
    ''' Count eviction handles empty recency queue gracefully. '''
    cache = module.ProbeCache( entries_max = 0 )
    # Force cache size above limit but with empty recency queue
    cache._cache[ 'url1' ] = Mock( )
    cache._recency.clear( )
    # Should not crash when trying to evict from empty queue
    cache._evict_by_count( )
    assert len( cache._cache ) == 1  # Unchanged since nothing to evict


def test_804_extract_charset_no_semicolon( ):
    ''' Content-Type without semicolon returns charset default. '''
    headers = _httpx.Headers( { 'content-type': 'text/plain' } )
    result = module._extract_charset_from_headers( headers, 'utf-8' )
    assert result == 'utf-8'  # Default returned when no semicolon


#
# Series 900: HTTP Request Deduplication Tests
#


@pytest.mark.asyncio
async def test_900_probe_url_concurrent_requests_deduplication( ):
    ''' Concurrent probe requests for same URL are deduplicated. '''
    cache = module.ProbeCache( )
    url = Url(
        scheme = 'http', netloc = 'example.com', path = '/test',
        params = '', query = '', fragment = '' )
    call_count = 0
    def handler( request ):
        nonlocal call_count
        call_count += 1
        return _httpx.Response( 200 )
    mock_transport = _httpx.MockTransport( handler )
    def client_factory( ):
        return _httpx.AsyncClient( transport = mock_transport )
    results = await asyncio.gather(
        module.probe_url(
            url, cache = cache, client_factory = client_factory ),
        module.probe_url(
            url, cache = cache, client_factory = client_factory ),
        module.probe_url(
            url, cache = cache, client_factory = client_factory ) )
    assert all( results )
    # But only one HTTP request should have been made due to deduplication
    assert call_count == 1


@pytest.mark.asyncio
async def test_901_retrieve_url_concurrent_requests_deduplication( ):
    ''' Concurrent retrieve requests for same URL are deduplicated. '''
    cache = module.ContentCache( )
    url = Url(
        scheme = 'http', netloc = 'example.com', path = '/test',
        params = '', query = '', fragment = '' )
    test_content = b'Test content'
    call_count = 0
    def handler( request ):
        nonlocal call_count
        call_count += 1
        return _httpx.Response(
            200, content = test_content,
            headers = { 'content-type': 'text/plain' } )
    mock_transport = _httpx.MockTransport( handler )
    def client_factory( ):
        return _httpx.AsyncClient( transport = mock_transport )
    results = await asyncio.gather(
        module.retrieve_url(
            url, cache = cache, client_factory = client_factory ),
        module.retrieve_url(
            url, cache = cache, client_factory = client_factory ),
        module.retrieve_url(
            url, cache = cache, client_factory = client_factory ) )
    # All should return same content
    assert all( result == test_content for result in results )
    # But only one HTTP request should have been made due to deduplication
    assert call_count == 1


@pytest.mark.asyncio
async def test_902_request_mutex_cleanup_after_completion( ):
    ''' Request mutexes are cleaned up after completion. '''
    url = Url(
        scheme = 'http', netloc = 'example.com', path = '/test',
        params = '', query = '', fragment = '' )
    url_key = url.geturl( )
    def handler( request ):
        return _httpx.Response( 200 )
    mock_transport = _httpx.MockTransport( handler )
    def client_factory( ):
        return _httpx.AsyncClient( transport = mock_transport )

    # Test probe cache mutex cleanup
    probe_cache = module.ProbeCache( )
    await module.probe_url(
        url, cache = probe_cache, client_factory = client_factory )
    # Mutex should be cleaned up after request completes
    assert url_key not in probe_cache._request_mutexes

    # Test content cache mutex cleanup
    content_cache = module.ContentCache( )
    await module.retrieve_url(
        url, cache = content_cache, client_factory = client_factory )
    # Mutex should be cleaned up after request completes
    assert url_key not in content_cache._request_mutexes


#
# Series 400: RobotsCache Class Tests
#


@pytest.fixture
def robots_cache( test_delay_fn ):
    ''' Robots cache with test configuration. '''
    return module.RobotsCache(
        entries_max = 250,
        ttl = 1800.0,
        request_timeout = 2.5,
        user_agent = 'test-agent',
        error_ttl = 30.0,
        success_ttl = 300.0,
        delay_function = test_delay_fn )


@pytest.fixture
def robots_txt_samples( ):
    ''' Loads sample robots.txt content for testing. '''
    import pathlib
    samples_dir = (
        pathlib.Path( __file__ ).parent.parent
        / 'data' / 'robots_txt_samples' )
    samples = { }
    for sample_file in samples_dir.glob( '*.txt' ):
        samples[ sample_file.stem ] = sample_file.read_text( )
    return samples


def test_400_robots_cache_initialization( test_delay_fn ):
    ''' RobotsCache initializes with constructor parameters correctly. '''
    cache = module.RobotsCache(
        entries_max = 100,
        ttl = 1800.0,
        request_timeout = 5.0,
        user_agent = 'test-bot/1.0',
        error_ttl = 45.0,
        success_ttl = 600.0,
        delay_function = test_delay_fn )
    assert cache.entries_max == 100
    assert cache.ttl == 1800.0
    assert cache.request_timeout == 5.0
    assert cache.user_agent == 'test-bot/1.0'
    assert cache.error_ttl == 45.0
    assert cache.success_ttl == 600.0
    assert cache.delay_function == test_delay_fn
    assert len( cache._cache ) == 0
    assert len( cache._recency ) == 0
    assert len( cache._request_delays ) == 0


@pytest.mark.asyncio
async def test_401_robots_cache_access_missing_returns_absent( robots_cache ):
    ''' Cache miss returns absent when domain not cached. '''
    result = await robots_cache.access( 'https://example.com' )
    assert __.is_absent( result )


@pytest.mark.asyncio
async def test_402_robots_cache_access_fresh_returns_parser( robots_cache ):
    ''' Fresh entries return robots parser from cache access. '''
    from urllib.robotparser import RobotFileParser
    parser = RobotFileParser( )
    parser.set_url( 'https://example.com/robots.txt' )
    parser.parse( [ 'User-agent: *', 'Allow: /' ] )
    response = _generics.Value( parser )
    with patch.object( module.__.time, 'time', return_value = 1000.0 ):
        await robots_cache.store( 'https://example.com', response, 3600.0 )
    with patch.object( module.__.time, 'time', return_value = 1100.0 ):
        result = await robots_cache.access( 'https://example.com' )
    assert not __.is_absent( result )
    assert isinstance( result, RobotFileParser )


@pytest.mark.asyncio
async def test_403_robots_cache_access_expired_returns_absent( robots_cache ):
    ''' Expired entries return absent and are removed from cache. '''
    from urllib.robotparser import RobotFileParser
    parser = RobotFileParser( )
    response = _generics.Value( parser )
    domain = 'https://example.com'
    with patch.object( module.__.time, 'time', return_value = 1000.0 ):
        await robots_cache.store( domain, response, 3600.0 )
    with patch.object( module.__.time, 'time', return_value = 5000.0 ):
        result = await robots_cache.access( domain )
    assert __.is_absent( result )
    assert domain not in robots_cache._cache


@pytest.mark.asyncio
async def test_404_robots_cache_store_robots_parser( robots_cache ):
    ''' Storing robots parser creates cache entry correctly. '''
    from urllib.robotparser import RobotFileParser
    parser = RobotFileParser( )
    parser.set_url( 'https://example.com/robots.txt' )
    response = _generics.Value( parser )
    domain = 'https://example.com'
    with patch.object( module.__.time, 'time', return_value = 1000.0 ):
        await robots_cache.store( domain, response, 3600.0 )
    assert domain in robots_cache._cache
    entry = robots_cache._cache[ domain ]
    assert entry.response == response
    assert entry.timestamp == 1000.0
    assert entry.ttl == 3600.0


def test_405_robots_cache_calculate_delay_remainder( robots_cache ):
    ''' Crawl delay remainder calculation works correctly. '''
    domain = 'https://example.com'
    with patch.object( module.__.time, 'time', return_value = 1000.0 ):
        robots_cache.assign_delay( domain, 5.0 )
    with patch.object( module.__.time, 'time', return_value = 1003.0 ):
        remainder = robots_cache.calculate_delay_remainder( domain )
    assert remainder == 2.0


def test_406_robots_cache_assign_delay( robots_cache ):
    ''' Setting crawl delay updates delay timestamp correctly. '''
    domain = 'https://example.com'
    with patch.object( module.__.time, 'time', return_value = 1000.0 ):
        robots_cache.assign_delay( domain, 10.0 )
    expected_time = 1000.0 + 10.0
    assert robots_cache._request_delays[ domain ] == expected_time


@pytest.mark.asyncio
async def test_407_robots_cache_eviction_by_count( test_delay_fn ):
    ''' LRU eviction works when cache exceeds max entries. '''
    cache = module.RobotsCache(
        entries_max = 2, delay_function = test_delay_fn )
    from urllib.robotparser import RobotFileParser
    # Store 3 entries to trigger eviction
    for i in range( 3 ):
        parser = RobotFileParser( )
        response = _generics.Value( parser )
        domain = f'https://example{i}.com'
        with patch.object( module.__.time, 'time', return_value = 1000.0 + i ):
            await cache.store( domain, response, 3600.0 )
    assert len( cache._cache ) == 2
    assert 'https://example1.com' in cache._cache
    assert 'https://example2.com' in cache._cache
    assert 'https://example0.com' not in cache._cache


def test_408_robots_cache_determine_ttl_success_vs_error( robots_cache ):
    ''' TTL determination differs for success vs error responses. '''
    from urllib.robotparser import RobotFileParser
    parser = RobotFileParser( )
    success_response = _generics.Value( parser )
    error_response = _generics.Error( Exception( 'Test error' ) )
    success_ttl = robots_cache.determine_ttl( success_response )
    error_ttl = robots_cache.determine_ttl( error_response )
    assert success_ttl == robots_cache.ttl
    assert error_ttl == robots_cache.error_ttl
    assert success_ttl > error_ttl


@pytest.mark.asyncio
async def test_409_robots_cache_record_access_updates_lru( ):
    ''' Accessing entries moves domains to end of recency queue. '''
    cache = module.RobotsCache( )
    from urllib.robotparser import RobotFileParser
    # Store multiple entries
    for i in range( 3 ):
        parser = RobotFileParser( )
        response = _generics.Value( parser )
        domain = f'https://example{i}.com'
        with patch.object( module.__.time, 'time', return_value = 1000.0 + i ):
            await cache.store( domain, response, 3600.0 )
    # Access middle entry
    with patch.object( module.__.time, 'time', return_value = 1100.0 ):
        await cache.access( 'https://example1.com' )
    # Should have moved example1 to end
    assert list( cache._recency ) == [
        'https://example0.com',
        'https://example2.com',
        'https://example1.com'
    ]


#
# Series 410: Domain Extraction Utility Tests
#


def test_410_extract_domain_http_url( ):
    ''' HTTP URL domain extraction works correctly. '''
    url = Url(
        scheme = 'http', netloc = 'example.com', path = '/test',
        params = '', query = '', fragment = '' )
    domain = module._extract_domain( url )
    assert domain == 'http://example.com'


def test_411_extract_domain_https_url( ):
    ''' HTTPS URL domain extraction works correctly. '''
    url = Url(
        scheme = 'https', netloc = 'secure.example.com', path = '/test',
        params = '', query = '', fragment = '' )
    domain = module._extract_domain( url )
    assert domain == 'https://secure.example.com'


def test_412_extract_domain_with_port( ):
    ''' URL with explicit port extracts domain correctly. '''
    url = Url(
        scheme = 'https', netloc = 'example.com:8080', path = '/test',
        params = '', query = '', fragment = '' )
    domain = module._extract_domain( url )
    assert domain == 'https://example.com:8080'


def test_413_extract_domain_with_path( ):
    ''' URL with path components extracts base domain. '''
    url = Url(
        scheme = 'https', netloc = 'example.com', path = '/deep/nested/path',
        params = '', query = '', fragment = '' )
    domain = module._extract_domain( url )
    assert domain == 'https://example.com'


def test_414_extract_domain_with_query( ):
    ''' URL with query parameters extracts base domain. '''
    url = Url(
        scheme = 'https', netloc = 'example.com', path = '/search',
        params = '', query = 'q=test&lang=en', fragment = '' )
    domain = module._extract_domain( url )
    assert domain == 'https://example.com'


#
# Series 420: robots.txt Permission Checking Tests
#


@pytest.mark.asyncio
async def test_420_check_robots_txt_allowed_url( robots_txt_samples ):
    ''' URLs allowed by robots.txt return True. '''
    robots_cache = module.RobotsCache( )
    def handler( request ):
        return _httpx.Response( 200, text = robots_txt_samples[ 'allow_all' ] )
    mock_transport = _httpx.MockTransport( handler )
    def client_factory( ):
        return _httpx.AsyncClient( transport = mock_transport )
    url = Url(
        scheme = 'https', netloc = 'allowed-example.com', path = '/test',
        params = '', query = '', fragment = '' )
    result = await module._check_robots_txt(
        url, robots_cache = robots_cache, client_factory = client_factory )
    assert result is True


@pytest.mark.asyncio
async def test_421_check_robots_txt_blocked_url( robots_txt_samples ):
    ''' URLs blocked by robots.txt return False. '''
    robots_cache = module.RobotsCache( )
    def handler( request ):
        return _httpx.Response( 200, text = robots_txt_samples[ 'block_all' ] )
    mock_transport = _httpx.MockTransport( handler )
    def client_factory( ):
        return _httpx.AsyncClient( transport = mock_transport )
    url = Url(
        scheme = 'https', netloc = 'blocked-example.com', path = '/test',
        params = '', query = '', fragment = '' )
    result = await module._check_robots_txt(
        url, robots_cache = robots_cache, client_factory = client_factory )
    assert result is False


@pytest.mark.asyncio
async def test_422_check_robots_txt_non_http_scheme( ):
    ''' File and FTP schemes always return True. '''
    file_url = Url(
        scheme = 'file', netloc = '', path = '/test/file.txt',
        params = '', query = '', fragment = '' )
    ftp_url = Url(
        scheme = 'ftp', netloc = 'ftp.example.com', path = '/test',
        params = '', query = '', fragment = '' )
    assert await module._check_robots_txt( file_url ) is True
    assert await module._check_robots_txt( ftp_url ) is True


@pytest.mark.asyncio
async def test_423_check_robots_txt_missing_robots_file( ):
    ''' Missing robots.txt allows access by default. '''
    robots_cache = module.RobotsCache( )
    def handler( request ):
        return _httpx.Response( 404 )
    mock_transport = _httpx.MockTransport( handler )
    def client_factory( ):
        return _httpx.AsyncClient( transport = mock_transport )
    url = Url(
        scheme = 'https', netloc = 'missing-robots.com', path = '/test',
        params = '', query = '', fragment = '' )
    result = await module._check_robots_txt(
        url, robots_cache = robots_cache, client_factory = client_factory )
    assert result is True


@pytest.mark.asyncio
async def test_424_check_robots_txt_malformed_robots_file(
        robots_txt_samples ):
    ''' Malformed robots.txt content allows access by default. '''
    robots_cache = module.RobotsCache( )
    def handler( request ):
        return _httpx.Response( 200, text = robots_txt_samples[ 'malformed' ] )
    mock_transport = _httpx.MockTransport( handler )
    def client_factory( ):
        return _httpx.AsyncClient( transport = mock_transport )
    url = Url(
        scheme = 'https', netloc = 'malformed-example.com', path = '/test',
        params = '', query = '', fragment = '' )
    result = await module._check_robots_txt(
        url, robots_cache = robots_cache, client_factory = client_factory )
    assert result is True


@pytest.mark.asyncio
async def test_425_check_robots_txt_cache_hit( robots_txt_samples ):
    ''' Cached robots.txt parser is used when available. '''
    from urllib.robotparser import RobotFileParser
    robots_cache = module.RobotsCache( )
    parser = RobotFileParser( )
    parser.set_url( 'https://example.com/robots.txt' )
    parser.parse( robots_txt_samples[ 'allow_all' ].splitlines( ) )
    response = _generics.Value( parser )
    with patch.object( module.__.time, 'time', return_value = 1000.0 ):
        await robots_cache.store( 'https://example.com', response, 3600.0 )
    url = Url(
        scheme = 'https', netloc = 'example.com', path = '/test',
        params = '', query = '', fragment = '' )
    result = await module._check_robots_txt(
        url, robots_cache = robots_cache )
    assert result is True


@pytest.mark.asyncio
async def test_426_check_robots_txt_cache_miss_fetch( robots_txt_samples ):
    ''' Cache miss triggers robots.txt fetch and parsing. '''
    robots_cache = module.RobotsCache( )
    def handler( request ):
        return _httpx.Response(
            200, text = robots_txt_samples[ 'block_specific' ] )
    mock_transport = _httpx.MockTransport( handler )
    def client_factory( ):
        return _httpx.AsyncClient( transport = mock_transport )
    url = Url(
        scheme = 'https', netloc = 'example.com', path = '/public/test',
        params = '', query = '', fragment = '' )
    result = await module._check_robots_txt(
        url, robots_cache = robots_cache, client_factory = client_factory )
    assert result is True
    # Should have cached the result
    cached_parser = await robots_cache.access( 'https://example.com' )
    assert not __.is_absent( cached_parser )


@pytest.mark.asyncio
async def test_427_check_robots_txt_custom_user_agent( robots_txt_samples ):
    ''' Custom user agent is passed to robots.txt parser. '''
    def handler( request ):
        return _httpx.Response( 200, text = robots_txt_samples[ 'allow_all' ] )
    mock_transport = _httpx.MockTransport( handler )
    def client_factory( ):
        return _httpx.AsyncClient( transport = mock_transport )
    url = Url(
        scheme = 'https', netloc = 'example.com', path = '/test',
        params = '', query = '', fragment = '' )
    result = await module._check_robots_txt(
        url, user_agent = 'custom-bot/1.0', client_factory = client_factory )
    assert result is True


@pytest.mark.asyncio
async def test_428_check_robots_txt_default_user_agent( robots_txt_samples ):
    ''' Default user agent from configuration is used. '''
    def handler( request ):
        return _httpx.Response( 200, text = robots_txt_samples[ 'allow_all' ] )
    mock_transport = _httpx.MockTransport( handler )
    def client_factory( ):
        return _httpx.AsyncClient( transport = mock_transport )
    url = Url(
        scheme = 'https', netloc = 'example.com', path = '/test',
        params = '', query = '', fragment = '' )
    result = await module._check_robots_txt(
        url, client_factory = client_factory )
    assert result is True


@pytest.mark.asyncio
async def test_429_check_robots_txt_parser_exception( robots_txt_samples ):
    ''' Exception during parser can_fetch call allows access. '''
    from urllib.robotparser import RobotFileParser
    robots_cache = module.RobotsCache( )
    # Create a mock parser that raises exception on can_fetch
    parser = Mock( spec = RobotFileParser )
    parser.can_fetch.side_effect = Exception( 'Parser error' )
    response = _generics.Value( parser )
    with patch.object( module.__.time, 'time', return_value = 1000.0 ):
        await robots_cache.store( 'https://example.com', response, 3600.0 )
    url = Url(
        scheme = 'https', netloc = 'example.com', path = '/test',
        params = '', query = '', fragment = '' )
    result = await module._check_robots_txt(
        url, robots_cache = robots_cache )
    assert result is True


#
# Series 440: robots.txt Fetching and Parsing Tests
#


@pytest.mark.asyncio
async def test_440_retrieve_robots_txt_success( robots_txt_samples ):
    ''' Successful fetch and parse returns parser. '''
    robots_cache = module.RobotsCache( )
    def handler( request ):
        return _httpx.Response( 200, text = robots_txt_samples[ 'allow_all' ] )
    mock_transport = _httpx.MockTransport( handler )
    def client_factory( ):
        return _httpx.AsyncClient( transport = mock_transport )
    result = await module._retrieve_robots_txt(
        'https://example.com', robots_cache, client_factory = client_factory )
    assert not __.is_absent( result )
    assert result.can_fetch( 'test-agent', 'https://example.com/test' )


@pytest.mark.asyncio
async def test_441_retrieve_robots_txt_http_error( ):
    ''' HTTP 404 for robots.txt returns empty parser allowing all access. '''
    robots_cache = module.RobotsCache( )
    def handler( request ):
        return _httpx.Response( 404 )
    mock_transport = _httpx.MockTransport( handler )
    def client_factory( ):
        return _httpx.AsyncClient( transport = mock_transport )
    result = await module._retrieve_robots_txt(
        'https://example.com', robots_cache, client_factory = client_factory )
    assert not __.is_absent( result )
    assert result.can_fetch( 'librovore/1.0', '/objects.inv' )


@pytest.mark.asyncio
async def test_442_retrieve_robots_txt_timeout( ):
    ''' Request timeout returns absent. '''
    robots_cache = module.RobotsCache( )
    def handler( request ):
        raise _httpx.TimeoutException( 'Timeout' )
    mock_transport = _httpx.MockTransport( handler )
    def client_factory( ):
        return _httpx.AsyncClient( transport = mock_transport )
    result = await module._retrieve_robots_txt(
        'https://example.com', robots_cache, client_factory = client_factory )
    assert __.is_absent( result )


@pytest.mark.asyncio
async def test_443_retrieve_robots_txt_parse_error( ):
    ''' robots.txt parsing failure returns absent. '''
    robots_cache = module.RobotsCache( )
    def handler( request ):
        return _httpx.Response(
            200, text = 'Invalid robots.txt\nwith bad syntax' )
    mock_transport = _httpx.MockTransport( handler )
    def client_factory( ):
        return _httpx.AsyncClient( transport = mock_transport )
    result = await module._retrieve_robots_txt(
        'https://example.com', robots_cache, client_factory = client_factory )
    # Should still work as robotparser is quite forgiving
    assert not __.is_absent( result )


@pytest.mark.asyncio
async def test_444_retrieve_robots_txt_empty_content( robots_txt_samples ):
    ''' Empty robots.txt file parses successfully. '''
    robots_cache = module.RobotsCache( )
    def handler( request ):
        return _httpx.Response( 200, text = robots_txt_samples[ 'empty' ] )
    mock_transport = _httpx.MockTransport( handler )
    def client_factory( ):
        return _httpx.AsyncClient( transport = mock_transport )
    result = await module._retrieve_robots_txt(
        'https://example.com', robots_cache, client_factory = client_factory )
    assert not __.is_absent( result )
    assert result.can_fetch( 'test-agent', 'https://example.com/test' )


@pytest.mark.asyncio
async def test_445_retrieve_robots_txt_mutex_deduplication(
        robots_txt_samples ):
    ''' Multiple concurrent requests ensure consistent cache state. '''
    robots_cache = module.RobotsCache( )
    def handler( request ):
        return _httpx.Response( 200, text = robots_txt_samples[ 'allow_all' ] )
    mock_transport = _httpx.MockTransport( handler )
    def client_factory( ):
        return _httpx.AsyncClient( transport = mock_transport )
    # Make concurrent requests
    results = await asyncio.gather(
        module._retrieve_robots_txt(
            'https://dedupe-test.com', robots_cache,
            client_factory = client_factory ),
        module._retrieve_robots_txt(
            'https://dedupe-test.com', robots_cache,
            client_factory = client_factory ),
        module._retrieve_robots_txt(
            'https://dedupe-test.com', robots_cache,
            client_factory = client_factory ) )
    # All should succeed
    assert all( not __.is_absent( result ) for result in results )
    # Cache should contain exactly one entry for the domain
    assert len( robots_cache._cache ) == 1
    assert 'https://dedupe-test.com' in robots_cache._cache


@pytest.mark.asyncio
async def test_446_retrieve_robots_txt_custom_client_factory(
        robots_txt_samples ):
    ''' Custom httpx client factory is used correctly. '''
    robots_cache = module.RobotsCache( )
    def handler( request ):
        return _httpx.Response( 200, text = robots_txt_samples[ 'allow_all' ] )
    mock_transport = _httpx.MockTransport( handler )
    def custom_client_factory( ):
        return _httpx.AsyncClient( transport = mock_transport )
    result = await module._retrieve_robots_txt(
        'https://example.com', robots_cache,
        client_factory = custom_client_factory )
    assert not __.is_absent( result )


@pytest.mark.asyncio
async def test_447_retrieve_robots_txt_cache_storage( robots_txt_samples ):
    ''' Result is stored in cache after fetch. '''
    robots_cache = module.RobotsCache( )
    def handler( request ):
        return _httpx.Response( 200, text = robots_txt_samples[ 'allow_all' ] )
    mock_transport = _httpx.MockTransport( handler )
    def client_factory( ):
        return _httpx.AsyncClient( transport = mock_transport )
    result = await module._retrieve_robots_txt(
        'https://example.com', robots_cache, client_factory = client_factory )
    assert not __.is_absent( result )
    # Should be cached now
    cached_result = await robots_cache.access( 'https://example.com' )
    assert not __.is_absent( cached_result )


@pytest.mark.asyncio
async def test_448_retrieve_robots_txt_ttl_determination( ):
    ''' TTL is calculated and applied correctly. '''
    robots_cache = module.RobotsCache( )
    def handler( request ):
        return _httpx.Response( 404 )  # Missing robots.txt (success case)
    mock_transport = _httpx.MockTransport( handler )
    def client_factory( ):
        return _httpx.AsyncClient( transport = mock_transport )
    await module._retrieve_robots_txt(
        'https://example.com', robots_cache, client_factory = client_factory )
    # Check that success was cached with appropriate TTL
    assert 'https://example.com' in robots_cache._cache
    entry = robots_cache._cache[ 'https://example.com' ]
    assert entry.response.is_value( )
    assert entry.ttl == robots_cache.ttl


@pytest.mark.asyncio
async def test_449_retrieve_robots_txt_error_result_extraction( ):
    ''' Error result extraction returns absent correctly. '''
    robots_cache = module.RobotsCache( )
    def handler( request ):
        raise _httpx.ConnectError( 'Connection failed' )
    mock_transport = _httpx.MockTransport( handler )
    def client_factory( ):
        return _httpx.AsyncClient( transport = mock_transport )
    result = await module._retrieve_robots_txt(
        'https://example.com', robots_cache, client_factory = client_factory )
    assert __.is_absent( result )


#
# Series 460: Crawl Delay Logic Tests
#


@pytest.mark.asyncio
async def test_460_apply_request_delay_non_http_scheme( ):
    ''' Non-HTTP schemes have no delay applied. '''
    file_url = Url(
        scheme = 'file', netloc = '', path = '/test/file.txt',
        params = '', query = '', fragment = '' )
    # Should return immediately without delay
    await module._apply_request_delay( file_url )
    # No assertion needed - just ensuring no exception


@pytest.mark.asyncio
async def test_461_apply_request_delay_no_robots_cached( robots_txt_samples ):
    ''' Fetches robots.txt when not cached. '''
    robots_cache = module.RobotsCache( )
    def handler( request ):
        return _httpx.Response(
            200, text = robots_txt_samples[ 'with_crawl_delay' ] )
    mock_transport = _httpx.MockTransport( handler )
    def client_factory( ):
        return _httpx.AsyncClient( transport = mock_transport )
    url = Url(
        scheme = 'https', netloc = 'example.com', path = '/test',
        params = '', query = '', fragment = '' )
    await module._apply_request_delay(
        url, robots_cache = robots_cache, client_factory = client_factory )
    # Should have cached robots.txt
    cached_parser = await robots_cache.access( 'https://example.com' )
    assert not __.is_absent( cached_parser )


@pytest.mark.asyncio
async def test_462_apply_request_delay_active_delay( ):
    ''' Sleep occurs when delay is active. '''
    mock_delay_fn = AsyncMock( )
    robots_cache = module.RobotsCache( delay_function = mock_delay_fn )
    domain = 'https://example.com'
    # Set active delay
    with patch.object( module.__.time, 'time', return_value = 1000.0 ):
        robots_cache.assign_delay( domain, 2.0 )
    url = Url(
        scheme = 'https', netloc = 'example.com', path = '/test',
        params = '', query = '', fragment = '' )
    # Check delay function is called
    with patch.object( module.__.time, 'time', return_value = 1001.0 ):
        await module._apply_request_delay(
            url, robots_cache = robots_cache )
    mock_delay_fn.assert_called_once_with( 1.0 )


@pytest.mark.asyncio
async def test_463_apply_request_delay_expired_delay( ):
    ''' No sleep when delay has expired. '''
    robots_cache = module.RobotsCache( )
    domain = 'https://example.com'
    # Set expired delay
    with patch.object( module.__.time, 'time', return_value = 1000.0 ):
        robots_cache.assign_delay( domain, 2.0 )
    url = Url(
        scheme = 'https', netloc = 'example.com', path = '/test',
        params = '', query = '', fragment = '' )
    with (
        patch.object( module.__.asyncio, 'sleep' ) as mock_sleep,
        patch.object( module.__.time, 'time', return_value = 1005.0 )
    ):
        await module._apply_request_delay(
            url, robots_cache = robots_cache )
    mock_sleep.assert_not_called( )


@pytest.mark.asyncio
async def test_464_apply_request_delay_set_new_delay( robots_txt_samples ):
    ''' Sets delay from robots.txt crawl-delay directive. '''
    robots_cache = module.RobotsCache( )
    from urllib.robotparser import RobotFileParser
    parser = RobotFileParser( )
    parser.set_url( 'https://example.com/robots.txt' )
    parser.parse( robots_txt_samples[ 'with_crawl_delay' ].splitlines( ) )
    response = _generics.Value( parser )
    with patch.object( module.__.time, 'time', return_value = 1000.0 ):
        await robots_cache.store( 'https://example.com', response, 3600.0 )
    url = Url(
        scheme = 'https', netloc = 'example.com', path = '/test',
        params = '', query = '', fragment = '' )
    with patch.object( module.__.time, 'time', return_value = 1000.0 ):
        await module._apply_request_delay(
            url, robots_cache = robots_cache )
    # Should have set delay for 2 seconds (from robots.txt)
    expected_time = 1000.0 + 2.0
    assert (
        robots_cache._request_delays[ 'https://example.com' ]
        == expected_time )


@pytest.mark.asyncio
async def test_465_apply_request_delay_no_crawl_delay( robots_txt_samples ):
    ''' robots.txt with no Crawl-delay sets no delay. '''
    robots_cache = module.RobotsCache( )
    from urllib.robotparser import RobotFileParser
    parser = RobotFileParser( )
    parser.set_url( 'https://example.com/robots.txt' )
    parser.parse( robots_txt_samples[ 'allow_all' ].splitlines( ) )
    response = _generics.Value( parser )
    with patch.object( module.__.time, 'time', return_value = 1000.0 ):
        await robots_cache.store( 'https://example.com', response, 3600.0 )
    url = Url(
        scheme = 'https', netloc = 'example.com', path = '/test',
        params = '', query = '', fragment = '' )
    await module._apply_request_delay( url, robots_cache = robots_cache )
    # Should not have set any delay
    assert 'https://example.com' not in robots_cache._request_delays


@pytest.mark.asyncio
async def test_466_apply_request_delay_invalid_crawl_delay( ):
    ''' Non-numeric Crawl-delay values are handled gracefully. '''
    robots_cache = module.RobotsCache( )
    from urllib.robotparser import RobotFileParser
    parser = RobotFileParser( )
    parser.set_url( 'https://example.com/robots.txt' )
    parser.parse( [ 'User-agent: *', 'Crawl-delay: invalid' ] )
    response = _generics.Value( parser )
    with patch.object( module.__.time, 'time', return_value = 1000.0 ):
        await robots_cache.store( 'https://example.com', response, 3600.0 )
    url = Url(
        scheme = 'https', netloc = 'example.com', path = '/test',
        params = '', query = '', fragment = '' )
    await module._apply_request_delay( url, robots_cache = robots_cache )
    # Should handle gracefully without setting delay
    assert 'https://example.com' not in robots_cache._request_delays


@pytest.mark.asyncio
async def test_467_apply_request_delay_robots_parser_exception( ):
    ''' Exception getting crawl delay is handled gracefully. '''
    robots_cache = module.RobotsCache( )
    from urllib.robotparser import RobotFileParser
    parser = Mock( spec = RobotFileParser )
    parser.crawl_delay.side_effect = Exception( 'Parser error' )
    response = _generics.Value( parser )
    with patch.object( module.__.time, 'time', return_value = 1000.0 ):
        await robots_cache.store( 'https://example.com', response, 3600.0 )
    url = Url(
        scheme = 'https', netloc = 'example.com', path = '/test',
        params = '', query = '', fragment = '' )
    await module._apply_request_delay( url, robots_cache = robots_cache )
    # Should handle exception gracefully
    assert 'https://example.com' not in robots_cache._request_delays


@pytest.mark.asyncio
async def test_468_apply_request_delay_with_custom_client(
        robots_txt_samples ):
    ''' Custom client factory is used for robots.txt fetch. '''
    robots_cache = module.RobotsCache( )
    def handler( request ):
        return _httpx.Response(
            200, text = robots_txt_samples[ 'with_crawl_delay' ] )
    mock_transport = _httpx.MockTransport( handler )
    def client_factory( ):
        return _httpx.AsyncClient( transport = mock_transport )
    url = Url(
        scheme = 'https', netloc = 'example.com', path = '/test',
        params = '', query = '', fragment = '' )
    await module._apply_request_delay(
        url, robots_cache = robots_cache, client_factory = client_factory )
    # Should have fetched and cached robots.txt
    cached_parser = await robots_cache.access( 'https://example.com' )
    assert not __.is_absent( cached_parser )


@pytest.mark.asyncio
async def test_469_apply_request_delay_time_calculation( ):
    ''' Delay timestamp calculation is correct. '''
    robots_cache = module.RobotsCache( )
    domain = 'https://example.com'
    with patch.object( module.__.time, 'time', return_value = 1234.5 ):
        robots_cache.assign_delay( domain, 7.5 )
    expected_time = 1234.5 + 7.5
    assert robots_cache._request_delays[ domain ] == expected_time


#
# Series 480: Integration Tests
#


@pytest.mark.asyncio
async def test_480_probe_url_robots_txt_blocked( robots_txt_samples ):
    ''' probe_url respects robots.txt blocking. '''
    probe_cache = module.ProbeCache( )
    def handler( request ):
        if request.url.path == '/robots.txt':
            return _httpx.Response(
                200, text = robots_txt_samples[ 'block_all' ] )
        return _httpx.Response( 200 )
    mock_transport = _httpx.MockTransport( handler )
    def client_factory( ):
        return _httpx.AsyncClient( transport = mock_transport )
    url = Url(
        scheme = 'https', netloc = 'block-test.com', path = '/test',
        params = '', query = '', fragment = '' )
    with pytest.raises( _exceptions.UrlImpermissibility ):
        await module.probe_url(
            url, cache = probe_cache, client_factory = client_factory )


@pytest.mark.asyncio
async def test_481_probe_url_robots_txt_allowed( robots_txt_samples ):
    ''' probe_url allows access when robots.txt permits. '''
    probe_cache = module.ProbeCache( )
    def handler( request ):
        if request.url.path == '/robots.txt':
            return _httpx.Response(
                200, text = robots_txt_samples[ 'allow_all' ] )
        return _httpx.Response( 200 )
    mock_transport = _httpx.MockTransport( handler )
    def client_factory( ):
        return _httpx.AsyncClient( transport = mock_transport )
    url = Url(
        scheme = 'https', netloc = 'allow-test.com', path = '/test',
        params = '', query = '', fragment = '' )
    result = await module.probe_url(
        url, cache = probe_cache, client_factory = client_factory )
    assert result is True


@pytest.mark.asyncio
async def test_482_retrieve_url_robots_txt_blocked( robots_txt_samples ):
    ''' retrieve_url respects robots.txt blocking. '''
    def handler( request ):
        if request.url.path == '/robots.txt':
            return _httpx.Response(
                200, text = robots_txt_samples[ 'block_all' ] )
        return _httpx.Response( 200, content = b'test content' )
    mock_transport = _httpx.MockTransport( handler )
    def client_factory( ):
        return _httpx.AsyncClient( transport = mock_transport )
    content_cache = module.ContentCache( )
    url = Url(
        scheme = 'https', netloc = 'blocked-retrieve.com', path = '/test',
        params = '', query = '', fragment = '' )
    with pytest.raises( _exceptions.UrlImpermissibility ):
        await module.retrieve_url(
            url, cache = content_cache, client_factory = client_factory )


@pytest.mark.asyncio
async def test_483_retrieve_url_robots_txt_allowed( robots_txt_samples ):
    ''' retrieve_url allows access when robots.txt permits. '''
    test_content = b'allowed content'
    def handler( request ):
        if request.url.path == '/robots.txt':
            return _httpx.Response(
                200, text = robots_txt_samples[ 'allow_all' ] )
        return _httpx.Response( 200, content = test_content )
    mock_transport = _httpx.MockTransport( handler )
    def client_factory( ):
        return _httpx.AsyncClient( transport = mock_transport )
    content_cache = module.ContentCache( )
    url = Url(
        scheme = 'https', netloc = 'allowed-retrieve.com', path = '/test',
        params = '', query = '', fragment = '' )
    result = await module.retrieve_url(
        url, cache = content_cache, client_factory = client_factory )
    assert result == test_content


@pytest.mark.asyncio
async def test_484_retrieve_url_as_text_robots_txt_blocked(
        robots_txt_samples ):
    ''' retrieve_url_as_text respects robots.txt blocking. '''
    def handler( request ):
        if request.url.path == '/robots.txt':
            return _httpx.Response(
                200, text = robots_txt_samples[ 'block_all' ] )
        return _httpx.Response(
            200, content = b'test content',
            headers = { 'content-type': 'text/plain' } )
    mock_transport = _httpx.MockTransport( handler )
    def client_factory( ):
        return _httpx.AsyncClient( transport = mock_transport )
    content_cache = module.ContentCache( )
    url = Url(
        scheme = 'https', netloc = 'blocked-text.com', path = '/test',
        params = '', query = '', fragment = '' )
    with pytest.raises( _exceptions.UrlImpermissibility ):
        await module.retrieve_url_as_text(
            url, cache = content_cache, client_factory = client_factory )


@pytest.mark.asyncio
async def test_485_robots_txt_integration_with_caching( robots_txt_samples ):
    ''' robots.txt works correctly with HTTP caching. '''
    content_cache = module.ContentCache( )
    test_content = b'cached content'
    def handler( request ):
        if request.url.path == '/robots.txt':
            return _httpx.Response(
                200, text = robots_txt_samples[ 'block_specific' ] )
        return _httpx.Response( 200, content = test_content )
    mock_transport = _httpx.MockTransport( handler )
    def client_factory( ):
        return _httpx.AsyncClient( transport = mock_transport )
    # Allowed path
    allowed_url = Url(
        scheme = 'https', netloc = 'example.com', path = '/public/data',
        params = '', query = '', fragment = '' )
    result = await module.retrieve_url(
        allowed_url, cache = content_cache, client_factory = client_factory )
    assert result == test_content
    # Should be cached
    cached_result = await content_cache.access( allowed_url.geturl( ) )
    assert not __.is_absent( cached_result )


@pytest.mark.asyncio
async def test_486_robots_txt_crawl_delay_integration( robots_txt_samples ):
    ''' Crawl delay integrates correctly with HTTP requests. '''
    content_cache = module.ContentCache( )
    test_content = b'delayed content'
    def handler( request ):
        if request.url.path == '/robots.txt':
            return _httpx.Response(
                200, text = robots_txt_samples[ 'with_crawl_delay' ] )
        return _httpx.Response( 200, content = test_content )
    mock_transport = _httpx.MockTransport( handler )
    def client_factory( ):
        return _httpx.AsyncClient( transport = mock_transport )
    url = Url(
        scheme = 'https', netloc = 'crawl-delay.com', path = '/test',
        params = '', query = '', fragment = '' )
    # First request should set delay
    with patch.object( module.__.time, 'time', return_value = 1000.0 ):
        result = await module.retrieve_url(
            url, cache = content_cache, client_factory = client_factory )
    assert result == test_content
    # Should have set crawl delay in default cache
    assert (
        'https://crawl-delay.com'
        in module._robots_cache_default._request_delays )


@pytest.mark.asyncio
async def test_487_robots_txt_custom_user_agent_integration(
        robots_txt_samples ):
    ''' Custom user agent works through entire integration. '''
    robots_cache1 = module.RobotsCache( )
    robots_cache2 = module.RobotsCache( )
    custom_robots_txt = (
        'User-agent: custom-bot\nDisallow: /\n\nUser-agent: *\nAllow: /' )
    def handler( request ):
        if request.url.path == '/robots.txt':
            return _httpx.Response( 200, text = custom_robots_txt )
        return _httpx.Response( 200, content = b'content' )
    mock_transport = _httpx.MockTransport( handler )
    def client_factory( ):
        return _httpx.AsyncClient( transport = mock_transport )
    url = Url(
        scheme = 'https', netloc = 'custom-agent.com', path = '/test',
        params = '', query = '', fragment = '' )
    # Should be blocked for custom-bot but allowed for default agent
    result = await module._check_robots_txt(
        url, robots_cache = robots_cache1, user_agent = 'custom-bot',
        client_factory = client_factory )
    assert result is False
    result = await module._check_robots_txt(
        url, robots_cache = robots_cache2, client_factory = client_factory )
    assert result is True


@pytest.mark.asyncio
async def test_488_robots_txt_domain_based_caching( robots_txt_samples ):
    ''' Multiple domains are cached separately. '''
    robots_cache = module.RobotsCache( )
    def handler( request ):
        if 'example1' in str( request.url ):
            return _httpx.Response(
                200, text = robots_txt_samples[ 'allow_all' ] )
        return _httpx.Response(
            200, text = robots_txt_samples[ 'block_all' ] )
    mock_transport = _httpx.MockTransport( handler )
    def client_factory( ):
        return _httpx.AsyncClient( transport = mock_transport )
    url1 = Url(
        scheme = 'https', netloc = 'example1.com', path = '/test',
        params = '', query = '', fragment = '' )
    url2 = Url(
        scheme = 'https', netloc = 'example2.com', path = '/test',
        params = '', query = '', fragment = '' )
    result1 = await module._check_robots_txt(
        url1, robots_cache = robots_cache, client_factory = client_factory )
    result2 = await module._check_robots_txt(
        url2, robots_cache = robots_cache, client_factory = client_factory )
    assert result1 is True
    assert result2 is False
    # Both domains should be cached
    assert 'https://example1.com' in robots_cache._cache
    assert 'https://example2.com' in robots_cache._cache


@pytest.mark.asyncio
async def test_489_robots_txt_error_propagation( ):
    ''' Network errors propagate correctly through call chain. '''
    def handler( request ):
        if request.url.path == '/robots.txt':
            raise _httpx.ConnectError( 'Connection failed' )
        return _httpx.Response( 200, content = b'content' )
    mock_transport = _httpx.MockTransport( handler )
    def client_factory( ):
        return _httpx.AsyncClient( transport = mock_transport )
    url = Url(
        scheme = 'https', netloc = 'example.com', path = '/test',
        params = '', query = '', fragment = '' )
    # Should allow access when robots.txt fetch fails
    result = await module._check_robots_txt(
        url, client_factory = client_factory )
    assert result is True


#
# Series 490: Exception Handling and Edge Cases Tests
#


def test_490_robots_txt_blocked_url_exception( ):
    ''' RobotsTxtBlockedUrl exception creates correctly. '''
    url = 'https://example.com/blocked'
    user_agent = 'test-bot/1.0'
    exc = _exceptions.UrlImpermissibility( url, user_agent )
    assert exc.url == url
    assert exc.user_agent == user_agent
    expected_message = (
        f"URL '{url}' blocked by robots.txt for user agent '{user_agent}'" )
    assert str( exc ) == expected_message


def test_491_robots_txt_blocked_url_exception_attributes( ):
    ''' Exception attributes are accessible and correct. '''
    url = 'https://example.com/test'
    user_agent = 'custom-agent'
    exc = _exceptions.UrlImpermissibility( url, user_agent )
    assert hasattr( exc, 'url' )
    assert hasattr( exc, 'user_agent' )
    assert exc.url == url
    assert exc.user_agent == user_agent


def test_492_robots_txt_blocked_url_exception_inheritance( ):
    ''' Exception inherits from correct base classes. '''
    exc = _exceptions.UrlImpermissibility( 'test-url', 'test-agent' )
    assert isinstance( exc, _exceptions.Omnierror )
    assert isinstance( exc, PermissionError )
    assert isinstance( exc, Exception )


def test_493_robots_txt_blocked_url_exception_message( ):
    ''' Error message format is consistent and informative. '''
    url = 'https://api.example.com/v1/data'
    user_agent = 'my-scraper/2.1'
    exc = _exceptions.UrlImpermissibility( url, user_agent )
    message = str( exc )
    assert url in message
    assert user_agent in message
    assert 'blocked by robots.txt' in message


@pytest.mark.asyncio
async def test_494_robots_txt_network_failure_fallback( ):
    ''' Network errors default to allowing access. '''
    def handler( request ):
        raise _httpx.NetworkError( 'Network unreachable' )
    mock_transport = _httpx.MockTransport( handler )
    def client_factory( ):
        return _httpx.AsyncClient( transport = mock_transport )
    url = Url(
        scheme = 'https', netloc = 'unreachable.com', path = '/test',
        params = '', query = '', fragment = '' )
    result = await module._check_robots_txt(
        url, client_factory = client_factory )
    assert result is True


@pytest.mark.asyncio
async def test_495_robots_txt_dns_resolution_failure( ):
    ''' DNS resolution failures allow access by default. '''
    def handler( request ):
        raise _httpx.ConnectError( 'DNS resolution failed' )
    mock_transport = _httpx.MockTransport( handler )
    def client_factory( ):
        return _httpx.AsyncClient( transport = mock_transport )
    url = Url(
        scheme = 'https', netloc = 'nonexistent.example', path = '/test',
        params = '', query = '', fragment = '' )
    result = await module._check_robots_txt(
        url, client_factory = client_factory )
    assert result is True


@pytest.mark.asyncio
async def test_496_robots_txt_invalid_url_handling( ):
    ''' Malformed URLs are handled gracefully. '''
    # Test with unusual but valid URL structures
    url = Url(
        scheme = 'https', netloc = 'example.com:8080', path = '',
        params = '', query = '', fragment = '' )
    domain = module._extract_domain( url )
    assert domain == 'https://example.com:8080'


@pytest.mark.asyncio
async def test_497_robots_txt_concurrent_cache_access( robots_txt_samples ):
    ''' Race conditions in cache access are handled correctly. '''
    robots_cache = module.RobotsCache( )
    def handler( request ):
        return _httpx.Response( 200, text = robots_txt_samples[ 'allow_all' ] )
    mock_transport = _httpx.MockTransport( handler )
    def client_factory( ):
        return _httpx.AsyncClient( transport = mock_transport )
    url = Url(
        scheme = 'https', netloc = 'example.com', path = '/test',
        params = '', query = '', fragment = '' )
    # Multiple concurrent requests should not cause issues
    results = await asyncio.gather(
        module._check_robots_txt(
            url, robots_cache = robots_cache,
            client_factory = client_factory ),
        module._check_robots_txt(
            url, robots_cache = robots_cache,
            client_factory = client_factory ),
        module._check_robots_txt(
            url, robots_cache = robots_cache,
            client_factory = client_factory ) )
    assert all( results )


@pytest.mark.asyncio
async def test_498_robots_txt_cache_corruption_recovery( ):
    ''' Cache corruption scenarios are handled gracefully. '''
    robots_cache = module.RobotsCache( )
    # Manually clear cache state to simulate corruption
    robots_cache._cache.clear( )
    url = Url(
        scheme = 'https', netloc = 'corrupted-cache.com', path = '/test',
        params = '', query = '', fragment = '' )
    # Should handle gracefully and allow access when cache is empty
    result = await module._check_robots_txt(
        url, robots_cache = robots_cache )
    assert result is True


def test_499_robots_txt_configuration_edge_cases( ):
    ''' Configuration edge cases are handled correctly. '''
    # Test with extreme configuration values
    cache = module.RobotsCache(
        entries_max = 0, ttl = 0.0, error_ttl = 0.0 )
    assert cache.entries_max == 0
    assert cache.ttl == 0.0
    assert cache.error_ttl == 0.0


#
# Series 910: HTTP Error Conditions Tests
#


@pytest.mark.asyncio
async def test_910_probe_url_http_timeout_exception( ):
    ''' HTTP timeout exceptions are raised in probing. '''
    cache = module.ProbeCache( )
    url = Url(
        scheme = 'http', netloc = 'example.com', path = '/test',
        params = '', query = '', fragment = '' )
    def handler( request ):
        raise _httpx.TimeoutException( 'Request timeout' )
    mock_transport = _httpx.MockTransport( handler )
    def client_factory( ):
        return _httpx.AsyncClient( transport = mock_transport )
    with pytest.raises( _httpx.TimeoutException ):
        await module.probe_url(
            url, cache = cache, client_factory = client_factory )


@pytest.mark.asyncio
async def test_911_retrieve_url_http_connection_error( ):
    ''' HTTP connection errors are propagated as ConnectError. '''
    cache = module.ContentCache( )
    url = Url(
        scheme = 'http', netloc = 'unreachable.example', path = '/test',
        params = '', query = '', fragment = '' )
    def handler( request ):
        raise _httpx.ConnectError( 'Connection refused' )
    mock_transport = _httpx.MockTransport( handler )
    def client_factory( ):
        return _httpx.AsyncClient( transport = mock_transport )
    with pytest.raises( _httpx.ConnectError ):
        await module.retrieve_url(
            url, cache = cache, client_factory = client_factory )


@pytest.mark.asyncio
async def test_912_retrieve_url_http_status_error( ):
    ''' HTTP status errors are propagated as HTTPStatusError. '''
    cache = module.ContentCache( )
    url = Url(
        scheme = 'http', netloc = 'example.com', path = '/notfound',
        params = '', query = '', fragment = '' )
    def handler( request ):
        raise _httpx.HTTPStatusError(
            'HTTP 404', request = request, response = _httpx.Response( 404 ) )
    mock_transport = _httpx.MockTransport( handler )
    def client_factory( ):
        return _httpx.AsyncClient( transport = mock_transport )
    with pytest.raises( _httpx.HTTPStatusError ):
        await module.retrieve_url(
            url, cache = cache, client_factory = client_factory )


# Exception coverage tests for uncovered lines

@pytest.mark.asyncio
async def test_500_check_robots_txt_can_fetch_exception( ):
    ''' Exception in robots_parser.can_fetch() returns True (line 343-345). '''
    robots_cache = module.RobotsCache( )

    # Create a mock RobotFileParser that raises an exception on can_fetch
    class FaultyRobotFileParser:
        def can_fetch( self, user_agent, url ):
            raise ValueError( "Simulated can_fetch exception" )

    # Store faulty parser in cache
    faulty_parser = FaultyRobotFileParser( )
    await robots_cache.store(
        'https://faulty-example.com',
        __.generics.Value( faulty_parser ),
        ttl = 3600 )

    url = Url(
        scheme = 'https', netloc = 'faulty-example.com', path = '/test',
        params = '', query = '', fragment = '' )

    # Should return True when can_fetch raises exception
    result = await module._check_robots_txt(
        url, robots_cache = robots_cache )
    assert result is True


@pytest.mark.asyncio
async def test_501_retrieve_robots_txt_crawl_delay_exception( ):
    ''' Exception in robots_parser.crawl_delay() is handled (line 466-467). '''
    robots_cache = module.RobotsCache( )

    # Create robots.txt content that will parse successfully with crawl delay
    robots_txt_content = "User-agent: *\nCrawl-delay: 2\nAllow: /"

    def handler( request ):
        if 'robots.txt' in request.url.path:
            return _httpx.Response( 200, text = robots_txt_content )
        return _httpx.Response( 200, text = "test content" )

    mock_transport = _httpx.MockTransport( handler )

    def client_factory( ):
        return _httpx.AsyncClient( transport = mock_transport )

    # First populate the robots cache with successful robots.txt
    url = Url(
        scheme = 'https', netloc = 'crawl-delay-exception.com', path = '/test',
        params = '', query = '', fragment = '' )

    # Patch the RobotFileParser to raise exception on crawl_delay
    original_crawl_delay = _urllib_robotparser.RobotFileParser.crawl_delay

    def faulty_crawl_delay( self, user_agent ):
        raise RuntimeError( "Simulated crawl_delay exception" )

    _urllib_robotparser.RobotFileParser.crawl_delay = faulty_crawl_delay

    try:
        # This should trigger _apply_request_delay which calls crawl_delay
        result = await module.probe_url(
            url, client_factory = client_factory )
        # Should still succeed despite crawl_delay exception
        assert not __.is_absent( result )
        # Domain should not have delay assigned due to exception
        delay_remainder = robots_cache.calculate_delay_remainder(
            'https://crawl-delay-exception.com' )
        assert delay_remainder == 0.0
    finally:
        # Restore original method
        _urllib_robotparser.RobotFileParser.crawl_delay = original_crawl_delay


@pytest.mark.asyncio
async def test_502_retrieve_robots_txt_parse_exception( ):
    ''' Exception in robots_parser.parse() returns Error result (564-567). '''
    robots_cache = module.RobotsCache( )

    # Return content that will trigger parse exception
    def handler( request ):
        return _httpx.Response( 200, text = "valid http response" )

    mock_transport = _httpx.MockTransport( handler )

    def client_factory( ):
        return _httpx.AsyncClient( transport = mock_transport )

    # Patch the RobotFileParser to raise exception on parse
    original_parse = _urllib_robotparser.RobotFileParser.parse

    def faulty_parse( self, lines ):
        raise ValueError( "Simulated parse exception" )

    _urllib_robotparser.RobotFileParser.parse = faulty_parse

    try:
        result = await module._retrieve_robots_txt(
            'https://parse-exception.com', robots_cache,
            client_factory = client_factory )
        # Should return absent due to parse exception
        assert __.is_absent( result )
        # Verify the error is stored in cache as Error result
        assert 'https://parse-exception.com' in robots_cache._cache
        cache_entry = robots_cache._cache[ 'https://parse-exception.com' ]
        assert not cache_entry.response.is_value( )
    finally:
        # Restore original method
        _urllib_robotparser.RobotFileParser.parse = original_parse


