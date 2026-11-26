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


''' Preserved disabled tests for crawl delay and integration. '''

# ruff: noqa: E501

#
# Series 460: Crawl Delay Logic Tests
#


# @pytest.mark.asyncio
# async def test_460_apply_request_delay_non_http_scheme( ):
#     ''' Non-HTTP schemes have no delay applied. '''
#     file_url = Url(
#         scheme = 'file', netloc = '', path = '/test/file.txt',
#         params = '', query = '', fragment = '' )
#     # Should return immediately without delay
#     await module._apply_request_delay( file_url )
#     # No assertion needed - just ensuring no exception




# @pytest.mark.asyncio
# async def test_462_apply_request_delay_active_delay( ):
#     ''' Sleep occurs when delay is active. '''
#     mock_delay_fn = AsyncMock( )
#     robots_cache = module.RobotsCache( delay_function = mock_delay_fn )
#     domain = 'https://example.com'
#     # Set active delay
#     with patch.object( module.__.time, 'time', return_value = 1000.0 ):
#         robots_cache.assign_delay( domain, 2.0 )
#     url = Url(
#         scheme = 'https', netloc = 'example.com', path = '/test',
#         params = '', query = '', fragment = '' )
#     # Check delay function is called, use mock client factory to avoid network
#     mock_client = AsyncMock( )
#     mock_client_factory = Mock( return_value = mock_client )
#     with patch.object( module.__.time, 'time', return_value = 1001.0 ):
#         await module._apply_request_delay(
#             url, robots_cache = robots_cache,
#             client_factory = mock_client_factory )
#     mock_delay_fn.assert_called_once_with( 1.0 )


# @pytest.mark.asyncio
# async def test_463_apply_request_delay_expired_delay( ):
#     ''' No sleep when delay has expired. '''
#     robots_cache = module.RobotsCache( )
#     domain = 'https://example.com'
#     # Set expired delay
#     with patch.object( module.__.time, 'time', return_value = 1000.0 ):
#         robots_cache.assign_delay( domain, 2.0 )
#     url = Url(
#         scheme = 'https', netloc = 'example.com', path = '/test',
#         params = '', query = '', fragment = '' )
#     # Use mock client factory to avoid network calls
#     mock_client = AsyncMock( )
#     mock_client_factory = Mock( return_value = mock_client )
#     with (
#         patch.object( module.__.asyncio, 'sleep' ) as mock_sleep,
#         patch.object( module.__.time, 'time', return_value = 1005.0 )
#     ):
#         await module._apply_request_delay(
#             url, robots_cache = robots_cache,
#             client_factory = mock_client_factory )
#     mock_sleep.assert_not_called( )


# @pytest.mark.asyncio
# async def test_464_apply_request_delay_set_new_delay(
#     safe_robots_parser_factory
# ):
#     ''' Sets delay from robots.txt crawl-delay directive. '''
#     robots_cache = module.RobotsCache( )
#     parser = safe_robots_parser_factory( 'with_crawl_delay' )
#     response = _generics.Value( parser )
#     with patch.object( module.__.time, 'time', return_value = 1000.0 ):
#         await robots_cache.store( 'https://example.com', response, 3600.0 )
#     url = Url(
#         scheme = 'https', netloc = 'example.com', path = '/test',
#         params = '', query = '', fragment = '' )
#     with patch.object( module.__.time, 'time', return_value = 1000.0 ):
#         await module._apply_request_delay(
#             url, robots_cache = robots_cache )
#     # Should have set delay for 2 seconds (from robots.txt)
#     expected_time = 1000.0 + 2.0
#     assert (
#         robots_cache._request_delays[ 'https://example.com' ]
#         == expected_time )


# @pytest.mark.asyncio
# async def test_465_apply_request_delay_no_crawl_delay( robots_txt_samples ):
#     ''' robots.txt with no Crawl-delay sets no delay. '''
#     robots_cache = module.RobotsCache( )
#     from urllib.robotparser import RobotFileParser
#     parser = RobotFileParser( )
#     parser.set_url( 'https://example.com/robots.txt' )
#     parser.parse( robots_txt_samples[ 'allow_all' ].splitlines( ) )
#     response = _generics.Value( parser )
#     with patch.object( module.__.time, 'time', return_value = 1000.0 ):
#         await robots_cache.store( 'https://example.com', response, 3600.0 )
#     url = Url(
#         scheme = 'https', netloc = 'example.com', path = '/test',
#         params = '', query = '', fragment = '' )
#     await module._apply_request_delay( url, robots_cache = robots_cache )
#     # Should not have set any delay
#     assert 'https://example.com' not in robots_cache._request_delays


