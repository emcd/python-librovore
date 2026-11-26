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


''' Tests for text decoding, edge cases, and request dedup. '''

# ruff: noqa: E501

import asyncio

from unittest.mock import Mock
from urllib.parse import ParseResult as Url

import appcore.generics as _generics
import httpx as _httpx
import pytest

import librovore.cacheproxy as module

from librovore import __
from librovore import exceptions as _exceptions

from .shared import _HEADERS_IMAGE_PNG, _URL_HTTP_TEST

#
# Series 350: retrieve_url_as_text Function Tests
#


@pytest.mark.asyncio
async def test_351_retrieve_url_as_text_unsupported_scheme_raises_exception( content_cache, robots_cache ):
    ''' Unsupported schemes raise DocumentationInaccessibility for text. '''
    url_ftp_txt = Url(
        scheme = 'ftp', netloc = 'example.com', path = '/test.txt',
        params = '', query = '', fragment = '' )
    with pytest.raises( _exceptions.DocumentationInaccessibility ):
        await module.retrieve_url_as_text( content_cache, url_ftp_txt )


@pytest.mark.asyncio
async def test_360_retrieve_url_as_text_file_scheme_utf8( fs, behaviors_harness, content_cache, robots_cache ):
    ''' UTF-8 files return decoded content as text. '''
    test_content = 'UTF-8 text content with émojis 🚀'
    fs.create_file(
        '/test/utf8.txt', contents = test_content, encoding = 'utf-8' )
    url = Url(
        scheme = 'file', netloc = '', path = '/test/utf8.txt',
        params = '', query = '', fragment = '' )
    result = await module.retrieve_url_as_text(
        content_cache, url, behaviors = behaviors_harness )
    assert result == test_content


@pytest.mark.asyncio
async def test_361_retrieve_url_as_text_file_scheme_custom_charset( fs, behaviors_harness, content_cache, robots_cache ):
    ''' Custom default charset is used for file text retrieval. '''
    test_content = 'ASCII content only'
    fs.create_file(
        '/test/ascii.txt', contents = test_content.encode( 'ascii' ) )
    url = Url(
        scheme = 'file', netloc = '', path = '/test/ascii.txt',
        params = '', query = '', fragment = '' )
    result = await module.retrieve_url_as_text(
        content_cache, url, charset_default = 'ascii',
        behaviors = behaviors_harness )
    assert result == test_content


@pytest.mark.asyncio
async def test_362_retrieve_url_as_text_http_cache_hit_with_charset( robots_cache ):
    ''' Cache hits extract charset from headers for text retrieval. '''
    mock_cache = Mock( spec = module.ContentCache )
    test_content = 'Cached text content'
    test_headers = _httpx.Headers( {
        'content-type': 'text/html; charset=iso-8859-1',
    } )
    mock_cache.access.return_value = (
        test_content.encode( 'iso-8859-1' ), test_headers )
    result = await module.retrieve_url_as_text(
        mock_cache, _URL_HTTP_TEST )
    assert result == test_content
    mock_cache.access.assert_called_once_with( _URL_HTTP_TEST.geturl( ) )


@pytest.mark.asyncio
async def test_363_retrieve_url_as_text_http_validates_content_type( robots_cache ):
    ''' Textual content type is validated for text retrieval. '''
    mock_cache = Mock( spec = module.ContentCache )
    mock_cache.access.return_value = ( b'binary data', _HEADERS_IMAGE_PNG )
    url_image = Url(
        scheme = 'http', netloc = 'example.com', path = '/image',
        params = '', query = '', fragment = '' )
    with pytest.raises( _exceptions.HttpContentTypeInvalidity ):
        await module.retrieve_url_as_text( mock_cache, url_image )


@pytest.mark.asyncio
async def test_364_retrieve_url_as_text_http_default_charset_fallback( robots_cache ):
    ''' Default charset is used as fallback when none specified. '''
    mock_cache = Mock( spec = module.ContentCache )
    test_content = 'Default charset content'
    test_headers = _httpx.Headers( { 'content-type': 'text/plain' } )
    mock_cache.access.return_value = (
        test_content.encode( 'utf-8' ), test_headers )
    url = Url(
        scheme = 'http', netloc = 'example.com', path = '/text',
        params = '', query = '', fragment = '' )
    result = await module.retrieve_url_as_text( mock_cache, url )
    assert result == test_content


@pytest.mark.asyncio
async def test_365_retrieve_url_as_text_http_cache_miss( robots_cache ):
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
        cache, url, client_factory = client_factory )
    assert result == test_content
    cached_result = await cache.access( url.geturl( ) )
    assert not __.is_absent( cached_result )
    cached_content, _ = cached_result
    assert cached_content.decode( 'utf-8' ) == test_content


