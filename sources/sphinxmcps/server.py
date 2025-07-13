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


mcp = _FastMCP( 'Sphinx MCP Server' )


@mcp.tool( )
def hello( name: str = 'World' ) -> str:
    ''' Says hello with the given name. '''
    return _functions.hello( name )


async def serve(
    auxdata: __.Globals, /, *,
    port: int = 0,
    socket: __.Absential[ str ] = __.absent,
    transport: str = 'stdio',
) -> None:
    ''' Runs MCP server with specified transport. '''
    match transport:
        case 'stdio':
            await mcp.run_stdio_async( )
        case 'sse':
            # TODO: Figure out how to specify port with FastMCP SSE
            # Currently FastMCP seems to use a hardcoded port (8000)
            await mcp.run_sse_async( mount_path = None )
        case 'unix':
            # TODO: Implement Unix socket transport for development
            if __.sys.platform == 'win32':
                raise NotImplementedError(
                    "Unix sockets not supported on Windows."
                )
            raise NotImplementedError(
                f"Unix socket transport not yet implemented ({socket})."
            )
        case _: raise ValueError


def resolve_socket_location(
    auxdata: __.Globals, socket: __.Absential[ str ] = __.absent
) -> __.Path:
    ''' Resolves socket location.

        Accounts for local development versus production.
    '''
    if not __.is_absent( socket ):
        return __.Path( socket ).resolve( )
    name = 'sphinxmcps.sock'
    if __.sys.platform == 'win32':
        # TODO: Use named pipes on Windows
        raise NotImplementedError
    if auxdata.distribution.editable: # local development
        directory = __.Path( '.auxiliary/exercise' )
        directory.mkdir( parents = True, exist_ok = True )
        return directory / name
    return auxdata.directories.user_cache_path / name
