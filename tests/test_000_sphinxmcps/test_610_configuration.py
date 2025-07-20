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


''' Extension configuration parsing and validation tests. '''


import pytest
from unittest.mock import Mock

import sphinxmcps.xtnsmgr.configuration as module
import sphinxmcps.exceptions as _exceptions


def test_000_validate_extension_valid_intrinsic( ):
    ''' Valid built-in extension configuration passes validation. '''
    config = {
        'name': 'sphinx.domains.python',
        'enabled': True,
        'arguments': { 'option1': 'value1' }
    }
    module.validate_extension( config )


def test_010_validate_extension_valid_external( ):
    ''' Valid external extension configuration passes validation. '''
    config = {
        'name': 'custom.processor',
        'package': 'file:///path/to/external-extension',
        'enabled': True,
        'arguments': { }
    }
    module.validate_extension( config )


def test_020_validate_extension_disabled( ):
    ''' Disabled extension configuration passes validation. '''
    config = {
        'name': 'sphinx.domains.python',
        'enabled': False,
        'arguments': { }
    }
    module.validate_extension( config )


def test_030_validate_extension_complex_arguments( ):
    ''' Extension with complex nested arguments passes validation. '''
    config = {
        'name': 'custom.processor',
        'enabled': True,
        'arguments': {
            'options': {
                'depth': 5,
                'filters': [ 'filter1', 'filter2' ]
            },
            'paths': [ '/path1', '/path2' ]
        }
    }
    module.validate_extension( config )


def test_040_validate_extension_missing_name_field( ):
    ''' Missing name field raises ExtensionConfigError. '''
    config = {
        'enabled': True,
        'arguments': { }
    }
    with pytest.raises(
        _exceptions.ExtensionConfigError, match="Required field 'name'" ):
        module.validate_extension( config )


def test_050_validate_extension_empty_name_field( ):
    ''' Empty name field raises ExtensionConfigError. '''
    config = {
        'name': '',
        'enabled': True,
        'arguments': { }
    }
    with pytest.raises(
        _exceptions.ExtensionConfigError, match="Required field 'name'" ):
        module.validate_extension( config )


def test_060_validate_extension_non_string_name( ):
    ''' Non-string name field raises ExtensionConfigError. '''
    config = {
        'name': 123,
        'enabled': True,
        'arguments': { }
    }
    with pytest.raises(
        _exceptions.ExtensionConfigError, match="must be a non-empty string" ):
        module.validate_extension( config )


def test_070_validate_extension_non_boolean_enabled( ):
    ''' Non-boolean enabled field raises ExtensionConfigError. '''
    config = {
        'name': 'test.extension',
        'enabled': 'true',
        'arguments': { }
    }
    with pytest.raises(
        _exceptions.ExtensionConfigError, match="must be a boolean" ):
        module.validate_extension( config )


def test_080_validate_extension_non_string_package( ):
    ''' Non-string package field raises ExtensionConfigError. '''
    config = {
        'name': 'test.extension',
        'package': 123,
        'enabled': True,
        'arguments': { }
    }
    with pytest.raises(
        _exceptions.ExtensionConfigError, match="must be a string" ):
        module.validate_extension( config )


def test_090_validate_extension_non_dict_arguments( ):
    ''' Non-dict arguments field raises ExtensionConfigError. '''
    config = {
        'name': 'test.extension',
        'enabled': True,
        'arguments': 'invalid'
    }
    with pytest.raises(
        _exceptions.ExtensionConfigError, match="must be a dictionary" ):
        module.validate_extension( config )


def test_100_validate_extension_minimal_config( ):
    ''' Minimal configuration with only name field passes validation. '''
    config = { 'name': 'test.extension' }
    module.validate_extension( config )


