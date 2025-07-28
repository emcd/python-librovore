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
async def test_100_explore_local_file( ):
    ''' Explore function processes local inventory files. '''
    inventory_path = get_test_inventory_path( 'sphinxmcps' )
    result = await module.explore(
        inventory_path, "", include_documentation = False )
    assert 'project' in result
    assert 'documents' in result


@pytest.mark.asyncio
async def test_110_explore_with_domain_filter( ):
    ''' Explore function applies domain filtering correctly. '''
    inventory_path = get_test_inventory_path( 'sphinxmcps' )
    filters = _interfaces.Filters( domain = 'py' )
    result = await module.explore(
        inventory_path, "", filters = filters, include_documentation = False )
    assert 'search_metadata' in result
    assert result[ 'search_metadata' ][ 'filters' ][ 'domain' ] == 'py'


@pytest.mark.asyncio
async def test_120_explore_with_role_filter( ):
    ''' Explore function applies role filtering correctly. '''
    inventory_path = get_test_inventory_path( 'sphinxmcps' )
    filters = _interfaces.Filters( role = 'module' )
    result = await module.explore(
        inventory_path, "", filters = filters, include_documentation = False )
    assert 'search_metadata' in result
    assert result[ 'search_metadata' ][ 'filters' ][ 'role' ] == 'module'


@pytest.mark.asyncio
async def test_130_explore_with_search_query( ):
    ''' Explore function applies search filtering correctly. '''
    inventory_path = get_test_inventory_path( 'sphinxmcps' )
    result = await module.explore(
        inventory_path, "test", include_documentation = False )
    assert 'search_metadata' in result
    assert result[ 'query' ] == 'test'


@pytest.mark.asyncio
async def test_140_explore_with_all_filters( ):
    ''' Explore function applies multiple filters correctly. '''
    inventory_path = get_test_inventory_path( 'sphinxmcps' )
    filters = _interfaces.Filters( domain = 'py', role = 'module' )
    result = await module.explore(
        inventory_path, "test", filters = filters,
        include_documentation = False )
    assert 'search_metadata' in result
    search_filters = result[ 'search_metadata' ][ 'filters' ]
    assert search_filters[ 'domain' ] == 'py'
    assert search_filters[ 'role' ] == 'module'
    assert result[ 'query' ] == 'test'


@pytest.mark.asyncio
async def test_150_explore_nonexistent_file( ):
    ''' Explore function raises appropriate exception for missing files. '''
    with pytest.raises( _exceptions.ProcessorInavailability ):
        await module.explore(
            "/nonexistent/path.inv", "", include_documentation = False )


@pytest.mark.asyncio
async def test_160_explore_auto_append_objects_inv( ):
    ''' Explore function auto-appends objects.inv to URLs/paths. '''
    real_inventory_path = get_test_inventory_path( 'sphinxmcps' )
    inventory_dir = str( Path( real_inventory_path ).parent )
    result = await module.explore(
        inventory_dir, "", include_documentation = False )
    assert 'project' in result
    assert 'documents' in result


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
    filters = module._interfaces.Filters( domain = 'py' )
    result = await module.summarize_inventory(
        inventory_path, filters = filters )
    assert 'objects' in result
    assert 'filter' in result.lower( ) or 'domain' in result.lower( )


@pytest.mark.asyncio
async def test_215_summarize_inventory_with_regex( ):
    ''' Summarize inventory includes regex filter information. '''
    inventory_path = get_test_inventory_path( 'sphobjinv' )
    filters = module._interfaces.Filters(
        match_mode = _interfaces.MatchMode.Regex )
    result = await module.summarize_inventory(
        inventory_path, '.*inventory.*', filters = filters )
    assert 'objects' in result
    assert 'regex' in result.lower( )


@pytest.mark.asyncio
async def test_250_summarize_inventory_with_fuzzy( ):
    ''' Summarize inventory includes fuzzy filter information. '''
    inventory_path = get_test_inventory_path( 'sphobjinv' )
    filters = module._interfaces.Filters(
        match_mode = _interfaces.MatchMode.Fuzzy, fuzzy_threshold = 70 )
    result = await module.summarize_inventory(
        inventory_path, 'inventory', filters = filters )
    assert 'objects' in result
    assert 'fuzzy' in result.lower( )
    assert '70' in result


@pytest.mark.asyncio
async def test_260_match_mode_enum_values( ):
    ''' MatchMode enum has correct string values. '''
    assert _interfaces.MatchMode.Exact.value == 'exact'
    assert _interfaces.MatchMode.Regex.value == 'regex'
    assert _interfaces.MatchMode.Fuzzy.value == 'fuzzy'


