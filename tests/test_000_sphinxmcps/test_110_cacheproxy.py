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

from unittest.mock import patch, Mock
from urllib.parse import ParseResult as Url

import httpx as _httpx
import appcore.generics as _generics
import pytest

import sphinxmcps.cacheproxy as module
from sphinxmcps import __
from sphinxmcps import exceptions as _exceptions


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
def default_config( ):
    ''' Default cache configuration for tests. '''
    return module.CacheConfiguration( )


@pytest.fixture
def content_cache( default_config ):
    ''' Content cache with default configuration. '''
    return module.ContentCache( default_config )


@pytest.fixture
def probe_cache( default_config ):
    ''' Probe cache with default configuration. '''
    return module.ProbeCache( default_config )


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
# Series 000: Configuration and Entry Classes
#


def test_000_cache_configuration_defaults( ):
    ''' Configuration uses expected default values. '''
    config = module.CacheConfiguration( )
    assert config.contents_memory_max == 32 * 1024 * 1024  # 32 MiB
    assert config.probe_entries_max == 1000
    assert config.error_ttl == 30.0
    assert config.network_error_ttl == 10.0
    assert config.success_ttl == 300.0


def test_001_cache_configuration_custom_values( ):
    ''' Configuration accepts custom values. '''
    config = module.CacheConfiguration(
        contents_memory_max = 64 * 1024 * 1024,
        probe_entries_max = 2000,
        error_ttl = 60.0,
        network_error_ttl = 20.0,
        success_ttl = 600.0 )
    assert config.contents_memory_max == 64 * 1024 * 1024
    assert config.probe_entries_max == 2000
    assert config.error_ttl == 60.0
    assert config.network_error_ttl == 20.0
    assert config.success_ttl == 600.0


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


def test_100_content_cache_initialization( ):
    ''' Content cache initializes with configuration. '''
    config = module.CacheConfiguration( contents_memory_max = 1024 )
    cache = module.ContentCache( config )
    assert cache._configuration == config
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


def test_120_content_cache_determine_ttl_success( ):
    ''' Successful responses get appropriate TTL. '''
    config = module.CacheConfiguration( success_ttl = 123.0 )
    cache = module.ContentCache( config )
    response = _generics.Value( b'content' )
    ttl = cache.determine_ttl( response )
    assert ttl == 123.0


def test_121_content_cache_determine_ttl_error( ):
    ''' Error responses get appropriate TTL. '''
    config = module.CacheConfiguration( error_ttl = 45.0 )
    cache = module.ContentCache( config )
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
async def test_132_content_cache_eviction_by_memory( ):
    ''' LRU entries are evicted when memory limit exceeded. '''
    config = module.CacheConfiguration( contents_memory_max = 300 )
    cache = module.ContentCache( config )
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
async def test_133_content_cache_record_access_updates_lru( ):
    ''' Accessing entries moves URLs to end of recency queue. '''
    config = module.CacheConfiguration( )
    cache = module.ContentCache( config )
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


def test_150_probe_cache_initialization( ):
    ''' Probe cache initializes with configuration. '''
    config = module.CacheConfiguration( probe_entries_max = 500 )
    cache = module.ProbeCache( config )
    assert cache._configuration == config
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


def test_170_probe_cache_determine_ttl_success( ):
    ''' Successful probe responses get appropriate TTL. '''
    config = module.CacheConfiguration( success_ttl = 456.0 )
    cache = module.ProbeCache( config )
    response = _generics.Value( True )
    ttl = cache.determine_ttl( response )
    assert ttl == 456.0


def test_171_probe_cache_determine_ttl_error( ):
    ''' Error probe responses get appropriate TTL. '''
    config = module.CacheConfiguration( error_ttl = 78.0 )
    cache = module.ProbeCache( config )
    response = _generics.Error( Exception( 'test error' ) )
    ttl = cache.determine_ttl( response )
    assert ttl == 78.0


@pytest.mark.asyncio
async def test_172_probe_cache_store_updates_recency( ):
    ''' Storing probe entries updates recency tracking correctly. '''
    config = module.CacheConfiguration( )
    cache = module.ProbeCache( config )
    response = _generics.Value( True )

    with patch.object( module.__.time, 'time', return_value = 1000.0 ):
        await cache.store( 'http://example.com/test', response, 300.0 )

    assert 'http://example.com/test' in cache._cache
    assert list( cache._recency ) == [ 'http://example.com/test' ]


@pytest.mark.asyncio
async def test_173_probe_cache_eviction_by_count( ):
    ''' Oldest entries are evicted when count limit exceeded. '''
    config = module.CacheConfiguration( probe_entries_max = 3 )
    cache = module.ProbeCache( config )
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
async def test_174_probe_cache_record_access_updates_lru( ):
    ''' Accessing probe entries moves URLs to end of recency queue. '''
    config = module.CacheConfiguration( )
    cache = module.ProbeCache( config )
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
async def test_220_probe_url_dependency_injection_with_custom_cache( ):
    ''' Injected cache dependencies are accepted and used for probing. '''
    custom_config = module.CacheConfiguration( probe_entries_max = 5 )
    custom_cache = module.ProbeCache( custom_config )
    url = Url(
        scheme = 'file', netloc = '', path = '/nonexistent',
        params = '', query = '', fragment = '' )
    result = await module.probe_url( url, cache = custom_cache )
    assert result is False
    assert custom_cache._configuration.probe_entries_max == 5


