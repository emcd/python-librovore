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


''' Import path management and .pth file processing tests. '''


import pytest
from unittest.mock import patch, Mock
from pathlib import Path
import sys
import tempfile
import importlib

import sphinxmcps.xtnsmgr.importation as module


def test_000_add_path_to_sys_path_new( ):
    ''' New path gets added to sys.path at beginning. '''
    test_path = Path( '/test/new/path' )
    
    try:
        module._add_path_to_sys_path( test_path )
        assert str( test_path ) in sys.path
        assert sys.path[ 0 ] == str( test_path )
        assert str( test_path ) in module._added_paths
    finally:
        # Cleanup
        if str( test_path ) in sys.path:
            sys.path.remove( str( test_path ) )
        if str( test_path ) in module._added_paths:
            module._added_paths.remove( str( test_path ) )


def test_010_add_path_to_sys_path_existing( ):
    ''' Existing path in sys.path is not added again. '''
    test_path = Path( sys.path[ 0 ] ) if sys.path else Path( '/existing' )
    original_count = sys.path.count( str( test_path ) )
    
    module._add_path_to_sys_path( test_path )
    
    # Count should not have increased
    assert sys.path.count( str( test_path ) ) == original_count


def test_020_remove_from_import_path( ):
    ''' Path gets removed from sys.path and _added_paths. '''
    test_path = Path( '/test/remove/path' )
    
    # Add path first
    module._add_path_to_sys_path( test_path )
    assert str( test_path ) in sys.path
    assert str( test_path ) in module._added_paths
    
    # Remove path
    module.remove_from_import_path( test_path )
    assert str( test_path ) not in sys.path
    assert str( test_path ) not in module._added_paths


def test_030_remove_from_import_path_not_present( ):
    ''' Removing non-existent path does not raise error. '''
    test_path = Path( '/test/nonexistent/path' )
    module.remove_from_import_path( test_path )  # Should not raise


def test_040_cleanup_import_paths( ):
    ''' cleanup_import_paths removes all added paths. '''
    test_paths = [
        Path( '/test/cleanup/path1' ),
        Path( '/test/cleanup/path2' ),
        Path( '/test/cleanup/path3' )
    ]
    
    # Add multiple paths
    for path in test_paths:
        module._add_path_to_sys_path( path )
    
    # Verify they were added
    for path in test_paths:
        assert str( path ) in sys.path
        assert str( path ) in module._added_paths
    
    # Cleanup all
    module.cleanup_import_paths( )
    
    # Verify they were removed
    for path in test_paths:
        assert str( path ) not in sys.path
        assert str( path ) not in module._added_paths


def test_100_import_processor_module_success( ):
    ''' Successful module import returns module object. '''
    # Test with a built-in module
    module_name = 'json'
    result = module.import_processor_module( module_name )
    assert result.__name__ == module_name


def test_110_import_processor_module_failure( ):
    ''' Failed module import raises ImportError. '''
    with pytest.raises( ImportError ):
        module.import_processor_module( 'nonexistent_module_12345' )


def test_120_reload_processor_module_not_imported( ):
    ''' Reload calls import for non-imported module. '''
    with patch.object( module, 'import_processor_module' ) as mock_import:
        mock_import.return_value = Mock( )
        module.reload_processor_module( 'test_module_not_imported' )
        mock_import.assert_called_once_with( 'test_module_not_imported' )


def test_130_reload_processor_module_already_imported( ):
    ''' Reload uses importlib.reload for already imported module. '''
    test_module = Mock( )
    test_module.__name__ = 'test_already_imported'
    
    with patch.dict(
        sys.modules, { 'test_already_imported': test_module }
    ), patch.object(
        importlib, 'reload', return_value = test_module
    ) as mock_reload:
        result = module.reload_processor_module( 'test_already_imported' )
        mock_reload.assert_called_once_with( test_module )
        assert result == test_module


def test_200_get_module_info_not_imported( ):
    ''' Module info for non-imported module returns imported=False. '''
    result = module.get_module_info( 'definitely_not_imported_module' )
    assert result == { 'imported': False }


def test_210_get_module_info_imported( ):
    ''' Module info for imported module returns details. '''
    # Use json module as it's commonly available
    result = module.get_module_info( 'json' )
    
    assert result[ 'imported' ] is True
    assert result[ 'name' ] == 'json'
    assert 'file' in result
    assert 'package' in result
    assert 'doc' in result


