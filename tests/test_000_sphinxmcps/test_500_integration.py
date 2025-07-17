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


''' Full MCP protocol integration tests using SSE transport. '''


import pytest

from .fixtures import (
    MCPTestClient, get_test_inventory_path, mcp_test_server )


@pytest.mark.slow
@pytest.mark.asyncio
async def test_000_mcp_server_startup_and_initialization( ):
    ''' MCP server starts and completes initialization handshake. '''
    async with (
        mcp_test_server( ) as port,
        MCPTestClient( port ) as client
    ):
        response = await client.initialize( )
        assert response[ 'jsonrpc' ] == '2.0'
        assert 'result' in response
        assert 'serverInfo' in response[ 'result' ]
        assert (
            response[ 'result' ][ 'serverInfo' ][ 'name' ] ==
            'Sphinx MCP Server'
        )


@pytest.mark.slow
@pytest.mark.asyncio
async def test_010_mcp_tools_list( ):
    ''' MCP server provides expected tools list. '''
    async with (
        mcp_test_server( ) as port,
        MCPTestClient( port ) as client
    ):
        await client.initialize( )
        response = await client.list_tools( )
        assert response[ 'jsonrpc' ] == '2.0'
        assert 'result' in response
        assert 'tools' in response[ 'result' ]
        tools = response[ 'result' ][ 'tools' ]
        tool_names = [ tool[ 'name' ] for tool in tools ]
        assert 'extract_inventory' in tool_names
        assert 'summarize_inventory' in tool_names


@pytest.mark.slow
@pytest.mark.asyncio
async def test_100_mcp_extract_inventory_tool( ):
    ''' MCP extract_inventory tool processes inventory files. '''
    inventory_path = get_test_inventory_path( 'sphinxmcps' )
    async with (
        mcp_test_server( ) as port,
        MCPTestClient( port ) as client
    ):
        await client.initialize( )
        response = await client.call_tool( 'extract_inventory', {
            'source': inventory_path
        } )
        assert response[ 'jsonrpc' ] == '2.0'
        assert 'result' in response
        content = response[ 'result' ][ 'content' ]
        assert len( content ) > 0
        assert content[ 0 ][ 'type' ] == 'text'
        text_content = content[ 0 ][ 'text' ]
        assert 'project' in text_content
        assert 'objects' in text_content


@pytest.mark.slow
@pytest.mark.asyncio
async def test_110_mcp_extract_inventory_nonexistent_file( ):
    ''' MCP extract_inventory tool handles nonexistent files gracefully. '''
    async with (
        mcp_test_server( ) as port,
        MCPTestClient( port ) as client
    ):
        await client.initialize( )
        response = await client.call_tool( 'extract_inventory', {
            'source': '/nonexistent/path.inv'
        } )
        assert response[ 'jsonrpc' ] == '2.0'
        assert 'result' in response
        assert 'isError' in response[ 'result' ]
        assert response[ 'result' ][ 'isError' ]


@pytest.mark.slow
@pytest.mark.asyncio
async def test_200_mcp_summarize_inventory_tool( ):
    ''' MCP summarize_inventory tool provides human-readable summary. '''
    inventory_path = get_test_inventory_path( 'sphinxmcps' )
    async with (
        mcp_test_server( ) as port,
        MCPTestClient( port ) as client
    ):
        await client.initialize( )
        response = await client.call_tool( 'summarize_inventory', {
            'source': inventory_path
        } )
        assert response[ 'jsonrpc' ] == '2.0'
        assert 'result' in response
        content = response[ 'result' ][ 'content' ]
        assert len( content ) > 0
        assert content[ 0 ][ 'type' ] == 'text'
        text_content = content[ 0 ][ 'text' ]
        assert 'Sphinx Inventory' in text_content
        assert 'objects' in text_content


