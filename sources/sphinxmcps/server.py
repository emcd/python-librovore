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


''' MCP server implementation. '''


from mcp.server.fastmcp import FastMCP as _FastMCP

from . import __
from . import functions as _functions


def extract_inventory(
    source: str,
    domain: str | None = None,
    role: str | None = None,
    search: str | None = None,
) -> dict[ str, __.typx.Any ]:
    ''' Extracts Sphinx inventory from URL or file path with optional
    filtering.

        Args:
            source: URL or file path to Sphinx documentation
                    (objects.inv auto-appended)
            domain: Filter objects by domain (e.g., 'py', 'std')
            role: Filter objects by role (e.g., 'function', 'class', 'method')
            search: Filter objects by name containing this text
                    (case-insensitive)

        Returns structured data with project info, domains, and objects.
        When filters are applied, includes 'filters' field showing active
        filters.
    '''
    return _functions.extract_inventory(
        source, domain = domain, role = role, search = search
    )


def hello( name: str = 'World' ) -> str:
    ''' Says hello with the given name. '''
    return _functions.hello( name )


def summarize_inventory( source: str ) -> str:
    ''' Provides human-readable summary of Sphinx inventory. '''
    return _functions.summarize_inventory( source )


async def serve(
    auxdata: __.Globals, /, *,
    port: int = 0,
    transport: str = 'stdio',
) -> None:
    ''' Runs MCP server. '''
    # Standard MCP server modes
    mcp = _FastMCP( 'Sphinx MCP Server', port = port )
    mcp.tool( )( hello )
    mcp.tool( )( extract_inventory )
    mcp.tool( )( summarize_inventory )
    match transport:
        case 'sse': await mcp.run_sse_async( mount_path = None )
        case 'stdio': await mcp.run_stdio_async( )
        case 'stdio-over-tcp': await _serve_stdio_over_tcp( port )
        case _: raise ValueError


async def _serve_stdio_over_tcp( port: int ) -> None:
    ''' Serves MCP stdio protocol over TCP.

        Bridges connections to subprocesses.

        Eliminates the need for external tools, like 'socat', by providing
        built-in TCP bridging functionality for development and testing.

        Args:
            port: TCP port to bind to. Use 0 for dynamic port assignment.
    '''
    async def handle_client(
        reader: __.asyncio.StreamReader,
        writer: __.asyncio.StreamWriter
    ) -> None:
        ''' Handles a single TCP client by bridging to MCP subprocess. '''
        addr = writer.get_extra_info( 'peername' )
        print( f"Connection from {addr}", file = __.sys.stderr )
        # Start MCP server subprocess in stdio mode
        process = await __.asyncio.create_subprocess_exec(
            # TODO? Might not need to `hatch run` in this case,
            #       since we are clearly running in a proper environment.
            'hatch', 'run', 'sphinxmcps', 'serve',
            stdin = __.asyncio.subprocess.PIPE,
            stdout = __.asyncio.subprocess.PIPE,
            stderr = __.asyncio.subprocess.PIPE )
        try:
            # Pyright needs explicit None checks for subprocess pipes
            if process.stdin is None or process.stdout is None:
                # TODO: Improve exception.
                raise RuntimeError
            await __.asyncio.gather(
                _bridge_reader_to_writer( reader, process.stdin ),
                _bridge_reader_to_writer( process.stdout, writer ),
                return_exceptions = True )
        finally:
            writer.close( )
            await writer.wait_closed( )
            if process.returncode is None:
                process.terminate( )
                try:
                    await __.asyncio.wait_for( process.wait( ), timeout = 5.0 )
                except __.asyncio.TimeoutError:
                    process.kill( )
                    await process.wait( )
            print( f"Disconnected {addr}", file = __.sys.stderr )
    server = await __.asyncio.start_server( handle_client, 'localhost', port )
    addr = server.sockets[ 0 ].getsockname( )
    actual_port = addr[ 1 ]
    print(
        f"Serving MCP stdio over TCP on {addr[ 0 ]}:{actual_port}",
        # TODO: Use designated diagnostic stream.
        file = __.sys.stderr )
    # For dynamic port assignment, ensure port is captured for clients
    if port == 0:
        print(
            f"Dynamic port assigned: {actual_port}",
            # TODO: Use designated diagnostic stream.
            file = __.sys.stderr )
    async with server:
        await server.serve_forever( )


async def _bridge_reader_to_writer(
    reader: __.asyncio.StreamReader,
    writer: __.asyncio.StreamWriter,
) -> None:
    ''' Bridges data from a reader to a writer until EOF or error. '''
    try:
        while True:
            data = await reader.read( 8192 )
            if not data:
                break
            writer.write( data )
            await writer.drain( )
    except Exception:
        # Connection closed or other error - normal during cleanup
        return
    finally:
        try:
            writer.close( )
            await writer.wait_closed( )
        except Exception:
            return
