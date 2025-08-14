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
from unittest.mock import Mock

import librovore.functions as module
import librovore.exceptions as _exceptions
import librovore.interfaces as _interfaces

from .fixtures import get_test_inventory_path


@pytest.fixture
def mock_auxdata( ):
    ''' Fixture providing mock auxdata/globals object. '''
    return Mock( )


@pytest.mark.asyncio
async def test_100_explore_local_file( mock_auxdata ):
    ''' Query inventory function processes local inventory files. '''
    inventory_path = get_test_inventory_path( 'librovore' )
    result = await module.query_inventory(
        mock_auxdata, inventory_path, "",
        details = module._interfaces.InventoryQueryDetails.Name )
    assert 'project' in result
    assert 'documents' in result


@pytest.mark.asyncio
async def test_110_explore_with_domain_filter( mock_auxdata ):
    ''' Explore function applies domain filtering correctly. '''
    inventory_path = get_test_inventory_path( 'librovore' )
    search_behaviors = _interfaces.SearchBehaviors( )
    filters = { 'domain': 'py' }
    result = await module.query_inventory(
        mock_auxdata, inventory_path, "",
        search_behaviors = search_behaviors,
        filters = filters,
        details = module._interfaces.InventoryQueryDetails.Name )
    assert 'search_metadata' in result


@pytest.mark.asyncio
async def test_120_explore_with_role_filter( mock_auxdata ):
    ''' Explore function applies role filtering correctly. '''
    inventory_path = get_test_inventory_path( 'librovore' )
    search_behaviors = _interfaces.SearchBehaviors( )
    filters = { 'role': 'module' }
    result = await module.query_inventory(
        mock_auxdata, inventory_path, "",
        search_behaviors = search_behaviors,
        filters = filters,
        details = module._interfaces.InventoryQueryDetails.Name )
    assert 'search_metadata' in result


@pytest.mark.asyncio
async def test_130_explore_with_search_query( mock_auxdata ):
    ''' Explore function applies search filtering correctly. '''
    inventory_path = get_test_inventory_path( 'librovore' )
    result = await module.query_inventory(
        mock_auxdata, inventory_path, "test",
        details = module._interfaces.InventoryQueryDetails.Name )
    assert 'search_metadata' in result
    assert result[ 'query' ] == 'test'


@pytest.mark.asyncio
async def test_140_explore_with_all_filters( mock_auxdata ):
    ''' Explore function applies multiple filters correctly. '''
    inventory_path = get_test_inventory_path( 'librovore' )
    search_behaviors = _interfaces.SearchBehaviors( )
    filters = { 'domain': 'py', 'role': 'module' }
    result = await module.query_inventory(
        mock_auxdata, inventory_path, "test",
        search_behaviors = search_behaviors,
        filters = filters,
        details = module._interfaces.InventoryQueryDetails.Name )
    assert 'search_metadata' in result
    assert result[ 'query' ] == 'test'


@pytest.mark.asyncio
async def test_150_explore_nonexistent_file( mock_auxdata ):
    ''' Explore function raises appropriate exception for missing files. '''
    with pytest.raises( _exceptions.ProcessorInavailability ):
        await module.query_inventory(
            mock_auxdata, "/nonexistent/path.inv", "",
            details = module._interfaces.InventoryQueryDetails.Name )


@pytest.mark.asyncio
async def test_160_explore_auto_append_objects_inv( mock_auxdata ):
    ''' Explore function auto-appends objects.inv to URLs/paths. '''
    real_inventory_path = get_test_inventory_path( 'librovore' )
    inventory_dir = str( Path( real_inventory_path ).parent )
    result = await module.query_inventory(
        mock_auxdata, inventory_dir, "",
        details = module._interfaces.InventoryQueryDetails.Name )
    assert 'project' in result
    assert 'documents' in result


@pytest.mark.asyncio
async def test_200_summarize_inventory_basic( mock_auxdata ):
    ''' Summarize inventory provides structured summary data. '''
    inventory_path = get_test_inventory_path( 'librovore' )
    result = await module.summarize_inventory( mock_auxdata, inventory_path )
    assert 'objects' in result
    assert 'project' in result
    assert 'version' in result
    assert 'objects_count' in result


