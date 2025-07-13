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

from . import functions as _functions


mcp = _FastMCP( "Sphinx MCP Server" )


@mcp.tool( )
def hello( name: str = 'World' ) -> str:
    ''' Invokes hello function. '''
    return _functions.hello( name )


async def serve( transport: str, port: int, socket_path: str ) -> None:
    # TODO: Enum or typing.Literal for transport.
    # TODO: Handle port. Ideally, port 0 would mean choose a port.
    #       Need to investigate how MCP clients know the server port.
    ''' Runs MCP server with specified transport. '''
    match transport:
        case 'sse' | 'stdio':
            mcp.run( transport = transport )
        case 'unix':
            # TODO: Implement Unix socket transport for development
            raise NotImplementedError(
                "Unix socket transport not yet implemented." )
        case _: raise ValueError
