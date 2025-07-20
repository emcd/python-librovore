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


''' Import path management and .pth file processing for extension packages. '''


import io as _io
import locale as _locale
import stat as _stat
import importlib as _importlib

from . import __


_scribe = __.acquire_scribe( __name__ )
_added_paths: list[ str ] = [ ]


def add_package_to_import_path( package_path: __.Path ) -> None:
    ''' Add package to sys.path and process any .pth files. '''
    _add_path_to_sys_path( package_path )
    process_pth_files( package_path )


def _add_path_to_sys_path( package_path: __.Path ) -> None:
    ''' Add single path to sys.path if not already present. '''
    path_str = str( package_path )
    if path_str not in __.sys.path:
        __.sys.path.insert( 0, path_str )
        _added_paths.append( path_str )
        _scribe.debug( f"Added to sys.path: {path_str}." )
    else:
        _scribe.debug( f"Path already in sys.path: {path_str}." )


def remove_from_import_path( package_path: __.Path ) -> None:
    ''' Remove package path from sys.path. '''
    path_str = str( package_path )
    if path_str in __.sys.path:
        __.sys.path.remove( path_str )
        if path_str in _added_paths:
            _added_paths.remove( path_str )
        _scribe.debug( f"Removed from sys.path: {path_str}." )


def cleanup_import_paths( ) -> None:
    ''' Remove all extension-added paths from sys.path. '''
    # Copy list to avoid modification during iteration
    for path_str in _added_paths[ : ]:
        if path_str in __.sys.path:
            __.sys.path.remove( path_str )
        _added_paths.remove( path_str )
        _scribe.debug( f"Cleaned up sys.path: {path_str}." )


def import_processor_module( module_name: str ) -> __.types.ModuleType:
    ''' Import a processor module by name.
    
        Uses standard Python import machinery. For builtin processors,
        pass f"{__.package_name}.processors.{name}". For external processors,
        pass the module name directly.
    '''
    try:
        _scribe.debug( f"Importing processor module: {module_name}." )
        module = _importlib.import_module( module_name )
    except ImportError as exc:
        _scribe.error( f"Failed to import {module_name}: {exc}." )
        raise
    else:
        _scribe.info( f"Successfully imported: {module_name}." )
        return module


def reload_processor_module( module_name: str ) -> __.types.ModuleType:
    ''' Reload a processor module if it's already imported. '''
    if module_name in __.sys.modules:
        _scribe.debug( f"Reloading processor module: {module_name}." )
        module = __.sys.modules[ module_name ]
        return _importlib.reload( module )
    _scribe.debug( f"Module not yet imported, importing: {module_name}." )
    return import_processor_module( module_name )


def list_registered_processors( ) -> list[ str ]:
    ''' List all currently registered processor names from the registry. '''
    from .. import xtnsapi as _xtnsapi
    return list( _xtnsapi.processors.keys( ) )


def get_module_info( module_name: str ) -> dict[ str, __.typx.Any ]:
    ''' Get information about an imported module. '''
    if module_name not in __.sys.modules:
        return { 'imported': False }
    module = __.sys.modules[ module_name ]
    return {
        'imported': True,
        'name': module.__name__,
        'file': getattr( module, '__file__', None ),
        'package': getattr( module, '__package__', None ),
        'version': getattr( module, '__version__', None ),
        'doc': getattr( module, '__doc__', None )
    }


def process_pth_files( package_path: __.Path ) -> None:
    ''' Process .pth files in package directory to update sys.path.
    
        Handles proper encoding, hidden file detection, and security.
    '''
    if not package_path.is_dir( ): return
    try:
        pth_files = (
            file for file in package_path.iterdir( )
            if '.pth' == file.suffix
            and not file.name.startswith( '.' ) )
    except OSError: return
    for pth_file in sorted( pth_files ):
        _process_pth_file( pth_file )


def _process_pth_file( pth_file: __.Path ) -> None:
    ''' Process single .pth file. '''
    if not pth_file.exists( ) or _is_hidden( pth_file ): return
    try: content = _acquire_pth_file_content( pth_file )
    except OSError: return
    _process_pth_file_lines( pth_file, content )


def _acquire_pth_file_content( pth_file: __.Path ) -> str:
    ''' Read .pth file content with proper encoding handling. '''
    with _io.open_code( str( pth_file ) ) as stream:
        content_bytes = stream.read( )
    # Accept BOM markers in .pth files - same as with source files
    try: return content_bytes.decode( 'utf-8-sig' )
    except UnicodeDecodeError:
        return content_bytes.decode( _locale.getpreferredencoding( ) )


def _is_hidden( path: __.Path ) -> bool:
    ''' Check if path is hidden via system attributes. '''
    try: inode = path.lstat( )
    except OSError: return False
    match __.sys.platform:
        case 'darwin':
            return bool( getattr( inode, 'st_flags', 0 ) & _stat.UF_HIDDEN )
        case 'win32':
            # Windows FILE_ATTRIBUTE_HIDDEN constant (0x2)
            return bool(
                getattr( inode, 'st_file_attributes', 0 )
                & getattr( _stat, 'FILE_ATTRIBUTE_HIDDEN', 0x2 ) )
        case _: return False


def _process_pth_file_lines( pth_file: __.Path, content: str ) -> None:
    ''' Process lines in .pth file content. '''
    for n, line in enumerate( content.splitlines( ), 1 ):
        if line.startswith( '#' ) or '' == line.strip( ): continue
        if line.startswith( ( 'import ', 'import\t' ) ):
            _scribe.debug( f"Executing import from {pth_file.name}: {line}" )
            try: exec( line )  # noqa: S102
            except Exception:
                _scribe.exception( f"Error on line {n} of {pth_file}." )
                break
            continue
        # Add directory path relative to .pth file location
        path_to_add = pth_file.parent / line.rstrip( )
        if path_to_add.exists( ):
            _add_path_to_sys_path( path_to_add )
