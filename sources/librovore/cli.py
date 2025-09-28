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


import appcore.cli as _appcore_cli

from . import __
from . import cacheproxy as _cacheproxy
from . import exceptions as _exceptions
from . import functions as _functions
from . import interfaces as _interfaces
from . import results as _results
from . import server as _server
from . import state as _state


_scribe = __.acquire_scribe( __name__ )


def intercept_errors( ) -> __.cabc.Callable[
    [ __.cabc.Callable[
        ..., __.typx.Coroutine[ __.typx.Any, __.typx.Any, None ] ] ],
    __.cabc.Callable[
        ..., __.typx.Coroutine[ __.typx.Any, __.typx.Any, None ] ]
]:
    ''' Decorator for CLI handlers to intercept exceptions.

        Catches Omnierror exceptions and renders them appropriately.
        Other exceptions are logged and formatted simply.
    '''
    def decorator(
        function: __.cabc.Callable[
            ..., __.typx.Coroutine[ __.typx.Any, __.typx.Any, None ] ]
    ) -> __.cabc.Callable[
        ..., __.typx.Coroutine[ __.typx.Any, __.typx.Any, None ]
    ]:
        @__.funct.wraps( function )
        async def wrapper(
            self: __.typx.Any,
            auxdata: _state.Globals,
            *posargs: __.typx.Any,
            **nomargs: __.typx.Any,
        ) -> None:
            if not isinstance( # pragma: no cover
                auxdata, _state.Globals
            ): raise _exceptions.ContextInvalidity
            stream = await auxdata.display.provide_stream( auxdata.exits )
            try: return await function( self, auxdata, *posargs, **nomargs )
            except _exceptions.Omnierror as exc:
                match auxdata.display.format:
                    case _interfaces.DisplayFormat.JSON:
                        serialized = dict( exc.render_as_json( ) )
                        error_message = __.json.dumps( serialized, indent = 2 )
                    case _interfaces.DisplayFormat.Markdown:
                        lines = exc.render_as_markdown( )
                        error_message = '\n'.join( lines )
                print( error_message, file = stream )
                raise SystemExit( 1 ) from None
            except Exception as exc:
                _scribe.error( f"{function.__name__} failed: %s", exc )
                match auxdata.display.format:
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

_MARKDOWN_OBJECT_LIMIT = 10
_MARKDOWN_CONTENT_LIMIT = 200


class DetectCommand(
    _appcore_cli.Command, decorators = ( __.standard_tyro_class, )
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
    async def execute( self, auxdata: __.Globals ) -> None:  # pyright: ignore[reportIncompatibleMethodOverride]
        if not isinstance( auxdata, _state.Globals ):  # pragma: no cover
            raise _exceptions.ContextInvalidity
        processor_name = (
            self.processor_name if self.processor_name is not None
            else __.absent )
        result = await _functions.detect(
            auxdata, self.location, self.genus,
            processor_name = processor_name )
        await _render_and_print_result(
            result, auxdata.display, auxdata.exits, reveal_internals = False )


class QueryInventoryCommand(
    _appcore_cli.Command, decorators = ( __.standard_tyro_class, )
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
        __.cabc.Sequence[ str ],
        __.tyro.conf.arg( prefix_name = False ),
    ] = ( )
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
                "project, version)." ) ),
    ] = False

    @intercept_errors( )
    async def execute( self, auxdata: __.Globals ) -> None:  # pyright: ignore[reportIncompatibleMethodOverride]
        if not isinstance( auxdata, _state.Globals ):  # pragma: no cover
            raise _exceptions.ContextInvalidity
        result = await _functions.query_inventory(
            auxdata,
            self.location,
            self.term,
            search_behaviors = self.search_behaviors,
            filters = _filters_to_dictionary( self.filters ),
            results_max = self.results_max )
        await _render_and_print_result(
            result, auxdata.display, auxdata.exits,
            reveal_internals = self.reveal_internals )


