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
from . import cacheproxy as _cacheproxy
from . import exceptions as _exceptions
from . import functions as _functions
from . import interfaces as _interfaces
from . import server as _server
from . import state as _state


_scribe = __.acquire_scribe( __name__ )


GroupByArgument: __.typx.TypeAlias = __.typx.Annotated[
    __.typx.Optional[ str ],
    __.tyro.conf.arg( help = __.access_doctab( 'group by argument' ) ),
]
IncludeSnippets: __.typx.TypeAlias = __.typx.Annotated[
    bool,
    __.tyro.conf.arg( help = __.access_doctab( 'include snippets argument' ) ),
]
PortArgument: __.typx.TypeAlias = __.typx.Annotated[
    __.typx.Optional[ int ],
    __.tyro.conf.arg( help = __.access_doctab( 'server port argument' ) ),
]
QueryArgument: __.typx.TypeAlias = __.typx.Annotated[
    str,
    __.tyro.conf.arg( help = __.access_doctab( 'query argument' ) ),
]
ResultsMax: __.typx.TypeAlias = __.typx.Annotated[
    int,
    __.tyro.conf.arg( help = __.access_doctab( 'results max argument' ) ),
]
SourceArgument: __.typx.TypeAlias = __.typx.Annotated[
    str,
    __.tyro.conf.arg( help = __.access_doctab( 'source argument' ) ),
]
TransportArgument: __.typx.TypeAlias = __.typx.Annotated[
    __.typx.Optional[ str ],
    __.tyro.conf.arg( help = __.access_doctab( 'transport argument' ) ),
]


_search_behaviors_default = _interfaces.SearchBehaviors( )
_filters_default = __.immut.Dictionary[ str, __.typx.Any ]( )


class DetectCommand(
    __.CliCommand, decorators = ( __.standard_tyro_class, ),
):
    ''' Detect which processors can handle a documentation source. '''

    source: SourceArgument
    genus: __.typx.Annotated[
        _interfaces.ProcessorGenera,
        __.tyro.conf.arg( help = "Processor genus (inventory or structure)." ),
    ]
    processor_name: __.typx.Annotated[
        __.typx.Optional[ str ],
        __.tyro.conf.arg( help = "Specific processor to use." ),
    ] = None

    async def __call__(
        self, auxdata: __.Globals, display: __.ConsoleDisplay
    ) -> None:
        stream = await display.provide_stream( )
        try:
            processor_name = (
                self.processor_name if self.processor_name is not None
                else __.absent )
            result = await _functions.detect(
                auxdata, self.source, self.genus,
                processor_name = processor_name )
            print( __.json.dumps( result, indent = 2 ), file = stream )
        except Exception as exc:
            _scribe.error( "detect failed: %s", exc )
            print( _format_cli_exception( exc ), file = stream )
            raise SystemExit( 1 ) from None


class QueryInventoryCommand(
    __.CliCommand, decorators = ( __.standard_tyro_class, ),
):
    ''' Searches object inventory by name with fuzzy matching. '''

    source: SourceArgument
    query: QueryArgument
    details: __.typx.Annotated[
        _interfaces.InventoryQueryDetails,
        __.tyro.conf.arg(
            help = __.access_doctab( 'query details argument' ) ),
    ] = _interfaces.InventoryQueryDetails.Documentation
    filters: __.typx.Annotated[
        dict[ str, __.typx.Any ],
        __.tyro.conf.arg( prefix_name = False ),
    ] = __.dcls.field( default_factory = lambda: dict( _filters_default ) )
    search_behaviors: __.typx.Annotated[
        _interfaces.SearchBehaviors,
        __.tyro.conf.arg( prefix_name = False ),
    ] = _search_behaviors_default
    results_max: __.typx.Annotated[
        int,
        __.tyro.conf.arg( help = __.access_doctab( 'results max argument' ) ),
    ] = 5

    async def __call__(
        self, auxdata: __.Globals, display: __.ConsoleDisplay
    ) -> None:
        stream = await display.provide_stream( )
        try:
            result = await _functions.query_inventory(
                auxdata,
                self.source,
                self.query,
                search_behaviors = self.search_behaviors,
                filters = self.filters,
                results_max = self.results_max,
                details = self.details )
            print( __.json.dumps( result, indent = 2 ), file = stream )
        except Exception as exc:
            _scribe.error( "query-inventory failed: %s", exc )
            print( _format_cli_exception( exc ), file = stream )
            raise SystemExit( 1 ) from None


