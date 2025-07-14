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


''' Shared test fixtures and utilities using dependency injection patterns. '''


import asyncio
import json
import os
import re
import signal
import sys
from contextlib import asynccontextmanager


class MCPTestClient:
    '''
    Async context manager for MCP server testing with dependency injection.
    '''
    
    def __init__( self, port: int ):
        self.port = port
        self.reader = None
        self.writer = None
        self.request_id = 0
        
    async def __aenter__( self ):
        self.reader, self.writer = await asyncio.open_connection(
            'localhost', self.port
        )
        return self
        
    async def __aexit__( self, exc_type, exc_val, exc_tb ):
        if self.writer:
            self.writer.close( )
            await self.writer.wait_closed( )
            
    async def send_request( self, request: dict ) -> dict:
        ''' Send MCP request and receive response. '''
        self.request_id += 1
        if 'id' not in request:
            request[ 'id' ] = self.request_id
            
        request_line = json.dumps( request ) + '\n'
        self.writer.write( request_line.encode( ) )
        await self.writer.drain( )
        
        response_line = await self.reader.readline( )
        return json.loads( response_line.decode( ).strip( ) )
        
    async def initialize( self ) -> dict:
        ''' Complete MCP initialization handshake. '''
        request = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "roots": { "listChanged": True }, 
                    "sampling": { }
                },
                "clientInfo": { "name": "test-client", "version": "1.0.0" }
            }
        }
        result = await self.send_request( request )
        
        # Send initialized notification (no ID for notifications)
        request_line = json.dumps( {
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        } ) + '\n'
        self.writer.write( request_line.encode( ) )
        await self.writer.drain( )
        
        return result
        
    async def list_tools( self ) -> dict:
        ''' List available MCP tools. '''
        return await self.send_request( {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "params": { }
        } )
        
    async def call_tool( self, name: str, arguments: dict ) -> dict:
        ''' Call MCP tool with arguments. '''
        return await self.send_request( {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": { "name": name, "arguments": arguments }
        } )


@asynccontextmanager
async def mcp_test_server( ):
    ''' Context manager for MCP server with dependency injection. '''
    process = await asyncio.create_subprocess_exec(
        sys.executable, '-m', 'sphinxmcps', 'serve', 
        '--transport', 'stdio-over-tcp', '--port', '0',
        stdout = asyncio.subprocess.PIPE,
        stderr = asyncio.subprocess.PIPE,
        preexec_fn = os.setsid
    )
    
    try:
        # Extract dynamic port from stderr
        await asyncio.sleep( 1 )
        stderr_data = await process.stderr.read( 1024 )
        port_match = re.search( r'127\.0\.0\.1:(\d+)', stderr_data.decode( ) )
        
        if not port_match:
            raise RuntimeError(
                "Could not extract dynamic port from server output"
            )
            
        port = int( port_match.group( 1 ) )
        yield port
        
    finally:
        await cleanup_server_process( process )


async def cleanup_server_process( process ):
    ''' Clean up server process using dependency injection pattern. '''
    if process.returncode is not None:
        # Process already terminated
        return
        
    try:
        # Try graceful termination first
        process.terminate( )
        try:
            await asyncio.wait_for( process.wait( ), timeout = 2.0 )
            return  # Graceful termination worked
        except asyncio.TimeoutError:
            pass
            
        # If still running, try process group termination
        try:
            os.killpg( os.getpgid( process.pid ), signal.SIGTERM )
            await asyncio.wait_for( process.wait( ), timeout = 2.0 )
            return  # Process group termination worked
        except ( ProcessLookupError, OSError, asyncio.TimeoutError ):
            pass
            
        # Last resort: force kill
        try:
            process.kill( )
            await asyncio.wait_for( process.wait( ), timeout = 1.0 )
        except ( ProcessLookupError, asyncio.TimeoutError ):
            # Process might be stuck, try process group kill
            try:
                os.killpg( os.getpgid( process.pid ), signal.SIGKILL )
                await process.wait( )
            except ( ProcessLookupError, OSError ):
                pass  # Process is gone or cleanup failed
                
    finally:
        # Always close pipes to prevent warnings
        try:
            if process.stdin and not process.stdin.is_closing( ):
                process.stdin.close( )
            if process.stdout and not process.stdout.is_closing( ):
                process.stdout.close( )
            if process.stderr and not process.stderr.is_closing( ):
                process.stderr.close( )
        except ( OSError, AttributeError, ValueError ):
            pass  # Ignore expected pipe cleanup errors


def mock_inventory_bytes( ) -> bytes:
    ''' Create minimal valid inventory data for testing.
    
        Returns minimal sphobjinv-compatible inventory data to avoid
        external dependencies in unit tests.
    '''
    # Basic inventory structure with minimal content for testing
    # This is a simplified version that satisfies sphobjinv requirements
    header = (
        b"# Sphinx inventory version 2\n# Project: test\n# Version: 1.0\n"
        b"# The remainder of this file is compressed using zlib.\n"
    )
    
    # Minimal compressed inventory content
    import zlib
    inventory_data = "test py:module 1 test.html#module-test Test module\n"
    compressed_data = zlib.compress( inventory_data.encode( 'utf-8' ) )
    
    return header + compressed_data


class MockCompletedProcess:
    ''' Mock subprocess.CompletedProcess for testing CLI commands. '''
    
    def __init__( self, returncode: int, stdout: str, stderr: str ):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


async def run_cli_command( args: list[ str ] ):
    ''' Run CLI command and return result using dependency injection. '''
    process = await asyncio.create_subprocess_exec(
        sys.executable, '-m', 'sphinxmcps', *args,
        stdout = asyncio.subprocess.PIPE,
        stderr = asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate( )
    return MockCompletedProcess( 
        returncode = process.returncode,
        stdout = stdout.decode( ),
        stderr = stderr.decode( )
    )


async def start_server_process( args: list[ str ] ):
    ''' Start server subprocess with dependency injection. '''
    return await asyncio.create_subprocess_exec(
        sys.executable, '-m', 'sphinxmcps', 'serve', *args,
        stdout = asyncio.subprocess.PIPE,
        stderr = asyncio.subprocess.PIPE,
        preexec_fn = os.setsid
    )


async def extract_dynamic_port( process ) -> int:
    ''' Extract dynamic port from server process stderr. '''
    await asyncio.sleep( 1 )
    stderr_data = await process.stderr.read( 1024 )
    port_match = re.search( r'127\.0\.0\.1:(\d+)', stderr_data.decode( ) )
    
    if not port_match:
        raise RuntimeError(
            "Could not extract dynamic port from server output"
        )
        
    return int( port_match.group( 1 ) )


async def find_free_port( ) -> int:
    ''' Find a free TCP port for testing. '''
    import socket
    with socket.socket( socket.AF_INET, socket.SOCK_STREAM ) as s:
        s.bind( ( '', 0 ) )
        s.listen( 1 )
        return s.getsockname( )[ 1 ]


async def test_mcp_connection( port: int ):
    ''' Test basic MCP connection to server. '''
    async with MCPTestClient( port ) as client:
        response = await client.initialize( )
        assert 'result' in response
        assert 'serverInfo' in response[ 'result' ]


async def test_http_connection( port: int ):
    ''' Test basic HTTP connection to SSE server. '''
    import aiohttp
    async with (
        aiohttp.ClientSession( ) as session,
        session.get( f"http://localhost:{port}/health" ) as response
    ):
        # 404 is ok if health endpoint doesn't exist
        assert response.status in ( 200, 404 )