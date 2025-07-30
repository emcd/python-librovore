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


@__.dcls.dataclass( kw_only = True, slots = True )
class SearchBehaviorsMutable:
    ''' Mutable version of SearchBehaviors for FastMCP/Pydantic compatibility.

        Note: Fields are manually duplicated from SearchBehaviors to avoid
        immutable dataclass internals leaking into JSON schema generation.
    '''

    match_mode: _interfaces.MatchMode = _interfaces.MatchMode.Fuzzy
    fuzzy_threshold: int = 50


FiltersMutable: __.typx.TypeAlias = dict[ str, __.typx.Any ]
GroupByArgument: __.typx.TypeAlias = __.typx.Annotated[
    __.typx.Optional[ str ],
    _Field( description = __.access_doctab( 'group by argument' ) ),
]
IncludeSnippets: __.typx.TypeAlias = __.typx.Annotated[
    bool,
    _Field( description = __.access_doctab( 'include snippets argument' ) ),
]
Query: __.typx.TypeAlias = __.typx.Annotated[
    str, _Field( description = __.access_doctab( 'query argument' ) ) ]
ResultsMax: __.typx.TypeAlias = __.typx.Annotated[
    int, _Field( description = __.access_doctab( 'results max argument' ) ) ]
SourceArgument: __.typx.TypeAlias = __.typx.Annotated[
    str, _Field( description = __.access_doctab( 'source argument' ) ) ]
TermFilter: __.typx.TypeAlias = __.typx.Annotated[
    str, _Field( description = __.access_doctab( 'term filter argument' ) ) ]


_filters_default = FiltersMutable( )
_search_behaviors_default = SearchBehaviorsMutable( )

_scribe = __.acquire_scribe( __name__ )


async def detect(
    source: SourceArgument,
    all_detections: __.typx.Annotated[
        bool,
        _Field( description = "Return all detections or just best" ),
    ] = False,
) -> dict[ str, __.typx.Any ]:
    ''' Detects which processor(s) can handle a documentation source. '''
    _scribe.debug( "Starting detection for source: %s", source )
    return await _functions.detect( source, all_detections = all_detections )


async def query_inventory(  # noqa: PLR0913
    source: SourceArgument,
    query: Query,
    search_behaviors: __.typx.Annotated[
        SearchBehaviorsMutable,
        _Field( description = "Search behavior configuration" ),
    ] = _search_behaviors_default,
    filters: __.typx.Annotated[
        FiltersMutable,
        _Field( description = "Processor-specific filters" ),
    ] = _filters_default,
    details: __.typx.Annotated[
        _interfaces.InventoryQueryDetails,
        _Field( description = "Detail level for inventory results" ),
    ] = _interfaces.InventoryQueryDetails.Documentation,
    results_max: ResultsMax = 5,
) -> dict[ str, __.typx.Any ]:
    ''' Searches object inventory by name with fuzzy matching. '''
    _scribe.debug(
        "query_inventory called: source=%s, query=%s, "
        "search_behaviors=%s, filters=%s, results_max=%s, details=%s",
        source, query, search_behaviors, filters, results_max, details )
    try:
        immutable_search_behaviors = _to_immutable_search_behaviors(
            search_behaviors )
        immutable_filters = _to_immutable_filters( filters )
        return await _functions.query_inventory(
            source, query,
            search_behaviors = immutable_search_behaviors,
            filters = immutable_filters,
            results_max = results_max,
            details = details )
    except Exception as exc:
        # TODO: No log-and-raise pattern.
        _scribe.error( "Error in query_inventory: %s", exc )
        raise


async def query_content(  # noqa: PLR0913
    source: SourceArgument,
    query: Query,
    search_behaviors: __.typx.Annotated[
        SearchBehaviorsMutable,
        _Field( description = "Search behavior configuration" ),
    ] = _search_behaviors_default,
    filters: __.typx.Annotated[
        FiltersMutable,
        _Field( description = "Processor-specific filters" ),
    ] = _filters_default,
    include_snippets: IncludeSnippets = True,
    results_max: ResultsMax = 10,
) -> dict[ str, __.typx.Any ]:
    ''' Searches documentation content with relevance ranking and snippets. '''
    _scribe.debug(
        "query_content called: source=%s, query=%s, "
        "search_behaviors=%s, filters=%s",
        source, query, search_behaviors, filters )
    immutable_search_behaviors = _to_immutable_search_behaviors(
        search_behaviors )
    immutable_filters = _to_immutable_filters( filters )
    return await _functions.query_content(
        source, query,
        search_behaviors = immutable_search_behaviors,
        filters = immutable_filters,
        results_max = results_max, include_snippets = include_snippets )


async def summarize_inventory(
    source: SourceArgument,
    search_behaviors: __.typx.Annotated[
        SearchBehaviorsMutable,
        _Field( description = "Search behavior configuration." ),
    ] = _search_behaviors_default,
    filters: __.typx.Annotated[
        FiltersMutable,
        _Field( description = "Processor-specific filters." ),
    ] = _filters_default,
    group_by: GroupByArgument = None,
    term: TermFilter = '',
) -> str:
    ''' Provides human-readable summary of inventory. '''
    try:
        immutable_search_behaviors = _to_immutable_search_behaviors(
            search_behaviors )
        immutable_filters = _to_immutable_filters( filters )
        return await _functions.summarize_inventory(
            source, term,
            search_behaviors = immutable_search_behaviors,
            filters = immutable_filters,
            group_by = group_by )
    except Exception as exc:
        # TODO: No log-and-raise pattern.
        _scribe.error( "Error in summarize_inventory: %s", exc )
        raise


async def survey_processors(
    name: __.typx.Annotated[
        __.typx.Optional[ str ],
        _Field( description = "Optional processor name to filter results." )
    ] = None,
) -> dict[ str, __.typx.Any ]:
    ''' Lists all processors or specific processor capabilities. '''
    _scribe.debug( "Surveying processors: %s", name or "all" )
    return await _functions.survey_processors( name )


async def serve(
    auxdata: __.Globals, /, *,
    port: int = 0,
    transport: str = 'stdio',
) -> None:
    ''' Runs MCP server. '''
    _scribe.debug( "Initializing FastMCP server." )
    mcp = _FastMCP( 'Sphinx MCP Server', port = port )
    _scribe.debug( "Registering tools." )
    mcp.tool( )( detect )
    mcp.tool( )( query_inventory )
    mcp.tool( )( query_content )
    mcp.tool( )( summarize_inventory )
    mcp.tool( )( survey_processors )
    _scribe.debug( "All tools registered successfully." )
    match transport:
        case 'sse': await mcp.run_sse_async( mount_path = None )
        case 'stdio': await mcp.run_stdio_async( )
        case _: raise ValueError


def _to_immutable_filters(
    mutable_filters: FiltersMutable
) -> __.immut.Dictionary[ str, __.typx.Any ]:
    ''' Converts mutable filters dict to immutable dictionary. '''
    return __.immut.Dictionary[ str, __.typx.Any ]( mutable_filters )


def _to_immutable_search_behaviors(
    mutable_behaviors: SearchBehaviorsMutable
) -> _interfaces.SearchBehaviors:
    ''' Converts mutable search behaviors to immutable. '''
    field_values = {
        field.name: getattr( mutable_behaviors, field.name )
        for field in __.dcls.fields( mutable_behaviors )
        if not field.name.startswith( '_' ) }
    return _interfaces.SearchBehaviors( **field_values )
