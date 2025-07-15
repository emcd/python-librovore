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

# FastMCP uses Pydantic to generate JSON schemas from function signatures.
from pydantic import Field as _Field

from . import __
from . import functions as _functions


_scribe = __.acquire_scribe( __name__ )


def extract_inventory(
    source: __.typx.Annotated[
        str,
        _Field(
            description = "URL or file path to Sphinx documentation"
        )
    ],
    domain: __.typx.Annotated[
        str,
        _Field(
            default = '',
            description = "Filter objects by domain (e.g., 'py', 'std')"
        )
    ] = '',
    role: __.typx.Annotated[
        str,
        _Field(
            default = '',
            description = "Filter objects by role (e.g., 'function', 'class')"
        )
    ] = '',
    term: __.typx.Annotated[
        str,
        _Field(
            default = '',
            description = "Filter objects by name (case-insensitive)"
        )
    ] = '',
) -> dict[ str, __.typx.Any ]:
    ''' Extracts Sphinx inventory from URL or file path with optional
    filtering.

        Args:
            source: URL or file path to Sphinx documentation
                    (objects.inv auto-appended)
            domain: Filter objects by domain (e.g., 'py', 'std')
            role: Filter objects by role (e.g., 'function', 'class', 'method')
            term: Filter objects by name containing this text
                    (case-insensitive)
    '''
    _scribe.debug(
        "extract_inventory called: source=%s, domain=%s, role=%s, term=%s",
        source, domain, role, term
    )
    _scribe.debug( "Processing extract_inventory request after hot-reload..." )
    nomargs: __.NominativeArguments = { }
    if domain:
        nomargs[ 'domain' ] = domain
    if role:
        nomargs[ 'role' ] = role
    if term:
        nomargs[ 'term' ] = term
    return _functions.extract_inventory( source, **nomargs )


def summarize_inventory(
    source: __.typx.Annotated[
        str,
        _Field(
            description = "URL or file path to Sphinx documentation"
        )
    ],
    domain: __.typx.Annotated[
        str,
        _Field(
            default = '',
            description = "Filter objects by domain (e.g., 'py', 'std')"
        )
    ] = '',
    role: __.typx.Annotated[
        str,
        _Field(
            default = '',
            description = "Filter objects by role (e.g., 'function', 'class')"
        )
    ] = '',
    term: __.typx.Annotated[
        str,
        _Field(
            default = '',
            description = "Filter objects by name (case-insensitive)"
        )
    ] = '',
) -> str:
    ''' Provides human-readable summary of Sphinx inventory.

        Args:
            source: URL or file path to Sphinx documentation
                    (objects.inv auto-appended)
            domain: Filter objects by domain (e.g., 'py', 'std')
            role: Filter objects by role (e.g., 'function', 'class', 'method')
            term: Filter objects by name containing this text
                    (case-insensitive)
    '''
    _scribe.debug(
        "summarize_inventory called: source=%s, domain=%s, role=%s, term=%s",
        source, domain, role, term
    )
    nomargs: __.NominativeArguments = { }
    if domain:
        nomargs[ 'domain' ] = domain
    if role:
        nomargs[ 'role' ] = role
    if term:
        nomargs[ 'term' ] = term
    return _functions.summarize_inventory( source, **nomargs )


async def serve(
    auxdata: __.Globals, /, *,
    port: int = 0,
    transport: str = 'stdio',
    develop: bool = False,
) -> None:
    ''' Runs MCP server. '''
    if develop:
        await _serve_develop( auxdata, port = port, transport = transport )
        return
    # Standard MCP server modes
    _scribe.debug( "Initializing FastMCP server" )
    mcp = _FastMCP( 'Sphinx MCP Server', port = port )
    _scribe.debug( "Registering extract_inventory tool" )
    mcp.tool( )( extract_inventory )
    _scribe.debug( "Registering summarize_inventory tool" )
    mcp.tool( )( summarize_inventory )
    _scribe.debug( "Tools registered successfully" )
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
            __.sys.executable, '-m', 'sphinxmcps', 'serve',
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


def _build_child_args( port: int, transport: str ) -> list[ str ]:
    ''' Builds subprocess arguments with develop flag filtered out. '''
    args = [ __.sys.executable, '-m', 'sphinxmcps', '--logfile', '.auxiliary/inscriptions/server-child.txt', 'serve' ]
    # Force stdio transport for child process
    if transport != 'stdio':
        args.extend( [ '--transport', 'stdio' ] )
    # Pass through port if specified
    if port != 0:
        args.extend( [ '--port', str( port ) ] )
    # develop flag is never passed to child process
    return args


