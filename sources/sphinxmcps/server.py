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


McpDomainFilter: __.typx.TypeAlias = __.typx.Annotated[
    str,
    _Field(
        description = "Filter objects by domain (e.g., 'py', 'std')"
    )
]
McpFuzzyThreshold: __.typx.TypeAlias = __.typx.Annotated[
    int,
    _Field(
        description = "Fuzzy matching threshold (0-100, higher = stricter)"
    )
]
McpIncludeSnippets: __.typx.TypeAlias = __.typx.Annotated[
    bool,
    _Field(
        description = "Include content snippets in results"
    )
]
McpMatchMode: __.typx.TypeAlias = __.typx.Annotated[
    str,
    _Field(
        description = "Term matching mode: 'exact', 'regex', or 'fuzzy'"
    )
]
McpMaxResults: __.typx.TypeAlias = __.typx.Annotated[
    int,
    _Field(
        description = "Maximum number of results to return"
    )
]
McpObjectName: __.typx.TypeAlias = __.typx.Annotated[
    str,
    _Field(
        description = "Name of the object to extract documentation for"
    )
]
McpOutputFormat: __.typx.TypeAlias = __.typx.Annotated[
    str,
    _Field(
        description = "Output format: 'markdown' or 'text'"
    )
]
McpPriorityFilter: __.typx.TypeAlias = __.typx.Annotated[
    str,
    _Field(
        description = "Filter objects by priority level (e.g., '1', '0')"
    )
]
McpQuery: __.typx.TypeAlias = __.typx.Annotated[
    str,
    _Field(
        description = "Search query for documentation content"
    )
]
McpRoleFilter: __.typx.TypeAlias = __.typx.Annotated[
    str,
    _Field(
        description = "Filter objects by role (e.g., 'function', 'class')"
    )
]
McpSourceArgument: __.typx.TypeAlias = __.typx.Annotated[
    str,
    _Field(
        description = "URL or file path to Sphinx documentation"
    )
]
McpTermFilter: __.typx.TypeAlias = __.typx.Annotated[
    str,
    _Field(
        description = "Filter objects by name (case-insensitive)"
    )
]


_scribe = __.acquire_scribe( __name__ )


async def extract_documentation(
    source: McpSourceArgument,
    object_name: McpObjectName,
    output_format: McpOutputFormat = 'markdown',
) -> __.cabc.Mapping[ str, __.typx.Any ]:
    ''' Extract documentation for a specific object from Sphinx docs. '''
    _scribe.debug(
        "extract_documentation called: source=%s, object_name=%s, format=%s",
        source, object_name, output_format )
    format_arg = (
        output_format if output_format in ( 'markdown', 'text' )
        else 'markdown'
    )
    try:
        return await _functions.extract_documentation(
            source, object_name, output_format = format_arg )
    except Exception as exc:
        _scribe.error( "Error extracting documentation: %s", exc )
        return { 'error': str( exc ) }


async def query_documentation(  # noqa: PLR0913
    source: McpSourceArgument,
    query: McpQuery,
    domain: McpDomainFilter = '',
    role: McpRoleFilter = '',
    priority: McpPriorityFilter = '',
    match_mode: McpMatchMode = 'fuzzy',
    fuzzy_threshold: McpFuzzyThreshold = 50,
    max_results: McpMaxResults = 10,
    include_snippets: McpIncludeSnippets = True,
) -> list[ __.cabc.Mapping[ str, __.typx.Any ] ]:
    ''' Query documentation content with relevance ranking. '''
    _scribe.debug(
        "query_documentation called: source=%s, query=%s", source, query )
    
    # Convert string match_mode to enum
    match_mode_enum = _functions.MatchMode.Exact
    if match_mode == 'regex':
        match_mode_enum = _functions.MatchMode.Regex
    elif match_mode == 'fuzzy':
        match_mode_enum = _functions.MatchMode.Fuzzy
    
    nomargs: __.NominativeArguments = { }
    if domain: nomargs[ 'domain' ] = domain
    if role: nomargs[ 'role' ] = role
    if priority: nomargs[ 'priority' ] = priority
    
    nomargs[ 'match_mode' ] = match_mode_enum
    nomargs[ 'fuzzy_threshold' ] = fuzzy_threshold
    nomargs[ 'max_results' ] = max_results
    nomargs[ 'include_snippets' ] = include_snippets
    
    try:
        return await _functions.query_documentation(
            source, query, **nomargs )
    except Exception as exc:
        _scribe.error( "Error querying documentation: %s", exc )
        return [ { 'error': str( exc ) } ]


