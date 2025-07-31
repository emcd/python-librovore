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



import sphinxmcps.xtnsmgr.installation as module

from .fixtures import get_fake_extension_url



def test_100_module_imports_correctly( ):
    ''' Installation module imports without errors. '''
    assert hasattr( module, 'install_package' )


def test_110_fake_extension_url_format( ):
    ''' Fake extension URL has correct file:// format. '''
    fake_url = get_fake_extension_url( )
    assert fake_url.startswith( 'file://' )
    assert 'fake-extension' in fake_url