@pytest.mark.slow
@pytest.mark.asyncio
async def test_210_mcp_summarize_inventory_nonexistent_file( ):
    ''' MCP summarize_inventory tool handles nonexistent files gracefully. '''
    async with (
        mcp_test_server( ) as port,
        MCPTestClient( port ) as client
    ):
        await client.initialize( )
        response = await client.call_tool( 'summarize_inventory', {
            'source': '/nonexistent/path.inv'
        } )
        assert response[ 'jsonrpc' ] == '2.0'
        assert 'result' in response
        assert 'isError' in response[ 'result' ]
        assert response[ 'result' ][ 'isError' ]


@pytest.mark.slow
@pytest.mark.asyncio
async def test_300_mcp_invalid_tool_name( ):
    ''' MCP server handles invalid tool names gracefully. '''
    async with (
        mcp_test_server( ) as port,
        MCPTestClient( port ) as client
    ):
        await client.initialize( )
        response = await client.call_tool( 'nonexistent_tool', { } )
        assert response[ 'jsonrpc' ] == '2.0'
        assert 'result' in response
        assert 'isError' in response[ 'result' ]
        assert response[ 'result' ][ 'isError' ]


@pytest.mark.slow
@pytest.mark.asyncio
async def test_310_mcp_protocol_error_handling( ):
    ''' MCP server handles malformed requests gracefully. '''
    async with (
        mcp_test_server( ) as port,
        MCPTestClient( port ) as client
    ):
        await client.initialize( )
        malformed_request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            # Missing required params
            "id": 1
        }
        response = await client.send_request( malformed_request )
        assert response[ 'jsonrpc' ] == '2.0'
        assert 'error' in response
        assert response[ 'id' ] == 1


@pytest.mark.slow
@pytest.mark.asyncio
async def test_400_mcp_stdio_transport( ):
    ''' stdio transport works correctly with MCP protocol. '''
    # This test is implicit in all the above tests, but let's be explicit
    async with (
        mcp_test_server( ) as process,
        MCPTestClient( process ) as client
    ):
        assert client.process == process
        response = await client.initialize( )
        assert response[ 'jsonrpc' ] == '2.0'
        assert 'result' in response
        inventory_path = get_test_inventory_path( 'sphinxmcps' )
        response = await client.call_tool(
            'summarize_inventory', { 'source': inventory_path } )
        assert response[ 'jsonrpc' ] == '2.0'
        assert 'result' in response
        content = response[ 'result' ][ 'content' ]
        assert 'Sphinx Inventory' in content[ 0 ][ 'text' ]


@pytest.mark.slow
@pytest.mark.asyncio
async def test_410_mcp_multiple_requests( ):
    ''' MCP server can handle multiple sequential requests. '''
    # Note: Cannot test concurrent clients with stdio transport
    # since each process has only one stdin/stdout pair
    async with (
        mcp_test_server( ) as process,
        MCPTestClient( process ) as client
    ):
        await client.initialize( )
        inventory_path = get_test_inventory_path( 'sphinxmcps' )
        response1 = await client.call_tool(
            'summarize_inventory', { 'source': inventory_path } )
        assert response1[ 'jsonrpc' ] == '2.0'
        assert 'result' in response1
        response2 = await client.call_tool(
            'extract_inventory', { 'source': inventory_path } )
        assert response2[ 'jsonrpc' ] == '2.0'
        assert 'result' in response2
        assert (
            'Sphinx Inventory' in
            response1[ 'result' ][ 'content' ][ 0 ][ 'text' ] )
        assert (
            'project' in
            response2[ 'result' ][ 'content' ][ 0 ][ 'text' ] )


@pytest.mark.slow
@pytest.mark.asyncio
async def test_500_mcp_server_shutdown_cleanup( ):
    ''' MCP server shuts down cleanly and cleans up resources. '''
    # Start server and get port
    async with (
        mcp_test_server( ) as port,
        MCPTestClient( port ) as client
    ):
        await client.initialize( )
        inventory_path = get_test_inventory_path( 'sphinxmcps' )
        response = await client.call_tool(
            'summarize_inventory', { 'source': inventory_path } )
        assert (
            'Sphinx Inventory' in
            response[ 'result' ][ 'content' ][ 0 ][ 'text' ] )
        # Client connection should close cleanly
    # Server should shut down cleanly (tested by context manager)