@pytest.mark.asyncio
async def test_270_summarize_inventory_nonexistent_file( ):
    ''' Summarize inventory raises appropriate exception for missing files. '''
    with pytest.raises( _exceptions.ProcessorInavailability ):
        await module.summarize_inventory( "/nonexistent/path.inv" )


@pytest.mark.asyncio
async def test_430_summarize_inventory_with_priority( ):
    ''' Summarize inventory includes priority filter information. '''
    inventory_path = get_test_inventory_path( 'sphobjinv' )
    filters = module._interfaces.Filters( priority = '1' )
    result = await module.summarize_inventory(
        inventory_path, filters = filters )
    assert 'priority=1' in result
    assert 'Filters:' in result


@pytest.mark.asyncio
async def test_500_query_documentation_basic( ):
    ''' Query documentation returns relevant results for basic queries. '''
    inventory_path = get_test_inventory_path( 'sphobjinv' )
    result = await module.query_documentation( inventory_path, 'inventory' )
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
async def test_510_query_documentation_with_domain_filter( ):
    ''' Query documentation applies domain filtering correctly. '''
    inventory_path = get_test_inventory_path( 'sphobjinv' )
    filters = _interfaces.Filters( domain = 'py' )
    result = await module.query_documentation(
        inventory_path, 'inventory', filters = filters )
    assert isinstance( result, dict )
    assert 'documents' in result
    for document in result[ 'documents' ]:
        assert document[ 'domain' ] == 'py'


@pytest.mark.asyncio
async def test_520_query_documentation_with_role_filter( ):
    ''' Query documentation applies role filtering correctly. '''
    inventory_path = get_test_inventory_path( 'sphobjinv' )
    filters = _interfaces.Filters( role = 'function' )
    result = await module.query_documentation(
        inventory_path, 'inventory', filters = filters )
    assert isinstance( result, dict )
    assert 'documents' in result
    for document in result[ 'documents' ]:
        assert document[ 'type' ] == 'function'


@pytest.mark.asyncio
async def test_530_query_documentation_with_priority_filter( ):
    ''' Query documentation applies priority filtering correctly. '''
    inventory_path = get_test_inventory_path( 'sphobjinv' )
    filters = _interfaces.Filters( priority = '1' )
    result = await module.query_documentation(
        inventory_path, 'inventory', filters = filters )
    assert isinstance( result, dict )
    assert 'documents' in result
    for document in result[ 'documents' ]:
        assert document[ 'priority' ] == '1'


@pytest.mark.asyncio
async def test_540_query_documentation_with_exact_match( ):
    ''' Query documentation uses exact matching when specified. '''
    inventory_path = get_test_inventory_path( 'sphobjinv' )
    filters = _interfaces.Filters( match_mode = _interfaces.MatchMode.Exact )
    result = await module.query_documentation(
        inventory_path, 'inventory', filters = filters )
    assert isinstance( result, dict )
    assert 'documents' in result
    for document in result[ 'documents' ]:
        assert 'inventory' in document[ 'name' ].lower( )


@pytest.mark.asyncio
async def test_550_query_documentation_with_regex_match( ):
    ''' Query documentation uses regex matching when specified. '''
    inventory_path = get_test_inventory_path( 'sphobjinv' )
    filters = _interfaces.Filters( match_mode = _interfaces.MatchMode.Regex )
    result = await module.query_documentation(
        inventory_path, r'.*inventory.*', filters = filters )
    assert isinstance( result, dict )
    assert 'documents' in result
    for document in result[ 'documents' ]:
        assert 'inventory' in document[ 'name' ].lower( )


@pytest.mark.asyncio
async def test_560_query_documentation_with_fuzzy_match( ):
    ''' Query documentation uses fuzzy matching when specified. '''
    inventory_path = get_test_inventory_path( 'sphobjinv' )
    filters = _interfaces.Filters(
        match_mode = _interfaces.MatchMode.Fuzzy, fuzzy_threshold = 60 )
    result = await module.query_documentation(
        inventory_path, 'inventori', filters = filters )
    assert isinstance( result, dict )
    assert 'documents' in result
    for document in result[ 'documents' ]:
        assert 'inventory' in document[ 'name' ].lower( )


@pytest.mark.asyncio
async def test_570_query_documentation_with_results_max( ):
    ''' Query documentation respects results_max parameter. '''
    inventory_path = get_test_inventory_path( 'sphobjinv' )
    result = await module.query_documentation(
        inventory_path, 'inventory', results_max = 3 )
    assert isinstance( result, dict )
    assert 'documents' in result
    assert len( result[ 'documents' ] ) <= 3


