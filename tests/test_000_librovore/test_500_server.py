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


''' Unit tests for server module without MCP protocol dependencies. '''


import pytest
from unittest.mock import Mock, AsyncMock, patch

import librovore.server as module
import librovore.interfaces as _interfaces
import librovore.state as _state

from .fixtures import get_test_inventory_path


@pytest.fixture
def mock_auxdata( ):
    ''' Fixture providing mock auxdata/globals object. '''
    return Mock( spec = _state.Globals )


@pytest.mark.asyncio
async def test_100_summarize_inventory_wrapper( mock_auxdata ):
    ''' Server summarize_inventory factory produces working function. '''
    test_inventory_path = get_test_inventory_path( 'librovore' )
    search_behaviors = module.SearchBehaviorsMutable( )
    filters = module.FiltersMutable( { 'domain': 'py' } )
    summarize_func = module._produce_summarize_inventory_function(
        mock_auxdata )
    result = await summarize_func(
        location = test_inventory_path,
        search_behaviors = search_behaviors,
        filters = filters )
    assert isinstance( result, dict )
    assert result[ 'project' ] == 'python-sphinx-mcp-server'
    assert any( 'py' == obj.get( 'domain' ) for obj in result[ 'objects' ] )


@pytest.mark.asyncio
async def test_110_summarize_inventory_wrapper_no_filters( mock_auxdata ):
    ''' Server summarize_inventory works without filters. '''
    test_inventory_path = get_test_inventory_path( 'librovore' )
    summarize_func = module._produce_summarize_inventory_function(
        mock_auxdata )
    result = await summarize_func( location = test_inventory_path )
    assert isinstance( result, dict )
    assert result[ 'project' ] == 'python-sphinx-mcp-server'


@pytest.mark.asyncio
async def test_120_summarize_inventory_wrapper_with_regex( mock_auxdata ):
    ''' Server summarize_inventory handles match_mode parameter correctly. '''
    test_inventory_path = get_test_inventory_path( 'librovore' )
    search_behaviors = module.SearchBehaviorsMutable(
        match_mode = _interfaces.MatchMode.Regex )
    filters = module.FiltersMutable( )
    summarize_func = module._produce_summarize_inventory_function(
        mock_auxdata )
    result = await summarize_func(
        location = test_inventory_path,
        term = 'test.*pattern',
        search_behaviors = search_behaviors,
        filters = filters )
    assert isinstance( result, dict )
    assert result[ 'project' ] == 'python-sphinx-mcp-server'


@pytest.mark.asyncio
async def test_150_summarize_inventory_wrapper_with_priority( mock_auxdata ):
    ''' Server summarize_inventory handles priority filtering correctly. '''
    test_inventory_path = get_test_inventory_path( 'sphobjinv' )
    search_behaviors = module.SearchBehaviorsMutable( )
    filters = module.FiltersMutable( { 'priority': '0' } )
    summarize_func = module._produce_summarize_inventory_function(
        mock_auxdata )
    result = await summarize_func(
        location = test_inventory_path,
        search_behaviors = search_behaviors,
        filters = filters )
    assert isinstance( result, dict )
    assert 'objects' in result
    assert 'project' in result


@pytest.mark.asyncio
async def test_170_explore_wrapper( mock_auxdata ):
    ''' Server query_inventory factory produces working function. '''
    test_inventory_path = get_test_inventory_path( 'librovore' )
    search_behaviors = module.SearchBehaviorsMutable( )
    filters = module.FiltersMutable( { 'domain': 'py', 'role': 'function' } )
    query_func = module._produce_query_inventory_function( mock_auxdata )
    result = await query_func(
        location = test_inventory_path, term = 'test',
        search_behaviors = search_behaviors,
        filters = filters )
    assert isinstance( result, dict )
    assert 'project' in result
    assert 'search_metadata' in result


@pytest.mark.asyncio
async def test_180_explore_wrapper_no_filters( mock_auxdata ):
    ''' Server query_inventory works without filters. '''
    test_inventory_path = get_test_inventory_path( 'librovore' )
    query_func = module._produce_query_inventory_function( mock_auxdata )
    result = await query_func(
        location = test_inventory_path, term = 'test',
        details = module._interfaces.InventoryQueryDetails.Name )
    assert isinstance( result, dict )
    assert 'project' in result
    assert 'documents' in result
    assert 'search_metadata' in result


@pytest.mark.asyncio
async def test_190_explore_wrapper_with_fuzzy( mock_auxdata ):
    ''' Server query_inventory handles fuzzy matching correctly. '''
    test_inventory_path = get_test_inventory_path( 'sphobjinv' )
    search_behaviors = module.SearchBehaviorsMutable(
        match_mode = _interfaces.MatchMode.Fuzzy, fuzzy_threshold = 60 )
    filters = module.FiltersMutable( )
    query_func = module._produce_query_inventory_function( mock_auxdata )
    result = await query_func(
        location = test_inventory_path,
        term = 'DataObj',
        search_behaviors = search_behaviors,
        filters = filters,
        details = module._interfaces.InventoryQueryDetails.Name )
    assert isinstance( result, dict )
    assert 'search_metadata' in result
    assert 'documents' in result


@pytest.mark.asyncio
async def test_200_serve_transport_validation( ):
    ''' Serve function validates transport parameter correctly. '''
    mock_auxdata = Mock( )
    with pytest.raises( ValueError ):
        await module.serve( mock_auxdata, transport = 'invalid' )


@pytest.mark.asyncio
async def test_210_serve_stdio_transport( ):
    ''' Serve function accepts stdio transport without error. '''
    mock_auxdata = Mock( )
    with patch( 'mcp.server.fastmcp.FastMCP.run_stdio_async' ) as mock_run:
        mock_run.return_value = AsyncMock( )
        try: await module.serve( mock_auxdata, transport = 'stdio' )
        except ValueError:
            pytest.fail( "ValueError raised for valid transport 'stdio'" )


@pytest.mark.asyncio
async def test_220_serve_sse_transport( ):
    ''' Serve function accepts sse transport without error. '''
    mock_auxdata = Mock( )
    with patch( 'mcp.server.fastmcp.FastMCP.run_sse_async' ) as mock_run:
        mock_run.return_value = AsyncMock( )
        try: await module.serve( mock_auxdata, transport = 'sse' )
        except ValueError:
            pytest.fail( "ValueError raised for valid transport 'sse'" )


@pytest.mark.asyncio
async def test_230_serve_default_transport( ):
    ''' Serve function uses default transport when none specified. '''
    mock_auxdata = Mock( )
    with patch( 'mcp.server.fastmcp.FastMCP.run_stdio_async' ) as mock_run:
        mock_run.return_value = AsyncMock( )
        try: await module.serve( mock_auxdata )
        except ValueError:
            pytest.fail( "ValueError raised for default transport" )
