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
from pathlib import Path
import sys
import tempfile

import librovore.xtnsmgr.importation as module


def test_000_new_paths_are_added_to_sys_path( ):
    ''' New paths are inserted at the beginning of sys.path. '''
    test_path = Path( '/test/new/path' )
    try:
        module._add_path_to_sys_path( test_path )
        assert str( test_path ) in sys.path
        assert sys.path[ 0 ] == str( test_path )
        assert str( test_path ) in module._added_paths
    finally:
        if str( test_path ) in sys.path:
            sys.path.remove( str( test_path ) )
        if str( test_path ) in module._added_paths:
            module._added_paths.remove( str( test_path ) )


def test_010_existing_paths_are_not_duplicated( ):
    ''' Paths already in sys.path are not added again. '''
    test_path = Path( sys.path[ 0 ] ) if sys.path else Path( '/existing' )
    original_count = sys.path.count( str( test_path ) )
    module._add_path_to_sys_path( test_path )
    assert sys.path.count( str( test_path ) ) == original_count


def test_020_paths_can_be_removed_from_sys_path( ):
    ''' Paths are cleanly removed from sys.path and tracking. '''
    test_path = Path( '/test/remove/path' )
    module._add_path_to_sys_path( test_path )
    assert str( test_path ) in sys.path
    assert str( test_path ) in module._added_paths
    module.remove_from_import_path( test_path )
    assert str( test_path ) not in sys.path
    assert str( test_path ) not in module._added_paths


def test_030_removing_nonexistent_paths_is_safe( ):
    ''' Removing paths that don't exist does not raise errors. '''
    test_path = Path( '/test/nonexistent/path' )
    module.remove_from_import_path( test_path )


def test_040_all_added_paths_can_be_cleaned_up( ):
    ''' Cleanup removes all extension-added paths from sys.path. '''
    test_paths = [
        Path( '/test/cleanup/path1' ),
        Path( '/test/cleanup/path2' ),
        Path( '/test/cleanup/path3' )
    ]
    for path in test_paths:
        module._add_path_to_sys_path( path )
    for path in test_paths:
        assert str( path ) in sys.path
        assert str( path ) in module._added_paths
    module.cleanup_import_paths( )
    for path in test_paths:
        assert str( path ) not in sys.path
        assert str( path ) not in module._added_paths


def test_100_valid_modules_can_be_imported( ):
    ''' Built-in modules can be successfully imported. '''
    module_name = 'json'
    result = module.import_processor_module( module_name )
    assert result.__name__ == module_name


def test_110_invalid_modules_raise_import_error( ):
    ''' Non-existent modules raise ImportError. '''
    with pytest.raises( ImportError ):
        module.import_processor_module( 'nonexistent_module_12345' )


def test_120_unimported_modules_trigger_import( ):
    ''' Reloading unimported modules calls import. '''
    import_called_with = None
    def mock_import( name ):
        nonlocal import_called_with
        import_called_with = name
        return type( 'Module', ( ), { '__name__': name } )( )
    
    module.reload_processor_module(
        'test_module_not_imported', importer = mock_import )
    assert import_called_with == 'test_module_not_imported'

def test_130_imported_modules_are_reloaded( ):
    ''' Already imported modules use importlib.reload. '''
    test_module = type(
        'Module', ( ), { '__name__': 'test_already_imported' }
    )( )
    reload_called_with = None
    def mock_reload( mod ):
        nonlocal reload_called_with
        reload_called_with = mod
        return mod
    try:
        sys.modules[ 'test_already_imported' ] = test_module
        result = module.reload_processor_module(
            'test_already_imported', reloader = mock_reload )
        assert reload_called_with is test_module
        assert result is test_module
    finally:
        if 'test_already_imported' in sys.modules:
            del sys.modules[ 'test_already_imported' ]


def test_200_unimported_modules_show_not_imported( ):
    ''' Module info for unimported modules returns imported=False. '''
    result = module.get_module_info( 'definitely_not_imported_module' )
    assert result == { 'imported': False }