# @pytest.mark.asyncio
# async def test_466_apply_request_delay_invalid_crawl_delay( ):
#     ''' Non-numeric Crawl-delay values are handled gracefully. '''
#     robots_cache = module.RobotsCache( )
#     from urllib.robotparser import RobotFileParser
#     parser = RobotFileParser( )
#     parser.set_url( 'https://example.com/robots.txt' )
#     parser.parse( [ 'User-agent: *', 'Crawl-delay: invalid' ] )
#     response = _generics.Value( parser )
#     with patch.object( module.__.time, 'time', return_value = 1000.0 ):
#         await robots_cache.store( 'https://example.com', response, 3600.0 )
#     url = Url(
#         scheme = 'https', netloc = 'example.com', path = '/test',
#         params = '', query = '', fragment = '' )
#     await module._apply_request_delay( url, robots_cache = robots_cache )
#     # Should handle gracefully without setting delay
#     assert 'https://example.com' not in robots_cache._request_delays


# @pytest.mark.asyncio
# async def test_467_apply_request_delay_robots_parser_exception( ):
#     ''' Exception getting crawl delay is handled gracefully. '''
#     robots_cache = module.RobotsCache( )
#     from urllib.robotparser import RobotFileParser
#     parser = Mock( spec = RobotFileParser )
#     parser.crawl_delay.side_effect = Exception( 'Parser error' )
#     response = _generics.Value( parser )
#     with patch.object( module.__.time, 'time', return_value = 1000.0 ):
#         await robots_cache.store( 'https://example.com', response, 3600.0 )
#     url = Url(
#         scheme = 'https', netloc = 'example.com', path = '/test',
#         params = '', query = '', fragment = '' )
#     await module._apply_request_delay( url, robots_cache = robots_cache )
#     # Should handle exception gracefully
#     assert 'https://example.com' not in robots_cache._request_delays


# @pytest.mark.asyncio
# async def test_469_apply_request_delay_time_calculation( ):
#     ''' Delay timestamp calculation is correct. '''
#     robots_cache = module.RobotsCache( )
#     domain = 'https://example.com'
#     with patch.object( module.__.time, 'time', return_value = 1234.5 ):
#         robots_cache.assign_delay( domain, 7.5 )
#     expected_time = 1234.5 + 7.5
#     assert robots_cache._request_delays[ domain ] == expected_time


#
# Series 480: Integration Tests
#


# @pytest.mark.asyncio
# async def test_480_probe_url_robots_txt_blocked( robots_txt_samples ):
#     ''' probe_url respects robots.txt blocking. '''
#     probe_cache = module.ProbeCache( )
#     def handler( request ):
#         if request.url.path == '/robots.txt':
#             return _httpx.Response(
#                 200, text = robots_txt_samples[ 'block_all' ] )
#         return _httpx.Response( 200 )
#     mock_transport = _httpx.MockTransport( handler )
#     def client_factory( ):
#         return _httpx.AsyncClient( transport = mock_transport )
#     url = Url(
#         scheme = 'https', netloc = 'block-test.com', path = '/test',
#         params = '', query = '', fragment = '' )
#     with pytest.raises( _exceptions.UrlImpermissibility ):
#         await module.probe_url(
#             url, cache = probe_cache, client_factory = client_factory )


# @pytest.mark.asyncio
# async def test_481_probe_url_robots_txt_allowed( robots_txt_samples ):
#     ''' probe_url allows access when robots.txt permits. '''
#     probe_cache = module.ProbeCache( )
#     def handler( request ):
#         if request.url.path == '/robots.txt':
#             return _httpx.Response(
#                 200, text = robots_txt_samples[ 'allow_all' ] )
#         return _httpx.Response( 200 )
#     mock_transport = _httpx.MockTransport( handler )
#     def client_factory( ):
#         return _httpx.AsyncClient( transport = mock_transport )
#     url = Url(
#         scheme = 'https', netloc = 'allow-test.com', path = '/test',
#         params = '', query = '', fragment = '' )
#     result = await module.probe_url(
#         url, cache = probe_cache, client_factory = client_factory )
#     assert result is True


