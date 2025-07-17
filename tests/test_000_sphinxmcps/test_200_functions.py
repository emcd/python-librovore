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


''' Core business logic functions tests using dependency injection. '''


import pytest
from pathlib import Path

import sphinxmcps.functions as module
import sphinxmcps.exceptions as exceptions_module
import sphinxmcps.interfaces as interfaces_module

from .fixtures import get_test_inventory_path



def test_100_extract_inventory_local_file( ):
    ''' Extract inventory processes local inventory files. '''
    inventory_path = get_test_inventory_path( 'sphinxmcps' )
    result = module.extract_inventory( inventory_path )
    assert 'project' in result
    assert 'objects' in result


def test_110_extract_inventory_with_domain_filter( ):
    ''' Extract inventory applies domain filtering correctly. '''
    inventory_path = get_test_inventory_path( 'sphinxmcps' )
    result = module.extract_inventory( inventory_path, domain = 'py' )
    assert 'filters' in result
    assert result[ 'filters' ][ 'domain' ] == 'py'


def test_120_extract_inventory_with_role_filter( ):
    ''' Extract inventory applies role filtering correctly. '''
    inventory_path = get_test_inventory_path( 'sphinxmcps' )
    result = module.extract_inventory(
        inventory_path, role = 'module' )
    assert 'filters' in result
    assert result[ 'filters' ][ 'role' ] == 'module'


def test_130_extract_inventory_with_search_filter( ):
    ''' Extract inventory applies search filtering correctly. '''
    inventory_path = get_test_inventory_path( 'sphinxmcps' )
    result = module.extract_inventory(
        inventory_path, term = 'test' )
    assert 'filters' in result
    assert result[ 'filters' ][ 'term' ] == 'test'


def test_140_extract_inventory_with_all_filters( ):
    ''' Extract inventory applies multiple filters correctly. '''
    inventory_path = get_test_inventory_path( 'sphinxmcps' )
    result = module.extract_inventory(
        inventory_path, domain = 'py', role = 'module', term = 'test' )
    assert 'filters' in result
    filters = result[ 'filters' ]
    assert filters[ 'domain' ] == 'py'
    assert filters[ 'role' ] == 'module'
    assert filters[ 'term' ] == 'test'


def test_150_extract_inventory_nonexistent_file( ):
    ''' Extract inventory raises appropriate exception for missing files. '''
    with pytest.raises( exceptions_module.InventoryInaccessibility ):
        module.extract_inventory( "/nonexistent/path.inv" )


def test_160_extract_inventory_auto_append_objects_inv( ):
    ''' Extract inventory auto-appends objects.inv to URLs/paths. '''
    real_inventory_path = get_test_inventory_path( 'sphinxmcps' )
    inventory_dir = str( Path( real_inventory_path ).parent )
    # Test without objects.inv suffix
    result = module.extract_inventory( inventory_dir )
    assert 'project' in result
    assert 'objects' in result


def test_170_extract_inventory_with_regex_term( ):
    ''' Extract inventory applies regex term filtering correctly. '''
    inventory_path = get_test_inventory_path( 'sphobjinv' )
    # Use regex to find objects containing "inventory"
    result = module.extract_inventory(
        inventory_path, term = '.*inventory.*',
        match_mode = interfaces_module.MatchMode.Regex )
    assert 'filters' in result
    assert result[ 'filters' ][ 'term' ] == '.*inventory.*'
    assert result[ 'filters' ][ 'match_mode' ] == 'regex'
    assert result[ 'object_count' ] > 0


def test_180_extract_inventory_with_regex_anchors( ):
    ''' Extract inventory handles regex anchor patterns correctly. '''
    inventory_path = get_test_inventory_path( 'sphobjinv' )
    # Use regex anchors to find objects starting with specific pattern
    result = module.extract_inventory(
        inventory_path, term = r'^sphobjinv\.',
        match_mode = interfaces_module.MatchMode.Regex )
    assert 'filters' in result
    assert result[ 'filters' ][ 'match_mode' ] == 'regex'
    if result[ 'object_count' ] > 0:
        for domain_objects in result[ 'objects' ].values( ):
            for obj in domain_objects:
                assert obj[ 'name' ].startswith( 'sphobjinv.' )


