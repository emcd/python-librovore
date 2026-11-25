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


''' Tests for robots cache, domains, and robots.txt fetching. '''

# ruff: noqa: E501

from unittest.mock import patch
from urllib.parse import ParseResult as Url

import appcore.generics as _generics
import pytest

import librovore.cacheproxy as module

#
# Series 400: RobotsCache Class Tests
#


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


# @pytest.mark.asyncio
# async def test_401_robots_cache_access_missing_returns_absent( robots_cache ):
#     ''' Cache miss returns absent when domain not cached. '''
#     result = await robots_cache.access( 'https://example.com' )
#     assert __.is_absent( result )


# @pytest.mark.asyncio
# async def test_402_robots_cache_access_fresh_returns_parser(
#     robots_cache, safe_robots_parser_factory
# ):
#     ''' Fresh entries return robots parser from cache access. '''
#     parser = safe_robots_parser_factory( )
#     response = _generics.Value( parser )
#     with patch.object( module.__.time, 'time', return_value = 1000.0 ):
#         await robots_cache.store( 'https://example.com', response, 3600.0 )
#     with patch.object( module.__.time, 'time', return_value = 1100.0 ):
#         result = await robots_cache.access( 'https://example.com' )
#     assert not __.is_absent( result )
#     from urllib.robotparser import RobotFileParser
#     assert isinstance( result, RobotFileParser )


# @pytest.mark.asyncio
# async def test_403_robots_cache_access_expired_returns_absent(
#     robots_cache, safe_robots_parser_factory
# ):
#     ''' Expired entries return absent and are removed from cache. '''
#     parser = safe_robots_parser_factory( )
#     response = _generics.Value( parser )
#     domain = 'https://example.com'
#     with patch.object( module.__.time, 'time', return_value = 1000.0 ):
#         await robots_cache.store( domain, response, 3600.0 )
#     with patch.object( module.__.time, 'time', return_value = 5000.0 ):
#         result = await robots_cache.access( domain )
#     assert __.is_absent( result )
#     assert domain not in robots_cache._cache


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


# @pytest.mark.asyncio
# async def test_409_robots_cache_record_access_updates_lru( ):
#     ''' Accessing entries moves domains to end of recency queue. '''
#     cache = module.RobotsCache( )
#     from urllib.robotparser import RobotFileParser
#     # Store multiple entries
#     for i in range( 3 ):
#         parser = RobotFileParser( )
#         response = _generics.Value( parser )
#         domain = f'https://example{i}.com'
#         with patch.object( module.__.time, 'time', return_value = 1000.0 + i ):
#             await cache.store( domain, response, 3600.0 )
#     # Access middle entry
#     with patch.object( module.__.time, 'time', return_value = 1100.0 ):
#         await cache.access( 'https://example1.com' )
#     # Should have moved example1 to end
#     assert list( cache._recency ) == [
#         'https://example0.com',
#         'https://example2.com',
#         'https://example1.com'
#     ]


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


# @pytest.mark.asyncio
# async def test_420_check_robots_txt_allowed_url( robots_txt_samples ):
#     ''' URLs allowed by robots.txt return True. '''
#     robots_cache = module.RobotsCache( )
#     def handler( request ):
#         return _httpx.Response( 200, text = robots_txt_samples[ 'allow_all' ] )
#     mock_transport = _httpx.MockTransport( handler )
#     def client_factory( ):
#         return _httpx.AsyncClient( transport = mock_transport )
#     url = Url(
#         scheme = 'https', netloc = 'allowed-example.com', path = '/test',
#         params = '', query = '', fragment = '' )
#     result = await module._check_robots_txt(
#         url, robots_cache = robots_cache, client_factory = client_factory )
#     assert result is True


# @pytest.mark.asyncio
# async def test_421_check_robots_txt_blocked_url( robots_txt_samples ):
#     ''' URLs blocked by robots.txt return False. '''
#     robots_cache = module.RobotsCache( )
#     def handler( request ):
#         return _httpx.Response( 200, text = robots_txt_samples[ 'block_all' ] )
#     mock_transport = _httpx.MockTransport( handler )
#     def client_factory( ):
#         return _httpx.AsyncClient( transport = mock_transport )
#     url = Url(
#         scheme = 'https', netloc = 'blocked-example.com', path = '/test',
#         params = '', query = '', fragment = '' )
#     result = await module._check_robots_txt(
#         url, robots_cache = robots_cache, client_factory = client_factory )
#     assert result is False