async def _bridge_stdio_streams(
    process: __.asyncio.subprocess.Process
) -> None:
    ''' Bridges stdio streams between parent and child process. '''
    if not process.stdin or not process.stdout:
        return
    # Use asyncio to bridge stdin/stdout with the child process
    await __.asyncio.gather(
        _bridge_stdin_to_child( process.stdin ),
        _bridge_child_to_stdout( process.stdout ),
        _bridge_child_to_stderr( process.stderr ),
        return_exceptions = True )


async def _bridge_stdin_to_child(
    child_stdin: __.asyncio.StreamWriter
) -> None:
    ''' Bridges parent stdin to child process stdin. '''
    try:
        # Create async stdin reader
        loop = __.asyncio.get_event_loop( )
        stdin_reader = __.asyncio.StreamReader( )
        stdin_protocol = __.asyncio.StreamReaderProtocol( stdin_reader )
        await loop.connect_read_pipe( lambda: stdin_protocol, __.sys.stdin )
        # Read from parent stdin and write to child stdin
        while True:
            data = await stdin_reader.read( 8192 )
            if not data:
                break
            child_stdin.write( data )
            await child_stdin.drain( )
    except Exception:
        # Connection closed or other error - normal during cleanup
        return
    finally:
        try:
            child_stdin.close( )
            await child_stdin.wait_closed( )
        except Exception:
            return


async def _bridge_child_to_stdout(
    child_stdout: __.asyncio.StreamReader
) -> None:
    ''' Bridges child process stdout to parent stdout. '''
    try:
        while True:
            data = await child_stdout.read( 8192 )
            if not data:
                break
            __.sys.stdout.buffer.write( data )
            __.sys.stdout.buffer.flush( )
    except Exception:
        # Connection closed or other error - normal during cleanup
        return


async def _bridge_child_to_stderr(
    child_stderr: __.typx.Optional[ __.asyncio.StreamReader ]
) -> None:
    ''' Bridges child process stderr to parent stderr. '''
    if not child_stderr:
        return
    try:
        while True:
            data = await child_stderr.read( 8192 )
            if not data:
                break
            __.sys.stderr.buffer.write( data )
            __.sys.stderr.buffer.flush( )
    except Exception:
        # Connection closed or other error - normal during cleanup
        return


def _python_files_only( change: __.typx.Any, path: str ) -> bool:
    ''' Filter function to watch only Python source files. '''
    return path.endswith( '.py' ) and '__pycache__' not in path


async def _serve_develop(
    auxdata: __.Globals, /, *,
    port: int = 0,
    transport: str = 'stdio',
) -> None:
    ''' Runs MCP server in development mode with hot reloading. '''
    _scribe.info( "Running MCP server in development mode." )
    from watchfiles import awatch  # type: ignore
    source_path = __.Path( __file__ ).parent
    current_process: __.typx.Optional[ __.asyncio.subprocess.Process ] = None
    try:
        current_process = await _start_child_server( port, transport )
        bridge_task = __.asyncio.create_task(
            _bridge_stdio_streams( current_process )
        )
        async for changes in awatch(
            source_path, watch_filter = _python_files_only
        ):
            if changes:
                print(
                    "Files changed, restarting server...",
                    file = __.sys.stderr
                )
                bridge_task.cancel( )
                with __.ctxl.suppress( __.asyncio.CancelledError ):
                    await bridge_task
                if current_process:
                    await _terminate_child_process( current_process )
                current_process = await _start_child_server( port, transport )
                bridge_task = __.asyncio.create_task(
                    _bridge_stdio_streams( current_process )
                )
                print( "Server restarted", file = __.sys.stderr )
    except __.asyncio.CancelledError:
        pass # Graceful shutdown
    except Exception as exc:
        print( f"Development server error: {exc}", file = __.sys.stderr )
        raise
    finally:
        if current_process and current_process.returncode is None:
            await _terminate_child_process( current_process )


async def _start_child_server(
    port: int, transport: str
) -> __.asyncio.subprocess.Process:
    ''' Starts child MCP server process with filtered arguments. '''
    args = _build_child_args( port, transport )
    return await __.asyncio.create_subprocess_exec(
        *args,
        stdin = __.asyncio.subprocess.PIPE,
        stdout = __.asyncio.subprocess.PIPE,
        stderr = __.asyncio.subprocess.PIPE )


async def _terminate_child_process(
    process: __.asyncio.subprocess.Process
) -> None:
    ''' Gracefully terminates child process. '''
    if process.returncode is not None:
        return  # Already terminated
    process.terminate( )
    try:
        await __.asyncio.wait_for( process.wait( ), timeout = 3.0 )
    except __.asyncio.TimeoutError:
        process.kill( )
        await process.wait( )