@pytest.mark.asyncio
async def test_210_summarize_inventory_with_filters( mock_auxdata ):
    ''' Summarize inventory works correctly when filters are provided. '''
    inventory_path = get_test_inventory_path( 'librovore' )
    search_behaviors = _interfaces.SearchBehaviors( )
    filters = { 'domain': 'py' }
    result = await module.summarize_inventory(
        mock_auxdata, inventory_path,
        search_behaviors = search_behaviors,
        filters = filters )
    assert 'objects' in result
    assert 'project' in result


@pytest.mark.asyncio
async def test_215_summarize_inventory_with_regex( mock_auxdata ):
    ''' Summarize inventory works correctly with regex search behaviors. '''
    inventory_path = get_test_inventory_path( 'sphobjinv' )
    search_behaviors = _interfaces.SearchBehaviors(
        match_mode = _interfaces.MatchMode.Regex )
    result = await module.summarize_inventory(
        mock_auxdata, inventory_path, '.*inventory.*',
        search_behaviors = search_behaviors )
    assert 'objects' in result
    assert 'project' in result


@pytest.mark.asyncio
async def test_250_summarize_inventory_with_fuzzy( mock_auxdata ):
    ''' Summarize inventory works correctly with fuzzy search behaviors. '''
    inventory_path = get_test_inventory_path( 'sphobjinv' )
    search_behaviors = _interfaces.SearchBehaviors(
        match_mode = _interfaces.MatchMode.Fuzzy, fuzzy_threshold = 70 )
    result = await module.summarize_inventory(
        mock_auxdata, inventory_path, 'inventory',
        search_behaviors = search_behaviors )
    assert 'objects' in result
    assert 'project' in result


@pytest.mark.asyncio
async def test_260_match_mode_enum_values( ):
    ''' MatchMode enum has correct string values. '''
    assert _interfaces.MatchMode.Exact.value == 'exact'
    assert _interfaces.MatchMode.Regex.value == 'regex'
    assert _interfaces.MatchMode.Fuzzy.value == 'fuzzy'


@pytest.mark.asyncio
async def test_270_summarize_inventory_nonexistent_file( mock_auxdata ):
    ''' Summarize inventory raises appropriate exception for missing files. '''
    with pytest.raises( _exceptions.ProcessorInavailability ):
        await module.summarize_inventory(
            mock_auxdata, "/nonexistent/path.inv" )


@pytest.mark.asyncio
async def test_430_summarize_inventory_with_priority( mock_auxdata ):
    ''' Summarize inventory works correctly with priority filters. '''
    inventory_path = get_test_inventory_path( 'sphobjinv' )
    search_behaviors = _interfaces.SearchBehaviors( )
    filters = { 'priority': '1' }
    result = await module.summarize_inventory(
        mock_auxdata, inventory_path,
        search_behaviors = search_behaviors,
        filters = filters )
    assert 'objects' in result
    assert 'project' in result


@pytest.mark.asyncio
async def test_500_query_documentation_basic( mock_auxdata ):
    ''' Query documentation returns relevant results for basic queries. '''
    inventory_path = get_test_inventory_path( 'sphobjinv' )
    result = await module.query_content(
        mock_auxdata, inventory_path, 'inventory' )
    assert isinstance( result, dict )
    assert 'documents' in result
    assert 'search_metadata' in result
    assert 'query' in result
    for document in result[ 'documents' ]:
        assert 'name' in document
        assert 'type' in document
        assert 'relevance_score' in document
        assert 'url' in document
        assert 'signature' in document
        assert 'description' in document


@pytest.mark.asyncio
async def test_510_query_documentation_with_domain_filter( mock_auxdata ):
    ''' Query documentation applies domain filtering correctly. '''
    inventory_path = get_test_inventory_path( 'sphobjinv' )
    search_behaviors = _interfaces.SearchBehaviors( )
    filters = { 'domain': 'py' }
    result = await module.query_content(
        mock_auxdata, inventory_path, 'inventory',
        search_behaviors = search_behaviors,
        filters = filters )
    assert isinstance( result, dict )
    assert 'documents' in result
    for document in result[ 'documents' ]:
        assert document[ 'domain' ] == 'py'


@pytest.mark.asyncio
async def test_520_query_documentation_with_role_filter( mock_auxdata ):
    ''' Query documentation applies role filtering correctly. '''
    inventory_path = get_test_inventory_path( 'sphobjinv' )
    search_behaviors = _interfaces.SearchBehaviors( )
    filters = { 'role': 'function' }
    result = await module.query_content(
        mock_auxdata, inventory_path, 'inventory',
        search_behaviors = search_behaviors,
        filters = filters )
    assert isinstance( result, dict )
    assert 'documents' in result
    for document in result[ 'documents' ]:
        assert document[ 'type' ] == 'function'


