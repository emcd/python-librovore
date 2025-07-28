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


class FiltersMutable( _interfaces.Filters, instances_mutables = '*' ):
    ''' Mutable version of Filters for FastMCP/Pydantic compatibility. '''


IncludeSnippets: __.typx.TypeAlias = __.typx.Annotated[
    bool,
    _Field( description = __.access_doctab( 'include snippets argument' ) ),
]
ResultsMax: __.typx.TypeAlias = __.typx.Annotated[
    int, _Field( description = __.access_doctab( 'results max argument' ) ) ]
Query: __.typx.TypeAlias = __.typx.Annotated[
    str, _Field( description = __.access_doctab( 'query argument' ) ) ]
SourceArgument: __.typx.TypeAlias = __.typx.Annotated[
    str, _Field( description = __.access_doctab( 'source argument' ) ) ]
TermFilter: __.typx.TypeAlias = __.typx.Annotated[
    str, _Field( description = __.access_doctab( 'term filter argument' ) ) ]


_filters_default = FiltersMutable( )
_scribe = __.acquire_scribe( __name__ )


async def describe_processor(
    processor_name: __.typx.Annotated[
        str,
        _Field( description = "Name of processor to describe" ),
    ],
) -> dict[ str, __.typx.Any ]:
    ''' Gets detailed capabilities for a specific processor. '''
    _scribe.debug( "Describing processor: %s", processor_name )
    return await _functions.describe_processor( processor_name )


async def detect(
    source: SourceArgument,
    all_detections: __.typx.Annotated[
        bool,
        _Field( description = "Return all detections or just best" ),
    ] = False,
) -> dict[ str, __.typx.Any ]:
    ''' Detects which processor(s) can handle a documentation source. '''
    _scribe.debug( "Starting detection for source: %s", source )
    return await _functions.detect( source, all_detections )


async def explore(
    source: SourceArgument,
    query: Query,
    filters: __.typx.Annotated[
        FiltersMutable,
        _Field( description = "Search and filtering options" ),
    ] = _filters_default,
    include_documentation: __.typx.Annotated[
        bool,
        _Field(
            description = __.access_doctab(
                'include documentation argument' ) ),
    ] = True,
    results_max: ResultsMax = 5,
) -> dict[ str, __.typx.Any ]:
    ''' Explores objects by combining inventory search with documentation. '''
    _scribe.debug(
        "explore called: source=%s, query=%s, filters=%s, results_max=%s, "
        "include_documentation=%s",
        source, query, filters, results_max, include_documentation )
    try:
        immutable_filters = _to_immutable_filters( filters )
        return await _functions.explore(
            source, query, filters = immutable_filters,
            results_max = results_max,
            include_documentation = include_documentation )
    except Exception as exc:
        _scribe.error( "Error exploring: %s", exc )
        raise RuntimeError from exc


async def query_documentation(
    source: SourceArgument,
    query: Query,
    filters: __.typx.Annotated[
        FiltersMutable,
        _Field( description = "Search and filtering options" ),
    ] = _filters_default,
    include_snippets: IncludeSnippets = True,
    results_max: ResultsMax = 10,
) -> dict[ str, __.typx.Any ]:
    ''' Query documentation content with relevance ranking. '''
    _scribe.debug(
        "query_documentation called: source=%s, query=%s, filters=%s",
        source, query, filters )
    immutable_filters = _to_immutable_filters( filters )
    return await _functions.query_documentation(
        source, query, filters = immutable_filters,
        results_max = results_max, include_snippets = include_snippets )


async def summarize_inventory(
    source: SourceArgument,
    filters: __.typx.Annotated[
        FiltersMutable,
        _Field( description = "Search and filtering options" ),
    ] = _filters_default,
    term: TermFilter = '',
) -> str:
    ''' Provides human-readable summary of inventory. '''
    try:
        immutable_filters = _to_immutable_filters( filters )
        return await _functions.summarize_inventory(
            source, term, filters = immutable_filters )
    except Exception as exc:
        _scribe.error( "Error summarizing inventory: %s", exc )
        raise RuntimeError from exc


async def survey_processors( ) -> dict[ str, __.typx.Any ]:
    ''' Lists all available processors and their capabilities. '''
    _scribe.debug( "Listing available processors" )
    return await _functions.survey_processors( )


async def serve(
    auxdata: __.Globals, /, *,
    port: int = 0,
    transport: str = 'stdio',
) -> None:
    ''' Runs MCP server. '''
    _scribe.debug( "Initializing FastMCP server" )
    mcp = _FastMCP( 'Sphinx MCP Server', port = port )
    _scribe.debug( "Registering core tools" )
    mcp.tool( )( summarize_inventory )
    mcp.tool( )( query_documentation )
    mcp.tool( )( explore )
    _scribe.debug( "Registering capability tools" )
    mcp.tool( )( detect )
    mcp.tool( )( survey_processors )
    mcp.tool( )( describe_processor )
    _scribe.debug( "All tools registered successfully" )
    match transport:
        case 'sse': await mcp.run_sse_async( mount_path = None )
        case 'stdio': await mcp.run_stdio_async( )
        case _: raise ValueError


def _to_immutable_filters(
    mutable_filters: FiltersMutable
) -> _interfaces.Filters:
    ''' Converts mutable filters to immutable using dataclass fields. '''
    field_values = {
        field.name: getattr( mutable_filters, field.name )
        for field in __.dcls.fields( mutable_filters )
        if not field.name.startswith( '_' ) }
    return _interfaces.Filters( **field_values )
