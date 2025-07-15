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


''' Exception hierarchy and error handling tests. '''



from . import PACKAGE_NAME, cache_import_module


def test_000_exception_hierarchy_inheritance( ):
    ''' Exception classes follow proper inheritance hierarchy. '''
    exceptions_module = cache_import_module( f"{PACKAGE_NAME}.exceptions" )
    
    exc = exceptions_module.InventoryInaccessibility(
        "test.inv", Exception( "test" )
    )
    assert isinstance( exc, exceptions_module.Omnierror )
    assert isinstance( exc, exceptions_module.Omniexception )


def test_010_network_failure_inheritance( ):
    ''' InventoryInaccessibility follows proper hierarchy. '''
    exceptions_module = cache_import_module( f"{PACKAGE_NAME}.exceptions" )
    
    exc = exceptions_module.InventoryInaccessibility(
        "http://example.com", Exception( "network error" )
    )
    assert isinstance( exc, exceptions_module.Omnierror )
    assert isinstance( exc, exceptions_module.Omniexception )


def test_020_omniexception_is_base( ):
    ''' Omniexception is the base exception class. '''
    exceptions_module = cache_import_module( f"{PACKAGE_NAME}.exceptions" )
    
    exc = exceptions_module.Omniexception( "test error" )
    assert isinstance( exc, BaseException )


def test_030_omnierror_inheritance( ):
    ''' Omnierror inherits from both Omniexception and Exception. '''
    exceptions_module = cache_import_module( f"{PACKAGE_NAME}.exceptions" )
    
    exc = exceptions_module.Omnierror( "test error" )
    assert isinstance( exc, exceptions_module.Omniexception )
    assert isinstance( exc, Exception )


def test_040_inventory_format_invalidity_inheritance( ):
    ''' InventoryInvalidity inherits from Omnierror. '''
    exceptions_module = cache_import_module( f"{PACKAGE_NAME}.exceptions" )
    
    exc = exceptions_module.InventoryInvalidity(
        "test.inv", Exception( "format error" )
    )
    assert isinstance( exc, exceptions_module.Omnierror )


def test_100_inventory_inaccessibility_message( ):
    ''' InventoryInaccessibility includes source in message. '''
    exceptions_module = cache_import_module( f"{PACKAGE_NAME}.exceptions" )
    
    source = "/path/to/missing.inv"
    exc = exceptions_module.InventoryInaccessibility(
        source, Exception( "not found" )
    )
    assert source in str( exc )


def test_110_inventory_inaccessibility_network_message( ):
    ''' InventoryInaccessibility includes source in network error messages. '''
    exceptions_module = cache_import_module( f"{PACKAGE_NAME}.exceptions" )
    
    source = "http://example.com/objects.inv"
    exc = exceptions_module.InventoryInaccessibility(
        source, Exception( "connection failed" )
    )
    assert source in str( exc )


def test_120_inventory_invalidity_message( ):
    ''' InventoryInvalidity includes source in message. '''
    exceptions_module = cache_import_module( f"{PACKAGE_NAME}.exceptions" )
    
    source = "/path/to/invalid.inv"
    exc = exceptions_module.InventoryInvalidity(
        source, Exception( "invalid format" )
    )
    assert source in str( exc )


def test_130_inventory_url_invalidity_message( ):
    ''' InventoryUrlInvalidity includes source in message. '''
    exceptions_module = cache_import_module( f"{PACKAGE_NAME}.exceptions" )
    
    source = "not-a-valid-url"
    exc = exceptions_module.InventoryUrlInvalidity( source )
    assert source in str( exc )


def test_200_exception_with_custom_reason( ):
    ''' Exceptions accept custom reason messages. '''
    exceptions_module = cache_import_module( f"{PACKAGE_NAME}.exceptions" )
    
    custom_reason = Exception( "Custom error reason" )
    exc = exceptions_module.InventoryInaccessibility(
        "test.inv", custom_reason
    )
    assert "Custom error reason" in str( exc )


def test_210_inaccessibility_with_custom_reason( ):
    ''' InventoryInaccessibility accepts custom reason. '''
    exceptions_module = cache_import_module( f"{PACKAGE_NAME}.exceptions" )
    
    custom_reason = Exception( "Connection timeout" )
    exc = exceptions_module.InventoryInaccessibility( 
        "http://example.com", custom_reason 
    )
    assert "Connection timeout" in str( exc )


def test_220_invalidity_with_custom_reason( ):
    ''' InventoryInvalidity accepts custom reason. '''
    exceptions_module = cache_import_module( f"{PACKAGE_NAME}.exceptions" )
    
    custom_reason = Exception( "Corrupted header" )
    exc = exceptions_module.InventoryInvalidity( 
        "test.inv", custom_reason 
    )
    assert "Corrupted header" in str( exc )


def test_230_url_invalidity_message( ):
    ''' InventoryUrlInvalidity includes source in message. '''
    exceptions_module = cache_import_module( f"{PACKAGE_NAME}.exceptions" )
    
    source = "not-a-valid-url"
    exc = exceptions_module.InventoryUrlInvalidity( source )
    assert source in str( exc )