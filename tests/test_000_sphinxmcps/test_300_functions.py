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
import sphinxmcps.exceptions as _exceptions  
import sphinxmcps.interfaces as _interfaces

from .fixtures import get_test_inventory_path



@pytest.mark.asyncio
async def test_100_extract_inventory_local_file( ):
    ''' Extract inventory processes local inventory files. '''
    inventory_path = get_test_inventory_path( 'sphinxmcps' )
    result = await module.extract_inventory( inventory_path )
    assert 'project' in result
    assert 'objects' in result


@pytest.mark.asyncio
async def test_110_extract_inventory_with_domain_filter( ):
    ''' Extract inventory applies domain filtering correctly. '''
    inventory_path = get_test_inventory_path( 'sphinxmcps' )
    result = await module.extract_inventory( inventory_path, domain = 'py' )
    assert 'filters' in result
    assert result[ 'filters' ][ 'domain' ] == 'py'


@pytest.mark.asyncio
async def test_120_extract_inventory_with_role_filter( ):
    ''' Extract inventory applies role filtering correctly. '''
    inventory_path = get_test_inventory_path( 'sphinxmcps' )
    result = await module.extract_inventory(
        inventory_path, role = 'module' )
    assert 'filters' in result
    assert result[ 'filters' ][ 'role' ] == 'module'


@pytest.mark.asyncio
async def test_130_extract_inventory_with_search_filter( ):
    ''' Extract inventory applies search filtering correctly. '''
    inventory_path = get_test_inventory_path( 'sphinxmcps' )
    result = await module.extract_inventory(
        inventory_path, term = 'test' )
    assert 'filters' in result
    assert result[ 'filters' ][ 'term' ] == 'test'


@pytest.mark.asyncio
async def test_140_extract_inventory_with_all_filters( ):
    ''' Extract inventory applies multiple filters correctly. '''
    inventory_path = get_test_inventory_path( 'sphinxmcps' )
    result = await module.extract_inventory(
        inventory_path, domain = 'py', role = 'module', term = 'test' )
    assert 'filters' in result
    filters = result[ 'filters' ]
    assert filters[ 'domain' ] == 'py'
    assert filters[ 'role' ] == 'module'
    assert filters[ 'term' ] == 'test'


@pytest.mark.asyncio
async def test_150_extract_inventory_nonexistent_file( ):
    ''' Extract inventory raises appropriate exception for missing files. '''
    with pytest.raises( _exceptions.ProcessorNotFound ):
        await module.extract_inventory( "/nonexistent/path.inv" )


@pytest.mark.asyncio
async def test_160_extract_inventory_auto_append_objects_inv( ):
    ''' Extract inventory auto-appends objects.inv to URLs/paths. '''
    real_inventory_path = get_test_inventory_path( 'sphinxmcps' )
    inventory_dir = str( Path( real_inventory_path ).parent )
    # Test without objects.inv suffix
    result = await module.extract_inventory( inventory_dir )
    assert 'project' in result
    assert 'objects' in result


@pytest.mark.asyncio
async def test_170_extract_inventory_with_regex_term( ):
    ''' Extract inventory applies regex term filtering correctly. '''
    inventory_path = get_test_inventory_path( 'sphobjinv' )
    # Use regex to find objects containing "inventory"
    result = await module.extract_inventory(
        inventory_path, term = '.*inventory.*',
        match_mode = _interfaces.MatchMode.Regex )
    assert 'filters' in result
    assert result[ 'filters' ][ 'term' ] == '.*inventory.*'
    assert result[ 'filters' ][ 'match_mode' ] == 'regex'
    assert result[ 'object_count' ] > 0


@pytest.mark.asyncio
async def test_180_extract_inventory_with_regex_anchors( ):
    ''' Extract inventory handles regex anchor patterns correctly. '''
    inventory_path = get_test_inventory_path( 'sphobjinv' )
    # Use regex anchors to find objects starting with specific pattern
    result = await module.extract_inventory(
        inventory_path, term = r'^sphobjinv\.',
        match_mode = _interfaces.MatchMode.Regex )
    assert 'filters' in result
    assert result[ 'filters' ][ 'match_mode' ] == 'regex'
    if result[ 'object_count' ] > 0:
        for domain_objects in result[ 'objects' ].values( ):
            for obj in domain_objects:
                assert obj[ 'name' ].startswith( 'sphobjinv.' )


