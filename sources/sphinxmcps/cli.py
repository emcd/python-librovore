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


''' Command-line interface. '''


from . import __
from . import functions as _functions
from . import interfaces as _interfaces
from . import server as _server


CliDomainFilter: __.typx.TypeAlias = __.typx.Annotated[
    __.typx.Optional[ str ],
    __.ddoc.Doc( '''
        Filter objects by Sphinx domain. Built-in domains:
        'py' (Python), 'std' (standard), 'c' (C), 'cpp' (C++),
        'js' (JavaScript), 'rst' (reStructuredText),
        'math' (Mathematics). Empty string shows all domains.
    ''' )
]
CliFuzzyThreshold: __.typx.TypeAlias = __.typx.Annotated[
    int,
    __.ddoc.Doc( ''' Fuzzy matching threshold (0-100, higher = stricter). ''' )
]
CliMatchMode: __.typx.TypeAlias = __.typx.Annotated[
    _interfaces.MatchMode,
    __.ddoc.Doc( ''' Term matching mode: Exact, Regex, or Fuzzy. ''' )
]
CliPortArgument: __.typx.TypeAlias = __.typx.Annotated[
    __.typx.Optional[ int ], __.ddoc.Doc( ''' TCP port for server. ''' )
]
CliPriorityFilter: __.typx.TypeAlias = __.typx.Annotated[
    __.typx.Optional[ str ],
    __.ddoc.Doc( ''' Filter objects by priority level (e.g., '1', '0'). ''' )
]
CliRoleFilter: __.typx.TypeAlias = __.typx.Annotated[
    __.typx.Optional[ str ],
    __.ddoc.Doc( ''' Filter objects by role (e.g., 'function'). ''' )
]
CliSourceArgument: __.typx.TypeAlias = __.typx.Annotated[
    str, __.ddoc.Doc( ''' URL or file path to documentation source. ''' )
]
CliTermFilter: __.typx.TypeAlias = __.typx.Annotated[
    __.typx.Optional[ str ],
    __.ddoc.Doc( ''' Filter objects by name containing this text. ''' )
]
CliTransportArgument: __.typx.TypeAlias = __.typx.Annotated[
    __.typx.Optional[ str ], __.ddoc.Doc( ''' Transport: stdio or sse. ''' )
]
CliQueryArgument: __.typx.TypeAlias = __.typx.Annotated[
    str,
    __.ddoc.Doc( ''' Search query for documentation content. ''' )
]
CliMaxResults: __.typx.TypeAlias = __.typx.Annotated[
    int,
    __.ddoc.Doc( ''' Maximum number of results to return. ''' )
]
CliIncludeSnippets: __.typx.TypeAlias = __.typx.Annotated[
    bool,
    __.ddoc.Doc( ''' Include content snippets in results. ''' )
]


class ExtractInventoryCommand(
    _interfaces.CliCommand, decorators = ( __.standard_tyro_class, ),
):
    ''' Extracts inventory with optional filtering. '''

    source: CliSourceArgument
    domain: CliDomainFilter = None
    role: CliRoleFilter = None
    term: CliTermFilter = None
    priority: CliPriorityFilter = None
    match_mode: CliMatchMode = _interfaces.MatchMode.Exact
    fuzzy_threshold: CliFuzzyThreshold = 50

    async def __call__(
        self, auxdata: __.Globals, display: _interfaces.ConsoleDisplay
    ) -> None:
        stream = await display.provide_stream( )
        nomargs: __.NominativeArguments = { }
        if self.domain is not None:
            nomargs[ 'domain' ] = self.domain
        if self.role is not None:
            nomargs[ 'role' ] = self.role
        if self.term is not None:
            nomargs[ 'term' ] = self.term
        if self.priority is not None:
            nomargs[ 'priority' ] = self.priority

        # Pass through match mode directly
        nomargs[ 'match_mode' ] = self.match_mode
        if self.match_mode == _interfaces.MatchMode.Fuzzy:
            nomargs[ 'fuzzy_threshold' ] = self.fuzzy_threshold

        data = await _functions.extract_inventory( self.source, **nomargs )
        print( __.json.dumps( data, indent = 2 ), file = stream )