def test_190_extract_inventory_invalid_regex( ):
    ''' Extract inventory raises exception for invalid regex patterns. '''
    inventory_path = get_test_inventory_path( 'sphobjinv' )
    with pytest.raises( exceptions_module.InventoryFilterInvalidity ):
        module.extract_inventory(
            inventory_path, term = '[invalid_regex',
            match_mode = interfaces_module.MatchMode.Regex )


def test_200_summarize_inventory_basic( ):
    ''' Summarize inventory provides human-readable summary. '''
    inventory_path = get_test_inventory_path( 'sphinxmcps' )
    result = module.summarize_inventory( inventory_path )
    assert 'objects' in result


def test_210_summarize_inventory_with_filters( ):
    ''' Summarize inventory includes filter information when provided. '''
    inventory_path = get_test_inventory_path( 'sphinxmcps' )
    result = module.summarize_inventory( inventory_path, domain = 'py' )
    assert 'objects' in result
    # Should mention filtering was applied
    assert 'filter' in result.lower( ) or 'domain' in result.lower( )


def test_215_summarize_inventory_with_regex( ):
    ''' Summarize inventory includes regex filter information. '''
    inventory_path = get_test_inventory_path( 'sphobjinv' )
    # Summarize with regex filter applied
    result = module.summarize_inventory(
        inventory_path, term = '.*inventory.*',
        match_mode = interfaces_module.MatchMode.Regex )
    assert 'objects' in result
    # Should mention regex filtering was applied
    assert 'regex' in result.lower( )


def test_220_extract_inventory_with_fuzzy_matching( ):
    ''' Extract inventory applies fuzzy matching correctly. '''
    inventory_path = get_test_inventory_path( 'sphobjinv' )
    # Use fuzzy matching to find objects similar to "DataObj"
    result = module.extract_inventory(
        inventory_path, term = 'DataObj',
        match_mode = interfaces_module.MatchMode.Fuzzy,
        fuzzy_threshold = 50 )
    assert 'filters' in result
    assert result[ 'filters' ][ 'term' ] == 'DataObj'
    assert result[ 'filters' ][ 'match_mode' ] == 'fuzzy'
    assert result[ 'filters' ][ 'fuzzy_threshold' ] == 50
    assert result[ 'object_count' ] > 0


def test_230_extract_inventory_fuzzy_with_high_threshold( ):
    ''' Extract inventory with high fuzzy threshold finds fewer matches. '''
    inventory_path = get_test_inventory_path( 'sphobjinv' )
    # Use high threshold for stricter matching
    result_strict = module.extract_inventory(
        inventory_path, term = 'DataObj',
        match_mode = interfaces_module.MatchMode.Fuzzy,
        fuzzy_threshold = 80 )
    # Use low threshold for looser matching
    result_loose = module.extract_inventory(
        inventory_path, term = 'DataObj',
        match_mode = interfaces_module.MatchMode.Fuzzy,
        fuzzy_threshold = 30 )
    # Stricter threshold should find fewer or equal matches
    assert result_strict[ 'object_count' ] <= result_loose[ 'object_count' ]
    assert result_strict[ 'filters' ][ 'fuzzy_threshold' ] == 80
    assert result_loose[ 'filters' ][ 'fuzzy_threshold' ] == 30


def test_240_extract_inventory_fuzzy_with_domain_filter( ):
    ''' Extract inventory combines fuzzy matching with domain filtering. '''
    inventory_path = get_test_inventory_path( 'sphobjinv' )
    # Combine fuzzy matching with domain filter
    result = module.extract_inventory(
        inventory_path,
        domain = 'py',
        term = 'inventory',
        match_mode = interfaces_module.MatchMode.Fuzzy,
        fuzzy_threshold = 60 )
    assert 'filters' in result
    assert result[ 'filters' ][ 'domain' ] == 'py'
    assert result[ 'filters' ][ 'match_mode' ] == 'fuzzy'
    # All objects should be from py domain
    if result[ 'object_count' ] > 0:
        assert 'py' in result[ 'objects' ]
        for domain_name in result[ 'objects' ]:
            assert domain_name == 'py'