@pytest.mark.asyncio
async def test_190_extract_inventory_invalid_regex( ):
    ''' Extract inventory raises exception for invalid regex patterns. '''
    inventory_path = get_test_inventory_path( 'sphobjinv' )
    with pytest.raises( _exceptions.InventoryFilterInvalidity ):
        await module.extract_inventory(
            inventory_path, term = '[invalid_regex',
            match_mode = _interfaces.MatchMode.Regex )


@pytest.mark.asyncio
async def test_200_summarize_inventory_basic( ):
    ''' Summarize inventory provides human-readable summary. '''
    inventory_path = get_test_inventory_path( 'sphinxmcps' )
    result = await module.summarize_inventory( inventory_path )
    assert 'objects' in result


@pytest.mark.asyncio
async def test_210_summarize_inventory_with_filters( ):
    ''' Summarize inventory includes filter information when provided. '''
    inventory_path = get_test_inventory_path( 'sphinxmcps' )
    result = await module.summarize_inventory( inventory_path, domain = 'py' )
    assert 'objects' in result
    # Should mention filtering was applied
    assert 'filter' in result.lower( ) or 'domain' in result.lower( )


@pytest.mark.asyncio
async def test_215_summarize_inventory_with_regex( ):
    ''' Summarize inventory includes regex filter information. '''
    inventory_path = get_test_inventory_path( 'sphobjinv' )
    # Summarize with regex filter applied
    result = await module.summarize_inventory(
        inventory_path, term = '.*inventory.*',
        match_mode = _interfaces.MatchMode.Regex )
    assert 'objects' in result
    # Should mention regex filtering was applied
    assert 'regex' in result.lower( )


@pytest.mark.asyncio
async def test_220_extract_inventory_with_fuzzy_matching( ):
    ''' Extract inventory applies fuzzy matching correctly. '''
    inventory_path = get_test_inventory_path( 'sphobjinv' )
    # Use fuzzy matching to find objects similar to "DataObj"
    result = await module.extract_inventory(
        inventory_path, term = 'DataObj',
        match_mode = _interfaces.MatchMode.Fuzzy,
        fuzzy_threshold = 50 )
    assert 'filters' in result
    assert result[ 'filters' ][ 'term' ] == 'DataObj'
    assert result[ 'filters' ][ 'match_mode' ] == 'fuzzy'
    assert result[ 'filters' ][ 'fuzzy_threshold' ] == 50
    assert result[ 'object_count' ] > 0


@pytest.mark.asyncio
async def test_230_extract_inventory_fuzzy_with_high_threshold( ):
    ''' Extract inventory with high fuzzy threshold finds fewer matches. '''
    inventory_path = get_test_inventory_path( 'sphobjinv' )
    # Use high threshold for stricter matching
    result_strict = await module.extract_inventory(
        inventory_path, term = 'DataObj',
        match_mode = _interfaces.MatchMode.Fuzzy,
        fuzzy_threshold = 80 )
    # Use low threshold for looser matching
    result_loose = await module.extract_inventory(
        inventory_path, term = 'DataObj',
        match_mode = _interfaces.MatchMode.Fuzzy,
        fuzzy_threshold = 30 )
    # Stricter threshold should find fewer or equal matches
    assert result_strict[ 'object_count' ] <= result_loose[ 'object_count' ]
    assert result_strict[ 'filters' ][ 'fuzzy_threshold' ] == 80
    assert result_loose[ 'filters' ][ 'fuzzy_threshold' ] == 30