# @pytest.mark.asyncio
# async def test_422_check_robots_txt_non_http_scheme( ):
#     ''' File and FTP schemes always return True. '''
#     file_url = Url(
#         scheme = 'file', netloc = '', path = '/test/file.txt',
#         params = '', query = '', fragment = '' )
#     ftp_url = Url(
#         scheme = 'ftp', netloc = 'ftp.example.com', path = '/test',
#         params = '', query = '', fragment = '' )
#     assert await module._check_robots_txt( file_url ) is True
#     assert await module._check_robots_txt( ftp_url ) is True


# @pytest.mark.asyncio
# async def test_423_check_robots_txt_missing_robots_file( ):
#     ''' Missing robots.txt allows access by default. '''
#     robots_cache = module.RobotsCache( )
#     def handler( request ):
#         return _httpx.Response( 404 )
#     mock_transport = _httpx.MockTransport( handler )
#     def client_factory( ):
#         return _httpx.AsyncClient( transport = mock_transport )
#     url = Url(
#         scheme = 'https', netloc = 'missing-robots.com', path = '/test',
#         params = '', query = '', fragment = '' )
#     result = await module._check_robots_txt(
#         url, robots_cache = robots_cache, client_factory = client_factory )
#     assert result is True


# @pytest.mark.asyncio
# async def test_424_check_robots_txt_malformed_robots_file(
#         robots_txt_samples ):
#     ''' Malformed robots.txt content allows access by default. '''
#     robots_cache = module.RobotsCache( )
#     def handler( request ):
#         return _httpx.Response( 200, text = robots_txt_samples[ 'malformed' ] )
#     mock_transport = _httpx.MockTransport( handler )
#     def client_factory( ):
#         return _httpx.AsyncClient( transport = mock_transport )
#     url = Url(
#         scheme = 'https', netloc = 'malformed-example.com', path = '/test',
#         params = '', query = '', fragment = '' )
#     result = await module._check_robots_txt(
#         url, robots_cache = robots_cache, client_factory = client_factory )
#     assert result is True


# @pytest.mark.asyncio
# async def test_425_check_robots_txt_cache_hit( robots_txt_samples ):
#     ''' Cached robots.txt parser is used when available. '''
#     from urllib.robotparser import RobotFileParser
#     robots_cache = module.RobotsCache( )
#     parser = RobotFileParser( )
#     parser.set_url( 'https://example.com/robots.txt' )
#     parser.parse( robots_txt_samples[ 'allow_all' ].splitlines( ) )
#     response = _generics.Value( parser )
#     with patch.object( module.__.time, 'time', return_value = 1000.0 ):
#         await robots_cache.store( 'https://example.com', response, 3600.0 )
#     url = Url(
#         scheme = 'https', netloc = 'example.com', path = '/test',
#         params = '', query = '', fragment = '' )
#     result = await module._check_robots_txt(
#         url, robots_cache = robots_cache )
#     assert result is True


# @pytest.mark.asyncio
# async def test_427_check_robots_txt_custom_user_agent( robots_txt_samples ):
#     ''' Custom user agent is passed to robots.txt parser. '''
#     def handler( request ):
#         return _httpx.Response( 200, text = robots_txt_samples[ 'allow_all' ] )
#     mock_transport = _httpx.MockTransport( handler )
#     def client_factory( ):
#         return _httpx.AsyncClient( transport = mock_transport )
#     url = Url(
#         scheme = 'https', netloc = 'example.com', path = '/test',
#         params = '', query = '', fragment = '' )
#     result = await module._check_robots_txt(
#         url, user_agent = 'custom-bot/1.0', client_factory = client_factory )
#     assert result is True