@pytest.mark.asyncio
async def test_221_probe_url_cache_configuration_affects_behavior( ):
    ''' Custom cache configuration affects probing behavior. '''
    restrictive_config = module.CacheConfiguration(
        probe_entries_max = 2, success_ttl = 60.0 )
    custom_cache = module.ProbeCache( restrictive_config )
    url = Url(
        scheme = 'file', netloc = '', path = '/nonexistent',
        params = '', query = '', fragment = '' )
    result = await module.probe_url( url, cache = custom_cache )
    assert result is False
    assert custom_cache._configuration.probe_entries_max == 2
    assert custom_cache._configuration.success_ttl == 60.0


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
    cache1 = module.ProbeCache( module.CacheConfiguration( ) )
    cache2 = module.ProbeCache( module.CacheConfiguration( ) )

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
    cache = module.ContentCache( module.CacheConfiguration( ) )
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
    custom_config = module.CacheConfiguration( contents_memory_max = 2048 )
    custom_cache = module.ContentCache( custom_config )
    test_content = b'custom cache test content'
    fs.create_file( '/test/custom.txt', contents = test_content )
    url = Url(
        scheme = 'file', netloc = '', path = '/test/custom.txt',
        params = '', query = '', fragment = '' )
    result = await module.retrieve_url( url, cache = custom_cache )
    assert result == test_content
    assert custom_cache._configuration.contents_memory_max == 2048


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
    cache1 = module.ContentCache( module.CacheConfiguration( ) )
    cache2 = module.ContentCache( module.CacheConfiguration( ) )

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
    cache = module.ContentCache( module.CacheConfiguration( ) )
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
    cache = module.ContentCache( module.CacheConfiguration( ) )
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
    custom_config = module.CacheConfiguration( contents_memory_max = 1024 )
    custom_cache = module.ContentCache( custom_config )
    test_content = 'Custom text content'
    fs.create_file( '/test/text.txt', contents = test_content )
    url = Url(
        scheme = 'file', netloc = '', path = '/test/text.txt',
        params = '', query = '', fragment = '' )
    result = await module.retrieve_url_as_text( url, cache = custom_cache )
    assert result == test_content
    assert custom_cache._configuration.contents_memory_max == 1024


#
# Series 800: Edge Case Coverage Tests
#


def test_800_content_cache_calculate_response_size_exception( ):
    ''' Exception responses use conservative size estimate. '''
    config = module.CacheConfiguration( )
    cache = module.ContentCache( config )
    error_response = _generics.Error( ValueError( 'Test error' ) )
    size = cache._calculate_response_size( error_response )
    assert size == 100  # Conservative estimate for exceptions


def test_801_content_cache_evict_empty_recency_queue( ):
    ''' Memory eviction handles empty recency queue gracefully. '''
    config = module.CacheConfiguration( contents_memory_max = 1 )
    cache = module.ContentCache( config )
    # Force memory total above limit but with empty recency queue
    cache._memory_total = 1000
    cache._recency.clear( )
    # Should not crash when trying to evict from empty queue
    cache._evict_by_memory( )
    assert cache._memory_total == 1000  # Unchanged since nothing to evict


def test_802_content_cache_remove_missing_entry( ):
    ''' Removing missing entry returns early without error. '''
    config = module.CacheConfiguration( )
    cache = module.ContentCache( config )
    # Should not crash when removing non-existent entry
    cache._remove( 'http://nonexistent.com' )
    assert len( cache._cache ) == 0


def test_803_probe_cache_evict_empty_recency_queue( ):
    ''' Count eviction handles empty recency queue gracefully. '''
    config = module.CacheConfiguration( probe_entries_max = 0 )
    cache = module.ProbeCache( config )
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
    cache = module.ProbeCache( module.CacheConfiguration( ) )
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
    cache = module.ContentCache( module.CacheConfiguration( ) )
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
    probe_cache = module.ProbeCache( module.CacheConfiguration( ) )
    await module.probe_url(
        url, cache = probe_cache, client_factory = client_factory )
    # Mutex should be cleaned up after request completes
    assert url_key not in probe_cache._request_mutexes

    # Test content cache mutex cleanup
    content_cache = module.ContentCache( module.CacheConfiguration( ) )
    await module.retrieve_url(
        url, cache = content_cache, client_factory = client_factory )
    # Mutex should be cleaned up after request completes
    assert url_key not in content_cache._request_mutexes


#
# Series 910: HTTP Error Conditions Tests
#


@pytest.mark.asyncio
async def test_910_probe_url_http_timeout_exception( ):
    ''' HTTP timeout exceptions are raised in probing. '''
    cache = module.ProbeCache( module.CacheConfiguration( ) )
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
    cache = module.ContentCache( module.CacheConfiguration( ) )
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
    cache = module.ContentCache( module.CacheConfiguration( ) )
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