def test_210_imported_modules_show_details( ):
    ''' Module info for imported modules includes metadata. '''
    result = module.get_module_info( 'json' )
    assert result[ 'imported' ] is True
    assert result[ 'name' ] == 'json'
    assert 'file' in result
    assert 'package' in result
    assert 'doc' in result


def test_220_processor_registry_is_accessible( ):
    ''' Registered processors can be listed from the registry. '''
    result = module.list_registered_processors( )
    assert isinstance( result, tuple )


def test_300_nonexistent_directories_are_handled_safely( ):
    ''' Processing non-existent directories does not raise errors. '''
    non_existent = Path( '/definitely/does/not/exist' )
    module.process_pth_files( non_existent )


def test_310_pth_files_are_discovered_and_processed( ):
    ''' .pth files in directories are found and processed correctly. '''
    with tempfile.TemporaryDirectory( ) as temp_dir:
        temp_path = Path( temp_dir )
        ( temp_path / 'test.pth' ).touch( )
        ( temp_path / 'another.pth' ).touch( )
        ( temp_path / 'not_pth.txt' ).touch( )
        processed_files = [ ]
        def mock_process( pth_file ):
            processed_files.append( pth_file.name )
        
        module.process_pth_files( temp_path, processor = mock_process )
        assert len( processed_files ) == 2
        assert 'another.pth' in processed_files
        assert 'test.pth' in processed_files

def test_320_hidden_pth_files_are_ignored( ):
    ''' Hidden .pth files are skipped during discovery. '''
    with tempfile.TemporaryDirectory( ) as temp_dir:
        temp_path = Path( temp_dir )
        ( temp_path / 'normal.pth' ).touch( )
        ( temp_path / '.hidden.pth' ).touch( )
        processed_files = [ ]
        def mock_process( pth_file ):
            processed_files.append( pth_file.name )
        
        module.process_pth_files( temp_path, processor = mock_process )
        assert len( processed_files ) == 1
        assert processed_files[ 0 ] == 'normal.pth'


def test_330_simple_paths_are_added_to_sys_path( ):
    ''' .pth files with directory paths update sys.path. '''
    with tempfile.TemporaryDirectory( ) as temp_dir:
        temp_path = Path( temp_dir )
        pth_file = temp_path / 'test.pth'
        target_dir = temp_path / 'target'
        target_dir.mkdir( )
        pth_file.write_text( 'target\n' )
        added_paths = [ ]
        def mock_add( path ):
            added_paths.append( path )
        
        module._process_pth_file(
            pth_file,
            line_processor = lambda pth_file, content: 
                module._process_pth_file_lines(
                    pth_file, content, path_adder = mock_add )
        )
        assert len( added_paths ) == 1
        assert added_paths[ 0 ] == target_dir


def test_340_import_statements_are_executed( ):
    ''' .pth files with import statements execute the imports. '''
    with tempfile.TemporaryDirectory( ) as temp_dir:
        temp_path = Path( temp_dir )
        pth_file = temp_path / 'test.pth'
        pth_file.write_text( 'import sys\n' )
        executed_code = [ ]
        def mock_exec( code ):
            executed_code.append( code )
        
        module._process_pth_file(
            pth_file,
            line_processor = lambda pth_file, content:
                module._process_pth_file_lines(
                    pth_file, content, executor = mock_exec )
        )
        assert len( executed_code ) == 1
        assert executed_code[ 0 ] == 'import sys'


def test_350_comments_and_blanks_are_ignored( ):
    ''' .pth files skip comment and blank lines. '''
    with tempfile.TemporaryDirectory( ) as temp_dir:
        temp_path = Path( temp_dir )
        pth_file = temp_path / 'test.pth'
        pth_file.write_text( '# This is a comment\n\n   \nvalid_path\n' )
        ( temp_path / 'valid_path' ).mkdir( )
        added_paths = [ ]
        def mock_add( path ):
            added_paths.append( path )
        
        module._process_pth_file(
            pth_file,
            line_processor = lambda pth_file, content:
                module._process_pth_file_lines(
                    pth_file, content, path_adder = mock_add )
        )
        assert len( added_paths ) == 1