# @pytest.mark.asyncio
# async def test_428_check_robots_txt_default_user_agent( robots_txt_samples ):
#     ''' Default user agent from configuration is used. '''
#     def handler( request ):
#         return _httpx.Response( 200, text = robots_txt_samples[ 'allow_all' ] )
#     mock_transport = _httpx.MockTransport( handler )
#     def client_factory( ):
#         return _httpx.AsyncClient( transport = mock_transport )
#     url = Url(
#         scheme = 'https', netloc = 'example.com', path = '/test',
#         params = '', query = '', fragment = '' )
#     result = await module._check_robots_txt(
#         url, client_factory = client_factory )
#     assert result is True


# @pytest.mark.asyncio
# async def test_429_check_robots_txt_parser_exception( robots_txt_samples ):
#     ''' Exception during parser can_fetch call allows access. '''
#     from urllib.robotparser import RobotFileParser
#     robots_cache = module.RobotsCache( )
#     # Create a mock parser that raises exception on can_fetch
#     parser = Mock( spec = RobotFileParser )
#     parser.can_fetch.side_effect = Exception( 'Parser error' )
#     response = _generics.Value( parser )
#     with patch.object( module.__.time, 'time', return_value = 1000.0 ):
#         await robots_cache.store( 'https://example.com', response, 3600.0 )
#     url = Url(
#         scheme = 'https', netloc = 'example.com', path = '/test',
#         params = '', query = '', fragment = '' )
#     result = await module._check_robots_txt(
#         url, robots_cache = robots_cache )
#     assert result is True


#
# Series 440: robots.txt Fetching and Parsing Tests
#


# @pytest.mark.asyncio
# async def test_440_retrieve_robots_txt_success( robots_txt_samples ):
#     ''' Successful fetch and parse returns parser. '''
#     robots_cache = module.RobotsCache( )
#     def handler( request ):
#         return _httpx.Response( 200, text = robots_txt_samples[ 'allow_all' ] )
#     mock_transport = _httpx.MockTransport( handler )
#     def client_factory( ):
#         return _httpx.AsyncClient( transport = mock_transport )
#     result = await module._retrieve_robots_txt(
#         'https://example.com', robots_cache, client_factory = client_factory )
#     assert not __.is_absent( result )
#     assert result.can_fetch( 'test-agent', 'https://example.com/test' )


# @pytest.mark.asyncio
# async def test_441_retrieve_robots_txt_http_error( ):
#     ''' HTTP 404 for robots.txt returns empty parser allowing all access. '''
#     robots_cache = module.RobotsCache( )
#     def handler( request ):
#         return _httpx.Response( 404 )
#     mock_transport = _httpx.MockTransport( handler )
#     def client_factory( ):
#         return _httpx.AsyncClient( transport = mock_transport )
#     result = await module._retrieve_robots_txt(
#         'https://example.com', robots_cache, client_factory = client_factory )
#     assert not __.is_absent( result )
#     assert result.can_fetch( 'librovore/1.0', '/objects.inv' )


# @pytest.mark.asyncio
# async def test_442_retrieve_robots_txt_timeout( ):
#     ''' Request timeout returns absent. '''
#     robots_cache = module.RobotsCache( )
#     def handler( request ):
#         raise _httpx.TimeoutException( 'Timeout' )
#     mock_transport = _httpx.MockTransport( handler )
#     def client_factory( ):
#         return _httpx.AsyncClient( transport = mock_transport )
#     result = await module._retrieve_robots_txt(
#         'https://example.com', robots_cache, client_factory = client_factory )
#     assert __.is_absent( result )


# @pytest.mark.asyncio
# async def test_443_retrieve_robots_txt_parse_error( ):
#     ''' robots.txt parsing failure returns absent. '''
#     robots_cache = module.RobotsCache( )
#     def handler( request ):
#         return _httpx.Response(
#             200, text = 'Invalid robots.txt\nwith bad syntax' )
#     mock_transport = _httpx.MockTransport( handler )
#     def client_factory( ):
#         return _httpx.AsyncClient( transport = mock_transport )
#     result = await module._retrieve_robots_txt(
#         'https://example.com', robots_cache, client_factory = client_factory )
#     # Should still work as robotparser is quite forgiving
#     assert not __.is_absent( result )


