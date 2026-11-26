# vim: set filetype=python fileencoding=utf-8:
# -*- coding: utf-8 -*-

#============================================================================#
#                                                                            #
#  Licensed under the Apache License, Version 2.0 (the "License");           #
#  you may not use this file except in compliance with the License.          #
#                                                                            #
#      http://www.apache.org/licenses/LICENSE-2.0                            #
#                                                                            #
#  Unless required by applicable law or agreed to in writing, software       #
#  distributed under the License is distributed on an "AS IS" BASIS,         #
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. #
#  See the License for the specific language governing permissions and       #
#  limitations under the License.                                            #
#                                                                            #
#============================================================================#


""" Real-filesystem decoding smoke tests with production defaults. """

from urllib.parse import ParseResult as Url

import pytest

import librovore.cacheproxy as module

from librovore import exceptions as _exceptions


@pytest.fixture
def delay_fn( ):
    """ No-op delay function for fast tests. """
    async def delay( seconds: float ) -> None:
        pass  # No-op for fast tests
    return delay


@pytest.fixture
def robots_cache( delay_fn ):
    """ Robots cache with test configuration. """
    return module.RobotsCache(
        entries_max = 250,
        ttl = 1800.0,
        request_timeout = 2.5,
        user_agent = 'test-agent',
        error_ttl = 30.0,
        success_ttl = 300.0,
        delay_function = delay_fn )


@pytest.fixture
def content_cache( delay_fn, robots_cache ):
    """ Content cache with test configuration. """
    return module.ContentCache(
        robots_cache = robots_cache,
        memory_max = 1024,
        error_ttl = 30.0,
        success_ttl = 300.0,
        delay_function = delay_fn )


def _file_url( path ) -> Url:
    return Url(
        scheme = 'file', netloc = '', path = str( path ),
        params = '', query = '', fragment = '' )


@pytest.mark.asyncio
async def test_010_utf8_file_decodes( tmp_path, content_cache ):
    """ UTF-8 file decodes with production-default detection. """
    target = tmp_path / 'utf8.txt'
    target.write_bytes( 'Caf\u00e9 \U0001f680'.encode( 'utf-8' ) )
    result = await module.retrieve_url_as_text(
        content_cache, _file_url( target ) )
    assert result == 'Caf\u00e9 \U0001f680'


@pytest.mark.asyncio
async def test_011_utf16_file_decodes( tmp_path, content_cache ):
    """ BOM-encoded file decodes via content detection. """
    target = tmp_path / 'utf16.txt'
    target.write_bytes( 'Caf\u00e9 au lait'.encode( 'utf-16' ) )
    result = await module.retrieve_url_as_text(
        content_cache, _file_url( target ) )
    assert result == 'Caf\u00e9 au lait'


@pytest.mark.asyncio
async def test_012_binary_file_rejected( tmp_path, content_cache ):
    """ Binary file raises inaccessibility with production defaults. """
    target = tmp_path / 'binary.bin'
    target.write_bytes( bytes( range( 256 ) ) * 4 )
    with pytest.raises( _exceptions.DocumentationInaccessibility ):
        await module.retrieve_url_as_text(
            content_cache, _file_url( target ) )


@pytest.mark.asyncio
async def test_013_empty_file_decodes_empty( tmp_path, content_cache ):
    """ Empty file decodes to empty string. """
    target = tmp_path / 'empty.txt'
    target.write_bytes( b'' )
    result = await module.retrieve_url_as_text(
        content_cache, _file_url( target ) )
    assert result == ''