@pytest.mark.asyncio
async def test_240_extract_inventory_fuzzy_with_domain_filter( ):
    ''' Extract inventory combines fuzzy matching with domain filtering. '''
    inventory_path = get_test_inventory_path( 'sphobjinv' )
    # Combine fuzzy matching with domain filter
    result = await module.extract_inventory(
        inventory_path,
        domain = 'py',
        term = 'inventory',
        match_mode = _interfaces.MatchMode.Fuzzy,
        fuzzy_threshold = 60 )
    assert 'filters' in result
    assert result[ 'filters' ][ 'domain' ] == 'py'
    assert result[ 'filters' ][ 'match_mode' ] == 'fuzzy'
    # All objects should be from py domain
    if result[ 'object_count' ] > 0:
        assert 'py' in result[ 'objects' ]
        for domain_name in result[ 'objects' ]:
            assert domain_name == 'py'


@pytest.mark.asyncio
async def test_250_summarize_inventory_with_fuzzy( ):
    ''' Summarize inventory includes fuzzy filter information. '''
    inventory_path = get_test_inventory_path( 'sphobjinv' )
    # Summarize with fuzzy filter applied
    result = await module.summarize_inventory(
        inventory_path, term = 'inventory',
        match_mode = _interfaces.MatchMode.Fuzzy,
        fuzzy_threshold = 70 )
    assert 'objects' in result
    # Should mention fuzzy filtering was applied
    assert 'fuzzy' in result.lower( )
    assert '70' in result  # Should show threshold


@pytest.mark.asyncio
async def test_260_match_mode_enum_values( ):
    ''' MatchMode enum has correct string values. '''
    assert _interfaces.MatchMode.Exact.value == 'exact'
    assert _interfaces.MatchMode.Regex.value == 'regex'
    assert _interfaces.MatchMode.Fuzzy.value == 'fuzzy'


@pytest.mark.asyncio
async def test_270_summarize_inventory_nonexistent_file( ):
    ''' Summarize inventory raises appropriate exception for missing files. '''
    with pytest.raises( _exceptions.ProcessorNotFound ):
        await module.summarize_inventory( "/nonexistent/path.inv" )




@pytest.mark.asyncio
async def test_400_extract_inventory_with_priority_filter( ):
    ''' Extract inventory filters objects by priority level. '''
    inventory_path = get_test_inventory_path( 'sphobjinv' )
    result = await module.extract_inventory(
        inventory_path, priority = '1' )
    assert 'filters' in result
    assert result[ 'filters' ][ 'priority' ] == '1'
    assert result[ 'object_count' ] > 0
    for domain_objects in result[ 'objects' ].values( ):
        for obj in domain_objects:
            assert obj[ 'priority' ] == '1'


@pytest.mark.asyncio
async def test_410_extract_inventory_priority_filter_different_values( ):
    ''' Extract inventory works with different priority values. '''
    inventory_path = get_test_inventory_path( 'sphobjinv' )
    result_0 = await module.extract_inventory(
        inventory_path, priority = '0')
    assert result_0[ 'filters' ][ 'priority' ] == '0'
    result_1 = await module.extract_inventory(
        inventory_path, priority = '1' )
    assert result_1[ 'filters' ][ 'priority' ] == '1'
    assert result_0[ 'object_count' ] != result_1[ 'object_count' ]


