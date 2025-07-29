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

import sphinxmcps.server as module
import sphinxmcps.interfaces as _interfaces

from .fixtures import get_test_inventory_path


@pytest.mark.asyncio
async def test_100_summarize_inventory_wrapper( ):
    ''' Server summarize_inventory delegates to functions correctly. '''
    test_inventory_path = get_test_inventory_path( 'sphinxmcps' )
    search_behaviors = module._interfaces.SearchBehaviors( )
    filters = module.FiltersMutable( { 'domain': 'py' } )
    result = await module.summarize_inventory(
        source = test_inventory_path,
        search_behaviors = search_behaviors,
        filters = filters )
    assert isinstance( result, str )
    assert 'Project:' in result
    assert 'py' in result


@pytest.mark.asyncio
async def test_110_summarize_inventory_wrapper_no_filters( ):
    ''' Server summarize_inventory works without filters. '''
    test_inventory_path = get_test_inventory_path( 'sphinxmcps' )
    result = await module.summarize_inventory( source = test_inventory_path )
    assert isinstance( result, str )
    assert 'Project:' in result


@pytest.mark.asyncio
async def test_120_summarize_inventory_wrapper_with_regex( ):
    ''' Server summarize_inventory handles match_mode parameter correctly. '''
    test_inventory_path = get_test_inventory_path( 'sphinxmcps' )
    search_behaviors = module.SearchBehaviorsMutable(
        match_mode = _interfaces.MatchMode.Regex )
    filters = module.FiltersMutable( )
    result = await module.summarize_inventory(
        source = test_inventory_path,
        term = 'test.*pattern',
        search_behaviors = search_behaviors,
        filters = filters )
    assert isinstance( result, str )
    assert 'Project:' in result


@pytest.mark.asyncio
async def test_150_summarize_inventory_wrapper_with_priority( ):
    ''' Server summarize_inventory handles priority filtering correctly. '''
    test_inventory_path = get_test_inventory_path( 'sphobjinv' )
    search_behaviors = module._interfaces.SearchBehaviors( )
    filters = module.FiltersMutable( { 'priority': '0' } )
    result = await module.summarize_inventory(
        source = test_inventory_path,
        search_behaviors = search_behaviors,
        filters = filters )
    assert isinstance( result, str )
    assert 'priority=0' in result
    assert 'Filters:' in result


@pytest.mark.asyncio
async def test_170_explore_wrapper( ):
    ''' Server explore delegates to functions correctly. '''
    test_inventory_path = get_test_inventory_path( 'sphinxmcps' )
    search_behaviors = module._interfaces.SearchBehaviors( )
    filters = module.FiltersMutable( { 'domain': 'py', 'role': 'function' } )
    result = await module.query_inventory(
        source = test_inventory_path, query = 'test',
        search_behaviors = search_behaviors,
        filters = filters )
    assert isinstance( result, dict )
    assert 'project' in result
    assert 'search_metadata' in result
    assert result[ 'search_metadata' ][ 'filters' ][ 'domain' ] == 'py'
    assert result[ 'search_metadata' ][ 'filters' ][ 'role' ] == 'function'


@pytest.mark.asyncio
async def test_180_explore_wrapper_no_filters( ):
    ''' Server explore works without filters. '''
    test_inventory_path = get_test_inventory_path( 'sphinxmcps' )
    result = await module.query_inventory(
        source = test_inventory_path, query = 'test', 
        details = module._interfaces.InventoryQueryDetails.Name )
    assert isinstance( result, dict )
    assert 'project' in result
    assert 'documents' in result
    assert 'search_metadata' in result


@pytest.mark.asyncio
async def test_190_explore_wrapper_with_fuzzy( ):
    ''' Server explore handles fuzzy matching correctly. '''
    test_inventory_path = get_test_inventory_path( 'sphobjinv' )
    search_behaviors = module.SearchBehaviorsMutable(
        match_mode = _interfaces.MatchMode.Fuzzy, fuzzy_threshold = 60 )
    filters = module.FiltersMutable( )
    result = await module.query_inventory(
        source = test_inventory_path,
        query = 'DataObj',
        search_behaviors = search_behaviors,
        filters = filters,
        details = module._interfaces.InventoryQueryDetails.Name )
    assert isinstance( result, dict )
    assert 'search_metadata' in result
    assert result[ 'search_metadata' ][ 'filters' ][ 'match_mode' ] == 'fuzzy'
    assert result[ 'search_metadata' ][ 'filters' ][ 'fuzzy_threshold' ] == 60
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
