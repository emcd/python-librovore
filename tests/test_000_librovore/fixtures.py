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
import signal
import sys

from contextlib import asynccontextmanager
from pathlib import Path


class MCPTestClient:
    ''' Async context manager for MCP server testing with dependency injection.
    '''

    def __init__( self, process ):
        self.process = process
        self.request_id = 0

    async def __aenter__( self ):
        return self

    async def __aexit__( self, exc_type, exc_val, exc_tb ):
        pass  # Process cleanup handled by mcp_test_server

    async def send_request( self, request: dict ) -> dict:
        ''' Send MCP request and receive response. '''
        self.request_id += 1
        if 'id' not in request:
            request[ 'id' ] = self.request_id

        # Send request via stdin
        request_line = json.dumps( request ) + '\n'
        self.process.stdin.write( request_line.encode( ) )
        await self.process.stdin.drain( )

        # Read response from stdout
        response_line = await self.process.stdout.readline( )
        if not response_line:
            raise RuntimeError( "No response from MCP server" )
        return json.loads( response_line.decode( ).strip( ) )

    async def initialize( self ) -> dict:
        ''' Completes MCP initialization handshake. '''
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
        notification = json.dumps( {
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        } ) + '\n'
        self.process.stdin.write( notification.encode( ) )
        await self.process.stdin.drain( )
        return result

    async def list_tools( self ) -> dict:
        ''' Lists available MCP tools. '''
        return await self.send_request( {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "params": { }
        } )

    async def call_tool( self, name: str, arguments: dict ) -> dict:
        ''' Calls MCP tool with arguments. '''
        return await self.send_request( {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": { "name": name, "arguments": arguments }
        } )


@asynccontextmanager
async def mcp_test_server( ):
    ''' Context manager for MCP server with dependency injection. '''
    process = await asyncio.create_subprocess_exec(
        sys.executable, '-m', 'librovore', 'serve',
        stdin = asyncio.subprocess.PIPE,
        stdout = asyncio.subprocess.PIPE,
        stderr = asyncio.subprocess.PIPE,
        preexec_fn = os.setsid
    )
    try:
        await asyncio.sleep( 1 )
        yield process
    finally: await cleanup_server_process( process )


async def cleanup_server_process( process ):
    ''' Clean up server process using dependency injection pattern. '''
    if process.returncode is not None: return
    try:
        process.terminate( )
        try:
            await asyncio.wait_for( process.wait( ), timeout = 2.0 )
            return  # Graceful termination worked
        except asyncio.TimeoutError:
            pass
        try:
            os.killpg( os.getpgid( process.pid ), signal.SIGTERM )
            await asyncio.wait_for( process.wait( ), timeout = 2.0 )
            return  # Process group termination worked
        except ( ProcessLookupError, OSError, asyncio.TimeoutError ):
            pass
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


def get_test_inventory_path( site_name: str = 'librovore' ) -> str:
    ''' Gets path to test inventory file. '''
    test_dir = Path( __file__ ).parent.parent
    inventory_path = (
        test_dir / 'data' / 'inventories' / site_name / 'objects.inv' )
    if not inventory_path.exists( ):
        raise FileNotFoundError(
            f"Test inventory file not found: {inventory_path}" )
    return str( inventory_path )


# Session-scoped cache for extracted test sites
_extracted_sites_cache = {}

def get_test_site_path( site_name: str = 'librovore' ) -> str:
    ''' Gets path to test site directory for structure detection. 
    
        Extracts archive to temporary directory once per session.
    '''
    if site_name in _extracted_sites_cache:
        return _extracted_sites_cache[site_name]
    import tempfile
    import tarfile
    import atexit
    test_dir = Path( __file__ ).parent.parent
    archive_path = test_dir / 'data' / 'sites' / f'{site_name}.tar.xz'
    if not archive_path.exists( ):
        raise FileNotFoundError(
            f"Test site archive not found: {archive_path}" )
    temp_dir = Path( tempfile.mkdtemp( 
        prefix = f'librovore_test_{site_name}_' ) )
    def cleanup_temp_site():
        import shutil
        if temp_dir.exists( ):
            shutil.rmtree( temp_dir )
        _extracted_sites_cache.pop( site_name, None )
    atexit.register( cleanup_temp_site )
    with tarfile.open( archive_path, 'r:xz' ) as archive:
        archive.extractall( path = temp_dir )  # noqa: S202
    site_path = temp_dir / site_name
    if not site_path.exists( ):
        raise FileNotFoundError(
            f"Extracted site directory not found: {site_path}" )
    file_url = f"file://{site_path}"
    _extracted_sites_cache[site_name] = file_url
    return file_url


def get_test_site_path_from_cache( 
    cached_test_sites, site_name: str = 'librovore' ) -> str:
    ''' Gets path to test site from session-scoped cache.
    
        Uses pre-extracted site from cached_test_sites fixture.
    '''
    site_path = cached_test_sites / site_name / site_name
    if not site_path.exists( ):
        raise FileNotFoundError(
            f"Cached test site not found: {site_path}" )
    
    return f"file://{site_path}"


class MockCompletedProcess:
    ''' Mock subprocess.CompletedProcess for testing CLI commands. '''

    def __init__( self, returncode: int, stdout: str, stderr: str ):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


async def run_cli_command( args: list[ str ] ):
    ''' Runs CLI command and return result using dependency injection. '''
    process = await asyncio.create_subprocess_exec(
        sys.executable, '-m', 'librovore', *args,
        stdout = asyncio.subprocess.PIPE,
        stderr = asyncio.subprocess.PIPE )
    stdout, stderr = await process.communicate( )
    return MockCompletedProcess(
        returncode = process.returncode,
        stdout = stdout.decode( ),
        stderr = stderr.decode( ) )


def get_fake_extension_url():
    ''' Get file:// URL for fake extension package. '''
    fake_extension_path = (
        Path( __file__ ).parent.parent / "fixtures" / "fake-extension" )
    return f"file://{fake_extension_path.absolute()}"


def get_broken_extension_url():
    ''' Get file:// URL for broken extension package. '''
    broken_extension_path = (
        Path( __file__ ).parent.parent / "fixtures" / "broken-extension" )
    return f"file://{broken_extension_path.absolute()}"
