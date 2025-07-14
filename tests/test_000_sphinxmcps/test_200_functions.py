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


''' Core business logic functions tests using dependency injection. '''


import pytest
from pyfakefs.fake_filesystem_unittest import Patcher

from . import PACKAGE_NAME, cache_import_module
from .fixtures import mock_inventory_bytes


def test_000_hello_world( ):
    ''' Hello function returns greeting with World. '''
    functions_module = cache_import_module( f"{PACKAGE_NAME}.functions" )
    result = functions_module.hello( "World" )
    assert result == "Hello, World!"


def test_010_hello_custom_name( ):
    ''' Hello function returns greeting with custom name. '''
    functions_module = cache_import_module( f"{PACKAGE_NAME}.functions" )
    result = functions_module.hello( "Claude" )
    assert result == "Hello, Claude!"


def test_020_hello_empty_name( ):
    ''' Hello function handles empty name gracefully. '''
    functions_module = cache_import_module( f"{PACKAGE_NAME}.functions" )
    result = functions_module.hello( "" )
    assert result == "Hello, !"


def test_030_hello_whitespace_name( ):
    ''' Hello function preserves whitespace in names. '''
    functions_module = cache_import_module( f"{PACKAGE_NAME}.functions" )
    result = functions_module.hello( "  Test  " )
    assert result == "Hello,   Test  !"


def test_100_extract_inventory_local_file( ):
    ''' Extract inventory processes local inventory files. '''
    functions_module = cache_import_module( f"{PACKAGE_NAME}.functions" )
    
    with Patcher( ) as patcher:
        fs = patcher.fs
        inventory_path = '/fake/objects.inv'
        fs.create_file( inventory_path, contents = mock_inventory_bytes( ) )
        
        result = functions_module.extract_inventory( inventory_path )
        assert 'project' in result
        assert 'objects' in result


def test_110_extract_inventory_with_domain_filter( ):
    ''' Extract inventory applies domain filtering correctly. '''
    functions_module = cache_import_module( f"{PACKAGE_NAME}.functions" )
    
    with Patcher( ) as patcher:
        fs = patcher.fs
        inventory_path = '/fake/objects.inv'
        fs.create_file( inventory_path, contents = mock_inventory_bytes( ) )
        
        result = functions_module.extract_inventory(
            inventory_path, domain = 'py'
        )
        assert 'filters' in result
        assert result[ 'filters' ][ 'domain' ] == 'py'


def test_120_extract_inventory_with_role_filter( ):
    ''' Extract inventory applies role filtering correctly. '''
    functions_module = cache_import_module( f"{PACKAGE_NAME}.functions" )
    
    with Patcher( ) as patcher:
        fs = patcher.fs
        inventory_path = '/fake/objects.inv'
        fs.create_file( inventory_path, contents = mock_inventory_bytes( ) )
        
        result = functions_module.extract_inventory(
            inventory_path, role = 'module'
        )
        assert 'filters' in result
        assert result[ 'filters' ][ 'role' ] == 'module'


def test_130_extract_inventory_with_search_filter( ):
    ''' Extract inventory applies search filtering correctly. '''
    functions_module = cache_import_module( f"{PACKAGE_NAME}.functions" )
    
    with Patcher( ) as patcher:
        fs = patcher.fs
        inventory_path = '/fake/objects.inv'
        fs.create_file( inventory_path, contents = mock_inventory_bytes( ) )
        
        result = functions_module.extract_inventory(
            inventory_path, search = 'test'
        )
        assert 'filters' in result
        assert result[ 'filters' ][ 'search' ] == 'test'


def test_140_extract_inventory_with_all_filters( ):
    ''' Extract inventory applies multiple filters correctly. '''
    functions_module = cache_import_module( f"{PACKAGE_NAME}.functions" )
    
    with Patcher( ) as patcher:
        fs = patcher.fs
        inventory_path = '/fake/objects.inv'
        fs.create_file( inventory_path, contents = mock_inventory_bytes( ) )
        
        result = functions_module.extract_inventory( 
            inventory_path, 
            domain = 'py', 
            role = 'module', 
            search = 'test' 
        )
        assert 'filters' in result
        filters = result[ 'filters' ]
        assert filters[ 'domain' ] == 'py'
        assert filters[ 'role' ] == 'module'
        assert filters[ 'search' ] == 'test'