@pytest.mark.asyncio
async def test_366_retrieve_url_as_text_http_cache_miss_custom_charset( robots_cache ):
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
        cache, url, client_factory = client_factory )
    assert result == test_content
    cached_result = await cache.access( url.geturl( ) )
    assert not __.is_absent( cached_result )
    cached_content, _ = cached_result
    assert cached_content.decode( 'iso-8859-1' ) == test_content


@pytest.mark.asyncio
async def test_367_unknown_header_charset_treated_as_absent( robots_cache ):
    ''' Unknown header charset falls back to detection. '''
    mock_cache = Mock( spec = module.ContentCache )
    test_content = 'UTF-8 text with emojis '
    test_headers = _httpx.Headers( {
        'content-type': 'text/plain; charset=invalid-review-charset',
    } )
    mock_cache.access.return_value = (
        test_content.encode( 'utf-8' ), test_headers )
    result = await module.retrieve_url_as_text(
        mock_cache, _URL_HTTP_TEST )
    assert result == test_content


@pytest.mark.asyncio
async def test_368_nontext_codec_header_stripped( robots_cache ):
    ''' Non-text codec header charset is stripped, MIME retained. '''
    mock_cache = Mock( spec = module.ContentCache )
    test_content = 'UTF-8 text with emojis '
    test_headers = _httpx.Headers( {
        'content-type': 'text/plain; charset=base64_codec',
    } )
    mock_cache.access.return_value = (
        test_content.encode( 'utf-8' ), test_headers )
    result = await module.retrieve_url_as_text(
        mock_cache, _URL_HTTP_TEST )
    assert result == test_content


@pytest.mark.asyncio
async def test_369_empty_nontextual_http_body_rejected( robots_cache ):
    ''' Empty body with non-textual MIME raises on cache hit. '''
    mock_cache = Mock( spec = module.ContentCache )
    mock_cache.access.return_value = ( b'', _HEADERS_IMAGE_PNG )
    url_image = Url(
        scheme = 'http', netloc = 'example.com', path = '/image',
        params = '', query = '', fragment = '' )
    with pytest.raises( _exceptions.HttpContentTypeInvalidity ):
        await module.retrieve_url_as_text( mock_cache, url_image )


@pytest.mark.asyncio
async def test_370_retrieve_url_as_text_dependency_injection( fs, behaviors_harness, robots_cache ):
    ''' Injected cache dependencies are accepted for text retrieval. '''
    custom_cache = module.ContentCache( memory_max = 1024 )
    test_content = 'Custom text content'
    fs.create_file( '/test/text.txt', contents = test_content )
    url = Url(
        scheme = 'file', netloc = '', path = '/test/text.txt',
        params = '', query = '', fragment = '' )
    result = await module.retrieve_url_as_text(
        custom_cache, url, behaviors = behaviors_harness )
    assert result == test_content
    assert custom_cache.memory_max == 1024


@pytest.mark.asyncio
async def test_371_empty_nontextual_http_body_rejected_miss( robots_cache ):
    ''' Empty body with non-textual MIME raises on cache miss. '''
    cache = module.ContentCache( )
    url_image = Url(
        scheme = 'http', netloc = 'example.com', path = '/image',
        params = '', query = '', fragment = '' )
    def handler( request ):
        return _httpx.Response(
            200, content = b'',
            headers = { 'content-type': 'image/png' } )
    mock_transport = _httpx.MockTransport( handler )
    def client_factory( ):
        return _httpx.AsyncClient( transport = mock_transport )
    with pytest.raises( _exceptions.HttpContentTypeInvalidity ):
        await module.retrieve_url_as_text(
            cache, url_image, client_factory = client_factory )


@pytest.mark.asyncio
async def test_372_empty_textual_body_valid( fs, behaviors_harness, content_cache, robots_cache ):
    ''' Empty textual bodies decode to empty string. '''
    mock_cache = Mock( spec = module.ContentCache )
    mock_cache.access.return_value = (
        b'', _httpx.Headers( { 'content-type': 'text/plain' } ) )
    result = await module.retrieve_url_as_text( mock_cache, _URL_HTTP_TEST )
    assert result == ''
    fs.create_file( '/test/empty.txt', contents = '' )
    url = Url(
        scheme = 'file', netloc = '', path = '/test/empty.txt',
        params = '', query = '', fragment = '' )
    result = await module.retrieve_url_as_text(
        content_cache, url, behaviors = behaviors_harness )
    assert result == ''