def extract_inventory( # noqa: PLR0913
    source: McpSourceArgument,
    domain: McpDomainFilter = '',
    role: McpRoleFilter = '',
    term: McpTermFilter = '',
    priority: McpPriorityFilter = '',
    match_mode: McpMatchMode = 'exact',
    fuzzy_threshold: McpFuzzyThreshold = 50,
) -> dict[ str, __.typx.Any ]:
    ''' Extracts Sphinx inventory from location with optional filtering. '''
    _scribe.debug(
        "extract_inventory called: source=%s, domain=%s, role=%s, term=%s, "
        "priority=%s, match_mode=%s, fuzzy_threshold=%s",
        source, domain, role, term, priority, match_mode, fuzzy_threshold )
    _scribe.debug( "Processing extract_inventory request with RELOADEROO!" )
    nomargs: __.NominativeArguments = { }
    if domain: nomargs[ 'domain' ] = domain
    if role: nomargs[ 'role' ] = role
    if term: nomargs[ 'term' ] = term
    if priority: nomargs[ 'priority' ] = priority
    if match_mode == 'fuzzy':
        nomargs[ 'match_mode' ] = _functions.MatchMode.Fuzzy
        nomargs[ 'fuzzy_threshold' ] = fuzzy_threshold
    elif match_mode == 'regex':
        nomargs[ 'match_mode' ] = _functions.MatchMode.Regex
    else:  # 'exact' or any other value defaults to exact
        nomargs[ 'match_mode' ] = _functions.MatchMode.Exact
    return _functions.extract_inventory( source, **nomargs )


def summarize_inventory( # noqa: PLR0913
    source: McpSourceArgument,
    domain: McpDomainFilter = '',
    role: McpRoleFilter = '',
    term: McpTermFilter = '',
    priority: McpPriorityFilter = '',
    match_mode: McpMatchMode = 'exact',
    fuzzy_threshold: McpFuzzyThreshold = 50,
) -> str:
    ''' Provides human-readable summary of Sphinx inventory. '''
    _scribe.debug(
        "summarize_inventory called: source=%s, domain=%s, role=%s, term=%s, "
        "priority=%s, match_mode=%s, fuzzy_threshold=%s",
        source, domain, role, term, priority, match_mode, fuzzy_threshold )
    nomargs: __.NominativeArguments = { }
    if domain: nomargs[ 'domain' ] = domain
    if role: nomargs[ 'role' ] = role
    if term: nomargs[ 'term' ] = term
    if priority: nomargs[ 'priority' ] = priority
    if match_mode == 'fuzzy':
        nomargs[ 'match_mode' ] = _functions.MatchMode.Fuzzy
        nomargs[ 'fuzzy_threshold' ] = fuzzy_threshold
    elif match_mode == 'regex':
        nomargs[ 'match_mode' ] = _functions.MatchMode.Regex
    else:  # 'exact' or any other value defaults to exact
        nomargs[ 'match_mode' ] = _functions.MatchMode.Exact
    return _functions.summarize_inventory( source, **nomargs )


async def serve(
    auxdata: __.Globals, /, *,
    port: int = 0,
    transport: str = 'stdio',
) -> None:
    ''' Runs MCP server. '''
    _scribe.debug( "Initializing FastMCP server" )
    mcp = _FastMCP( 'Sphinx MCP Server', port = port )
    _scribe.debug( "Registering extract_inventory tool" )
    mcp.tool( )( extract_inventory )
    _scribe.debug( "Registering summarize_inventory tool" )
    mcp.tool( )( summarize_inventory )
    _scribe.debug( "Registering extract_documentation tool" )
    mcp.tool( )( extract_documentation )
    _scribe.debug( "Registering query_documentation tool" )
    mcp.tool( )( query_documentation )
    _scribe.debug( "Tools registered successfully" )
    match transport:
        case 'sse': await mcp.run_sse_async( mount_path = None )
        case 'stdio': await mcp.run_stdio_async( )
        case _: raise ValueError
