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


''' Processor loading and registration management. '''


from . import __
from . import cachemgr as _cachemgr
from . import configuration as _configuration
from . import importation as _importation


_scribe = __.acquire_scribe( __name__ )


async def register_processors( auxdata: __.Globals ):
    ''' Registers processors based on configuration. '''
    try: extensions = _configuration.extract_extensions( auxdata )
    except ( KeyError, ValueError, TypeError ) as exc:
        _scribe.error( f"Configuration loading failed: {exc}." )
        _scribe.warning( "No processors loaded due to configuration errors." )
        return
    active_extensions = _configuration.select_active_extensions( extensions )
    if not active_extensions:
        _scribe.warning( "No enabled extensions found in configuration." )
        return
    intrinsic_extensions = (
        _configuration.select_intrinsic_extensions( active_extensions ) )
    external_extensions = tuple(
        ext for ext in active_extensions
        if ext.get( 'package' ) and ext not in intrinsic_extensions )
    await _ensure_external_packages( external_extensions )
    if not intrinsic_extensions and not external_extensions:
        _scribe.warning( "No processors could be loaded." )
        return
    for extension in active_extensions:
        _register_extension( extension )


async def _ensure_external_packages(
    extensions: __.cabc.Sequence[ _configuration.ExtensionConfig ]
) -> None:
    ''' Ensures external packages are installed and importable in parallel. '''
    if not extensions: return
    specifications = [ ext[ 'package' ] for ext in extensions ]
    count = len( specifications )
    _scribe.info( f"Ensuring {count} external packages available." )
    tasks = [ _cachemgr.ensure_package( spec ) for spec in specifications ]
    try:
        await __.asyncf.gather_async(
            *tasks, error_message = "Failed to install external packages." )
    except __.excg.ExceptionGroup as exc_group:
        for exc in exc_group.exceptions:
            _scribe.error( f"Package installation failed: {exc}." )
        raise
    else:
        _scribe.info( "Successfully ensured all external packages." )


def _register_extension(
    extension: _configuration.ExtensionConfig,
) -> None:
    ''' Registers extension from configuration. '''
    name = extension[ 'name' ]
    arguments = _configuration.extract_extension_arguments( extension )
    if 'package' not in extension:
        module_name = f"{__.package_name}.processors.{name}"
    else: module_name = name
    try: module = _importation.import_processor_module( module_name )
    except ( ImportError, ModuleNotFoundError ) as exc:
        _scribe.error( f"Failed to import processor {name}: {exc}" )
        return
    try: module.register( arguments )
    except Exception as exc:
        _scribe.error( f"Failed to register processor {name}: {exc}" )
        return
    _scribe.info( f"Registered extension: {name}." )
