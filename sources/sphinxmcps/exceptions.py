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


''' Family of exceptions for package API. '''


import urllib.parse as _urlparse

from . import __


class Omniexception( BaseException ):
    ''' Base for all exceptions raised by package API. '''
    # TODO: Class and instance attribute concealment and immutability.

    _attribute_visibility_includes_: __.cabc.Collection[ str ] = (
        frozenset( ( '__cause__', '__context__', ) ) )


class Omnierror( Omniexception, Exception ):
    ''' Base for error exceptions raised by package API. '''


class DocumentationContentAbsence( Omnierror, ValueError ):
    ''' Documentation main content container not found. '''

    def __init__( self, url: str ):
        message = f"No main content found in documentation at '{url}'."
        self.url = url
        super( ).__init__( message )


class DocumentationInaccessibility( Omnierror, RuntimeError ):
    ''' Documentation file or resource absent or inaccessible. '''

    def __init__( self, url: str, cause: Exception ):
        message = f"Documentation at '{url}' is inaccessible. Cause: {cause}"
        self.url = url
        super( ).__init__( message )


class DocumentationParseFailure( Omnierror, ValueError ):
    ''' Documentation HTML parsing failed or content malformed. '''

    def __init__( self, url: str, cause: Exception ):
        message = f"Cannot parse documentation at '{url}'. Cause: {cause}"
        self.url = url
        super( ).__init__( message )


class ExtensionRegisterFailure( Omnierror, TypeError ):
    ''' Invalid plugin could not be registered. '''

    def __init__( self, message: str ):
        # TODO: Canned message with extension name as argument.
        super( ).__init__( message )


class ProcessorTypeError( Omnierror, TypeError ):
    ''' Processor has wrong type. '''

    def __init__( self, expected_type: str, actual_type: type ):
        message = f"Expected {expected_type}, got {actual_type}"
        self.expected_type = expected_type
        self.actual_type = actual_type
        super( ).__init__( message )


class InventoryInaccessibility( Omnierror, RuntimeError ):
    ''' Inventory file or resource absent or inaccessible. '''

    def __init__( self, source: str, cause: Exception ):
        message = f"Inventory at '{source}' is inaccessible. Cause: {cause}"
        self.source = source
        super( ).__init__( message )


class InventoryInvalidity( Omnierror, ValueError ):
    ''' Inventory has invalid format or cannot be parsed. '''

    def __init__( self, source: str, cause: Exception ):
        message = f"Inventory at '{source}' is invalid. Cause: {cause}"
        self.source = source
        super( ).__init__( message )


class InventoryFilterInvalidity( Omnierror, ValueError ):
    ''' Inventory filter is invalid. '''

    def __init__( self, message: str ):
        super( ).__init__( message )


class InventoryUrlInvalidity( Omnierror, ValueError ):
    ''' Inventory URL is malformed or invalid. '''

    def __init__( self, source: str ):
        message = f"Invalid URL format: {source}"
        self.source = source
        super( ).__init__( message )


class InventoryUrlNoSupport( Omnierror, NotImplementedError ):
    ''' Inventory URL has unsupported component. '''

    def __init__(
        self, url: _urlparse.ParseResult, component: str,
        value: __.Absential[ str ] = __.absent,
    ):
        url_s = _urlparse.urlunparse( url )
        message_c = f"Component '{component}' "
        message_i = f"not supported in inventory URL '{url_s}'."
        message = (
            f"{message_c} {message_i}" if __.is_absent( value )
            else f"{message_c} with value '{value}' {message_i}" )
        self.url = url
        super( ).__init__( message )


class ProcessorNotFound( Omnierror, RuntimeError ):
    ''' No processor found to handle source. '''

    def __init__( self, source: str ):
        message = f"No processor found to handle source: {source}"
        self.source = source
        super( ).__init__( message )


class ExtensionConfigError( Omnierror, ValueError ):
    ''' Extension configuration is invalid. '''
    
    def __init__( self, extension_name: str, message: str ):
        self.extension_name = extension_name
        super( ).__init__( f"Extension '{extension_name}': {message}" )


class ExtensionInstallationError( Omnierror, RuntimeError ):
    ''' Extension package installation failed. '''
    
    def __init__( self, package_spec: str, message: str ):
        self.package_spec = package_spec
        super( ).__init__( f"Failed to install '{package_spec}': {message}" )


class ExtensionCacheError( Omnierror, RuntimeError ):
    ''' Extension cache operation failed. '''
    
    def __init__( self, cache_path: __.Path, message: str ):
        self.cache_path = cache_path
        super( ).__init__( f"Cache error at '{cache_path}': {message}" )


class ExtensionVersionConflictError( Omnierror, ImportError ):
    ''' Extension has incompatible version requirements. '''
    
    def __init__( self, package_name: str, required: str, available: str ):
        self.package_name = package_name
        self.required = required
        self.available = available
        super( ).__init__(
            f"Version conflict for '{package_name}': "
            f"required {required}, available {available}"
        )


