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


def extract_inventory( source: str ) -> dict[ str, __.typx.Any ]:
    ''' Extracts Sphinx inventory from URL or file path.

        Returns structured data with project info, domains, and objects.
    '''
    return _functions.extract_inventory( source )


def hello( name: str = 'World' ) -> str:
    ''' Says hello with the given name. '''
    return _functions.hello( name )


def summarize_inventory( source: str ) -> str:
    ''' Provides human-readable summary of Sphinx inventory. '''
    return _functions.summarize_inventory( source )


async def serve(
    auxdata: __.Globals, /, *,
    port: int = 0,
    socket: __.Absential[ str ] = __.absent,
    transport: str = 'stdio',
) -> None:
    ''' Runs MCP server. '''
    mcp = _FastMCP( 'Sphinx MCP Server', port = port )
    mcp.tool( )( hello )
    mcp.tool( )( extract_inventory )
    mcp.tool( )( summarize_inventory )
    match transport:
        case 'stdio': await mcp.run_stdio_async( )
        case 'sse': await mcp.run_sse_async( mount_path = None )
        case _: raise ValueError
