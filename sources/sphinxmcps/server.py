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


def extract_inventory( # noqa: PLR0913
    source: __.typx.Annotated[
        str,
        _Field(
            description = "URL or file path to Sphinx documentation"
        )
    ],
    domain: __.typx.Annotated[
        str,
        _Field(
            description = "Filter objects by domain (e.g., 'py', 'std')"
        )
    ] = '',
    role: __.typx.Annotated[
        str,
        _Field(
            description = "Filter objects by role (e.g., 'function', 'class')"
        )
    ] = '',
    term: __.typx.Annotated[
        str,
        _Field(
            description = "Filter objects by name (case-insensitive)"
        )
    ] = '',
    match_mode: __.typx.Annotated[
        str,
        _Field(
            description = "Term matching mode: 'exact', 'regex', or 'fuzzy'"
        )
    ] = 'exact',
    fuzzy_threshold: __.typx.Annotated[
        int,
        _Field(
            description = "Fuzzy matching threshold (0-100, higher = stricter)"
        )
    ] = 50,
) -> dict[ str, __.typx.Any ]:
    ''' Extracts Sphinx inventory from URL or file path with optional
    filtering.

        Args:
            source: URL or file path to Sphinx documentation
                    (objects.inv auto-appended)
            domain: Filter objects by domain (e.g., 'py', 'std')
            role: Filter objects by role (e.g., 'function', 'class', 'method')
            term: Filter objects by name containing this text
                    (case-insensitive unless match_mode='regex')
            match_mode: Term matching mode ('exact', 'regex', or 'fuzzy')
            fuzzy_threshold: Fuzzy matching threshold (0-100, higher stricter)
    '''
    _scribe.debug(
        "extract_inventory called: source=%s, domain=%s, role=%s, term=%s, "
        "match_mode=%s, fuzzy_threshold=%s",
        source, domain, role, term, match_mode, fuzzy_threshold
    )
    _scribe.debug( "Processing extract_inventory request with RELOADEROO!" )
    nomargs: __.NominativeArguments = { }
    if domain:
        nomargs[ 'domain' ] = domain
    if role:
        nomargs[ 'role' ] = role
    if term:
        nomargs[ 'term' ] = term

    # Convert string match_mode to enum
    if match_mode == 'fuzzy':
        nomargs[ 'match_mode' ] = _functions.MatchMode.Fuzzy
        nomargs[ 'fuzzy_threshold' ] = fuzzy_threshold
    elif match_mode == 'regex':
        nomargs[ 'match_mode' ] = _functions.MatchMode.Regex
    else:  # 'exact' or any other value defaults to exact
        nomargs[ 'match_mode' ] = _functions.MatchMode.Exact

    return _functions.extract_inventory( source, **nomargs )


def summarize_inventory( # noqa: PLR0913
    source: __.typx.Annotated[
        str,
        _Field(
            description = "URL or file path to Sphinx documentation"
        )
    ],
    domain: __.typx.Annotated[
        str,
        _Field(
            description = "Filter objects by domain (e.g., 'py', 'std')"
        )
    ] = '',
    role: __.typx.Annotated[
        str,
        _Field(
            description = "Filter objects by role (e.g., 'function', 'class')"
        )
    ] = '',
    term: __.typx.Annotated[
        str,
        _Field(
            description = "Filter objects by name (case-insensitive)"
        )
    ] = '',
    match_mode: __.typx.Annotated[
        str,
        _Field(
            description = "Term matching mode: 'exact', 'regex', or 'fuzzy'"
        )
    ] = 'exact',
    fuzzy_threshold: __.typx.Annotated[
        int,
        _Field(
            description = "Fuzzy matching threshold (0-100, higher = stricter)"
        )
    ] = 50,
) -> str:
    ''' Provides human-readable summary of Sphinx inventory.

        Args:
            source: URL or file path to Sphinx documentation
                    (objects.inv auto-appended)
            domain: Filter objects by domain (e.g., 'py', 'std')
            role: Filter objects by role (e.g., 'function', 'class', 'method')
            term: Filter objects by name containing this text
                    (case-insensitive unless match_mode='regex')
            match_mode: Term matching mode ('exact', 'regex', or 'fuzzy')
            fuzzy_threshold: Fuzzy matching threshold (0-100, higher stricter)
    '''
    _scribe.debug(
        "summarize_inventory called: source=%s, domain=%s, role=%s, term=%s, "
        "match_mode=%s, fuzzy_threshold=%s",
        source, domain, role, term, match_mode, fuzzy_threshold
    )
    nomargs: __.NominativeArguments = { }
    if domain:
        nomargs[ 'domain' ] = domain
    if role:
        nomargs[ 'role' ] = role
    if term:
        nomargs[ 'term' ] = term

    # Convert string match_mode to enum
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
    _scribe.debug( "Tools registered successfully" )
    match transport:
        case 'sse': await mcp.run_sse_async( mount_path = None )
        case 'stdio': await mcp.run_stdio_async( )
        case _: raise ValueError

