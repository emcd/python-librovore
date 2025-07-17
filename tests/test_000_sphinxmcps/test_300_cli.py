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


import pytest
from unittest.mock import Mock, AsyncMock, patch
from io import StringIO

from . import cache_import_module, PACKAGE_NAME
from .fixtures import run_cli_command, get_test_inventory_path


class MockConsoleDisplay:
    ''' Mock console display for testing CLI commands. '''

    def __init__( self ):
        self.stream = StringIO()

    async def provide_stream( self ):
        return self.stream


def create_test_auxdata():
    ''' Create mock auxdata for testing. '''
    return Mock()


@pytest.mark.asyncio
async def test_000_extract_inventory_command_unit():
    ''' ExtractInventoryCommand processes arguments correctly. '''
    cli = cache_import_module( f"{PACKAGE_NAME}.cli" )
    display = MockConsoleDisplay()
    auxdata = create_test_auxdata()
    test_inventory_path = get_test_inventory_path( 'sphinxmcps' )

    cmd = cli.ExtractInventoryCommand(
        source = test_inventory_path,
        domain = 'py'
    )

    await cmd( auxdata, display )

    output = display.stream.getvalue()
    assert 'project' in output
    assert 'domain' in output
    assert 'py' in output


@pytest.mark.asyncio
async def test_010_extract_inventory_command_no_filters():
    ''' ExtractInventoryCommand works without filters. '''
    cli = cache_import_module( f"{PACKAGE_NAME}.cli" )
    display = MockConsoleDisplay()
    auxdata = create_test_auxdata()
    test_inventory_path = get_test_inventory_path( 'sphinxmcps' )

    cmd = cli.ExtractInventoryCommand(
        source = test_inventory_path
    )

    await cmd( auxdata, display )

    output = display.stream.getvalue()
    assert 'project' in output
    assert 'objects' in output


@pytest.mark.asyncio
async def test_020_extract_inventory_command_all_filters():
    ''' ExtractInventoryCommand handles all filter parameters. '''
    cli = cache_import_module( f"{PACKAGE_NAME}.cli" )
    display = MockConsoleDisplay()
    auxdata = create_test_auxdata()
    test_inventory_path = get_test_inventory_path( 'sphinxmcps' )

    cmd = cli.ExtractInventoryCommand(
        source = test_inventory_path,
        domain = 'py',
        role = 'module',
        term = 'test'
    )

    await cmd( auxdata, display )

    output = display.stream.getvalue()
    assert 'project' in output
    # Command should execute without error


@pytest.mark.asyncio
async def test_030_summarize_inventory_command_unit():
    ''' SummarizeInventoryCommand processes arguments correctly. '''
    cli = cache_import_module( f"{PACKAGE_NAME}.cli" )
    display = MockConsoleDisplay()
    auxdata = create_test_auxdata()
    test_inventory_path = get_test_inventory_path( 'sphinxmcps' )

    cmd = cli.SummarizeInventoryCommand(
        source = test_inventory_path,
        domain = 'py'
    )

    await cmd( auxdata, display )

    output = display.stream.getvalue()
    assert 'Sphinx Inventory' in output
    assert 'py' in output


@pytest.mark.asyncio
async def test_040_summarize_inventory_command_no_filters():
    ''' SummarizeInventoryCommand works without filters. '''
    cli = cache_import_module( f"{PACKAGE_NAME}.cli" )
    display = MockConsoleDisplay()
    auxdata = create_test_auxdata()
    test_inventory_path = get_test_inventory_path( 'sphinxmcps' )

    cmd = cli.SummarizeInventoryCommand(
        source = test_inventory_path
    )

    await cmd( auxdata, display )

    output = display.stream.getvalue()
    assert 'Sphinx Inventory' in output


@pytest.mark.asyncio
async def test_050_use_command_extract_delegation():
    ''' UseCommand delegates to ExtractInventoryCommand correctly. '''
    cli = cache_import_module( f"{PACKAGE_NAME}.cli" )
    display = MockConsoleDisplay()
    auxdata = create_test_auxdata()
    test_inventory_path = get_test_inventory_path( 'sphinxmcps' )

    extract_cmd = cli.ExtractInventoryCommand(
        source = test_inventory_path,
        domain = 'py'
    )

    use_cmd = cli.UseCommand( operation = extract_cmd )
    await use_cmd( auxdata, display )

    output = display.stream.getvalue()
    assert 'project' in output
    assert 'py' in output


@pytest.mark.asyncio
async def test_060_use_command_summarize_delegation():
    ''' UseCommand delegates to SummarizeInventoryCommand correctly. '''
    cli = cache_import_module( f"{PACKAGE_NAME}.cli" )
    display = MockConsoleDisplay()
    auxdata = create_test_auxdata()
    test_inventory_path = get_test_inventory_path( 'sphinxmcps' )

    summarize_cmd = cli.SummarizeInventoryCommand(
        source = test_inventory_path,
        domain = 'py'
    )

    use_cmd = cli.UseCommand( operation = summarize_cmd )
    await use_cmd( auxdata, display )

    output = display.stream.getvalue()
    assert 'Sphinx Inventory' in output
    assert 'py' in output


@pytest.mark.asyncio
async def test_070_serve_command_unit():
    ''' ServeCommand processes arguments correctly. '''
    cli = cache_import_module( f"{PACKAGE_NAME}.cli" )
    display = MockConsoleDisplay()
    auxdata = create_test_auxdata()

    # Mock the server.serve function to avoid actual server startup
    with patch( f"{PACKAGE_NAME}.server.serve" ) as mock_serve:
        mock_serve.return_value = AsyncMock()

        cmd = cli.ServeCommand( port = 8080, transport = 'stdio' )
        await cmd( auxdata, display )

        # Verify serve was called with correct arguments
        mock_serve.assert_called_once_with(
            auxdata, port = 8080, transport = 'stdio'
        )