class QueryContentCommand(
    __.CliCommand, decorators = ( __.standard_tyro_class, ),
):
    ''' Searches documentation content with relevance ranking and snippets. '''

    source: SourceArgument
    query: QueryArgument
    search_behaviors: __.typx.Annotated[
        _interfaces.SearchBehaviors,
        __.tyro.conf.arg( prefix_name = False ),
    ] = _search_behaviors_default
    filters: __.typx.Annotated[
        dict[ str, __.typx.Any ],
        __.tyro.conf.arg( prefix_name = False ),
    ] = __.dcls.field( default_factory = lambda: dict( _filters_default ) )
    include_snippets: IncludeSnippets = True
    results_max: ResultsMax = 10

    async def __call__(
        self, auxdata: __.Globals, display: __.ConsoleDisplay
    ) -> None:
        stream = await display.provide_stream( )
        try:
            result = await _functions.query_content(
                auxdata, self.source, self.query,
                search_behaviors = self.search_behaviors,
                filters = self.filters,
                results_max = self.results_max,
                include_snippets = self.include_snippets )
            print( __.json.dumps( result, indent = 2 ), file = stream )
        except Exception as exc:
            _scribe.error( "query-content failed: %s", exc )
            print( _format_cli_exception( exc ), file = stream )
            raise SystemExit( 1 ) from None


class SummarizeInventoryCommand(
    __.CliCommand, decorators = ( __.standard_tyro_class, ),
):
    ''' Provides human-readable summary of inventory. '''

    source: SourceArgument
    query: QueryArgument = ''
    filters: __.typx.Annotated[
        dict[ str, __.typx.Any ],
        __.tyro.conf.arg( prefix_name = False ),
    ] = __.dcls.field( default_factory = lambda: dict( _filters_default ) )
    group_by: GroupByArgument = None
    search_behaviors: __.typx.Annotated[
        _interfaces.SearchBehaviors,
        __.tyro.conf.arg( prefix_name = False ),
    ] = _search_behaviors_default

    async def __call__(
        self, auxdata: __.Globals, display: __.ConsoleDisplay
    ) -> None:
        stream = await display.provide_stream( )
        result = await _functions.summarize_inventory(
            auxdata, self.source, self.query or '',
            search_behaviors = self.search_behaviors,
            filters = self.filters,
            group_by = self.group_by )
        print( result, file = stream )


class SurveyProcessorsCommand(
    __.CliCommand, decorators = ( __.standard_tyro_class, ),
):
    ''' List processors for specified genus and their capabilities. '''

    genus: __.typx.Annotated[
        _interfaces.ProcessorGenera,
        __.tyro.conf.arg( help = "Processor genus (inventory or structure)." ),
    ]
    name: __.typx.Annotated[
        __.typx.Optional[ str ],
        __.tyro.conf.arg( help = "Name of processor to describe" ),
    ] = None

    async def __call__(
        self, auxdata: __.Globals, display: __.ConsoleDisplay
    ) -> None:
        stream = await display.provide_stream( )
        nomargs: __.NominativeArguments = { 'genus': self.genus }
        if self.name is not None: nomargs[ 'name' ] = self.name
        try:
            result = await _functions.survey_processors( auxdata, **nomargs )
            print( __.json.dumps( result, indent = 2 ), file = stream )
        except Exception as exc:
            _scribe.error( "survey-processors failed: %s", exc )
            print( _format_cli_exception( exc ), file = stream )
            raise SystemExit( 1 ) from None


