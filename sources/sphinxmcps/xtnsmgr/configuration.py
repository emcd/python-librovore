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


''' Extension configuration loading and validation. '''


from . import __
from .. import exceptions as _exceptions


ExtensionArguments: __.typx.TypeAlias = __.typx.Annotated[
    __.cabc.Mapping[ str, __.typx.Any ],
    __.ddoc.Doc( ''' Arguments to pass to extension/processor. ''' )
]
ExtensionConfig: __.typx.TypeAlias = __.typx.Annotated[
    __.cabc.Mapping[ str, __.typx.Any ],
    __.ddoc.Doc( ''' Configuration for a single extension/processor. ''' )
]


def validate_extension( config: ExtensionConfig ) -> None:
    ''' Validates single extension configuration. '''
    name = config.get( 'name' )
    if not name or not isinstance( name, str ):
        raise _exceptions.ExtensionConfigError(
            name or '<unnamed>',
            "Required field 'name' must be a non-empty string" )
    enabled = config.get( 'enabled', True )
    if not isinstance( enabled, bool ):
        raise _exceptions.ExtensionConfigError(
            name, "Field 'enabled' must be a boolean" )
    package = config.get( 'package' )
    if package is not None and not isinstance( package, str ):
        raise _exceptions.ExtensionConfigError(
            name, "Field 'package' must be a string" )
    arguments = config.get( 'arguments', { } )
    if not isinstance( arguments, dict ):
        raise _exceptions.ExtensionConfigError(
            name, "Field 'arguments' must be a dictionary" )


def extract_extensions(
    auxdata: __.Globals
) -> tuple[ ExtensionConfig, ... ]:
    ''' Loads and validates extensions configuration. '''
    configuration = auxdata.configuration
    if not configuration: return ( )
    extensions_raw = configuration.get( 'extensions', [ ] )
    if not isinstance( extensions_raw, list ):
        raise _exceptions.ExtensionConfigError(
            '<root>', "Configuration 'extensions' must be a list" )
    extensions_raw = __.typx.cast( list[ __.typx.Any ], extensions_raw )
    extensions: list[ ExtensionConfig ] = [ ]
    for i, ext_config in enumerate( extensions_raw ):
        if not isinstance( ext_config, dict ):
            raise _exceptions.ExtensionConfigError(
                f'<extension[{i}]>',
                "Extension configuration must be a dictionary" )
        ext_config_typed = __.typx.cast( ExtensionConfig, ext_config )
        validate_extension( ext_config_typed )
        extensions.append( ext_config_typed )
    return tuple( extensions )


def select_active_extensions(
    extensions: __.cabc.Sequence[ ExtensionConfig ]
) -> tuple[ ExtensionConfig, ... ]:
    ''' Filters extensions to only enabled ones. '''
    return tuple( ext for ext in extensions if ext.get( 'enabled', True ) )


def select_intrinsic_extensions(
    extensions: __.cabc.Sequence[ ExtensionConfig ]
) -> tuple[ ExtensionConfig, ... ]:
    ''' Filters extensions to only built-in ones (no package field). '''
    return tuple( ext for ext in extensions if ext.get( 'package' ) is None )


def select_external_extensions(
    extensions: __.cabc.Sequence[ ExtensionConfig ]
) -> tuple[ ExtensionConfig, ... ]:
    ''' Filters extensions to only external ones (has package field). '''
    return tuple(
        ext for ext in extensions if ext.get( 'package' ) is not None )


def extract_extension_arguments(
    extension: ExtensionConfig
) -> ExtensionArguments:
    ''' Extracts arguments dictionary from extension configuration. '''
    return extension.get( 'arguments', { } )