@pytest.mark.asyncio
async def test_080_serve_command_defaults():
    ''' ServeCommand works with default arguments. '''
    cli = cache_import_module( f"{PACKAGE_NAME}.cli" )
    display = MockConsoleDisplay()
    auxdata = create_test_auxdata()

    # Mock the server.serve function to avoid actual server startup
    with patch( f"{PACKAGE_NAME}.server.serve" ) as mock_serve:
        mock_serve.return_value = AsyncMock()

        cmd = cli.ServeCommand()
        await cmd( auxdata, display )

        # Verify serve was called with no additional arguments
        mock_serve.assert_called_once_with( auxdata )


def test_090_cli_prepare_invocation_args():
    ''' CLI prepare_invocation_args returns correct arguments. '''
    cli = cache_import_module( f"{PACKAGE_NAME}.cli" )
    mock_display = Mock()
    mock_cmd = Mock()
    cli_obj = cli.Cli(
        display = mock_display,
        command = mock_cmd,
        logfile = '/test/log.txt'
    )
    args = cli_obj.prepare_invocation_args()
    assert args[ 'environment' ] is True
    assert args[ 'logfile' ] == '/test/log.txt'


def test_100_cli_prepare_invocation_args_no_logfile():
    ''' CLI prepare_invocation_args works without logfile. '''
    cli = cache_import_module( f"{PACKAGE_NAME}.cli" )
    mock_display = Mock()
    mock_cmd = Mock()
    cli_obj = cli.Cli(
        display = mock_display,
        command = mock_cmd,
        logfile = None
    )
    args = cli_obj.prepare_invocation_args()
    assert args[ 'environment' ] is True
    assert args[ 'logfile' ] is None


# Subprocess-based integration tests (existing)




@pytest.mark.slow
@pytest.mark.asyncio
async def test_100_cli_extract_inventory_local_file( ):
    ''' CLI extract-inventory processes local files. '''
    inventory_path = get_test_inventory_path( 'sphinxmcps' )
    result = await run_cli_command( [
        'use', 'extract-inventory', '--source', inventory_path
    ] )
    assert result.returncode == 0
    assert 'project' in result.stdout or 'project' in result.stderr
    assert 'objects' in result.stdout or 'objects' in result.stderr



@pytest.mark.slow
@pytest.mark.asyncio
async def test_140_cli_extract_inventory_nonexistent_file( ):
    ''' CLI extract-inventory fails gracefully for missing files. '''
    result = await run_cli_command( [
        'use', 'extract-inventory', '--source', '/nonexistent/path.inv'
    ] )
    assert result.returncode != 0
    assert (
        'inaccessible' in result.stderr.lower( ) or
        'not found' in result.stderr.lower( ) or
        'no such file' in result.stderr.lower( )
    )


@pytest.mark.slow
@pytest.mark.asyncio
async def test_200_cli_summarize_inventory_local_file( ):
    ''' CLI summarize-inventory processes local files. '''
    inventory_path = get_test_inventory_path( 'sphinxmcps' )
    result = await run_cli_command( [
        'use', 'summarize-inventory', '--source', inventory_path
    ] )
    assert result.returncode == 0
    assert (
        'Sphinx Inventory' in result.stdout or
        'Sphinx Inventory' in result.stderr
    )
    assert 'objects' in result.stdout or 'objects' in result.stderr




@pytest.mark.slow
@pytest.mark.asyncio
async def test_220_cli_summarize_inventory_nonexistent_file( ):
    ''' CLI summarize-inventory fails gracefully for missing files. '''
    result = await run_cli_command( [
        'use', 'summarize-inventory', '--source', '/nonexistent/path.inv'
    ] )
    assert result.returncode != 0
    assert (
        'inaccessible' in result.stderr.lower( ) or
        'not found' in result.stderr.lower( ) or
        'no such file' in result.stderr.lower( )
    )


@pytest.mark.slow
@pytest.mark.asyncio
async def test_300_cli_serve_help( ):
    ''' CLI serve command shows help information. '''
    result = await run_cli_command( [ 'serve', '--help' ] )
    assert result.returncode == 0
    assert 'serve' in result.stdout.lower( )
    assert 'transport' in result.stdout.lower( )
    assert 'port' in result.stdout.lower( )


@pytest.mark.slow
@pytest.mark.asyncio
async def test_310_cli_serve_invalid_transport( ):
    ''' CLI serve command fails with invalid transport. '''
    result = await run_cli_command( [ 'serve', '--transport', 'invalid' ] )
    assert result.returncode != 0
    # Main assertion is non-zero exit code for invalid transport


@pytest.mark.slow
@pytest.mark.asyncio
async def test_320_cli_serve_invalid_port( ):
    ''' CLI serve command fails with invalid port. '''
    result = await run_cli_command( [ 'serve', '--port', 'invalid' ] )
    assert result.returncode != 0
    # Main assertion is non-zero exit code for invalid port


@pytest.mark.slow
@pytest.mark.asyncio
async def test_400_cli_main_help( ):
    ''' CLI main command shows help information. '''
    result = await run_cli_command( [ '--help' ] )
    assert result.returncode == 0
    assert 'sphinxmcps' in result.stdout.lower( )
    assert 'command' in result.stdout.lower( )


@pytest.mark.slow
@pytest.mark.asyncio
async def test_410_cli_invalid_command( ):
    ''' CLI fails gracefully with invalid command. '''
    result = await run_cli_command( [ 'invalid-command' ] )
    assert result.returncode != 0
    assert (
        'error' in result.stderr.lower( ) or
        'invalid' in result.stderr.lower( )
    )
