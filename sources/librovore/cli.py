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
from . import results as _results
from . import server as _server
from . import state as _state

_scribe = __.acquire_scribe( __name__ )




class TargetStream( __.enum.Enum ):
    ''' Output stream selection. '''
    Stdout = 'stdout'
    Stderr = 'stderr'


TargetMutex = __.tyro.conf.create_mutex_group( required = False )


class DisplayOptions( __.immut.DataclassObject ):
    ''' Consolidated display configuration for CLI output. '''
    format: _interfaces.DisplayFormat = _interfaces.DisplayFormat.Markdown
    target_stream: __.typx.Annotated[
        __.typx.Optional[ TargetStream ],
        TargetMutex,
        __.tyro.conf.arg( help = "Output to stdout or stderr." )
    ] = TargetStream.Stderr
    target_file: __.typx.Annotated[
        __.typx.Optional[ __.Path ],
        TargetMutex,
        __.tyro.conf.arg( help = "Output to specified file." )
    ] = None
    color: __.typx.Annotated[
        bool,
        __.tyro.conf.arg(
            aliases = ( "--ansi-sgr", ),
            help = "Enable colored output and terminal formatting."
        ),
    ] = True

    async def provide_stream( 
        self, exits: __.ctxl.AsyncExitStack
    ) -> __.typx.TextIO:
        ''' Provides the target output stream. '''
        if self.target_file is not None:
            target_path = self.target_file.resolve( )
            target_path.parent.mkdir( parents = True, exist_ok = True )
            return exits.enter_context( target_path.open( 'w' ) )
        target_stream = self.target_stream or TargetStream.Stderr
        match target_stream:
            case TargetStream.Stdout: return __.sys.stdout
            case TargetStream.Stderr: return __.sys.stderr
            case _: return __.sys.stderr

    def decide_rich_markdown( self, stream: __.typx.TextIO ) -> bool:
        ''' Determines whether to use Rich markdown rendering. '''
        return decide_rich_markdown( stream, self.color )


def intercept_errors( ) -> __.cabc.Callable[ 
    [ __.cabc.Callable[ ..., __.cabc.Awaitable[ None ] ] ], 
    __.cabc.Callable[ ..., __.cabc.Awaitable[ None ] ] 
]:
    ''' Decorator for CLI handlers to intercept exceptions.
    
        Catches Omnierror exceptions and renders them appropriately.
        Other exceptions are logged and formatted simply.
    '''
    def decorator( 
        func: __.cabc.Callable[ ..., __.cabc.Awaitable[ None ] ]
    ) -> __.cabc.Callable[ ..., __.cabc.Awaitable[ None ] ]:
        @__.funct.wraps( func )
        async def wrapper( 
            self: __.typx.Any,
            auxdata: _state.Globals,
            display: DisplayOptions,
            *posargs: __.typx.Any,
            **nomargs: __.typx.Any,
        ) -> None:
            stream = await display.provide_stream( auxdata.exits )
            try:
                return await func( 
                    self, auxdata, display, *posargs, **nomargs )
            except _exceptions.Omnierror as exc:
                match display.format:
                    case _interfaces.DisplayFormat.JSON:
                        serialized = dict( exc.render_as_json( ) )
                        error_message = __.json.dumps( serialized, indent = 2 )
                    case _interfaces.DisplayFormat.Markdown:
                        lines = exc.render_as_markdown( )
                        error_message = '\n'.join( lines )
                print( error_message, file = stream )
                raise SystemExit( 1 ) from None
            except Exception as exc:
                _scribe.error( f"{func.__name__} failed: %s", exc )
                match display.format:
                    case _interfaces.DisplayFormat.JSON:
                        error_data = {
                            "type": "unexpected_error",
                            "title": "Unexpected Error",
                            "message": str( exc ),
                            "suggestion": (
                                "Please report this issue if it persists." ),
                        }
                        error_message = __.json.dumps( error_data, indent = 2 )
                    case _interfaces.DisplayFormat.Markdown:
                        error_message = f"❌ Unexpected error: {exc}"
                print( error_message, file = stream )
                raise SystemExit( 1 ) from None

        return wrapper
    return decorator


GroupByArgument: __.typx.TypeAlias = __.typx.Annotated[
    __.typx.Optional[ str ],
    __.tyro.conf.arg( help = __.access_doctab( 'group by argument' ) ),
]
PortArgument: __.typx.TypeAlias = __.typx.Annotated[
    __.typx.Optional[ int ],
    __.tyro.conf.arg( help = __.access_doctab( 'server port argument' ) ),
]
TermArgument: __.typx.TypeAlias = __.typx.Annotated[
    __.tyro.conf.Positional[ str ],
    __.tyro.conf.arg( help = __.access_doctab( 'term argument' ) ),
]
ResultsMax: __.typx.TypeAlias = __.typx.Annotated[
    int,
    __.tyro.conf.arg( help = __.access_doctab( 'results max argument' ) ),
]
LocationArgument: __.typx.TypeAlias = __.typx.Annotated[
    __.tyro.conf.Positional[ str ],
    __.tyro.conf.arg( help = __.access_doctab( 'location argument' ) ),
]
TransportArgument: __.typx.TypeAlias = __.typx.Annotated[
    __.typx.Optional[ str ],
    __.tyro.conf.arg( help = __.access_doctab( 'transport argument' ) ),
]


