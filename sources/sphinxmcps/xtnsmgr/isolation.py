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


''' Simple import path management for extension packages. '''


import importlib
import types

from . import __


_scribe = __.acquire_scribe( __name__ )
_added_paths: list[ str ] = [ ]


def add_to_import_path( package_path: __.Path ) -> None:
    ''' Add package path to sys.path for importing. '''
    path_str = str( package_path )
    if path_str not in __.sys.path:
        __.sys.path.insert( 0, path_str )
        _added_paths.append( path_str )
        _scribe.debug( f"Added to sys.path: {path_str}" )
    else:
        _scribe.debug( f"Path already in sys.path: {path_str}" )


def remove_from_import_path( package_path: __.Path ) -> None:
    ''' Remove package path from sys.path. '''
    path_str = str( package_path )
    if path_str in __.sys.path:
        __.sys.path.remove( path_str )
        if path_str in _added_paths:
            _added_paths.remove( path_str )
        _scribe.debug( f"Removed from sys.path: {path_str}" )


def cleanup_import_paths( ) -> None:
    ''' Remove all extension-added paths from sys.path. '''
    # Copy list to avoid modification during iteration
    for path_str in _added_paths[ : ]:
        if path_str in __.sys.path:
            __.sys.path.remove( path_str )
        _added_paths.remove( path_str )
        _scribe.debug( f"Cleaned up sys.path: {path_str}" )


def import_processor_module( module_name: str ) -> types.ModuleType:
    ''' Import a processor module by name.
    
        Uses standard Python import machinery. For builtin processors,
        pass f"{__.package_name}.processors.{name}". For external processors,
        pass the module name directly.
    '''
    try:
        _scribe.debug( f"Importing processor module: {module_name}" )
        module = importlib.import_module( module_name )
    except ImportError as exc:
        _scribe.error( f"Failed to import {module_name}: {exc}" )
        raise
    else:
        _scribe.info( f"Successfully imported: {module_name}" )
        return module


def reload_processor_module( module_name: str ) -> types.ModuleType:
    ''' Reload a processor module if it's already imported. '''
    if module_name in __.sys.modules:
        _scribe.debug( f"Reloading processor module: {module_name}" )
        module = __.sys.modules[ module_name ]
        return importlib.reload( module )
    _scribe.debug( f"Module not yet imported, importing: {module_name}" )
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
