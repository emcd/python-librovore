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
import tempfile
import os

from .fixtures import run_cli_command, mock_inventory_bytes


def temp_inventory_file( ):
    ''' Create temporary inventory file for testing. '''
    with tempfile.NamedTemporaryFile( suffix='.inv', delete=False ) as f:
        f.write( mock_inventory_bytes( ) )
        return f.name


@pytest.mark.slow
@pytest.mark.asyncio
async def test_000_cli_hello_command( ):
    ''' CLI hello command returns greeting. '''
    result = await run_cli_command( [ 'use', 'hello', '--name', 'World' ] )
    assert result.returncode == 0
    assert 'Hello, World!' in result.stdout or 'Hello, World!' in result.stderr


@pytest.mark.slow
@pytest.mark.asyncio
async def test_010_cli_hello_custom_name( ):
    ''' CLI hello command with custom name. '''
    result = await run_cli_command( [ 'use', 'hello', '--name', 'Claude' ] )
    assert result.returncode == 0
    assert (
        'Hello, Claude!' in result.stdout or 
        'Hello, Claude!' in result.stderr
    )


@pytest.mark.slow
@pytest.mark.asyncio
async def test_020_cli_hello_default_name( ):
    ''' CLI hello command uses default name. '''
    result = await run_cli_command( [ 'use', 'hello' ] )
    assert result.returncode == 0
    assert 'Hello, World!' in result.stdout or 'Hello, World!' in result.stderr


@pytest.mark.slow
@pytest.mark.asyncio
async def test_100_cli_inventory_local_file( ):
    ''' CLI inventory processes local files. '''
    inventory_path = temp_inventory_file( )
    try:
        result = await run_cli_command( [ 
            'use', 'inventory', '--source', inventory_path, '--format', 'json' 
        ] )
        assert result.returncode == 0
        assert 'project' in result.stdout or 'project' in result.stderr
        assert 'objects' in result.stdout or 'objects' in result.stderr
    finally:
        os.unlink( inventory_path )


@pytest.mark.slow
@pytest.mark.asyncio
async def test_110_cli_inventory_with_domain_filter( ):
    ''' CLI inventory applies domain filtering. '''
    inventory_path = temp_inventory_file( )
    try:
        result = await run_cli_command( [
            'use', 'inventory', '--source', inventory_path, 
            '--domain', 'py', '--format', 'json'
        ] )
        assert result.returncode == 0
        assert 'domain' in result.stdout or 'domain' in result.stderr
        assert 'py' in result.stdout or 'py' in result.stderr
    finally:
        os.unlink( inventory_path )


@pytest.mark.slow
@pytest.mark.asyncio
async def test_120_cli_inventory_with_role_filter( ):
    ''' CLI inventory applies role filtering. '''
    inventory_path = temp_inventory_file( )
    try:
        result = await run_cli_command( [
            'use', 'inventory', '--source', inventory_path, 
            '--role', 'module', '--format', 'json'
        ] )
        assert result.returncode == 0
        assert 'role' in result.stdout or 'role' in result.stderr
        assert 'module' in result.stdout or 'module' in result.stderr
    finally:
        os.unlink( inventory_path )


@pytest.mark.slow
@pytest.mark.asyncio
async def test_130_cli_inventory_with_search_filter( ):
    ''' CLI inventory applies search filtering. '''
    inventory_path = temp_inventory_file( )
    try:
        result = await run_cli_command( [
            'use', 'inventory', '--source', inventory_path, 
            '--search', 'test', '--format', 'json'
        ] )
        assert result.returncode == 0
        assert 'search' in result.stdout or 'search' in result.stderr
        assert 'test' in result.stdout or 'test' in result.stderr
    finally:
        os.unlink( inventory_path )


@pytest.mark.slow
@pytest.mark.asyncio
async def test_140_cli_inventory_nonexistent_file( ):
    ''' CLI inventory fails gracefully for missing files. '''
    result = await run_cli_command( [
        'use', 'inventory', '--source', '/nonexistent/path.inv'
    ] )
    assert result.returncode != 0
    assert (
        'error' in result.stderr.lower( ) or 
        'not found' in result.stderr.lower( )
    )


@pytest.mark.slow
@pytest.mark.asyncio
async def test_200_cli_inventory_summary_local_file( ):
    ''' CLI inventory summary processes local files. '''
    inventory_path = temp_inventory_file( )
    try:
        result = await run_cli_command( [ 
            'use', 'inventory', '--source', inventory_path, 
            '--format', 'summary' 
        ] )
        assert result.returncode == 0
        assert (
            'Sphinx Inventory' in result.stdout or 
            'Sphinx Inventory' in result.stderr
        )
        assert 'objects' in result.stdout or 'objects' in result.stderr
    finally:
        os.unlink( inventory_path )


@pytest.mark.slow
@pytest.mark.asyncio
async def test_210_cli_inventory_summary_with_filters( ):
    ''' CLI inventory summary includes filter information. '''
    inventory_path = temp_inventory_file( )
    try:
        result = await run_cli_command( [
            'use', 'inventory', '--source', inventory_path, 
            '--domain', 'py', '--format', 'summary'
        ] )
        assert result.returncode == 0
        assert (
            'Sphinx Inventory' in result.stdout or 
            'Sphinx Inventory' in result.stderr
        )
        assert 'py' in result.stdout or 'py' in result.stderr
    finally:
        os.unlink( inventory_path )


@pytest.mark.slow
@pytest.mark.asyncio
async def test_220_cli_inventory_summary_nonexistent_file( ):
    ''' CLI inventory summary fails gracefully for missing files. '''
    result = await run_cli_command( [
        'use', 'inventory', '--source', '/nonexistent/path.inv', 
        '--format', 'summary'
    ] )
    assert result.returncode != 0
    assert (
        'error' in result.stderr.lower( ) or 
        'not found' in result.stderr.lower( )
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