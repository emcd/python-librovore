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


''' Extension package installation tests. '''


import pytest
from pathlib import Path

import sphinxmcps.xtnsmgr.installation as module

from .test_utils import get_fake_extension_url


@pytest.mark.asyncio
async def test_000_install_packages_parallel_empty_list( ):
    ''' Empty package list returns empty list. '''
    result = await module.install_packages_parallel( [ ] )
    assert result == [ ]


@pytest.mark.asyncio  
async def test_010_install_packages_parallel_single_package( ):
    ''' Single package installation works through parallel interface. '''
    fake_url = get_fake_extension_url( )
    cache_path = Path( '/cache/path' )
    
    async def mock_installer( spec ):
        assert spec == fake_url
        return cache_path
    
    result = await module.install_packages_parallel(
        [ fake_url ], installer = mock_installer )
    assert result == ( cache_path, )

def test_100_module_imports_correctly( ):
    ''' Installation module imports without errors. '''
    assert hasattr( module, 'install_package' )
    assert hasattr( module, 'install_packages_parallel' )


def test_110_fake_extension_url_format( ):
    ''' Fake extension URL has correct file:// format. '''
    fake_url = get_fake_extension_url( )
    assert fake_url.startswith( 'file://' )
    assert 'fake-extension' in fake_url