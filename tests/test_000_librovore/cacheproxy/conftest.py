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


import httpx as _httpx
import pytest

import librovore.cacheproxy as module


@pytest.fixture
def test_delay_fn( ):
    ''' No-op delay function for fast tests. '''
    async def delay( seconds: float ) -> None:
        pass  # No-op for fast tests
    return delay


@pytest.fixture
def content_cache( test_delay_fn, robots_cache ):
    ''' Content cache with test configuration. '''
    return module.ContentCache(
        robots_cache = robots_cache,
        memory_max = 1024,
        error_ttl = 30.0,
        success_ttl = 300.0,
        delay_function = test_delay_fn )


@pytest.fixture
def probe_cache( test_delay_fn, robots_cache ):
    ''' Probe cache with test configuration. '''
    return module.ProbeCache(
        robots_cache = robots_cache,
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


@pytest.fixture
def safe_robots_parser_factory( robots_txt_samples ):
    ''' Factory for creating safe RobotFileParser instances. '''
    def _create_parser(
        sample_name = 'basic_allow_all',
        url = 'https://example.com/robots.txt'
    ):
        from urllib.robotparser import RobotFileParser
        parser = RobotFileParser( )
        parser.set_url( url )
        sample_content = robots_txt_samples.get(
            sample_name, 'User-agent: *\nAllow: /' )
        parser.parse( sample_content.splitlines( ) )
        return parser
    return _create_parser


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
        pathlib.Path( __file__ ).parent.parent.parent
        / 'data' / 'robots_txt_samples' )
    samples = { }
    for sample_file in samples_dir.glob( '*.txt' ):
        samples[ sample_file.stem ] = sample_file.read_text( )
    return samples
