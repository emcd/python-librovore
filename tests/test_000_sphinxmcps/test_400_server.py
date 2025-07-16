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


''' Unit tests for server module without MCP protocol dependencies. '''


import pytest
from unittest.mock import Mock, AsyncMock, patch

from . import cache_import_module, PACKAGE_NAME
from .fixtures import get_test_inventory_path


def test_000_extract_inventory_wrapper():
    ''' Server extract_inventory delegates to functions correctly. '''
    server = cache_import_module( f"{PACKAGE_NAME}.server" )
    test_inventory_path = get_test_inventory_path( 'sphinxmcps' )
    
    result = server.extract_inventory(
        source = test_inventory_path,
        domain = 'py',
        role = 'function'
    )
    
    # Verify structure and filtering
    assert isinstance( result, dict )
    assert 'project' in result
    assert 'filters' in result
    assert result[ 'filters' ][ 'domain' ] == 'py'
    assert result[ 'filters' ][ 'role' ] == 'function'


def test_010_extract_inventory_wrapper_no_filters():
    ''' Server extract_inventory works without filters. '''
    server = cache_import_module( f"{PACKAGE_NAME}.server" )
    test_inventory_path = get_test_inventory_path( 'sphinxmcps' )
    
    result = server.extract_inventory( source = test_inventory_path )
    
    # Verify structure without filters (no filters key when no filters applied)
    assert isinstance( result, dict )
    assert 'project' in result
    assert 'domains' in result
    assert 'objects' in result
    assert 'object_count' in result
    # No 'filters' key should be present when no filters applied
    assert 'filters' not in result


def test_020_extract_inventory_wrapper_with_regex():
    ''' Server extract_inventory handles match_mode parameter correctly. '''
    server = cache_import_module( f"{PACKAGE_NAME}.server" )
    test_inventory_path = get_test_inventory_path( 'sphinxmcps' )
    
    result = server.extract_inventory(
        source = test_inventory_path,
        term = 'test.*pattern',
        match_mode = 'regex'
    )
    
    # Verify match_mode is passed through
    assert isinstance( result, dict )
    assert 'filters' in result
    assert result[ 'filters' ][ 'term' ] == 'test.*pattern'
    assert result[ 'filters' ][ 'match_mode' ] == 'regex'


def test_100_summarize_inventory_wrapper():
    ''' Server summarize_inventory delegates to functions correctly. '''
    server = cache_import_module( f"{PACKAGE_NAME}.server" )
    test_inventory_path = get_test_inventory_path( 'sphinxmcps' )
    
    result = server.summarize_inventory(
        source = test_inventory_path,
        domain = 'py'
    )
    
    # Verify result is a string summary
    assert isinstance( result, str )
    assert 'Sphinx Inventory' in result
    assert 'py' in result


def test_110_summarize_inventory_wrapper_no_filters():
    ''' Server summarize_inventory works without filters. '''
    server = cache_import_module( f"{PACKAGE_NAME}.server" )
    test_inventory_path = get_test_inventory_path( 'sphinxmcps' )
    
    result = server.summarize_inventory( source = test_inventory_path )
    
    # Verify result is a string summary
    assert isinstance( result, str )
    assert 'Sphinx Inventory' in result


def test_120_summarize_inventory_wrapper_with_regex():
    ''' Server summarize_inventory handles match_mode parameter correctly. '''
    server = cache_import_module( f"{PACKAGE_NAME}.server" )
    test_inventory_path = get_test_inventory_path( 'sphinxmcps' )
    
    result = server.summarize_inventory(
        source = test_inventory_path,
        term = 'test.*pattern',
        match_mode = 'regex'
    )
    
    # Verify result is a string summary
    assert isinstance( result, str )
    assert 'Sphinx Inventory' in result


def test_130_extract_inventory_wrapper_with_fuzzy():
    ''' Server extract_inventory handles fuzzy matching correctly. '''
    server = cache_import_module( f"{PACKAGE_NAME}.server" )
    test_inventory_path = get_test_inventory_path( 'sphobjinv' )
    
    result = server.extract_inventory(
        source = test_inventory_path,
        term = 'DataObj',
        match_mode = 'fuzzy',
        fuzzy_threshold = 60
    )
    
    # Verify fuzzy matching is passed through
    assert isinstance( result, dict )
    assert 'filters' in result
    assert result[ 'filters' ][ 'term' ] == 'DataObj'
    assert result[ 'filters' ][ 'match_mode' ] == 'fuzzy'
    assert result[ 'filters' ][ 'fuzzy_threshold' ] == 60
    assert result[ 'object_count' ] > 0


@pytest.mark.asyncio
async def test_200_serve_transport_validation():
    ''' Serve function validates transport parameter correctly. '''
    server = cache_import_module( f"{PACKAGE_NAME}.server" )
    
    # Create mock auxdata
    mock_auxdata = Mock()
    
    # Test invalid transport raises ValueError (no message in actual code)
    with pytest.raises( ValueError ):
        await server.serve( mock_auxdata, transport = 'invalid' )


@pytest.mark.asyncio
async def test_210_serve_stdio_transport():
    ''' Serve function accepts stdio transport without error. '''
    server = cache_import_module( f"{PACKAGE_NAME}.server" )
    
    # Create mock auxdata
    mock_auxdata = Mock()
    
    # Mock the FastMCP run_stdio_async method to avoid actual server startup
    with patch( 'mcp.server.fastmcp.FastMCP.run_stdio_async' ) as mock_run:
        mock_run.return_value = AsyncMock()
        
        # Should not raise ValueError for valid transport
        try:
            await server.serve( mock_auxdata, transport = 'stdio' )
        except ValueError:
            # Should not get ValueError for valid transport
            pytest.fail( "ValueError raised for valid transport 'stdio'" )


@pytest.mark.asyncio
async def test_220_serve_sse_transport():
    ''' Serve function accepts sse transport without error. '''
    server = cache_import_module( f"{PACKAGE_NAME}.server" )
    
    # Create mock auxdata
    mock_auxdata = Mock()
    
    # Mock the FastMCP run_sse_async method to avoid actual server startup
    with patch( 'mcp.server.fastmcp.FastMCP.run_sse_async' ) as mock_run:
        mock_run.return_value = AsyncMock()
        
        # Should not raise ValueError for valid transport
        try:
            await server.serve( mock_auxdata, transport = 'sse' )
        except ValueError:
            # Should not get ValueError for valid transport
            pytest.fail( "ValueError raised for valid transport 'sse'" )


@pytest.mark.asyncio
async def test_230_serve_default_transport():
    ''' Serve function uses default transport when none specified. '''
    server = cache_import_module( f"{PACKAGE_NAME}.server" )
    
    # Create mock auxdata
    mock_auxdata = Mock()
    
    # Mock the FastMCP run_stdio_async method (default transport)
    with patch( 'mcp.server.fastmcp.FastMCP.run_stdio_async' ) as mock_run:
        mock_run.return_value = AsyncMock()
        
        # Should not raise ValueError when no transport specified
        try:
            await server.serve( mock_auxdata )
        except ValueError:
            # Should not get ValueError for default transport
            pytest.fail( "ValueError raised for default transport" )