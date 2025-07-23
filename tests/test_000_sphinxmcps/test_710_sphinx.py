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


''' Sphinx processor implementation tests using dependency injection. '''


import sphinxmcps.processors.sphinx as module


def test_100_normalize_inventory_source_basic_path( ):
    ''' URL normalization works correctly for inventory paths. '''
    test_path = '/home/user/test.inv'
    result = module.normalize_inventory_source( test_path )
    assert result.path.endswith( 'objects.inv' )


def test_110_normalize_inventory_source_with_objects_inv( ):
    ''' URL normalization doesn't double-append objects.inv. '''
    test_path = '/home/user/objects.inv'
    result = module.normalize_inventory_source( test_path )
    assert result.path.endswith( 'objects.inv' )
    # Should not have double objects.inv
    assert not result.path.endswith( 'objects.inv/objects.inv' )