@pytest.mark.asyncio
async def test_580_query_documentation_with_snippets_disabled( ):
    ''' Query documentation excludes snippets when disabled. '''
    inventory_path = get_test_inventory_path( 'sphobjinv' )
    result = await module.query_documentation(
        inventory_path, 'inventory', include_snippets = False )
    assert isinstance( result, dict )
    assert 'documents' in result
    for document in result[ 'documents' ]:
        assert document[ 'content_snippet' ] == ''


@pytest.mark.asyncio
async def test_590_query_documentation_with_snippets_enabled( ):
    ''' Query documentation includes snippets when enabled. '''
    inventory_path = get_test_inventory_path( 'sphobjinv' )
    result = await module.query_documentation(
        inventory_path, 'inventory', include_snippets = True )
    assert isinstance( result, dict )
    assert 'documents' in result
    for document in result[ 'documents' ]:
        assert 'content_snippet' in document


@pytest.mark.asyncio
async def test_600_query_documentation_relevance_ranking( ):
    ''' Query documentation returns results sorted by relevance. '''
    inventory_path = get_test_inventory_path( 'sphobjinv' )
    result = await module.query_documentation(
        inventory_path, 'inventory', results_max = 5 )
    assert isinstance( result, dict )
    assert 'documents' in result
    if len( result[ 'documents' ] ) > 1:
        prev_score = result[ 'documents' ][ 0 ][ 'relevance_score' ]
        for document in result[ 'documents' ][ 1: ]:
            assert document[ 'relevance_score' ] <= prev_score
            prev_score = document[ 'relevance_score' ]


@pytest.mark.asyncio
async def test_610_query_documentation_combined_filters( ):
    ''' Query documentation applies multiple filters correctly. '''
    inventory_path = get_test_inventory_path( 'sphobjinv' )
    filters = _interfaces.Filters(
        domain = 'py',
        role = 'function',
        priority = '1',
        match_mode = _interfaces.MatchMode.Fuzzy,
        fuzzy_threshold = 70 )
    result = await module.query_documentation(
        inventory_path, 'inventory', filters = filters )
    assert isinstance( result, dict )
    assert 'documents' in result
    for document in result[ 'documents' ]:
        assert document[ 'domain' ] == 'py'
        assert document[ 'type' ] == 'function'
        assert document[ 'priority' ] == '1'


@pytest.mark.asyncio
async def test_620_query_documentation_empty_query( ):
    ''' Query documentation handles empty query gracefully. '''
    inventory_path = get_test_inventory_path( 'sphobjinv' )
    result = await module.query_documentation( inventory_path, '' )
    assert isinstance( result, dict )
    assert 'documents' in result


@pytest.mark.asyncio
async def test_630_query_documentation_no_matches( ):
    ''' Query documentation returns empty list when no matches found. '''
    inventory_path = get_test_inventory_path( 'sphobjinv' )
    result = await module.query_documentation(
        inventory_path, 'nonexistent_term_xyz123' )
    assert isinstance( result, dict )
    assert 'documents' in result
    assert len( result[ 'documents' ] ) == 0


@pytest.mark.asyncio
async def test_640_query_documentation_nonexistent_file( ):
    ''' Query documentation handles nonexistent files gracefully. '''
    with pytest.raises( _exceptions.ProcessorInavailability ):
        await module.query_documentation(
            '/nonexistent/path.inv', 'inventory' )


@pytest.mark.asyncio
async def test_650_query_documentation_match_reasons( ):
    ''' Query documentation includes match reasons in results. '''
    inventory_path = get_test_inventory_path( 'sphobjinv' )
    result = await module.query_documentation(
        inventory_path, 'inventory', results_max = 1 )
    assert isinstance( result, dict )
    assert 'documents' in result
    for document in result[ 'documents' ]:
        assert 'match_reasons' in document
        assert isinstance( document[ 'match_reasons' ], list )


@pytest.mark.asyncio
async def test_660_query_documentation_result_structure( ):
    ''' Query documentation returns properly structured results. '''
    inventory_path = get_test_inventory_path( 'sphobjinv' )
    result = await module.query_documentation(
        inventory_path, 'inventory', results_max = 1 )
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
async def test_700_explore_with_object_not_found( ):
    ''' Explore function handles object not found gracefully. '''
    inventory_path = get_test_inventory_path( 'sphobjinv' )
    result = await module.explore(
        inventory_path, 'nonexistent_object_xyz123', results_max = 1 )
    assert 'documents' in result
    # When no objects are found, documents should be empty
    assert len( result[ 'documents' ] ) == 0
    assert result[ 'search_metadata' ][ 'object_count' ] == 0