def test_150_extract_inventory_nonexistent_file( ):
    ''' Extract inventory raises appropriate exception for missing files. '''
    functions_module = cache_import_module( f"{PACKAGE_NAME}.functions" )
    exceptions_module = cache_import_module( f"{PACKAGE_NAME}.exceptions" )
    
    with pytest.raises( exceptions_module.InventoryAbsence ):
        functions_module.extract_inventory( "/nonexistent/path.inv" )


def test_160_extract_inventory_auto_append_objects_inv( ):
    ''' Extract inventory auto-appends objects.inv to URLs/paths. '''
    functions_module = cache_import_module( f"{PACKAGE_NAME}.functions" )
    
    with Patcher( ) as patcher:
        fs = patcher.fs
        # Create directory structure
        fs.create_dir( '/fake/docs' )
        fs.create_file(
            '/fake/docs/objects.inv', 
            contents = mock_inventory_bytes( )
        )
        
        # Test without objects.inv suffix
        result = functions_module.extract_inventory( '/fake/docs' )
        assert 'project' in result
        assert 'objects' in result


def test_200_summarize_inventory_basic( ):
    ''' Summarize inventory provides human-readable summary. '''
    functions_module = cache_import_module( f"{PACKAGE_NAME}.functions" )
    
    with Patcher( ) as patcher:
        fs = patcher.fs
        inventory_path = '/fake/objects.inv'
        fs.create_file( inventory_path, contents = mock_inventory_bytes( ) )
        
        result = functions_module.summarize_inventory( inventory_path )
        assert 'objects' in result


def test_210_summarize_inventory_with_filters( ):
    ''' Summarize inventory includes filter information when provided. '''
    functions_module = cache_import_module( f"{PACKAGE_NAME}.functions" )
    
    with Patcher( ) as patcher:
        fs = patcher.fs
        inventory_path = '/fake/objects.inv'
        fs.create_file( inventory_path, contents = mock_inventory_bytes( ) )
        
        # First extract with filters to get filtered data
        filtered_data = functions_module.extract_inventory( 
            inventory_path, domain = 'py' 
        )
        
        # Then summarize the source with filter info
        result = functions_module.summarize_inventory( 
            inventory_path, filters = filtered_data.get( 'filters' ) 
        )
        
        assert 'objects' in result
        # Should mention filtering was applied
        assert 'filter' in result.lower( ) or 'domain' in result.lower( )


def test_220_summarize_inventory_nonexistent_file( ):
    ''' Summarize inventory raises appropriate exception for missing files. '''
    functions_module = cache_import_module( f"{PACKAGE_NAME}.functions" )
    exceptions_module = cache_import_module( f"{PACKAGE_NAME}.exceptions" )
    
    with pytest.raises( exceptions_module.InventoryAbsence ):
        functions_module.summarize_inventory( "/nonexistent/path.inv" )


def test_300_url_detection_http( ):
    ''' URL detection correctly identifies HTTP URLs. '''
    functions_module = cache_import_module( f"{PACKAGE_NAME}.functions" )
    
    # Access the _is_url helper function if it exists
    if hasattr( functions_module, '_is_url' ):
        assert functions_module._is_url( "http://example.com" )
        assert functions_module._is_url( "https://example.com" )


def test_310_url_detection_file_paths( ):
    ''' URL detection correctly identifies file paths as non-URLs. '''
    functions_module = cache_import_module( f"{PACKAGE_NAME}.functions" )
    
    # Access the _is_url helper function if it exists
    if hasattr( functions_module, '_is_url' ):
        assert not functions_module._is_url( "/path/to/file.inv" )
        assert not functions_module._is_url( "relative/path.inv" )


def test_320_url_detection_edge_cases( ):
    ''' URL detection handles edge cases correctly. '''
    functions_module = cache_import_module( f"{PACKAGE_NAME}.functions" )
    
    # Access the _is_url helper function if it exists
    if hasattr( functions_module, '_is_url' ):
        assert not functions_module._is_url( "" )
        assert functions_module._is_url( "file://" )  # Local file URL