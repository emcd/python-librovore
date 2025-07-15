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

from .fixtures import run_cli_command, get_test_inventory_path






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
async def test_110_cli_extract_inventory_with_domain_filter( ):
    ''' CLI extract-inventory applies domain filtering. '''
    inventory_path = get_test_inventory_path( 'sphinxmcps' )
    result = await run_cli_command( [
        'use', 'extract-inventory', '--source', inventory_path,
        '--domain', 'py'
    ] )
    assert result.returncode == 0
    assert 'domain' in result.stdout or 'domain' in result.stderr
    assert 'py' in result.stdout or 'py' in result.stderr


@pytest.mark.slow
@pytest.mark.asyncio
async def test_120_cli_extract_inventory_with_role_filter( ):
    ''' CLI extract-inventory applies role filtering. '''
    inventory_path = get_test_inventory_path( 'sphinxmcps' )
    result = await run_cli_command( [
        'use', 'extract-inventory', '--source', inventory_path,
        '--role', 'module'
    ] )
    assert result.returncode == 0
    assert 'role' in result.stdout or 'role' in result.stderr
    assert 'module' in result.stdout or 'module' in result.stderr


@pytest.mark.slow
@pytest.mark.asyncio
async def test_130_cli_extract_inventory_with_term_filter( ):
    ''' CLI extract-inventory applies term filtering. '''
    inventory_path = get_test_inventory_path( 'sphinxmcps' )
    result = await run_cli_command( [
        'use', 'extract-inventory', '--source', inventory_path,
        '--term', 'test'
    ] )
    assert result.returncode == 0
    assert 'term' in result.stdout or 'term' in result.stderr
    assert 'test' in result.stdout or 'test' in result.stderr


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
async def test_210_cli_summarize_inventory_with_filters( ):
    ''' CLI summarize-inventory includes filter information. '''
    inventory_path = get_test_inventory_path( 'sphinxmcps' )
    result = await run_cli_command( [
        'use', 'summarize-inventory', '--source', inventory_path,
        '--domain', 'py'
    ] )
    assert result.returncode == 0
    assert (
        'Sphinx Inventory' in result.stdout or
        'Sphinx Inventory' in result.stderr
    )
    assert 'py' in result.stdout or 'py' in result.stderr


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
async def test_410_cli_main_version( ):
    ''' CLI main command shows version information via application.version. '''
    result = await run_cli_command( [ '--help' ] )
    assert result.returncode == 0
    # Help should show version-related option
    assert (
        'application.version' in result.stdout.lower( ) or
        'version' in result.stdout.lower( )
    )


@pytest.mark.slow
@pytest.mark.asyncio
async def test_420_cli_invalid_command( ):
    ''' CLI fails gracefully with invalid command. '''
    result = await run_cli_command( [ 'invalid-command' ] )
    assert result.returncode != 0
    assert (
        'error' in result.stderr.lower( ) or
        'invalid' in result.stderr.lower( )
    )