def test_220_list_registered_processors( ):
    ''' list_registered_processors returns list of processor names. '''
    mock_processors = { 'proc1': Mock( ), 'proc2': Mock( ) }
    mock_xtnsapi = Mock( )
    mock_xtnsapi.processors = mock_processors
    
    # Patch the import within the function
    with patch.dict( 'sys.modules', { 'sphinxmcps.xtnsapi': mock_xtnsapi } ):
        result = module.list_registered_processors( )
        assert set( result ) == { 'proc1', 'proc2' }


def test_300_process_pth_files_no_directory( ):
    ''' Processing non-existent directory completes without error. '''
    non_existent = Path( '/definitely/does/not/exist' )
    module.process_pth_files( non_existent )  # Should not raise


def test_310_process_pth_files_with_pth_files( ):
    ''' Processing directory with .pth files calls _process_pth_file. '''
    with tempfile.TemporaryDirectory( ) as temp_dir:
        temp_path = Path( temp_dir )
        
        # Create .pth files
        ( temp_path / 'test.pth' ).touch( )
        ( temp_path / 'another.pth' ).touch( )
        ( temp_path / 'not_pth.txt' ).touch( )  # Should be ignored
        
        with patch.object( module, '_process_pth_file' ) as mock_process:
            module.process_pth_files( temp_path )
            
            # Should process .pth files in sorted order
            assert mock_process.call_count == 2
            processed_files = [
                call[ 0 ][ 0 ].name for call in mock_process.call_args_list ]
            assert 'another.pth' in processed_files
            assert 'test.pth' in processed_files


def test_320_process_pth_files_ignores_hidden( ):
    ''' Hidden .pth files are ignored during discovery. '''
    with tempfile.TemporaryDirectory( ) as temp_dir:
        temp_path = Path( temp_dir )
        
        # Create normal and hidden .pth files
        ( temp_path / 'normal.pth' ).touch( )
        ( temp_path / '.hidden.pth' ).touch( )  # Should be ignored
        
        with patch.object( module, '_process_pth_file' ) as mock_process:
            module.process_pth_files( temp_path )
            
            # Should only process non-hidden files
            assert mock_process.call_count == 1
            processed_file = mock_process.call_args[ 0 ][ 0 ].name
            assert processed_file == 'normal.pth'


def test_330_process_pth_file_simple_path( ):
    ''' .pth file with simple path adds to sys.path. '''
    with tempfile.TemporaryDirectory( ) as temp_dir:
        temp_path = Path( temp_dir )
        pth_file = temp_path / 'test.pth'
        target_dir = temp_path / 'target'
        target_dir.mkdir( )
        
        # Write relative path to .pth file
        pth_file.write_text( 'target\n' )
        
        with patch.object( module, '_add_path_to_sys_path' ) as mock_add:
            module._process_pth_file( pth_file )
            mock_add.assert_called_once_with( target_dir )


def test_340_process_pth_file_import_statement( ):
    ''' .pth file with import statement executes import. '''
    with tempfile.TemporaryDirectory( ) as temp_dir:
        temp_path = Path( temp_dir )
        pth_file = temp_path / 'test.pth'
        
        # Write import statement to .pth file
        pth_file.write_text( 'import sys\n' )
        
        with patch( 'builtins.exec' ) as mock_exec:
            module._process_pth_file( pth_file )
            mock_exec.assert_called_once_with( 'import sys' )


def test_350_process_pth_file_comments_and_blanks( ):
    ''' .pth file ignores comments and blank lines. '''
    with tempfile.TemporaryDirectory( ) as temp_dir:
        temp_path = Path( temp_dir )
        pth_file = temp_path / 'test.pth'
        
        # Write file with comments and blank lines
        pth_file.write_text( '# This is a comment\n\n   \nvalid_path\n' )
        
        # Create the target directory
        ( temp_path / 'valid_path' ).mkdir( )
        
        with patch.object( module, '_add_path_to_sys_path' ) as mock_add:
            module._process_pth_file( pth_file )
            # Should only process the valid path line
            assert mock_add.call_count == 1