class UseCommand(
    __.CliCommand, decorators = ( __.standard_tyro_class, ),
):
    ''' Use MCP server tools. '''

    operation: __.typx.Union[
        __.typx.Annotated[
            DetectCommand,
            __.tyro.conf.subcommand( 'detect', prefix_name = False ),
        ],
        __.typx.Annotated[
            QueryInventoryCommand,
            __.tyro.conf.subcommand( 'query-inventory', prefix_name = False ),
        ],
        __.typx.Annotated[
            QueryContentCommand,
            __.tyro.conf.subcommand(
                'query-content', prefix_name = False ),
        ],
        __.typx.Annotated[
            SummarizeInventoryCommand,
            __.tyro.conf.subcommand(
                'summarize-inventory', prefix_name = False ),
        ],
        __.typx.Annotated[
            SurveyProcessorsCommand,
            __.tyro.conf.subcommand(
                'survey-processors', prefix_name = False ),
        ],
    ]

    async def __call__(
        self, auxdata: __.Globals, display: __.ConsoleDisplay
    ) -> None:
        await self.operation( auxdata = auxdata, display = display )


class ServeCommand(
    __.CliCommand, decorators = ( __.standard_tyro_class, ),
):
    ''' Starts MCP server. '''

    port: PortArgument = None
    transport: TransportArgument = None
    serve_function: __.typx.Callable[
        [ __.Globals ], __.cabc.Awaitable[ None ]
    ] = _server.serve
    async def __call__(
        self, auxdata: __.Globals, display: __.ConsoleDisplay
    ) -> None:
        nomargs: __.NominativeArguments = { }
        if self.port is not None:
            nomargs[ 'port' ] = self.port
        if self.transport is not None:
            nomargs[ 'transport' ] = self.transport
        await self.serve_function( auxdata, **nomargs )


class Cli( __.immut.DataclassObject, decorators = ( __.simple_tyro_class, ) ):
    ''' MCP server CLI. '''

    display: __.ConsoleDisplay
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
    config = (
        __.tyro.conf.HelptextFromCommentsOff,
    )
    with __.warnings.catch_warnings( ):
        __.warnings.filterwarnings(
            'ignore',
            message = r'Mutable type .* is used as a default value.*',
            category = UserWarning,
            module = 'tyro.constructors._struct_spec_dataclass' )
        try: __.asyncio.run( __.tyro.cli( Cli, config = config )( ) )
        except SystemExit: raise
        except BaseException as exc:
            __.report_exceptions( exc, _scribe )
            raise SystemExit( 1 ) from None


def _format_cli_exception( exc: Exception ) -> str:  # noqa: PLR0911
    ''' Formats exceptions for user-friendly CLI output. '''
    match exc:
        case _exceptions.ProcessorInavailability( ):
            return (
                f"❌ No processor found to handle source: {exc.source}\n"
                f"💡 Verify this is a Sphinx documentation site" )
        case _exceptions.InventoryInaccessibility( ):
            return (
                f"❌ Cannot access documentation inventory: {exc.source}\n"
                f"💡 Check URL accessibility and network connection" )
        case _exceptions.DocumentationContentAbsence( ):
            return (
                f"❌ Documentation structure not recognized: {exc.url}\n"
                f"💡 This may be an unsupported Sphinx theme" )
        case _exceptions.DocumentationObjectAbsence( ):
            return (
                f"❌ Object '{exc.object_id}' not found in page: {exc.url}\n"
                f"💡 Verify the object name and try a broader search" )
        case _exceptions.InventoryInvalidity( ):
            return (
                f"❌ Invalid documentation inventory: {exc.source}\n"
                f"💡 The documentation site may be corrupted" )
        case _exceptions.DocumentationInaccessibility( ):
            return (
                f"❌ Documentation inaccessible: {exc.url}\n"
                f"💡 Check URL accessibility and network connection" )
        case _:
            return f"❌ Unexpected error: {exc}"


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
    _state.Globals,
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
    auxdata = await __.appcore.prepare( **nomargs )
    content_cache, probe_cache, robots_cache = _cacheproxy.prepare( auxdata )
    return _state.Globals(
        **__.dcls.asdict( auxdata ),
        content_cache = content_cache,
        probe_cache = probe_cache,
        robots_cache = robots_cache )