def test_200_extract_extensions_valid_list( ):
    ''' Valid extension list extracts correctly. '''
    mock_globals = Mock( )
    mock_globals.configuration = {
        'extensions': [
            {
                'name': 'sphinx.domains.python',
                'enabled': True,
                'arguments': { 'option1': 'value1' }
            },
            {
                'name': 'custom.processor',
                'package': 'file:///path/to/external',
                'enabled': False,
                'arguments': { }
            }
        ]
    }
    result = module.extract_extensions( mock_globals )
    assert len( result ) == 2
    assert result[ 0 ][ 'name' ] == 'sphinx.domains.python'
    assert result[ 1 ][ 'name' ] == 'custom.processor'


def test_210_extract_extensions_no_configuration( ):
    ''' No configuration returns empty tuple. '''
    mock_globals = Mock( )
    mock_globals.configuration = None
    result = module.extract_extensions( mock_globals )
    assert result == ( )


def test_220_extract_extensions_no_extensions_field( ):
    ''' Missing extensions field returns empty tuple. '''
    mock_globals = Mock( )
    mock_globals.configuration = { }
    result = module.extract_extensions( mock_globals )
    assert result == ( )


def test_230_extract_extensions_non_list_extensions( ):
    ''' Non-list extensions field raises ExtensionConfigError. '''
    mock_globals = Mock( )
    mock_globals.configuration = { 'extensions': 'not_a_list' }
    with pytest.raises(
        _exceptions.ExtensionConfigError, match="must be a list" ):
        module.extract_extensions( mock_globals )


def test_240_extract_extensions_non_dict_extension( ):
    ''' Non-dict extension in list raises ExtensionConfigError. '''
    mock_globals = Mock( )
    mock_globals.configuration = {
        'extensions': [ 'not_a_dict' ]
    }
    with pytest.raises(
        _exceptions.ExtensionConfigError, match="must be a dictionary" ):
        module.extract_extensions( mock_globals )


def test_250_extract_extensions_invalid_extension( ):
    ''' Invalid extension config raises ExtensionConfigError. '''
    mock_globals = Mock( )
    mock_globals.configuration = {
        'extensions': [
            { 'enabled': True }  # Missing name
        ]
    }
    with pytest.raises(
        _exceptions.ExtensionConfigError, match="Required field 'name'" ):
        module.extract_extensions( mock_globals )


def test_300_select_active_extensions( ):
    ''' Active extension filtering includes enabled extensions only. '''
    extensions = [
        { 'name': 'ext1', 'enabled': True },
        { 'name': 'ext2', 'enabled': False },
        { 'name': 'ext3' }  # Default enabled
    ]
    result = module.select_active_extensions( extensions )
    assert len( result ) == 2
    assert result[ 0 ][ 'name' ] == 'ext1'
    assert result[ 1 ][ 'name' ] == 'ext3'


def test_310_select_intrinsic_extensions( ):
    ''' Intrinsic extension filtering excludes extensions with package. '''
    extensions = [
        { 'name': 'ext1' },  # No package field
        { 'name': 'ext2', 'package': 'file:///path' },
        { 'name': 'ext3', 'package': None }  # Explicit None
    ]
    result = module.select_intrinsic_extensions( extensions )
    assert len( result ) == 2
    assert result[ 0 ][ 'name' ] == 'ext1'
    assert result[ 1 ][ 'name' ] == 'ext3'


def test_320_select_external_extensions( ):
    ''' External extension filtering includes only external extensions. '''
    extensions = [
        { 'name': 'ext1' },  # No package field
        { 'name': 'ext2', 'package': 'file:///path' },
        { 'name': 'ext3', 'package': None }  # Explicit None
    ]
    result = module.select_external_extensions( extensions )
    assert len( result ) == 1
    assert result[ 0 ][ 'name' ] == 'ext2'


def test_400_extract_extension_arguments( ):
    ''' Extension argument extraction returns argument dictionary. '''
    extension = {
        'name': 'test.extension',
        'arguments': { 'key1': 'value1', 'key2': 'value2' }
    }
    result = module.extract_extension_arguments( extension )
    assert result == { 'key1': 'value1', 'key2': 'value2' }


def test_410_extract_extension_arguments_default( ):
    ''' Extension argument extraction returns empty dict when missing. '''
    extension = { 'name': 'test.extension' }
    result = module.extract_extension_arguments( extension )
    assert result == { }