@pytest.mark.asyncio
async def test_530_query_documentation_with_priority_filter( mock_auxdata ):
    ''' Query documentation applies priority filtering correctly. '''
    inventory_path = get_test_inventory_path( 'sphobjinv' )
    search_behaviors = _interfaces.SearchBehaviors( )
    filters = { 'priority': '1' }
    result = await module.query_content(
        mock_auxdata, inventory_path, 'inventory',
        search_behaviors = search_behaviors,
        filters = filters )
    assert isinstance( result, dict )
    assert 'documents' in result
    for document in result[ 'documents' ]:
        assert document[ 'priority' ] == '1'


@pytest.mark.asyncio
async def test_540_query_documentation_with_exact_match( mock_auxdata ):
    ''' Query documentation uses exact matching when specified. '''
    inventory_path = get_test_inventory_path( 'sphobjinv' )
    search_behaviors = _interfaces.SearchBehaviors(
        match_mode = _interfaces.MatchMode.Exact )
    filters = { }
    result = await module.query_content(
        mock_auxdata, inventory_path, 'inventory',
        search_behaviors = search_behaviors,
        filters = filters )
    assert isinstance( result, dict )
    assert 'documents' in result
    for document in result[ 'documents' ]:
        assert 'inventory' in document[ 'name' ].lower( )


@pytest.mark.asyncio
async def test_550_query_documentation_with_regex_match( mock_auxdata ):
    ''' Query documentation uses regex matching when specified. '''
    inventory_path = get_test_inventory_path( 'sphobjinv' )
    search_behaviors = _interfaces.SearchBehaviors(
        match_mode = _interfaces.MatchMode.Regex )
    filters = { }
    result = await module.query_content(
        mock_auxdata, inventory_path, r'.*inventory.*',
        search_behaviors = search_behaviors,
        filters = filters )
    assert isinstance( result, dict )
    assert 'documents' in result
    for document in result[ 'documents' ]:
        assert 'inventory' in document[ 'name' ].lower( )


@pytest.mark.asyncio
async def test_560_query_documentation_with_fuzzy_match( mock_auxdata ):
    ''' Query documentation uses fuzzy matching when specified. '''
    inventory_path = get_test_inventory_path( 'sphobjinv' )
    search_behaviors = _interfaces.SearchBehaviors(
        match_mode = _interfaces.MatchMode.Fuzzy, fuzzy_threshold = 60 )
    filters = { }
    result = await module.query_content(
        mock_auxdata, inventory_path, 'inventori',
        search_behaviors = search_behaviors,
        filters = filters )
    assert isinstance( result, dict )
    assert 'documents' in result
    for document in result[ 'documents' ]:
        assert 'inventory' in document[ 'name' ].lower( )


@pytest.mark.asyncio
async def test_570_query_documentation_with_results_max( mock_auxdata ):
    ''' Query documentation respects results_max parameter. '''
    inventory_path = get_test_inventory_path( 'sphobjinv' )
    result = await module.query_content(
        mock_auxdata, inventory_path, 'inventory', results_max = 3 )
    assert isinstance( result, dict )
    assert 'documents' in result
    assert len( result[ 'documents' ] ) <= 3


@pytest.mark.asyncio
async def test_580_query_documentation_with_snippets_disabled( mock_auxdata ):
    ''' Query documentation excludes snippets when disabled. '''
    inventory_path = get_test_inventory_path( 'sphobjinv' )
    result = await module.query_content(
        mock_auxdata, inventory_path, 'inventory',
        include_snippets = False )
    assert isinstance( result, dict )
    assert 'documents' in result
    for document in result[ 'documents' ]:
        assert document[ 'content_snippet' ] == ''


@pytest.mark.asyncio
async def test_590_query_documentation_with_snippets_enabled( mock_auxdata ):
    ''' Query documentation includes snippets when enabled. '''
    inventory_path = get_test_inventory_path( 'sphobjinv' )
    result = await module.query_content(
        mock_auxdata, inventory_path, 'inventory',
        include_snippets = True )
    assert isinstance( result, dict )
    assert 'documents' in result
    for document in result[ 'documents' ]:
        assert 'content_snippet' in document


