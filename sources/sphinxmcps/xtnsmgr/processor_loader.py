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
from . import installation as _installation
from . import isolation as _isolation


_scribe = __.acquire_scribe( __name__ )


async def register_processors( auxdata: __.Globals ):
    ''' Load and register processors based on configuration. '''
    try: extensions = __.load_extensions_config( auxdata )
    except Exception as exc:
        _scribe.error( f"Configuration loading failed: {exc}." )
        _scribe.warning( "No processors loaded due to configuration errors." )
        return
    enabled_extensions = __.get_enabled_extensions( extensions )
    if not enabled_extensions:
        _scribe.warning( "No enabled extensions found in configuration." )
        return
    builtin_extensions = __.get_builtin_extensions( enabled_extensions )
    external_extensions = [
        ext for ext in enabled_extensions
        if ext.get( 'package' ) and ext not in builtin_extensions ]
    installations = (
        await _install_packages( external_extensions ) )
    # All install_results are successful (exceptions raised ExceptionGroup)
    # Map back to extension configs based on successful installations
    successful_external: list[ __.ExtensionConfig ] = (
        external_extensions[ : len( installations ) ]
        if installations else [ ] )
    all_extensions = builtin_extensions + successful_external
    if not all_extensions:
        _scribe.warning( "No processors could be loaded" )
        return
    for ext_config in all_extensions:
        _register_processor( ext_config, builtin_extensions )


async def _install_packages(
    extensions: list[ __.ExtensionConfig ]
) -> __.cabc.Sequence[ __.Path ]:
    ''' Install external packages and update import paths. '''
    if not extensions: return [ ]
    specifications = [ ext[ 'package' ] for ext in extensions ]
    count = len( specifications )
    _scribe.info( "Installing {} external packages.".format( count ) )
    try:
        install_results = (
            await _installation.install_packages_parallel( specifications ) )
    except __.excg.ExceptionGroup:
        # Error logging already done in install_packages_parallel
        # Continue with just builtin processors
        return [ ]
    else:
        # All installations succeeded
        for result in install_results:
            _isolation.add_to_import_path( result )
            _scribe.debug( f"Added to import path: {result}." )
        return install_results


def _register_processor(
    ext_config: __.ExtensionConfig,
    extensions: list[ __.ExtensionConfig ]
) -> None:
    ''' Register a single processor from configuration. '''
    name = ext_config[ 'name' ]
    arguments = __.get_extension_arguments( ext_config )
    if ext_config in extensions:
        module_name = f"{__.package_name}.processors.{name}"
    else:
        module_name = name
    try:
        module = _isolation.import_processor_module( module_name )
    except Exception as exc:
        _scribe.error( f"Failed to import processor {name}: {exc}." )
        return
    try:
        processor = module.register( arguments )
    except Exception as exc:
        _scribe.error( f"Failed to register processor {name}: {exc}." )
        return
    __.processors[ name ] = processor
    _scribe.info( f"Registered processor: {name}." )