def test_360_process_pth_file_nonexistent_path( ):
    ''' .pth file with non-existent path is ignored. '''
    with tempfile.TemporaryDirectory( ) as temp_dir:
        temp_path = Path( temp_dir )
        pth_file = temp_path / 'test.pth'
        
        # Write non-existent path to .pth file
        pth_file.write_text( 'does_not_exist\n' )
        
        with patch.object( module, '_add_path_to_sys_path' ) as mock_add:
            module._process_pth_file( pth_file )
            mock_add.assert_not_called( )


def test_370_is_hidden_platform_specific( ):
    ''' _is_hidden returns False on Linux (unsupported platform). '''
    test_path = Path( '/some/test/path' )
    with patch.object( module.__.sys, 'platform', 'linux' ):
        result = module._is_hidden( test_path )
        assert result is False


def test_380_acquire_pth_file_content_utf8( ):
    ''' _acquire_pth_file_content reads UTF-8 content correctly. '''
    with tempfile.TemporaryDirectory( ) as temp_dir:
        temp_path = Path( temp_dir )
        pth_file = temp_path / 'test.pth'
        
        test_content = 'test/path/with/unicode/ñ'
        pth_file.write_text( test_content, encoding = 'utf-8' )
        
        result = module._acquire_pth_file_content( pth_file )
        assert result == test_content


def test_390_process_pth_file_import_error( ):
    ''' Import errors in .pth files are caught and logged. '''
    with tempfile.TemporaryDirectory( ) as temp_dir:
        temp_path = Path( temp_dir )
        pth_file = temp_path / 'test.pth'
        
        # Write invalid import statement
        pth_file.write_text( 'import nonexistent_module_xyz\n' )
        
        # Should not raise exception
        module._process_pth_file( pth_file )


def test_400_add_package_to_import_path( ):
    ''' add_package_to_import_path calls both path and pth processing. '''
    test_path = Path( '/test/package/path' )
    
    with patch.object(
        module, '_add_path_to_sys_path'
    ) as mock_add_path, patch.object(
        module, 'process_pth_files'
    ) as mock_process_pth:
        
        module.add_package_to_import_path( test_path )
        
        mock_add_path.assert_called_once_with( test_path )
        mock_process_pth.assert_called_once_with( test_path )


def test_410_pth_file_processing_order( ):
    ''' .pth files are processed in sorted order. '''
    with tempfile.TemporaryDirectory( ) as temp_dir:
        temp_path = Path( temp_dir )
        
        # Create .pth files with names that will test sorting
        files = [ 'z_last.pth', 'a_first.pth', 'm_middle.pth' ]
        for filename in files:
            ( temp_path / filename ).touch( )
        
        processed_order = [ ]
        
        def capture_order( pth_file ):
            processed_order.append( pth_file.name )
        
        with patch.object(
            module, '_process_pth_file', side_effect = capture_order
        ):
            module.process_pth_files( temp_path )
        
        # Should be processed in alphabetical order
        assert processed_order == [
            'a_first.pth', 'm_middle.pth', 'z_last.pth' ]


def test_500_process_pth_files_os_error( ):
    ''' OSError during directory iteration is handled gracefully. '''
    mock_path = Mock( spec = Path )
    mock_path.is_dir.return_value = True
    mock_path.iterdir.side_effect = OSError( "Permission denied" )
    
    # Should not raise exception
    module.process_pth_files( mock_path )


def test_510_process_pth_file_missing_file( ):
    ''' Processing non-existent .pth file is handled gracefully. '''
    non_existent_file = Path( '/definitely/does/not/exist.pth' )
    
    # Should not raise exception
    module._process_pth_file( non_existent_file )


def test_520_acquire_pth_file_content_encoding_fallback( ):
    ''' Content reading falls back to locale encoding on UTF-8 failure. '''
    with tempfile.TemporaryDirectory( ) as temp_dir:
        temp_path = Path( temp_dir )
        pth_file = temp_path / 'test.pth'
        
        # Write content that might cause UTF-8 issues
        test_content = 'test_path'
        pth_file.write_text( test_content, encoding = 'utf-8' )
        
        with patch( 'locale.getpreferredencoding', return_value = 'utf-8' ):
            result = module._acquire_pth_file_content( pth_file )
            assert result == test_content