class SummarizeInventoryCommand(
    _interfaces.CliCommand, decorators = ( __.standard_tyro_class, ),
):
    ''' Provides human-readable summary of inventory. '''

    source: CliSourceArgument
    domain: CliDomainFilter = None
    role: CliRoleFilter = None
    term: CliTermFilter = None
    priority: CliPriorityFilter = None
    match_mode: CliMatchMode = _interfaces.MatchMode.Exact
    fuzzy_threshold: CliFuzzyThreshold = 50

    async def __call__(
        self, auxdata: __.Globals, display: _interfaces.ConsoleDisplay
    ) -> None:
        stream = await display.provide_stream( )
        nomargs: __.NominativeArguments = { }
        if self.domain is not None:
            nomargs[ 'domain' ] = self.domain
        if self.role is not None:
            nomargs[ 'role' ] = self.role
        if self.term is not None:
            nomargs[ 'term' ] = self.term
        if self.priority is not None:
            nomargs[ 'priority' ] = self.priority

        # Pass through match mode directly
        nomargs[ 'match_mode' ] = self.match_mode
        if self.match_mode == _interfaces.MatchMode.Fuzzy:
            nomargs[ 'fuzzy_threshold' ] = self.fuzzy_threshold

        result = await _functions.summarize_inventory( self.source, **nomargs )
        print( result, file = stream )


class ExtractDocumentationCommand(
    _interfaces.CliCommand, decorators = ( __.standard_tyro_class, ),
):
    ''' Extracts documentation for a specific object from source. '''

    source: CliSourceArgument
    object_name: __.typx.Annotated[
        str, __.ddoc.Doc(
            ''' Name of the object to extract documentation for. ''' )
    ]

    async def __call__(
        self, auxdata: __.Globals, display: _interfaces.ConsoleDisplay
    ) -> None:
        stream = await display.provide_stream( )

        result = await _functions.extract_documentation(
            self.source, self.object_name )
        print( __.json.dumps( result, indent = 2 ), file = stream )


class QueryDocumentationCommand(
    _interfaces.CliCommand, decorators = ( __.standard_tyro_class, ),
):
    ''' Queries documentation content with relevance ranking. '''

    source: CliSourceArgument
    query: CliQueryArgument
    domain: CliDomainFilter = None
    role: CliRoleFilter = None
    priority: CliPriorityFilter = None
    match_mode: CliMatchMode = _interfaces.MatchMode.Fuzzy
    fuzzy_threshold: CliFuzzyThreshold = 50
    max_results: CliMaxResults = 10
    include_snippets: CliIncludeSnippets = True

    async def __call__(
        self, auxdata: __.Globals, display: _interfaces.ConsoleDisplay
    ) -> None:
        stream = await display.provide_stream( )
        nomargs: __.NominativeArguments = { }

        if self.domain is not None:
            nomargs[ 'domain' ] = self.domain
        if self.role is not None:
            nomargs[ 'role' ] = self.role
        if self.priority is not None:
            nomargs[ 'priority' ] = self.priority

        nomargs[ 'match_mode' ] = self.match_mode
        nomargs[ 'fuzzy_threshold' ] = self.fuzzy_threshold
        nomargs[ 'max_results' ] = self.max_results
        nomargs[ 'include_snippets' ] = self.include_snippets

        result = await _functions.query_documentation(
            self.source, self.query, **nomargs )
        print( __.json.dumps( result, indent = 2 ), file = stream )


class UseCommand(
    _interfaces.CliCommand, decorators = ( __.standard_tyro_class, ),
):
    ''' Use MCP server tools. '''

    operation: __.typx.Union[
        __.typx.Annotated[
            ExtractInventoryCommand,
            __.tyro.conf.subcommand(
                'extract-inventory', prefix_name = False
            ),
        ],
        __.typx.Annotated[
            SummarizeInventoryCommand,
            __.tyro.conf.subcommand(
                'summarize-inventory', prefix_name = False
            ),
        ],
        __.typx.Annotated[
            ExtractDocumentationCommand,
            __.tyro.conf.subcommand(
                'extract-documentation', prefix_name = False
            ),
        ],
        __.typx.Annotated[
            QueryDocumentationCommand,
            __.tyro.conf.subcommand(
                'query-documentation', prefix_name = False
            ),
        ],
    ]

    async def __call__(
        self, auxdata: __.Globals, display: _interfaces.ConsoleDisplay
    ) -> None:
        await self.operation( auxdata = auxdata, display = display )


