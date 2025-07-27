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
from . import interfaces as _interfaces


DomainFilter: __.typx.TypeAlias = __.typx.Annotated[
    str, _Field( description = __.access_doctab( 'domain filter argument' ) ) ]
FuzzyThreshold: __.typx.TypeAlias = __.typx.Annotated[
    int,
    _Field( description = __.access_doctab( 'fuzzy threshold argument' ) ),
]
IncludeSnippets: __.typx.TypeAlias = __.typx.Annotated[
    bool,
    _Field( description = __.access_doctab( 'include snippets argument' ) ),
]
MatchMode: __.typx.TypeAlias = __.typx.Annotated[
    _interfaces.MatchMode,
    _Field( description = __.access_doctab( 'match mode argument' ) ),
]
ResultsMax: __.typx.TypeAlias = __.typx.Annotated[
    int, _Field( description = __.access_doctab( 'results max argument' ) ) ]
ObjectName: __.typx.TypeAlias = __.typx.Annotated[
    str, _Field( description = __.access_doctab( 'object name' ) ) ]
PriorityFilter: __.typx.TypeAlias = __.typx.Annotated[
    str,
    _Field( description = __.access_doctab( 'priority filter argument' ) ),
]
Query: __.typx.TypeAlias = __.typx.Annotated[
    str, _Field( description = __.access_doctab( 'query argument' ) ) ]
RoleFilter: __.typx.TypeAlias = __.typx.Annotated[
    str, _Field( description = __.access_doctab( 'role filter argument' ) ) ]
SourceArgument: __.typx.TypeAlias = __.typx.Annotated[
    str, _Field( description = __.access_doctab( 'source argument' ) ) ]
TermFilter: __.typx.TypeAlias = __.typx.Annotated[
    str, _Field( description = __.access_doctab( 'term filter argument' ) ) ]


_filters_default = _interfaces.Filters( )
_scribe = __.acquire_scribe( __name__ )


async def explore(
    source: SourceArgument,
    query: Query,
    filters: __.typx.Annotated[
        _interfaces.Filters,
        _Field( description = "Search and filtering options" ),
    ] = _filters_default,
    objects_max: __.typx.Annotated[
        int,
        _Field( description = __.access_doctab( 'objects max argument' ) ),
    ] = 5,
    include_documentation: __.typx.Annotated[
        bool,
        _Field(
            description = __.access_doctab(
                'include documentation argument' ) ),
    ] = True,
) -> dict[ str, __.typx.Any ]:
    ''' Explores objects by combining inventory search with documentation. '''
    _scribe.debug(
        "explore called: source=%s, query=%s, filters=%s, max_objects=%s, "
        "include_documentation=%s",
        source, query, filters, objects_max, include_documentation )
    try:
        return await _functions.explore(
            source, query, filters = filters,
            max_objects = objects_max,
            include_documentation = include_documentation )
    except Exception as exc:
        _scribe.error( "Error exploring: %s", exc )
        raise RuntimeError from exc


async def query_documentation(
    source: SourceArgument,
    query: Query,
    filters: __.typx.Annotated[
        _interfaces.Filters,
        _Field( description = "Search and filtering options" ),
    ] = _filters_default,
    results_max: ResultsMax = 10,
    include_snippets: IncludeSnippets = True,
) -> dict[ str, __.typx.Any ]:
    ''' Query documentation content with relevance ranking. '''
    _scribe.debug(
        "query_documentation called: source=%s, query=%s, filters=%s",
        source, query, filters )
    return await _functions.query_documentation(
        source, query, filters = filters,
        max_results = results_max, include_snippets = include_snippets )


async def summarize_inventory(
    source: SourceArgument,
    filters: __.typx.Annotated[
        _interfaces.Filters,
        _Field( description = "Search and filtering options" ),
    ] = _filters_default,
    term: TermFilter = '',
) -> str:
    ''' Provides human-readable summary of inventory. '''
    try:
        return await _functions.summarize_inventory(
            source, term, filters = filters )
    except Exception as exc:
        _scribe.error( "Error summarizing inventory: %s", exc )
        raise RuntimeError from exc


async def serve(
    auxdata: __.Globals, /, *,
    port: int = 0,
    transport: str = 'stdio',
) -> None:
    ''' Runs MCP server. '''
    _scribe.debug( "Initializing FastMCP server" )
    mcp = _FastMCP( 'Sphinx MCP Server', port = port )
    _scribe.debug( "Registering summarize_inventory tool" )
    mcp.tool( )( summarize_inventory )
    _scribe.debug( "Registering query_documentation tool" )
    mcp.tool( )( query_documentation )
    _scribe.debug( "Registering explore tool" )
    mcp.tool( )( explore )
    _scribe.debug( "Tools registered successfully" )
    match transport:
        case 'sse': await mcp.run_sse_async( mount_path = None )
        case 'stdio': await mcp.run_stdio_async( )
        case _: raise ValueError