@pytest.mark.asyncio
async def test_373_wrong_header_charset_falls_back_to_default( robots_cache ):
    ''' Undecodable header charset retries with default charset. '''
    mock_cache = Mock( spec = module.ContentCache )
    test_content = 'Caf\u00e9 \U0001f680'
    test_headers = _httpx.Headers( {
        'content-type': 'text/plain; charset=iso-8859-1',
    } )
    mock_cache.access.return_value = (
        test_content.encode( 'utf-8' ), test_headers )
    result = await module.retrieve_url_as_text( mock_cache, _URL_HTTP_TEST )
    assert result == test_content


@pytest.mark.asyncio
async def test_374_undefined_header_charset_falls_back_hit( robots_cache ):
    ''' Always-failing header codec falls back to detection (hit). '''
    mock_cache = Mock( spec = module.ContentCache )
    mock_cache.access.return_value = (
        b'hello',
        _httpx.Headers( { 'content-type': 'text/plain; charset=undefined' } ) )
    result = await module.retrieve_url_as_text( mock_cache, _URL_HTTP_TEST )
    assert result == 'hello'


@pytest.mark.asyncio
async def test_375_undefined_header_charset_falls_back_miss( robots_cache ):
    ''' Always-failing header codec falls back to detection (miss). '''
    cache = module.ContentCache( )
    def handler( request ):
        if request.url.path.endswith( 'robots.txt' ):
            return _httpx.Response(
                200, content = b'User-agent: *\nAllow: /',
                headers = { 'content-type': 'text/plain' } )
        return _httpx.Response(
            200, content = b'hello',
            headers = {
                'content-type': 'text/plain; charset=undefined' } )
    mock_transport = _httpx.MockTransport( handler )
    def client_factory( ):
        return _httpx.AsyncClient( transport = mock_transport )
    result = await module.retrieve_url_as_text(
        cache, _URL_HTTP_TEST, client_factory = client_factory )
    assert result == 'hello'


@pytest.mark.asyncio
async def test_376_nullbyte_header_charset_falls_back_hit( robots_cache ):
    ''' Null-byte header charset is refused, MIME retained (hit). '''
    mock_cache = Mock( spec = module.ContentCache )
    mock_cache.access.return_value = (
        b'hello',
        _httpx.Headers( {
            'content-type': 'text/plain; charset="utf-8\x00"' } ) )
    result = await module.retrieve_url_as_text( mock_cache, _URL_HTTP_TEST )
    assert result == 'hello'


@pytest.mark.asyncio
async def test_377_nullbyte_header_charset_falls_back_miss( robots_cache ):
    ''' Null-byte header charset is refused, MIME retained (miss). '''
    cache = module.ContentCache( )
    def handler( request ):
        if request.url.path.endswith( 'robots.txt' ):
            return _httpx.Response(
                200, content = b'User-agent: *\nAllow: /',
                headers = { 'content-type': 'text/plain' } )
        return _httpx.Response(
            200, content = b'hello',
            headers = [ (
                b'content-type',
                b'text/plain; charset="utf-8\x00"' ) ] )
    mock_transport = _httpx.MockTransport( handler )
    def client_factory( ):
        return _httpx.AsyncClient( transport = mock_transport )
    result = await module.retrieve_url_as_text(
        cache, _URL_HTTP_TEST, client_factory = client_factory )
    assert result == 'hello'


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


# Series 900: HTTP Request Deduplication Tests
#


@pytest.mark.asyncio
async def test_900_probe_url_concurrent_requests_deduplication( robots_cache ):
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
            cache, url, client_factory = client_factory ),
        module.probe_url(
            cache, url, client_factory = client_factory ),
        module.probe_url(
            cache, url, client_factory = client_factory ) )
    assert all( results )
    # HTTP requests should be minimal due to deduplication (includes robots.txt check)
    assert call_count <= 2  # Main request + possible robots.txt check


@pytest.mark.asyncio
async def test_901_retrieve_url_concurrent_requests_deduplication( robots_cache ):
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
            cache, url, client_factory = client_factory ),
        module.retrieve_url(
            cache, url, client_factory = client_factory ),
        module.retrieve_url(
            cache, url, client_factory = client_factory ) )
    # All should return same content
    assert all( result == test_content for result in results )
    # HTTP requests should be minimal due to deduplication (includes robots.txt check)
    assert call_count <= 2  # Main request + possible robots.txt check


@pytest.mark.asyncio
async def test_902_request_mutex_cleanup_after_completion( robots_cache ):
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
        probe_cache, url, client_factory = client_factory )
    # Mutex should be cleaned up after request completes
    assert url_key not in probe_cache._request_mutexes

    # Test content cache mutex cleanup
    content_cache = module.ContentCache( )
    await module.retrieve_url(
        content_cache, url, client_factory = client_factory )
    # Mutex should be cleaned up after request completes
    assert url_key not in content_cache._request_mutexes
