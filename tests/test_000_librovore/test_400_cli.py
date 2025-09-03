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


''' CLI command tests using subprocess injection. '''


from io import StringIO
from unittest.mock import AsyncMock, Mock

import pytest

import librovore.cli as module

# from .fixtures import run_cli_command, get_test_inventory_path


class MockDisplayTarget:
    ''' Mock console display for testing CLI commands. '''

    def __init__( self ):
        self.stream = StringIO( )

    async def provide_stream( self ):
        return self.stream


def create_test_auxdata( ):
    ''' Create mock auxdata for testing. '''
    return Mock( )


# @pytest.mark.asyncio
# @pytest.mark.asyncio
# async def test_060_use_command_summarize_delegation( ):
#     ''' UseCommand delegates to SummarizeInventoryCommand correctly. '''
#     display = MockDisplayTarget( )
#     auxdata = create_test_auxdata( )
#     test_inventory_path = get_test_inventory_path( 'librovore' )
#     search_behaviors = module._interfaces.SearchBehaviors( )
#     filters = { 'domain': 'py' }
#     summarize_cmd = module.SummarizeInventoryCommand(
#         location = test_inventory_path,
#         search_behaviors = search_behaviors,
#         filters = filters )
#     await summarize_cmd(
#         auxdata, display, module._interfaces.DisplayFormat.JSON )
#     output = display.stream.getvalue( )
#     assert '"project":' in output
#     assert 'py' in output
# 
# 
@pytest.mark.asyncio
async def test_070_serve_command_unit( ):
    ''' ServeCommand processes arguments correctly. '''
    display = MockDisplayTarget( )
    auxdata = create_test_auxdata( )
    mock_serve = AsyncMock( )
    cmd = module.ServeCommand(
        port = 8080, transport = 'stdio', serve_function = mock_serve
    )
    await cmd( auxdata, display, module._interfaces.DisplayFormat.JSON, True )
    mock_serve.assert_called_once_with(
        auxdata, port = 8080, transport = 'stdio', extra_functions = False )


@pytest.mark.asyncio
async def test_080_serve_command_defaults( ):
    ''' ServeCommand works with default arguments. '''
    display = MockDisplayTarget( )
    auxdata = create_test_auxdata( )
    mock_serve = AsyncMock( )
    cmd = module.ServeCommand( serve_function = mock_serve )
    await cmd( auxdata, display, module._interfaces.DisplayFormat.JSON, True )
    mock_serve.assert_called_once_with( auxdata, extra_functions = False )


@pytest.mark.asyncio
async def test_085_serve_command_extra_functions( ):
    ''' ServeCommand passes extra_functions flag correctly. '''
    display = MockDisplayTarget( )
    auxdata = create_test_auxdata( )
    mock_serve = AsyncMock( )
    cmd = module.ServeCommand(
        extra_functions = True, serve_function = mock_serve )
    await cmd( auxdata, display, module._interfaces.DisplayFormat.JSON, True )
    mock_serve.assert_called_once_with( auxdata, extra_functions = True )


def test_090_cli_prepare_invocation_args( ):
    ''' CLI prepare_invocation_args returns correct arguments. '''
    mock_display = Mock( )
    mock_cmd = Mock( )
    cli_obj = module.Cli(
        display = mock_display,
        command = mock_cmd,
        logfile = '/test/log.txt' )
    args = cli_obj.prepare_invocation_args( )
    assert args[ 'environment' ] is True
    assert args[ 'logfile' ] == '/test/log.txt'


# def test_100_cli_prepare_invocation_args_no_logfile( ):
#     ''' CLI prepare_invocation_args works without logfile. '''
#     mock_display = Mock( )
#     mock_cmd = Mock( )
#     cli_obj = module.Cli(
#         display = mock_display, command = mock_cmd, logfile = None )
#     args = cli_obj.prepare_invocation_args( )
#     assert args[ 'environment' ] is True
#     assert args[ 'logfile' ] is None
# 
# 
# @pytest.mark.slow
# @pytest.mark.asyncio
# async def test_500_cli_explore_local_file( ):
#     ''' CLI explore processes local files. '''
#     inventory_path = get_test_inventory_path( 'librovore' )
#     result = await run_cli_command( [
#         'use', 'query-inventory', '--source', inventory_path,
#         '--query', 'test', '--details', 'Name' ] )
#     assert result.returncode == 0
#     assert 'project' in result.stdout or 'project' in result.stderr
#     assert 'documents' in result.stdout or 'documents' in result.stderr



# @pytest.mark.slow
# @pytest.mark.asyncio
# async def test_700_cli_serve_help( ):
#     ''' CLI serve command shows help information. '''
#     result = await run_cli_command( [ 'serve', '--help' ] )
#     assert result.returncode == 0
#     assert 'serve' in result.stdout.lower( )
#     assert 'transport' in result.stdout.lower( )
#     assert 'port' in result.stdout.lower( )


# @pytest.mark.slow
# @pytest.mark.asyncio
# async def test_710_cli_serve_invalid_transport( ):
#     ''' CLI serve command fails with invalid transport. '''
#     result = await run_cli_command( [ 'serve', '--transport', 'invalid' ] )
#     assert result.returncode != 0


# @pytest.mark.slow
# @pytest.mark.asyncio
# async def test_720_cli_serve_invalid_port( ):
#     ''' CLI serve command fails with invalid port. '''
#     result = await run_cli_command( [ 'serve', '--port', 'invalid' ] )
#     assert result.returncode != 0


# @pytest.mark.slow
# @pytest.mark.asyncio
# async def test_800_cli_main_help( ):
#     ''' CLI main command shows help information. '''
#     result = await run_cli_command( [ '--help' ] )
#     assert result.returncode == 0
#     assert 'librovore' in result.stdout.lower( )
#     assert 'command' in result.stdout.lower( )


# @pytest.mark.slow
# @pytest.mark.asyncio
# async def test_810_cli_invalid_command( ):
#     ''' CLI fails gracefully with invalid command. '''
#     result = await run_cli_command( [ 'invalid-command' ] )
#     assert result.returncode != 0
#     assert (
#             'error' in result.stderr.lower( )
#         or 'invalid' in result.stderr.lower( ) )