# @pytest.mark.asyncio
# async def test_444_retrieve_robots_txt_empty_content( robots_txt_samples ):
#     ''' Empty robots.txt file parses successfully. '''
#     robots_cache = module.RobotsCache( )
#     def handler( request ):
#         return _httpx.Response( 200, text = robots_txt_samples[ 'empty' ] )
#     mock_transport = _httpx.MockTransport( handler )
#     def client_factory( ):
#         return _httpx.AsyncClient( transport = mock_transport )
#     result = await module._retrieve_robots_txt(
#         'https://example.com', robots_cache, client_factory = client_factory )
#     assert not __.is_absent( result )
#     assert result.can_fetch( 'test-agent', 'https://example.com/test' )


# @pytest.mark.asyncio
# async def test_445_retrieve_robots_txt_mutex_deduplication(
#         robots_txt_samples
# ):
#     ''' Multiple concurrent requests ensure consistent cache state. '''
#     robots_cache = module.RobotsCache( )
#     def handler( request ):
#         return _httpx.Response( 200, text = robots_txt_samples[ 'allow_all' ] )
#     mock_transport = _httpx.MockTransport( handler )
#     def client_factory( ):
#         return _httpx.AsyncClient( transport = mock_transport )
#     # Make concurrent requests
#     results = await asyncio.gather(
#         module._retrieve_robots_txt(
#             'https://dedupe-test.com', robots_cache,
#             client_factory = client_factory ),
#         module._retrieve_robots_txt(
#             'https://dedupe-test.com', robots_cache,
#             client_factory = client_factory ),
#         module._retrieve_robots_txt(
#             'https://dedupe-test.com', robots_cache,
#             client_factory = client_factory ) )
#     # All should succeed
#     assert all( not __.is_absent( result ) for result in results )
#     # Cache should contain exactly one entry for the domain
#     assert len( robots_cache._cache ) == 1
#     assert 'https://dedupe-test.com' in robots_cache._cache


# @pytest.mark.asyncio
# async def test_446_retrieve_robots_txt_custom_client_factory(
#         robots_txt_samples ):
#     ''' Custom httpx client factory is used correctly. '''
#     robots_cache = module.RobotsCache( )
#     def handler( request ):
#         return _httpx.Response( 200, text = robots_txt_samples[ 'allow_all' ] )
#     mock_transport = _httpx.MockTransport( handler )
#     def custom_client_factory( ):
#         return _httpx.AsyncClient( transport = mock_transport )
#     result = await module._retrieve_robots_txt(
#         'https://example.com', robots_cache,
#         client_factory = custom_client_factory )
#     assert not __.is_absent( result )


# @pytest.mark.asyncio
# async def test_448_retrieve_robots_txt_ttl_determination( ):
#     ''' TTL is calculated and applied correctly. '''
#     robots_cache = module.RobotsCache( )
#     def handler( request ):
#         return _httpx.Response( 404 )  # Missing robots.txt (success case)
#     mock_transport = _httpx.MockTransport( handler )
#     def client_factory( ):
#         return _httpx.AsyncClient( transport = mock_transport )
#     await module._retrieve_robots_txt(
#         'https://example.com', robots_cache, client_factory = client_factory )
#     # Check that success was cached with appropriate TTL
#     assert 'https://example.com' in robots_cache._cache
#     entry = robots_cache._cache[ 'https://example.com' ]
#     assert entry.response.is_value( )
#     assert entry.ttl == robots_cache.ttl


# @pytest.mark.asyncio
# async def test_449_retrieve_robots_txt_error_result_extraction( ):
#     ''' Error result extraction returns absent correctly. '''
#     robots_cache = module.RobotsCache( )
#     def handler( request ):
#         raise _httpx.ConnectError( 'Connection failed' )
#     mock_transport = _httpx.MockTransport( handler )
#     def client_factory( ):
#         return _httpx.AsyncClient( transport = mock_transport )
#     result = await module._retrieve_robots_txt(
#         'https://example.com', robots_cache, client_factory = client_factory )
#     assert __.is_absent( result )