def test_360_nonexistent_paths_are_ignored( ):
    ''' .pth files with non-existent paths are skipped safely. '''
    with tempfile.TemporaryDirectory( ) as temp_dir:
        temp_path = Path( temp_dir )
        pth_file = temp_path / 'test.pth'
        pth_file.write_text( 'does_not_exist\n' )
        added_paths = [ ]
        def mock_add( path ):
            added_paths.append( path )
        
        module._process_pth_file(
            pth_file,
            line_processor = lambda pth_file, content:
                module._process_pth_file_lines(
                    pth_file, content, path_adder = mock_add )
        )
        assert len( added_paths ) == 0


def test_370_hidden_detection_returns_false_on_linux( ):
    ''' Hidden file detection returns False on unsupported platforms. '''
    test_path = Path( '/some/test/path' )
    result = module._is_hidden( test_path, platform = 'linux' )
    assert result is False


def test_380_utf8_content_is_read_correctly( ):
    ''' .pth files with UTF-8 content are read properly. '''
    with tempfile.TemporaryDirectory( ) as temp_dir:
        temp_path = Path( temp_dir )
        pth_file = temp_path / 'test.pth'
        test_content = 'test/path/with/unicode/ñ'
        pth_file.write_text( test_content, encoding = 'utf-8' )
        result = module._acquire_pth_file_content( pth_file )
        assert result == test_content


def test_390_import_errors_are_handled_gracefully( ):
    ''' Import errors in .pth files do not crash processing. '''
    with tempfile.TemporaryDirectory( ) as temp_dir:
        temp_path = Path( temp_dir )
        pth_file = temp_path / 'test.pth'
        pth_file.write_text( 'import nonexistent_module_xyz\n' )
        module._process_pth_file( pth_file )


def test_400_package_addition_includes_both_operations( ):
    ''' Adding packages handles both sys.path and .pth files. '''
    test_path = Path( '/test/package/path' )
    add_called_with = None
    process_called_with = None
    def mock_add( path ):
        nonlocal add_called_with
        add_called_with = path
    def mock_process( path ):
        nonlocal process_called_with
        process_called_with = path
    
    module.add_package_to_import_path(
        test_path, path_adder = mock_add, pth_processor = mock_process )
    assert add_called_with == test_path
    assert process_called_with == test_path


def test_410_pth_files_are_processed_in_sorted_order( ):
    ''' .pth files are processed alphabetically. '''
    with tempfile.TemporaryDirectory( ) as temp_dir:
        temp_path = Path( temp_dir )
        files = [ 'z_last.pth', 'a_first.pth', 'm_middle.pth' ]
        for filename in files:
            ( temp_path / filename ).touch( )
        processed_order = [ ]
        def capture_order( pth_file ):
            processed_order.append( pth_file.name )
        
        module.process_pth_files( temp_path, processor = capture_order )
        assert processed_order == [
            'a_first.pth', 'm_middle.pth', 'z_last.pth' ]


def test_500_os_errors_during_iteration_are_handled( ):
    ''' OS errors during directory iteration are handled gracefully. '''
    mock_path = type( 'Path', ( ), {
        'is_dir': lambda self: True,
        'iterdir': lambda self: (
            _ for _ in ( )
        ).throw( OSError( "Permission denied" ) )
    } )( )
    module.process_pth_files( mock_path )


def test_510_missing_pth_files_are_handled_safely( ):
    ''' Processing non-existent .pth files does not raise errors. '''
    non_existent_file = Path( '/definitely/does/not/exist.pth' )
    module._process_pth_file( non_existent_file )


def test_520_encoding_fallback_works( ):
    ''' Content reading falls back to locale encoding gracefully. '''
    with tempfile.TemporaryDirectory( ) as temp_dir:
        temp_path = Path( temp_dir )
        pth_file = temp_path / 'test.pth'
        test_content = 'test_path'
        pth_file.write_text( test_content, encoding = 'utf-8' )
        
        result = module._acquire_pth_file_content(
            pth_file, encoding_provider = lambda: 'utf-8' )
        assert result == test_content