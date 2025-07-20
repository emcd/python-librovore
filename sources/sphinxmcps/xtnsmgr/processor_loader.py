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


async def _install_external_packages(
    external_extensions: list[ __.ExtensionConfig ]
) -> list[ __.Path ]:
    ''' Install external packages and update import paths. '''
    if not external_extensions: return [ ]
    package_specs = [ ext[ 'package' ] for ext in external_extensions ]
    _scribe.info( f"Installing {len( package_specs )} external packages" )
    install_results = (
        await _installation.install_packages_parallel( package_specs ) )
    for ext_config, result in zip( external_extensions, install_results ):
        if isinstance( result, Exception ):
            _scribe.error(
                f"Failed to install {ext_config[ 'package' ]}: {result}" )
            continue
        _isolation.add_to_import_path( result )
        _scribe.debug( f"Added to import path: {result}" )
    return install_results


def _register_processor(
    ext_config: __.ExtensionConfig,
    builtin_extensions: list[ __.ExtensionConfig ]
) -> None:
    ''' Register a single processor from configuration. '''
    name = ext_config[ 'name' ]
    arguments = __.get_extension_arguments( ext_config )
    try:
        if ext_config in builtin_extensions:
            module_name = f"{__.package_name}.processors.{name}"
            module = _isolation.import_processor_module( module_name )
        else: module = _isolation.import_processor_module( name )
        processor = module.register( arguments )
        __.processors[ name ] = processor
        _scribe.info( f"Registered processor: {name}" )
    except Exception as exc:
        _scribe.error( f"Failed to load processor {name}: {exc}" )


async def load_and_register_processors( auxdata: __.typx.Any = None ):
    ''' Load and register processors based on configuration. '''
    try:
        extensions = __.load_extensions_config( auxdata )
    except Exception as exc:
        _scribe.error( f"Configuration loading failed: {exc}" )
        _scribe.warning( "No processors loaded due to configuration errors" )
        return
    enabled_extensions = __.get_enabled_extensions( extensions )
    if not enabled_extensions:
        _scribe.warning( "No enabled extensions found in configuration" )
        return
    builtin_extensions = __.get_builtin_extensions( enabled_extensions )
    external_extensions = [
        ext for ext in enabled_extensions
        if ext.get( 'package' ) and ext not in builtin_extensions
    ]
    install_results = (
        await _install_external_packages( external_extensions ) )
    # Load all processors (builtin + successfully installed external)
    successful_external: list[ __.ExtensionConfig ] = [
        ext for ext, result in zip( external_extensions, install_results )
        if isinstance( result, __.Path )
    ] if external_extensions else [ ]
    all_extensions = builtin_extensions + successful_external
    if not all_extensions:
        _scribe.warning( "No processors could be loaded" )
        return
    for ext_config in all_extensions:
        _register_processor( ext_config, builtin_extensions )