@pytest.mark.asyncio
async def test_600_query_documentation_relevance_ranking( mock_auxdata ):
    ''' Query documentation returns results sorted by relevance. '''
    inventory_path = get_test_inventory_path( 'sphobjinv' )
    result = await module.query_content(
        mock_auxdata, inventory_path, 'inventory', results_max = 5 )
    assert isinstance( result, dict )
    assert 'documents' in result
    if len( result[ 'documents' ] ) > 1:
        prev_score = result[ 'documents' ][ 0 ][ 'relevance_score' ]
        for document in result[ 'documents' ][ 1: ]:
            assert document[ 'relevance_score' ] <= prev_score
            prev_score = document[ 'relevance_score' ]


@pytest.mark.asyncio
async def test_610_query_documentation_combined_filters( mock_auxdata ):
    ''' Query documentation applies multiple filters correctly. '''
    inventory_path = get_test_inventory_path( 'sphobjinv' )
    search_behaviors = _interfaces.SearchBehaviors(
        match_mode = _interfaces.MatchMode.Fuzzy, fuzzy_threshold = 70 )
    filters = {
        'domain': 'py', 'role': 'function', 'priority': '1' }
    result = await module.query_content(
        mock_auxdata, inventory_path, 'inventory',
        search_behaviors = search_behaviors,
        filters = filters )
    assert isinstance( result, dict )
    assert 'documents' in result
    for document in result[ 'documents' ]:
        assert document[ 'domain' ] == 'py'
        assert document[ 'type' ] == 'function'
        assert document[ 'priority' ] == '1'


@pytest.mark.asyncio
async def test_620_query_documentation_empty_query( mock_auxdata ):
    ''' Query documentation handles empty query gracefully. '''
    inventory_path = get_test_inventory_path( 'sphobjinv' )
    result = await module.query_content( mock_auxdata, inventory_path, '' )
    assert isinstance( result, dict )
    assert 'documents' in result


@pytest.mark.asyncio
async def test_630_query_documentation_no_matches( mock_auxdata ):
    ''' Query documentation returns empty list when no matches found. '''
    inventory_path = get_test_inventory_path( 'sphobjinv' )
    result = await module.query_content(
        mock_auxdata, inventory_path, 'nonexistent_term_xyz123' )
    assert isinstance( result, dict )
    assert 'documents' in result
    assert len( result[ 'documents' ] ) == 0


@pytest.mark.asyncio
async def test_640_query_documentation_nonexistent_file( mock_auxdata ):
    ''' Query documentation handles nonexistent files gracefully. '''
    with pytest.raises( _exceptions.ProcessorInavailability ):
        await module.query_content(
            mock_auxdata, '/nonexistent/path.inv', 'inventory' )


@pytest.mark.asyncio
async def test_650_query_documentation_match_reasons( mock_auxdata ):
    ''' Query documentation includes match reasons in results. '''
    inventory_path = get_test_inventory_path( 'sphobjinv' )
    result = await module.query_content(
        mock_auxdata, inventory_path, 'inventory', results_max = 1 )
    assert isinstance( result, dict )
    assert 'documents' in result
    for document in result[ 'documents' ]:
        assert 'match_reasons' in document
        assert isinstance( document[ 'match_reasons' ], list )


@pytest.mark.asyncio
async def test_660_query_documentation_result_structure( mock_auxdata ):
    ''' Query documentation returns properly structured results. '''
    inventory_path = get_test_inventory_path( 'sphobjinv' )
    result = await module.query_content(
        mock_auxdata, inventory_path, 'inventory', results_max = 1 )
    assert isinstance( result, dict )
    assert 'documents' in result
    if result[ 'documents' ]:
        document = result[ 'documents' ][ 0 ]
        required_keys = {
            'name', 'type', 'domain', 'priority',
            'url', 'signature', 'description', 'content_snippet',
            'relevance_score', 'match_reasons'
        }
        assert all( key in document for key in required_keys )
        assert isinstance( document[ 'relevance_score' ], float )
        assert isinstance( document[ 'match_reasons' ], list )


@pytest.mark.asyncio
async def test_700_explore_with_object_not_found( mock_auxdata ):
    ''' Explore function handles object not found gracefully. '''
    inventory_path = get_test_inventory_path( 'sphobjinv' )
    result = await module.query_inventory(
        mock_auxdata, inventory_path, 'nonexistent_object_xyz123',
        results_max = 1 )
    assert 'documents' in result
    # When no objects are found, documents should be empty
    assert len( result[ 'documents' ] ) == 0
    assert result[ 'search_metadata' ][ 'objects_count' ] == 0
