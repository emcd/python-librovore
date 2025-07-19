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


''' Configuration loading and validation for plugin system. '''


from . import __
from . import exceptions as _exceptions


ExtensionConfig: __.typx.TypeAlias = __.typx.Annotated[
    __.cabc.Mapping[ str, __.typx.Any ],
    __.ddoc.Doc( ''' Configuration for a single extension/processor. ''' )
]

ExtensionArguments: __.typx.TypeAlias = __.typx.Annotated[
    __.cabc.Mapping[ str, __.typx.Any ],
    __.ddoc.Doc( ''' Arguments to pass to extension/processor. ''' )
]



def validate_extension_config( config: ExtensionConfig ) -> None:
    ''' Validates a single extension configuration. '''
    name = config.get( 'name' )
    if not name or not isinstance( name, str ):
        raise _exceptions.ExtensionConfigError( 
            name or '<unnamed>',
            "Required field 'name' must be a non-empty string" 
        )
    
    enabled = config.get( 'enabled', True )
    if not isinstance( enabled, bool ):
        raise _exceptions.ExtensionConfigError(
            name,
            "Field 'enabled' must be a boolean"
        )
    
    package = config.get( 'package' )
    if package is not None and not isinstance( package, str ):
        raise _exceptions.ExtensionConfigError(
            name,
            "Field 'package' must be a string or None"
        )
    
    arguments = config.get( 'arguments', { } )
    if not isinstance( arguments, dict ):
        raise _exceptions.ExtensionConfigError(
            name,
            "Field 'arguments' must be a dictionary"
        )


def load_extensions_config(
    auxdata: __.Globals
) -> list[ ExtensionConfig ]:
    ''' Loads and validates extensions configuration from auxdata. '''
    configuration = auxdata.configuration
    if not configuration:
        return [ ]
    
    extensions_raw = configuration.get( 'extensions', [ ] )
    if not isinstance( extensions_raw, list ):
        raise _exceptions.ExtensionConfigError(
            '<root>',
            "Configuration 'extensions' must be a list"
        )
    
    # Type narrow after isinstance check
    extensions_raw = __.typx.cast( list[ __.typx.Any ], extensions_raw )
    
    extensions: list[ ExtensionConfig ] = [ ]
    for i, ext_config in enumerate( extensions_raw ):
        if not isinstance( ext_config, dict ):
            raise _exceptions.ExtensionConfigError(
                f'<extension[{i}]>',
                "Extension configuration must be a dictionary"
            )
        
        # Type cast after isinstance check
        ext_config_typed = __.typx.cast( ExtensionConfig, ext_config )
        validate_extension_config( ext_config_typed )
        extensions.append( ext_config_typed )
    
    return extensions


def get_enabled_extensions( 
    extensions: list[ ExtensionConfig ] 
) -> list[ ExtensionConfig ]:
    ''' Filters extensions to only enabled ones. '''
    return [ 
        ext for ext in extensions 
        if ext.get( 'enabled', True )
    ]


def get_builtin_extensions( 
    extensions: list[ ExtensionConfig ] 
) -> list[ ExtensionConfig ]:
    ''' Filters extensions to only built-in ones (no package field). '''
    return [ 
        ext for ext in extensions 
        if ext.get( 'package' ) is None
    ]


def get_external_extensions( 
    extensions: list[ ExtensionConfig ] 
) -> list[ ExtensionConfig ]:
    ''' Filters extensions to only external ones (has package field). '''
    return [ 
        ext for ext in extensions 
        if ext.get( 'package' ) is not None
    ]


def get_extension_arguments( 
    extension: ExtensionConfig 
) -> ExtensionArguments:
    ''' Extracts arguments dictionary from extension configuration. '''
    return extension.get( 'arguments', { } )


# Global configuration state
_global_auxdata: __.Globals | None = None


def initialize_configuration( auxdata: __.Globals ) -> None:
    ''' Initialize global configuration state. '''
    global _global_auxdata  # noqa: PLW0603
    _global_auxdata = auxdata


def get_global_auxdata( ) -> __.Globals | None:
    ''' Get the global auxdata instance. '''
    return _global_auxdata


def load_global_extensions_config( ) -> list[ ExtensionConfig ]:
    ''' Loads extensions configuration from global auxdata. '''
    if _global_auxdata is None:
        return [ ]
    return load_extensions_config( _global_auxdata )