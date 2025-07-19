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
from .. import configuration as _configuration
from .. import xtnsapi as _xtnsapi


_scribe = __.acquire_scribe( __name__ )


async def _install_external_packages( 
    external_extensions: list[ __.ExtensionConfig ], 
    scribe: __.typx.Any
) -> list[ __.Path | Exception ]:
    ''' Install external packages and update import paths. '''
    from . import installation
    from . import isolation
    
    if not external_extensions:
        return [ ]
    
    package_specs = [ ext[ 'package' ] for ext in external_extensions ]
    scribe.info( f"Installing {len( package_specs )} external packages" )
    
    install_results = await installation.install_packages_parallel( 
        package_specs )
    
    # Process installation results and update import paths
    for ext_config, result in zip( external_extensions, install_results ):
        if isinstance( result, Exception ):
            scribe.error(
                f"Failed to install {ext_config[ 'package' ]}: {result}"
            )
            continue
        
        # Add successful installation to import path
        isolation.add_to_import_path( result )
        scribe.debug( f"Added to import path: {result}" )
    
    return install_results


def _register_processor( 
    ext_config: __.ExtensionConfig, 
    builtin_extensions: list[ __.ExtensionConfig ], 
    scribe: __.typx.Any
) -> None:
    ''' Register a single processor from configuration. '''
    from . import isolation
    
    name = ext_config[ 'name' ]
    arguments = _configuration.get_extension_arguments( ext_config )
    
    try:
        # Check if this is a builtin or external processor
        if ext_config in builtin_extensions:
            # Builtin processor - construct path dynamically
            base_package = _xtnsapi.__name__.rsplit( '.', 1 )[ 0 ]
            module = isolation.import_builtin_processor( base_package, name )
        else:
            # External processor - import by name
            module = isolation.import_external_processor( name )
        
        processor = module.register( arguments )
        _xtnsapi.processors[ name ] = processor
        scribe.info( f"Registered processor: {name}" )
        
    except Exception as exc:
        scribe.error( f"Failed to load processor {name}: {exc}" )


async def load_and_register_processors( auxdata: __.typx.Any = None ):
    ''' Load and register processors based on configuration. '''
    scribe = __.acquire_scribe( __name__ )
    
    try:
        extensions = _configuration.load_extensions_config( auxdata )
        enabled_extensions = _configuration.get_enabled_extensions(
            extensions )
        
        if not enabled_extensions:
            scribe.warning( "No enabled extensions found in configuration" )
            return
        
        # Separate builtin vs external extensions
        builtin_extensions = _configuration.get_builtin_extensions(
            enabled_extensions )
        external_extensions = [
            ext for ext in enabled_extensions
            if ext.get( 'package' ) and ext not in builtin_extensions
        ]
        
        # Install external packages in parallel if any exist
        install_results = await _install_external_packages(
            external_extensions, scribe )
        
        # Load all processors (builtin + successfully installed external)
        successful_external: list[ __.ExtensionConfig ] = [
            ext for ext, result in zip( external_extensions, install_results )
            if isinstance( result, __.Path )
        ] if external_extensions else [ ]
        all_extensions = builtin_extensions + successful_external
        
        if not all_extensions:
            scribe.warning( "No processors could be loaded" )
            return
        
        for ext_config in all_extensions:
            _register_processor( ext_config, builtin_extensions, scribe )
            
    except Exception as exc:
        scribe.error( f"Configuration loading failed: {exc}" )
        scribe.warning( "No processors loaded due to configuration errors" )