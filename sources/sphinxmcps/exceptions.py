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


from . import __


class Omniexception( BaseException ):
    ''' Base for all exceptions raised by package API. '''
    # TODO: Class and instance attribute concealment and immutability.

    _attribute_visibility_includes_: __.cabc.Collection[ str ] = (
        frozenset( ( '__cause__', '__context__', ) ) )


class Omnierror( Omniexception, Exception ):
    ''' Base for error exceptions raised by package API. '''


class NetworkConnectionFailure( Omnierror ):
    ''' Network request failed when fetching inventory. '''
    
    def __init__(
        self, source: str, reason: str = "Network connection failed"
    ):
        message = f"{reason} when fetching inventory from {source}"
        super( ).__init__( message )
        self.source = source
        self.reason = reason


class InventoryAbsence( Omnierror ):
    ''' Inventory file or resource not found. '''
    
    def __init__( self, source: str, reason: str = "Resource not found" ):
        message = f"{reason}: {source}"
        super( ).__init__( message )
        self.source = source
        self.reason = reason


class InventoryFormatInvalidity( Omnierror ):
    ''' Inventory has invalid format or cannot be parsed. '''
    
    def __init__(
        self, source: str, reason: str = "Invalid inventory format"
    ):
        message = f"{reason} at {source}"
        super( ).__init__( message )
        self.source = source
        self.reason = reason


class InventoryUrlInvalidity( Omnierror ):
    ''' Inventory URL is malformed or invalid. '''
    
    def __init__( self, source: str, reason: str = "Invalid URL format" ):
        message = f"{reason}: {source}"
        super( ).__init__( message )
        self.source = source
        self.reason = reason
