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


''' Interface for extension development. '''

# ruff: noqa: F403,F405


from . import __
from . import configuration as _configuration

from .exceptions import *
from .interfaces import *


def _validator( name: str, value: Processor ) -> bool:
    return isinstance( value, Processor )


processors: __.accret.ValidatorDictionary[ str, Processor ] = (
    __.accret.ValidatorDictionary( _validator ) )


# Built-in processor modules mapping
_BUILTIN_PROCESSORS = {
    'sphinx': 'sphinxmcps.processors.sphinx',
}


def _import_processor_module( module_path: str ):
    ''' Import a processor module by path. '''
    import importlib
    return importlib.import_module( module_path )


def load_and_register_processors( ):
    ''' Load and register processors based on configuration. '''
    try:
        extensions = _configuration.load_global_extensions_config( )
        enabled_extensions = _configuration.get_enabled_extensions(
            extensions )
        builtin_extensions = _configuration.get_builtin_extensions(
            enabled_extensions )
        
        for ext_config in builtin_extensions:
            name = ext_config[ 'name' ]
            arguments = _configuration.get_extension_arguments( ext_config )
            
            # Look up built-in processor module
            module_path = _BUILTIN_PROCESSORS.get( name )
            if not module_path:
                # TODO: Log warning about unknown built-in processor
                continue
            
            # Import module and call register function
            try:
                module = _import_processor_module( module_path )
                processor = module.register( arguments )
                processors[ name ] = processor
            except Exception:  # noqa: S110
                # TODO: Log error loading processor
                pass
        
        # If no configuration found at all, register default sphinx as fallback
        if not extensions:
            from .processors.sphinx import register
            processor = register( )
            processors[ 'sphinx' ] = processor
            
    except Exception:
        # Fallback: Register default processors if configuration fails
        from .processors.sphinx import register
        processor = register( )
        processors[ 'sphinx' ] = processor


def ensure_intrinsic_processors_registered( ):
    ''' Ensures intrinsic processors are registered (idempotent). '''
    # Use the processor registry itself to check if registration has occurred
    if not processors:
        load_and_register_processors( )