def test_250_summarize_inventory_with_fuzzy( ):
    ''' Summarize inventory includes fuzzy filter information. '''
    inventory_path = get_test_inventory_path( 'sphobjinv' )
    # Summarize with fuzzy filter applied
    result = module.summarize_inventory(
        inventory_path, term = 'inventory',
        match_mode = interfaces_module.MatchMode.Fuzzy,
        fuzzy_threshold = 70 )
    assert 'objects' in result
    # Should mention fuzzy filtering was applied
    assert 'fuzzy' in result.lower( )
    assert '70' in result  # Should show threshold


def test_260_match_mode_enum_values( ):
    ''' MatchMode enum has correct string values. '''
    assert interfaces_module.MatchMode.Exact.value == 'exact'
    assert interfaces_module.MatchMode.Regex.value == 'regex'
    assert interfaces_module.MatchMode.Fuzzy.value == 'fuzzy'


def test_270_summarize_inventory_nonexistent_file( ):
    ''' Summarize inventory raises appropriate exception for missing files. '''
    with pytest.raises( exceptions_module.InventoryInaccessibility ):
        module.summarize_inventory( "/nonexistent/path.inv" )


def test_300_url_detection_http( ):
    ''' URL detection correctly identifies HTTP URLs. '''
    if hasattr( module, '_is_url' ):
        assert module._is_url( "http://example.com" )
        assert module._is_url( "https://example.com" )


def test_310_url_detection_file_paths( ):
    ''' URL detection correctly identifies file paths as non-URLs. '''
    if hasattr( module, '_is_url' ):
        assert not module._is_url( "/path/to/file.inv" )
        assert not module._is_url( "relative/path.inv" )


def test_320_url_detection_edge_cases( ):
    ''' URL detection handles edge cases correctly. '''
    if hasattr( module, '_is_url' ):
        assert not module._is_url( "" )
        assert module._is_url( "file://" )  # Local file URL


def test_400_extract_inventory_with_priority_filter( ):
    ''' Extract inventory filters objects by priority level. '''
    inventory_path = get_test_inventory_path( 'sphobjinv' )
    result = module.extract_inventory(
        inventory_path, priority = '1' )
    assert 'filters' in result
    assert result[ 'filters' ][ 'priority' ] == '1'
    assert result[ 'object_count' ] > 0
    for domain_objects in result[ 'objects' ].values( ):
        for obj in domain_objects:
            assert obj[ 'priority' ] == '1'


def test_410_extract_inventory_priority_filter_different_values( ):
    ''' Extract inventory works with different priority values. '''
    inventory_path = get_test_inventory_path( 'sphobjinv' )
    result_0 = module.extract_inventory(
        inventory_path, priority = '0')
    assert result_0[ 'filters' ][ 'priority' ] == '0'
    result_1 = module.extract_inventory(
        inventory_path, priority = '1' )
    assert result_1[ 'filters' ][ 'priority' ] == '1'
    assert result_0[ 'object_count' ] != result_1[ 'object_count' ]


def test_420_extract_inventory_priority_with_domain_filter( ):
    ''' Extract inventory combines priority and domain filtering. '''
    inventory_path = get_test_inventory_path( 'sphobjinv' )
    result = module.extract_inventory(
        inventory_path, domain = 'py', priority = '1' )
    assert 'filters' in result
    assert result[ 'filters' ][ 'domain' ] == 'py'
    assert result[ 'filters' ][ 'priority' ] == '1'
    if result[ 'object_count' ] > 0:
        assert 'py' in result[ 'objects' ]
        for domain_name in result[ 'objects' ]:
            assert domain_name == 'py'
        for obj in result[ 'objects' ][ 'py' ]:
            assert obj[ 'priority' ] == '1'


def test_430_summarize_inventory_with_priority( ):
    ''' Summarize inventory includes priority filter information. '''
    inventory_path = get_test_inventory_path( 'sphobjinv' )
    result = module.summarize_inventory( inventory_path, priority = '1')
    assert 'priority=1' in result
    assert 'Filters:' in result
