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


class ExtractInventoryCommand(
    _interfaces.CliCommand, decorators = ( __.standard_tyro_class, ),
):
    ''' Extracts Sphinx inventory with optional filtering. '''

    source: str
    domain: __.typx.Optional[ str ] = None
    role: __.typx.Optional[ str ] = None
    term: __.typx.Optional[ str ] = None

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
        data = _functions.extract_inventory( self.source, **nomargs )
        print( __.json.dumps( data, indent = 2 ), file = stream )


class SummarizeInventoryCommand(
    _interfaces.CliCommand, decorators = ( __.standard_tyro_class, ),
):
    ''' Provides human-readable summary of Sphinx inventory. '''

    source: str
    domain: __.typx.Optional[ str ] = None
    role: __.typx.Optional[ str ] = None
    term: __.typx.Optional[ str ] = None

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
        result = _functions.summarize_inventory( self.source, **nomargs )
        print( result, file = stream )


class UseCommand(
    _interfaces.CliCommand, decorators = ( __.standard_tyro_class, ),
):
    ''' Use Sphinx MCP server tools. '''

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
    ]

    async def __call__(
        self, auxdata: __.Globals, display: _interfaces.ConsoleDisplay
    ) -> None:
        await self.operation( auxdata = auxdata, display = display )


class ServeCommand(
    _interfaces.CliCommand, decorators = ( __.standard_tyro_class, ),
):
    ''' Starts MCP server. '''

    port: __.typx.Optional[ int ] = None
    ''' TCP port for server. '''
    transport: __.typx.Optional[ str ] = None
    ''' Transport: stdio, sse, or stdio-over-tcp. '''
    develop: bool = False
    ''' Enable development mode with hot reloading. '''

    async def __call__(
        self, auxdata: __.Globals, display: _interfaces.ConsoleDisplay
    ) -> None:
        nomargs: __.NominativeArguments = { }
        if self.port is not None:
            nomargs[ 'port' ] = self.port
        if self.transport is not None:
            nomargs[ 'transport' ] = self.transport
        if self.develop:
            nomargs[ 'develop' ] = self.develop
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
            await self.command( auxdata = auxdata, display = self.display )

    def prepare_invocation_args(
        self,
    ) -> __.cabc.Mapping[ str, __.typx.Any ]:
        ''' Prepares arguments for initial configuration. '''
        args: dict[ str, __.typx.Any ] = dict(
            application = self.application,
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
    application: __.appcore.ApplicationInformation,
    environment: bool,
    exits: __.ctxl.AsyncExitStack,
    logfile: __.typx.Optional[ str ],
) -> __.Globals:
    ''' Configures application based on arguments. '''
    nomargs: __.NominativeArguments = {
        'application': application,
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