_search_behaviors_default = _interfaces.SearchBehaviors( )
_filters_default = __.immut.Dictionary[ str, __.typx.Any ]( )

_MARKDOWN_OBJECT_LIMIT = 10
_MARKDOWN_CONTENT_LIMIT = 200


def decide_rich_markdown( 
    stream: __.typx.TextIO, colorize: bool 
) -> bool:
    ''' Determines whether to use Rich markdown rendering. '''
    return (
        colorize
        and stream.isatty( ) 
        and not __.os.environ.get( 'NO_COLOR' )
    )


async def _render_and_print_result(
    result: _results.ResultBase,
    display: DisplayOptions,
    exits: __.ctxl.AsyncExitStack,
    **nomargs: __.typx.Any
) -> None:
    ''' Centralizes result rendering logic with Rich formatting support. '''
    stream = await display.provide_stream( exits )
    match display.format:
        case _interfaces.DisplayFormat.JSON:
            nomargs_filtered = {
                key: value for key, value in nomargs.items()
                if key in [ 'lines_max', 'reveal_internals' ]
            }
            serialized = dict( result.render_as_json( **nomargs_filtered ) )
            output = __.json.dumps( serialized, indent = 2 )
            print( output, file = stream )
        case _interfaces.DisplayFormat.Markdown:
            lines = result.render_as_markdown( **nomargs )
            if display.decide_rich_markdown( stream ):
                from rich.console import Console
                from rich.markdown import Markdown
                console = Console( file = stream, force_terminal = True )
                markdown_obj = Markdown( '\n'.join( lines ) )
                console.print( markdown_obj )
            else:
                output = '\n'.join( lines )
                print( output, file = stream )


class _CliCommand(
    __.immut.DataclassProtocol, __.typx.Protocol,
    decorators = ( __.typx.runtime_checkable, ),
):
    ''' CLI command. '''

    @__.abc.abstractmethod
    def __call__(
        self,
        auxdata: _state.Globals,
        display: DisplayOptions,
    ) -> __.cabc.Awaitable[ None ]:
        ''' Executes command with global state. '''
        raise NotImplementedError


class DetectCommand(
    _CliCommand, decorators = ( __.standard_tyro_class, ),
):
    ''' Detect which processors can handle a documentation source. '''

    location: LocationArgument
    genus: __.typx.Annotated[
        _interfaces.ProcessorGenera,
        __.tyro.conf.arg( help = "Processor genus (inventory or structure)." ),
    ]
    processor_name: __.typx.Annotated[
        __.typx.Optional[ str ],
        __.tyro.conf.arg( help = "Specific processor to use." ),
    ] = None

    @intercept_errors( )
    async def __call__(
        self,
        auxdata: _state.Globals,
        display: DisplayOptions,
    ) -> None:
        processor_name = (
            self.processor_name if self.processor_name is not None
            else __.absent )
        result = await _functions.detect(
            auxdata, self.location, self.genus,
            processor_name = processor_name )
        await _render_and_print_result(
            result, display, auxdata.exits, reveal_internals = False )


class QueryInventoryCommand(
    _CliCommand, decorators = ( __.standard_tyro_class, ),
):
    ''' Explores documentation structure and object inventory.

        Use before content searches to:
        
        - Discover available topics and object types
        - Identify relevant search terms and filters
        - Understand documentation scope and organization
    '''

    location: LocationArgument
    term: TermArgument
    filters: __.typx.Annotated[
        __.cabc.Mapping[ str, __.typx.Any ],
        __.tyro.conf.arg( prefix_name = False ),
    ] = __.dcls.field( default_factory = lambda: dict( _filters_default ) )
    search_behaviors: __.typx.Annotated[
        _interfaces.SearchBehaviors,
        __.tyro.conf.arg( prefix_name = False ),
    ] = __.dcls.field(
        default_factory = lambda: _interfaces.SearchBehaviors( ) )
    results_max: __.typx.Annotated[
        int,
        __.tyro.conf.arg( help = __.access_doctab( 'results max argument' ) ),
    ] = 5
    reveal_internals: __.typx.Annotated[
        bool,
        __.tyro.conf.arg(
            help = (
                "Show internal implementation details (domain, priority, "
                "project, version)." )
        ),
    ] = False
    @intercept_errors( )
    async def __call__(
        self,
        auxdata: _state.Globals,
        display: DisplayOptions,
    ) -> None:
        result = await _functions.query_inventory(
            auxdata,
            self.location,
            self.term,
            search_behaviors = self.search_behaviors,
            filters = self.filters,
            results_max = self.results_max )
        await _render_and_print_result(
            result, display, auxdata.exits,
            reveal_internals = self.reveal_internals )


