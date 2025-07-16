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
    mcp_test_server, 
    MCPTestClient, 
    get_test_inventory_path
)


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
        
        # Response should be JSON containing inventory data
        text_content = content[ 0 ][ 'text' ]
        assert 'project' in text_content
        assert 'objects' in text_content


@pytest.mark.slow
@pytest.mark.asyncio
async def test_110_mcp_extract_inventory_with_domain_filter( ):
    ''' MCP extract_inventory tool applies domain filtering. '''
    inventory_path = get_test_inventory_path( 'sphinxmcps' )
    async with (
        mcp_test_server( ) as port,
        MCPTestClient( port ) as client
    ):
        await client.initialize( )
        response = await client.call_tool( 'extract_inventory', {
            'source': inventory_path,
            'domain': 'py'
        } )
        
        assert response[ 'jsonrpc' ] == '2.0'
        assert 'result' in response
        content = response[ 'result' ][ 'content' ]
        text_content = content[ 0 ][ 'text' ]
        assert 'domain' in text_content
        assert 'py' in text_content


@pytest.mark.slow
@pytest.mark.asyncio
async def test_120_mcp_extract_inventory_with_role_filter( ):
    ''' MCP extract_inventory tool applies role filtering. '''
    inventory_path = get_test_inventory_path( 'sphinxmcps' )
    async with (
        mcp_test_server( ) as port,
        MCPTestClient( port ) as client
    ):
        await client.initialize( )
        response = await client.call_tool( 'extract_inventory', {
            'source': inventory_path,
            'role': 'module'
        } )
        
        assert response[ 'jsonrpc' ] == '2.0'
        assert 'result' in response
        content = response[ 'result' ][ 'content' ]
        text_content = content[ 0 ][ 'text' ]
        assert 'role' in text_content
        assert 'module' in text_content


@pytest.mark.slow
@pytest.mark.asyncio
async def test_130_mcp_extract_inventory_with_search_filter( ):
    ''' MCP extract_inventory tool applies search filtering. '''
    inventory_path = get_test_inventory_path( 'sphinxmcps' )
    async with (
        mcp_test_server( ) as port,
        MCPTestClient( port ) as client
    ):
        await client.initialize( )
        response = await client.call_tool( 'extract_inventory', {
            'source': inventory_path,
            'term': 'test'
        } )
        
        assert response[ 'jsonrpc' ] == '2.0'
        assert 'result' in response
        content = response[ 'result' ][ 'content' ]
        text_content = content[ 0 ][ 'text' ]
        assert 'term' in text_content
        assert 'test' in text_content


@pytest.mark.slow
@pytest.mark.asyncio
async def test_140_mcp_extract_inventory_nonexistent_file( ):
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
        # Should return error for nonexistent file
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
async def test_210_mcp_summarize_inventory_with_filters( ):
    ''' MCP summarize_inventory tool includes filter information. '''
    inventory_path = get_test_inventory_path( 'sphinxmcps' )
    async with (
        mcp_test_server( ) as port,
        MCPTestClient( port ) as client
    ):
        await client.initialize( )
        response = await client.call_tool( 'summarize_inventory', {
            'source': inventory_path,
            'domain': 'py'
        } )
        
        assert response[ 'jsonrpc' ] == '2.0'
        assert 'result' in response
        content = response[ 'result' ][ 'content' ]
        text_content = content[ 0 ][ 'text' ]
        assert 'Sphinx Inventory' in text_content
        assert 'py' in text_content


@pytest.mark.slow
@pytest.mark.asyncio
async def test_220_mcp_summarize_inventory_nonexistent_file( ):
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
        # Should return error for nonexistent file
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
        
        # Send malformed request
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
        # Verify we can connect via stdio
        assert client.process == process
        
        # Verify MCP protocol works over stdio
        response = await client.initialize( )
        assert response[ 'jsonrpc' ] == '2.0'
        assert 'result' in response
        
        # Verify tool calls work over stdio using inventory tools
        inventory_path = get_test_inventory_path( 'sphinxmcps' )
        response = await client.call_tool(
            'summarize_inventory', { 'source': inventory_path }
        )
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
        # Initialize once
        await client.initialize( )
        
        # Make multiple tool calls sequentially
        inventory_path = get_test_inventory_path( 'sphinxmcps' )
        
        # First call
        response1 = await client.call_tool(
            'summarize_inventory', { 'source': inventory_path }
        )
        assert response1[ 'jsonrpc' ] == '2.0'
        assert 'result' in response1
        
        # Second call with different parameters
        response2 = await client.call_tool(
            'extract_inventory', { 'source': inventory_path }
        )
        assert response2[ 'jsonrpc' ] == '2.0'
        assert 'result' in response2
        
        # Both should have valid content
        assert (
            'Sphinx Inventory' in 
            response1[ 'result' ][ 'content' ][ 0 ][ 'text' ]
        )
        assert (
            'project' in 
            response2[ 'result' ][ 'content' ][ 0 ][ 'text' ]
        )


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
            'summarize_inventory', { 'source': inventory_path }
        )
        assert (
            'Sphinx Inventory' in 
            response[ 'result' ][ 'content' ][ 0 ][ 'text' ]
        )
        
        # Client connection should close cleanly
        
    # Server should shut down cleanly (tested by context manager)
    # If we get here without hanging, cleanup worked
    assert True