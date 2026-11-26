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


import asyncio
import os
import pathlib
import sys

from contextlib import suppress
from unittest.mock import ANY, Mock, patch

import pytest

from mcp.client.session import ClientSession
from mcp.client.sse import sse_client
from mcp.client.stdio import StdioServerParameters, stdio_client

import librovore.server as module
import librovore.state as _state


@pytest.fixture
def mock_auxdata( ):
    ''' Fixture providing mock auxdata/globals object. '''
    return Mock( spec = _state.Globals )


# @pytest.mark.asyncio
# @pytest.mark.asyncio
# async def test_170_explore_wrapper( mock_auxdata ):
#     ''' Server query_inventory factory produces working function. '''
#     test_inventory_path = get_test_inventory_path( 'librovore' )
#     search_behaviors = module.SearchBehaviorsMutable( )
#     filters = module.FiltersMutable( { 'domain': 'py', 'role': 'function' } )
#     query_func = module._produce_query_inventory_function( mock_auxdata )
#     result = await query_func(
#         location = test_inventory_path, term = 'test',
#         search_behaviors = search_behaviors,
#         filters = filters )
#     assert isinstance( result, dict )
#     assert 'project' in result
#     assert 'search_metadata' in result
# 
# 
# @pytest.mark.asyncio
# async def test_180_explore_wrapper_no_filters( mock_auxdata ):
#     ''' Server query_inventory works without filters. '''
#     test_inventory_path = get_test_inventory_path( 'librovore' )
#     query_func = module._produce_query_inventory_function( mock_auxdata )
#     result = await query_func(
#         location = test_inventory_path, term = 'test',
#         details = module._interfaces.InventoryQueryDetails.Name )
#     assert isinstance( result, dict )
#     assert 'project' in result
#     assert 'documents' in result
#     assert 'search_metadata' in result
# 
# 
# @pytest.mark.asyncio
# async def test_190_explore_wrapper_with_fuzzy( mock_auxdata ):
#     ''' Server query_inventory handles fuzzy matching correctly. '''
#     test_inventory_path = get_test_inventory_path( 'sphobjinv' )
#     search_behaviors = module.SearchBehaviorsMutable(
#         match_mode = _interfaces.MatchMode.Similar, fuzzy_threshold = 60 )
#     filters = module.FiltersMutable( )
#     query_func = module._produce_query_inventory_function( mock_auxdata )
#     result = await query_func(
#         location = test_inventory_path,
#         term = 'DataObj',
#         search_behaviors = search_behaviors,
#         filters = filters,
#         details = module._interfaces.InventoryQueryDetails.Name )
#     assert isinstance( result, dict )
#     assert 'search_metadata' in result
#     assert 'documents' in result
# 
# 
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
    with patch(
        'mcp.server.mcpserver.MCPServer.run_stdio_async', autospec = True
    ) as mock_run:
        try: await module.serve( mock_auxdata, transport = 'stdio' )
        except ValueError:
            pytest.fail( "ValueError raised for valid transport 'stdio'" )
        mock_run.assert_awaited_once_with( ANY )


@pytest.mark.asyncio
async def test_220_serve_sse_transport( ):
    ''' Serve function accepts sse transport without error. '''
    mock_auxdata = Mock( )
    with patch(
        'mcp.server.mcpserver.MCPServer.run_sse_async', autospec = True
    ) as mock_run:
        try:
            await module.serve(
                mock_auxdata, transport = 'sse', port = 8080 )
        except ValueError:
            pytest.fail( "ValueError raised for valid transport 'sse'" )
        mock_run.assert_awaited_once_with( ANY, port = 8080 )


@pytest.mark.asyncio
async def test_230_serve_default_transport( ):
    ''' Serve function uses default transport when none specified. '''
    mock_auxdata = Mock( )
    with patch(
        'mcp.server.mcpserver.MCPServer.run_stdio_async', autospec = True
    ) as mock_run:
        try: await module.serve( mock_auxdata )
        except ValueError:
            pytest.fail( "ValueError raised for default transport" )
        mock_run.assert_awaited_once_with( ANY )

@pytest.mark.asyncio
async def test_240_list_tools_registers_default_tools( ):
    """ In-process tool listing pins registration and schemas. """
    from mcp.server.mcpserver import MCPServer
    mcp = MCPServer( 'Librovore Documentation Server' )
    module._register_server_functions( Mock( ), mcp )
    tools = await mcp.list_tools( )
    assert [ tool.name for tool in tools ] == [
        'query_inventory', 'query_content' ]
    assert all( tool.input_schema for tool in tools )


@pytest.mark.asyncio
async def test_250_sse_transport_serves_tools_to_real_client( ):
    """ Real SSE client lists tools on a non-default port. """
    port = _free_port( )
    task = asyncio.create_task(
        module.serve( Mock( ), transport = 'sse', port = port ) )
    try:
        await _wait_for_port( port )
        async with asyncio.timeout( 60.0 ):
            async with sse_client(
                f'http://127.0.0.1:{port}/sse', sse_read_timeout = 30.0
            ) as ( read, write ), ClientSession(
                read, write
            ) as session:
                await session.initialize( )
                tools = await session.list_tools( )
                assert [ tool.name for tool in tools.tools ] == [
                    'query_inventory', 'query_content' ]
    finally:
        task.cancel( )
        with suppress( asyncio.CancelledError ):
            await task


@pytest.mark.asyncio
async def test_260_stdio_transport_serves_tools_to_real_client( ):
    """ Real stdio client lists tools from the served subprocess. """
    sources = str(
        pathlib.Path( __file__ ).resolve( ).parent.parent.parent
        / 'sources' )
    environment = dict( os.environ )
    existing = environment.get( 'PYTHONPATH' )
    environment[ 'PYTHONPATH' ] = (
        sources if not existing else sources + os.pathsep + existing )
    params = StdioServerParameters(
        command = sys.executable,
        args = [ '-m', 'librovore', 'serve' ],
        env = environment )
    async with stdio_client( params ) as ( read, write ), ClientSession(
        read, write
    ) as session:
        await asyncio.wait_for( session.initialize( ), timeout = 120.0 )
        tools = await asyncio.wait_for(
            session.list_tools( ), timeout = 120.0 )
        assert [ tool.name for tool in tools.tools ] == [
            'query_inventory', 'query_content' ]


def _free_port( ) -> int:
    """ Finds a free loopback port other than the SDK default. """
    import socket
    while True:
        with socket.socket( ) as sock:
            sock.bind( ( '127.0.0.1', 0 ) )
            port: int = sock.getsockname( )[ 1 ]
        if port != 8000:
            return port


async def _wait_for_port( port: int, timeout: float = 30.0 ) -> None:
    """ Waits until the loopback port accepts connections. """
    loop = asyncio.get_running_loop( )
    deadline = loop.time( ) + timeout
    while True:
        try:
            _, writer = await asyncio.open_connection(
                '127.0.0.1', port )
            writer.close( )
            await writer.wait_closed( )
            return
        except OSError:
            if loop.time( ) >= deadline:
                raise
            await asyncio.sleep( 0.1 )