class QueryContentCommand(
    _CliCommand, decorators = ( __.standard_tyro_class, ),
):
    ''' Searches documentation with flexible preview/extraction modes.

        Workflows:
        
        - Sample: Use --lines-max 5-10 to preview results and identify relevant
          content
        - Extract: Use --content-id from sample results to retrieve full
          content  
        - Direct: Search with higher --lines-max for immediate full results
    '''

    location: LocationArgument
    term: TermArgument
    search_behaviors: __.typx.Annotated[
        _interfaces.SearchBehaviors,
        __.tyro.conf.arg( prefix_name = False ),
    ] = __.dcls.field(
        default_factory = lambda: _interfaces.SearchBehaviors( ) )
    filters: __.typx.Annotated[
        __.cabc.Mapping[ str, __.typx.Any ],
        __.tyro.conf.arg( prefix_name = False ),
    ] = __.dcls.field( default_factory = lambda: dict( _filters_default ) )
    results_max: ResultsMax = 10
    lines_max: __.typx.Annotated[
        int,
        __.tyro.conf.arg(
            help = (
                "Lines per result for preview/sampling. Use 5-10 for "
                "discovery, omit for full content extraction via "
                "content-id." ) ),
    ] = 40
    content_id: __.typx.Annotated[
        __.typx.Optional[ str ],
        __.tyro.conf.arg(
            help = (
                "Extract full content for specific result. Obtain IDs from "
                "previous query-content calls with limited lines-max." ) ),
    ] = None
    reveal_internals: __.typx.Annotated[
        bool,
        __.tyro.conf.arg(
            help = (
                "Show internal implementation details (domain, priority, "
                "project, version)." )
        ),
    ] = False
    @intercept_errors( )
    async def __call__(
        self,
        auxdata: _state.Globals,
        display: DisplayOptions,
    ) -> None:
        content_id_ = (
            __.absent if self.content_id is None else self.content_id )
        result = await _functions.query_content(
            auxdata, self.location, self.term,
            search_behaviors = self.search_behaviors,
            filters = self.filters,
            content_id = content_id_,
            results_max = self.results_max,
            lines_max = self.lines_max )
        await _render_and_print_result(
            result, display, auxdata.exits,
            reveal_internals = self.reveal_internals,
            lines_max = self.lines_max )




class SurveyProcessorsCommand(
    _CliCommand, decorators = ( __.standard_tyro_class, ),
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

    @intercept_errors( )
    async def __call__(
        self,
        auxdata: _state.Globals,
        display: DisplayOptions,
    ) -> None:
        nomargs: __.NominativeArguments = { 'genus': self.genus }
        if self.name is not None: nomargs[ 'name' ] = self.name
        result = await _functions.survey_processors( auxdata, **nomargs )
        await _render_and_print_result(
            result, display, auxdata.exits, reveal_internals = False )



class ServeCommand(
    _CliCommand, decorators = ( __.standard_tyro_class, ),
):
    ''' Starts MCP server. '''

    port: PortArgument = None
    transport: TransportArgument = None
    extra_functions: __.typx.Annotated[
        bool,
        __.tyro.conf.arg(
            help = "Enable extra functions (detect and survey-processors)." ),
    ] = False
    serve_function: __.typx.Callable[
        [ _state.Globals ], __.cabc.Awaitable[ None ]
    ] = _server.serve
    async def __call__(
        self,
        auxdata: _state.Globals,
        display: DisplayOptions,
    ) -> None:
        nomargs: __.NominativeArguments = { }
        if self.port is not None: nomargs[ 'port' ] = self.port
        if self.transport is not None: nomargs[ 'transport' ] = self.transport
        nomargs[ 'extra_functions' ] = self.extra_functions
        await self.serve_function( auxdata, **nomargs )


class Cli( __.immut.DataclassObject, decorators = ( __.simple_tyro_class, ) ):
    ''' MCP server CLI. '''

    display: DisplayOptions = __.dcls.field( 
        default_factory = lambda: DisplayOptions( ) )
    command: __.typx.Union[
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
            __.tyro.conf.subcommand( 'query-content', prefix_name = False ),
        ],
        __.typx.Annotated[
            SurveyProcessorsCommand,
            __.tyro.conf.subcommand(
                'survey-processors', prefix_name = False ),
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
            from . import xtnsmgr
            await xtnsmgr.register_processors( auxdata )
            await self.command(
                auxdata = auxdata,
                display = self.display )

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
        application = auxdata.application,
        configuration = auxdata.configuration,
        directories = auxdata.directories,
        distribution = auxdata.distribution,
        exits = auxdata.exits,
        content_cache = content_cache,
        probe_cache = probe_cache,
        robots_cache = robots_cache )
