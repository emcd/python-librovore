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


''' Processor loading and registration tests. '''


import pytest

import librovore.xtnsmgr.processors as module

from .fixtures import get_broken_extension_url, get_fake_extension_url


def test_000_module_imports_correctly( ):
    ''' Processors module imports without errors. '''
    assert hasattr( module, 'register_processors' )
    assert callable( module.register_processors )


def test_100_private_functions_exist( ):
    ''' Internal processor functions are available for testing. '''
    assert hasattr( module, '_ensure_external_packages' )
    assert hasattr( module, '_register_extension' )
    assert callable( module._ensure_external_packages )
    assert callable( module._register_extension )


@pytest.mark.asyncio
async def test_200_ensure_external_packages_handles_empty_list( ):
    ''' Empty extension list returns without error. '''
    await module._ensure_external_packages( [ ] )


@pytest.mark.asyncio  
async def test_210_ensure_external_packages_with_fake_package( ):
    ''' External package processing handles fake local packages. '''
    fake_url = get_fake_extension_url( )
    fake_extensions = [ 
        { 'name': 'test-ext', 'package': fake_url }
    ]
    # Should successfully install the fake extension
    await module._ensure_external_packages( fake_extensions )


def test_300_register_extension_handles_missing_name( ):
    ''' Extension registration handles missing name key. '''
    assert callable( module._register_extension )
    
    # Should raise KeyError for missing required 'name' field
    with pytest.raises( KeyError ):
        module._register_extension( { }, 'inventory' )


def test_310_register_extension_handles_valid_config( ):
    ''' Extension registration processes valid intrinsic config. '''
    # Test with minimal valid intrinsic processor config
    valid_config = { 
        'name': 'nonexistent-processor',
        'enabled': True,
        'arguments': { }
    }
    # This should attempt to import the processor but fail gracefully
    # The function should return without raising for missing modules
    module._register_extension( valid_config, 'inventory' )


def test_320_register_extension_handles_external_config( ):
    ''' Extension registration processes external processor config. '''
    # Test with external processor config
    external_config = { 
        'name': 'external-processor',
        'package': 'nonexistent-package',
        'enabled': True,
        'arguments': { }
    }
    # Should attempt to import external module but handle gracefully
    module._register_extension( external_config, 'structure' )


@pytest.mark.asyncio
async def test_400_ensure_external_packages_with_multiple_packages( ):
    ''' Multiple external packages are processed in parallel. '''
    fake_url = get_fake_extension_url( )
    multiple_extensions = [
        { 'name': 'ext1', 'package': fake_url },
        { 'name': 'ext2', 'package': fake_url }
    ]
    # Should successfully process multiple valid extensions in parallel
    await module._ensure_external_packages( multiple_extensions )


@pytest.mark.asyncio
async def test_410_ensure_external_packages_with_broken_package( ):
    ''' External package processing installs broken packages successfully. '''
    broken_url = get_broken_extension_url( )
    broken_extensions = [ 
        { 'name': 'broken-ext', 'package': broken_url }
    ]
    # Package installation should succeed even if the package itself is broken
    # The "broken" nature only manifests during import/registration
    await module._ensure_external_packages( broken_extensions )