# @pytest.mark.asyncio
# async def test_482_retrieve_url_robots_txt_blocked( robots_txt_samples ):
#     ''' retrieve_url respects robots.txt blocking. '''
#     def handler( request ):
#         if request.url.path == '/robots.txt':
#             return _httpx.Response(
#                 200, text = robots_txt_samples[ 'block_all' ] )
#         return _httpx.Response( 200, content = b'test content' )
#     mock_transport = _httpx.MockTransport( handler )
#     def client_factory( ):
#         return _httpx.AsyncClient( transport = mock_transport )
#     content_cache = module.ContentCache( )
#     url = Url(
#         scheme = 'https', netloc = 'blocked-retrieve.com', path = '/test',
#         params = '', query = '', fragment = '' )
#     with pytest.raises( _exceptions.UrlImpermissibility ):
#         await module.retrieve_url(
#             url, cache = content_cache, client_factory = client_factory )


# @pytest.mark.asyncio
# async def test_483_retrieve_url_robots_txt_allowed( robots_txt_samples ):
#     ''' retrieve_url allows access when robots.txt permits. '''
#     test_content = b'allowed content'
#     def handler( request ):
#         if request.url.path == '/robots.txt':
#             return _httpx.Response(
#                 200, text = robots_txt_samples[ 'allow_all' ] )
#         return _httpx.Response( 200, content = test_content )
#     mock_transport = _httpx.MockTransport( handler )
#     def client_factory( ):
#         return _httpx.AsyncClient( transport = mock_transport )
#     content_cache = module.ContentCache( )
#     url = Url(
#         scheme = 'https', netloc = 'allowed-retrieve.com', path = '/test',
#         params = '', query = '', fragment = '' )
#     result = await module.retrieve_url(
#         url, cache = content_cache, client_factory = client_factory )
#     assert result == test_content


# @pytest.mark.asyncio
# async def test_484_retrieve_url_as_text_robots_txt_blocked(
#         robots_txt_samples ):
#     ''' retrieve_url_as_text respects robots.txt blocking. '''
#     def handler( request ):
#         if request.url.path == '/robots.txt':
#             return _httpx.Response(
#                 200, text = robots_txt_samples[ 'block_all' ] )
#         return _httpx.Response(
#             200, content = b'test content',
#             headers = { 'content-type': 'text/plain' } )
#     mock_transport = _httpx.MockTransport( handler )
#     def client_factory( ):
#         return _httpx.AsyncClient( transport = mock_transport )
#     content_cache = module.ContentCache( )
#     url = Url(
#         scheme = 'https', netloc = 'blocked-text.com', path = '/test',
#         params = '', query = '', fragment = '' )
#     with pytest.raises( _exceptions.UrlImpermissibility ):
#         await module.retrieve_url_as_text(
#             url, cache = content_cache, client_factory = client_factory )


# @pytest.mark.asyncio
# async def test_485_robots_txt_integration_with_caching( robots_txt_samples ):
#     ''' robots.txt works correctly with HTTP caching. '''
#     content_cache = module.ContentCache( )
#     test_content = b'cached content'
#     def handler( request ):
#         if request.url.path == '/robots.txt':
#             return _httpx.Response(
#                 200, text = robots_txt_samples[ 'block_specific' ] )
#         return _httpx.Response( 200, content = test_content )
#     mock_transport = _httpx.MockTransport( handler )
#     def client_factory( ):
#         return _httpx.AsyncClient( transport = mock_transport )
#     # Allowed path
#     allowed_url = Url(
#         scheme = 'https', netloc = 'example.com', path = '/public/data',
#         params = '', query = '', fragment = '' )
#     result = await module.retrieve_url(
#         allowed_url, cache = content_cache, client_factory = client_factory )
#     assert result == test_content
#     # Should be cached
#     cached_result = await content_cache.access( allowed_url.geturl( ) )
#     assert not __.is_absent( cached_result )