class QueryContentCommand(
    _appcore_cli.Command, decorators = ( __.standard_tyro_class, )
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
        __.cabc.Sequence[ str ],
        __.tyro.conf.arg( prefix_name = False ),
    ] = ( )
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
                "project, version)." ) ),
    ] = False
    @intercept_errors( )
    async def execute( self, auxdata: __.Globals ) -> None:  # pyright: ignore[reportIncompatibleMethodOverride]
        if not isinstance( auxdata, _state.Globals ):  # pragma: no cover
            raise _exceptions.ContextInvalidity
        content_id_ = (
            __.absent if self.content_id is None else self.content_id )
        result = await _functions.query_content(
            auxdata, self.location, self.term,
            search_behaviors = self.search_behaviors,
            filters = _filters_to_dictionary( self.filters ),
            content_id = content_id_,
            results_max = self.results_max,
            lines_max = self.lines_max )
        await _render_and_print_result(
            result, auxdata.display, auxdata.exits,
            reveal_internals = self.reveal_internals,
            lines_max = self.lines_max )


class SurveyProcessorsCommand(
    _appcore_cli.Command, decorators = ( __.standard_tyro_class, )
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
    async def execute( self, auxdata: __.Globals ) -> None:  # pyright: ignore[reportIncompatibleMethodOverride]
        if not isinstance( auxdata, _state.Globals ):  # pragma: no cover
            raise _exceptions.ContextInvalidity
        nomargs: __.NominativeArguments = { 'genus': self.genus }
        if self.name is not None: nomargs[ 'name' ] = self.name
        result = await _functions.survey_processors( auxdata, **nomargs )
        await _render_and_print_result(
            result, auxdata.display, auxdata.exits, reveal_internals = False )


class ServeCommand(
    _appcore_cli.Command, decorators = ( __.standard_tyro_class, )
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
    async def execute( self, auxdata: __.Globals ) -> None:
        if not isinstance( auxdata, _state.Globals ):  # pragma: no cover
            raise _exceptions.ContextInvalidity
        nomargs: __.NominativeArguments = { }
        if self.port is not None: nomargs[ 'port' ] = self.port
        if self.transport is not None: nomargs[ 'transport' ] = self.transport
        nomargs[ 'extra_functions' ] = self.extra_functions
        await self.serve_function( auxdata, **nomargs )


class Cli( _appcore_cli.Application ):
    ''' MCP server CLI. '''

    display: _state.DisplayOptions = __.dcls.field(
        default_factory = _state.DisplayOptions )
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

    async def execute( self, auxdata: __.Globals ) -> None:
        ''' Executes command with extension registration. '''
        if not isinstance( auxdata, _state.Globals ):  # pragma: no cover
            raise _exceptions.ContextInvalidity
        from . import xtnsmgr
        await xtnsmgr.register_processors( auxdata )
        await self.command( auxdata )

    async def prepare(
        self, exits: __.ctxl.AsyncExitStack
    ) -> _state.Globals:
        ''' Prepares librovore-specific global state with cache proxies. '''
        auxdata_base = await super( ).prepare( exits )
        content_cache, probe_cache, robots_cache = _cacheproxy.prepare(
            auxdata_base )
        nomargs = {
            field.name: getattr( auxdata_base, field.name )
            for field in __.dcls.fields( auxdata_base )
            if not field.name.startswith( '_' ) }
        return _state.Globals(
            display = self.display,
            content_cache = content_cache,
            probe_cache = probe_cache,
            robots_cache = robots_cache,
            **nomargs )


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


def _filters_to_dictionary(
    filters: __.cabc.Sequence[ str ]
) -> dict[ str, str ]:
    return dict( map( lambda s: s.split( '=' ), filters ) )


async def _render_and_print_result(
    result: _results.ResultBase,
    display: _state.DisplayOptions,
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
            if display.determine_colorization( stream ):
                from rich.console import Console
                from rich.markdown import Markdown
                console = Console( file = stream, force_terminal = True )
                markdown_obj = Markdown( '\n'.join( lines ) )
                console.print( markdown_obj )
            else:
                output = '\n'.join( lines )
                print( output, file = stream )