class ServeCommand(
    _interfaces.CliCommand, decorators = ( __.standard_tyro_class, ),
):
    ''' Starts MCP server. '''

    port: CliPortArgument = None
    transport: CliTransportArgument = None
    serve_function: __.typx.Callable[
        [ __.Globals ], __.cabc.Awaitable[ None ]
    ] = _server.serve
    async def __call__(
        self, auxdata: __.Globals, display: _interfaces.ConsoleDisplay
    ) -> None:
        nomargs: __.NominativeArguments = { }
        if self.port is not None:
            nomargs[ 'port' ] = self.port
        if self.transport is not None:
            nomargs[ 'transport' ] = self.transport
        await self.serve_function( auxdata, **nomargs )


class Cli(
    __.immut.DataclassObject,
    decorators = ( __.simple_tyro_class, ),
):
    ''' MCP server CLI. '''

    display: _interfaces.ConsoleDisplay
    command: __.typx.Union[
        __.typx.Annotated[
            UseCommand,
            __.tyro.conf.subcommand( 'use', prefix_name = False ),
        ],
        __.typx.Annotated[
            ServeCommand,
            __.tyro.conf.subcommand( 'serve', prefix_name = False ),
        ],
    ]
    logfile: __.typx.Annotated[
        __.typx.Optional[ str ],
        __.ddoc.Doc( ''' Path to log capture file. ''' ),
    ] = None

    async def __call__( self ):
        ''' Invokes command after library preparation. '''
        nomargs = self.prepare_invocation_args( )
        async with __.ctxl.AsyncExitStack( ) as exits:
            auxdata = await _prepare( exits = exits, **nomargs )
            # Load processors for CLI operations
            from . import xtnsmgr
            await xtnsmgr.register_processors( auxdata )
            await self.command( auxdata = auxdata, display = self.display )

    def prepare_invocation_args(
        self,
    ) -> __.cabc.Mapping[ str, __.typx.Any ]:
        ''' Prepares arguments for initial configuration. '''
        args: dict[ str, __.typx.Any ] = dict(
            environment = True,
            logfile = self.logfile,
        )
        return args


def execute( ) -> None:
    ''' Entrypoint for CLI execution. '''
    from asyncio import run
    config = (
        __.tyro.conf.HelptextFromCommentsOff,
    )
    try: run( __.tyro.cli( Cli, config = config )( ) )
    except SystemExit: raise
    except BaseException as exc:
        print( exc, file = __.sys.stderr )
        raise SystemExit( 1 ) from None


async def _prepare(
    environment: __.typx.Annotated[
        bool,
        __.ddoc.Doc( ''' Whether to configure environment. ''' )
    ],
    exits: __.typx.Annotated[
        __.ctxl.AsyncExitStack,
        __.ddoc.Doc( ''' Exit stack for resource management. ''' )
    ],
    logfile: __.typx.Annotated[
        __.typx.Optional[ str ],
        __.ddoc.Doc( ''' Path to log capture file. ''' )
    ],
) -> __.typx.Annotated[
    __.Globals,
    __.ddoc.Doc( ''' Configured global state. ''' )
]:
    ''' Configures application based on arguments. '''
    nomargs: __.NominativeArguments = {
        'environment': environment,
        'exits': exits,
    }
    if logfile:
        logfile_p = __.Path( logfile ).resolve( )
        ( logfile_p.parent ).mkdir( parents = True, exist_ok = True )
        logstream = exits.enter_context( logfile_p.open( 'w' ) )
        inscription = __.appcore.inscription.Control(
            level = 'debug', target = logstream )
        nomargs[ 'inscription' ] = inscription
    return await __.appcore.prepare( **nomargs )
