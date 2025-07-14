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


class HelloCommand(
    _interfaces.CliCommand, decorators = ( __.standard_tyro_class, ),
):
    ''' Says hello with the given name. '''

    name: str = 'World'

    async def __call__(
        self, auxdata: __.Globals, display: _interfaces.ConsoleDisplay
    ) -> None:
        result = _functions.hello( self.name )
        stream = await display.provide_stream( )
        print( result, file = stream )


class InventoryCommand(
    _interfaces.CliCommand, decorators = ( __.standard_tyro_class, ),
):
    ''' Extracts and displays Sphinx inventory information. '''

    source: str
    format: str = 'summary'
    domain: __.typx.Optional[ str ] = None
    role: __.typx.Optional[ str ] = None
    search: __.typx.Optional[ str ] = None

    async def __call__(
        self, auxdata: __.Globals, display: _interfaces.ConsoleDisplay
    ) -> None:
        stream = await display.provide_stream( )
        # Extract inventory with optional filtering
        data = _functions.extract_inventory(
            self.source,
            domain = self.domain,
            role = self.role,
            search = self.search,
        )
        match self.format:
            case 'summary':
                result = _functions.summarize_inventory( 
                    data[ 'source' ], filters = data.get( 'filters' ) )
                print( result, file = stream )
            case 'json':
                print( __.json.dumps( data, indent = 2 ), file = stream )
            case _:
                # TODO? Use logger.
                print( f"Unknown format: {self.format}", file = __.sys.stderr )
                return


class ServeCommand(
    _interfaces.CliCommand, decorators = ( __.standard_tyro_class, ),
):
    ''' Starts MCP server. '''

    port: __.typx.Optional[ int ] = None
    socket: __.typx.Optional[ str ] = None
    transport: __.typx.Optional[ str ] = None

    async def __call__(
        self, auxdata: __.Globals, display: _interfaces.ConsoleDisplay
    ) -> None:
        nomargs: __.NominativeArguments = { }
        if self.port is not None:
            nomargs[ 'port' ] = self.port
        if self.transport is not None:
            nomargs[ 'transport' ] = self.transport
        await _server.serve( auxdata, **nomargs )


class Cli(
    __.immut.DataclassObject,
    decorators = ( __.simple_tyro_class, ),
):
    ''' Sphinx MCP server CLI. '''

    application: __.appcore.ApplicationInformation
    display: _interfaces.ConsoleDisplay
    command: __.typx.Union[
        __.typx.Annotated[
            HelloCommand,
            __.tyro.conf.subcommand( 'hello', prefix_name = False ),
        ],
        __.typx.Annotated[
            InventoryCommand,
            __.tyro.conf.subcommand( 'inventory', prefix_name = False ),
        ],
        __.typx.Annotated[
            ServeCommand,
            __.tyro.conf.subcommand( 'serve', prefix_name = False ),
        ],
    ]

    async def __call__( self ):
        ''' Invokes command after library preparation. '''
        nomargs = self.prepare_invocation_args( )
        async with __.ctxl.AsyncExitStack( ) as exits:
            auxdata = await _prepare( exits = exits, **nomargs )
            await self.command( auxdata = auxdata, display = self.display )

    def prepare_invocation_args(
        self,
    ) -> __.cabc.Mapping[ str, __.typx.Any ]:
        ''' Prepares arguments for initial configuration. '''
        args: dict[ str, __.typx.Any ] = dict(
            application = self.application,
            environment = True,
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
    application: __.appcore.ApplicationInformation,
    environment: bool,
    exits: __.ctxl.AsyncExitStack,
) -> __.Globals:
    ''' Configures application based on arguments. '''
    return await __.appcore.prepare(
        application = application, environment = environment, exits = exits )