@pytest.mark.asyncio
async def test_420_extract_inventory_priority_with_domain_filter( ):
    ''' Extract inventory combines priority and domain filtering. '''
    inventory_path = get_test_inventory_path( 'sphobjinv' )
    result = await module.extract_inventory(
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


@pytest.mark.asyncio
async def test_430_summarize_inventory_with_priority( ):
    ''' Summarize inventory includes priority filter information. '''
    inventory_path = get_test_inventory_path( 'sphobjinv' )
    result = await module.summarize_inventory( inventory_path, priority = '1')
    assert 'priority=1' in result
    assert 'Filters:' in result


@pytest.mark.asyncio
async def test_500_query_documentation_basic( ):
    ''' Query documentation returns relevant results for basic queries. '''
    inventory_path = get_test_inventory_path( 'sphobjinv' )
    results = await module.query_documentation( inventory_path, 'inventory' )
    assert isinstance( results, list )
    for result in results:
        assert 'object_name' in result
        assert 'object_type' in result
        assert 'relevance_score' in result
        assert 'url' in result
        assert 'signature' in result
        assert 'description' in result


@pytest.mark.asyncio
async def test_510_query_documentation_with_domain_filter( ):
    ''' Query documentation applies domain filtering correctly. '''
    inventory_path = get_test_inventory_path( 'sphobjinv' )
    results = await module.query_documentation(
        inventory_path, 'inventory', domain = 'py' )
    assert isinstance( results, list )
    for result in results:
        assert result[ 'domain' ] == 'py'


@pytest.mark.asyncio
async def test_520_query_documentation_with_role_filter( ):
    ''' Query documentation applies role filtering correctly. '''
    inventory_path = get_test_inventory_path( 'sphobjinv' )
    results = await module.query_documentation(
        inventory_path, 'inventory', role = 'function' )
    assert isinstance( results, list )
    for result in results:
        assert result[ 'object_type' ] == 'function'


@pytest.mark.asyncio
async def test_530_query_documentation_with_priority_filter( ):
    ''' Query documentation applies priority filtering correctly. '''
    inventory_path = get_test_inventory_path( 'sphobjinv' )
    results = await module.query_documentation(
        inventory_path, 'inventory', priority = '1' )
    assert isinstance( results, list )
    for result in results:
        assert result[ 'priority' ] == '1'


@pytest.mark.asyncio
async def test_540_query_documentation_with_exact_match( ):
    ''' Query documentation uses exact matching when specified. '''
    inventory_path = get_test_inventory_path( 'sphobjinv' )
    results = await module.query_documentation(
        inventory_path, 'inventory',
        match_mode = _interfaces.MatchMode.Exact )
    assert isinstance( results, list )
    for result in results:
        assert 'inventory' in result[ 'object_name' ].lower( )


@pytest.mark.asyncio
async def test_550_query_documentation_with_regex_match( ):
    ''' Query documentation uses regex matching when specified. '''
    inventory_path = get_test_inventory_path( 'sphobjinv' )
    results = await module.query_documentation(
        inventory_path, r'.*inventory.*',
        match_mode = _interfaces.MatchMode.Regex )
    assert isinstance( results, list )
    for result in results:
        assert 'inventory' in result[ 'object_name' ].lower( )


@pytest.mark.asyncio
async def test_560_query_documentation_with_fuzzy_match( ):
    ''' Query documentation uses fuzzy matching when specified. '''
    inventory_path = get_test_inventory_path( 'sphobjinv' )
    results = await module.query_documentation(
        inventory_path, 'inventori',
        match_mode = _interfaces.MatchMode.Fuzzy,
        fuzzy_threshold = 60 )
    assert isinstance( results, list )
    for result in results:
        assert 'inventory' in result[ 'object_name' ].lower( )


@pytest.mark.asyncio
async def test_570_query_documentation_with_max_results( ):
    ''' Query documentation respects max_results parameter. '''
    inventory_path = get_test_inventory_path( 'sphobjinv' )
    results = await module.query_documentation(
        inventory_path, 'inventory', max_results = 3 )
    assert isinstance( results, list )
    assert len( results ) <= 3


@pytest.mark.asyncio
async def test_580_query_documentation_with_snippets_disabled( ):
    ''' Query documentation excludes snippets when disabled. '''
    inventory_path = get_test_inventory_path( 'sphobjinv' )
    results = await module.query_documentation(
        inventory_path, 'inventory', include_snippets = False )
    assert isinstance( results, list )
    for result in results:
        assert result[ 'content_snippet' ] == ''


@pytest.mark.asyncio
async def test_590_query_documentation_with_snippets_enabled( ):
    ''' Query documentation includes snippets when enabled. '''
    inventory_path = get_test_inventory_path( 'sphobjinv' )
    results = await module.query_documentation(
        inventory_path, 'inventory', include_snippets = True )
    assert isinstance( results, list )
    for result in results:
        assert 'content_snippet' in result


@pytest.mark.asyncio
async def test_600_query_documentation_relevance_ranking( ):
    ''' Query documentation returns results sorted by relevance. '''
    inventory_path = get_test_inventory_path( 'sphobjinv' )
    results = await module.query_documentation(
        inventory_path, 'inventory', max_results = 5 )
    assert isinstance( results, list )
    if len( results ) > 1:
        prev_score = results[ 0 ][ 'relevance_score' ]
        for result in results[ 1: ]:
            assert result[ 'relevance_score' ] <= prev_score
            prev_score = result[ 'relevance_score' ]


@pytest.mark.asyncio
async def test_610_query_documentation_combined_filters( ):
    ''' Query documentation applies multiple filters correctly. '''
    inventory_path = get_test_inventory_path( 'sphobjinv' )
    results = await module.query_documentation(
        inventory_path, 'inventory',
        domain = 'py',
        role = 'function',
        priority = '1',
        match_mode = _interfaces.MatchMode.Fuzzy,
        fuzzy_threshold = 70 )
    assert isinstance( results, list )
    for result in results:
        assert result[ 'domain' ] == 'py'
        assert result[ 'object_type' ] == 'function'
        assert result[ 'priority' ] == '1'


@pytest.mark.asyncio
async def test_620_query_documentation_empty_query( ):
    ''' Query documentation handles empty query gracefully. '''
    inventory_path = get_test_inventory_path( 'sphobjinv' )
    results = await module.query_documentation( inventory_path, '' )
    assert isinstance( results, list )


@pytest.mark.asyncio
async def test_630_query_documentation_no_matches( ):
    ''' Query documentation returns empty list when no matches found. '''
    inventory_path = get_test_inventory_path( 'sphobjinv' )
    results = await module.query_documentation(
        inventory_path, 'nonexistent_term_xyz123' )
    assert isinstance( results, list )
    assert len( results ) == 0


@pytest.mark.asyncio
async def test_640_query_documentation_nonexistent_file( ):
    ''' Query documentation handles nonexistent files gracefully. '''
    with pytest.raises( _exceptions.ProcessorNotFound ):
        await module.query_documentation(
            '/nonexistent/path.inv', 'inventory' )


@pytest.mark.asyncio
async def test_650_query_documentation_match_reasons( ):
    ''' Query documentation includes match reasons in results. '''
    inventory_path = get_test_inventory_path( 'sphobjinv' )
    results = await module.query_documentation(
        inventory_path, 'inventory', max_results = 1 )
    assert isinstance( results, list )
    for result in results:
        assert 'match_reasons' in result
        assert isinstance( result[ 'match_reasons' ], list )


@pytest.mark.asyncio
async def test_660_query_documentation_result_structure( ):
    ''' Query documentation returns properly structured results. '''
    inventory_path = get_test_inventory_path( 'sphobjinv' )
    results = await module.query_documentation(
        inventory_path, 'inventory', max_results = 1 )
    assert isinstance( results, list )
    if results:
        result = results[ 0 ]
        required_keys = {
            'object_name', 'object_type', 'domain', 'priority',
            'url', 'signature', 'description', 'content_snippet',
            'relevance_score', 'match_reasons'
        }
        assert all( key in result for key in required_keys )
        assert isinstance( result[ 'relevance_score' ], float )
        assert isinstance( result[ 'match_reasons' ], list )


@pytest.mark.asyncio
async def test_700_extract_documentation_with_object_not_found( ):
    ''' Extract documentation handles object not found gracefully. '''
    inventory_path = get_test_inventory_path( 'sphobjinv' )
    result = await module.extract_documentation(
        inventory_path, 'nonexistent_object' )
    assert 'error' in result
    assert 'not found in inventory' in result[ 'error' ]



@pytest.mark.asyncio
async def test_870_extract_inventory_unsupported_url_scheme( ):
    ''' Extract inventory handles unsupported URL schemes gracefully. '''
    with pytest.raises( _exceptions.ProcessorNotFound ):
        await module.extract_inventory( 'ftp://invalid.com/objects.inv' )