# @pytest.mark.asyncio
# async def test_486_robots_txt_crawl_delay_integration( robots_txt_samples ):
#     ''' Crawl delay integrates correctly with HTTP requests. '''
#     content_cache = module.ContentCache( )
#     test_content = b'delayed content'
#     def handler( request ):
#         if request.url.path == '/robots.txt':
#             return _httpx.Response(
#                 200, text = robots_txt_samples[ 'with_crawl_delay' ] )
#         return _httpx.Response( 200, content = test_content )
#     mock_transport = _httpx.MockTransport( handler )
#     def client_factory( ):
#         return _httpx.AsyncClient( transport = mock_transport )
#     url = Url(
#         scheme = 'https', netloc = 'crawl-delay.com', path = '/test',
#         params = '', query = '', fragment = '' )
#     # First request should set delay
#     with patch.object( module.__.time, 'time', return_value = 1000.0 ):
#         result = await module.retrieve_url(
#             url, cache = content_cache, client_factory = client_factory )
#     assert result == test_content
#     # Should have set crawl delay in default cache
#     assert (
#         'https://crawl-delay.com'
#         in module._robots_cache_default._request_delays )


# @pytest.mark.asyncio
# async def test_487_robots_txt_custom_user_agent_integration(
#         robots_txt_samples ):
#     ''' Custom user agent works through entire integration. '''
#     robots_cache1 = module.RobotsCache( )
#     robots_cache2 = module.RobotsCache( )
#     custom_robots_txt = (
#         'User-agent: custom-bot\nDisallow: /\n\nUser-agent: *\nAllow: /' )
#     def handler( request ):
#         if request.url.path == '/robots.txt':
#             return _httpx.Response( 200, text = custom_robots_txt )
#         return _httpx.Response( 200, content = b'content' )
#     mock_transport = _httpx.MockTransport( handler )
#     def client_factory( ):
#         return _httpx.AsyncClient( transport = mock_transport )
#     url = Url(
#         scheme = 'https', netloc = 'custom-agent.com', path = '/test',
#         params = '', query = '', fragment = '' )
#     # Should be blocked for custom-bot but allowed for default agent
#     result = await module._check_robots_txt(
#         url, robots_cache = robots_cache1, user_agent = 'custom-bot',
#         client_factory = client_factory )
#     assert result is False
#     result = await module._check_robots_txt(
#         url, robots_cache = robots_cache2, client_factory = client_factory )
#     assert result is True


# @pytest.mark.asyncio
# async def test_488_robots_txt_domain_based_caching( robots_txt_samples ):
#     ''' Multiple domains are cached separately. '''
#     robots_cache = module.RobotsCache( )
#     def handler( request ):
#         if 'example1' in str( request.url ):
#             return _httpx.Response(
#                 200, text = robots_txt_samples[ 'allow_all' ] )
#         return _httpx.Response(
#             200, text = robots_txt_samples[ 'block_all' ] )
#     mock_transport = _httpx.MockTransport( handler )
#     def client_factory( ):
#         return _httpx.AsyncClient( transport = mock_transport )
#     url1 = Url(
#         scheme = 'https', netloc = 'example1.com', path = '/test',
#         params = '', query = '', fragment = '' )
#     url2 = Url(
#         scheme = 'https', netloc = 'example2.com', path = '/test',
#         params = '', query = '', fragment = '' )
#     result1 = await module._check_robots_txt(
#         url1, robots_cache = robots_cache, client_factory = client_factory )
#     result2 = await module._check_robots_txt(
#         url2, robots_cache = robots_cache, client_factory = client_factory )
#     assert result1 is True
#     assert result2 is False
#     # Both domains should be cached
#     assert 'https://example1.com' in robots_cache._cache
#     assert 'https://example2.com' in robots_cache._cache


# @pytest.mark.asyncio
# async def test_489_robots_txt_error_propagation( ):
#     ''' Network errors propagate correctly through call chain. '''
#     def handler( request ):
#         if request.url.path == '/robots.txt':
#             raise _httpx.ConnectError( 'Connection failed' )
#         return _httpx.Response( 200, content = b'content' )
#     mock_transport = _httpx.MockTransport( handler )
#     def client_factory( ):
#         return _httpx.AsyncClient( transport = mock_transport )
#     url = Url(
#         scheme = 'https', netloc = 'example.com', path = '/test',
#         params = '', query = '', fragment = '' )
#     # Should allow access when robots.txt fetch fails
#     result = await module._check_robots_txt(
#         url, client_factory = client_factory )
#     assert result is True
