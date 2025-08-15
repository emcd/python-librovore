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

from .fixtures import get_test_inventory_path, get_test_site_path


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
    site_url = get_test_site_path( 'librovore' )
    result = await module.query_content(
        mock_auxdata, site_url, 'inventory' )
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
async def test_640_query_documentation_nonexistent_file( mock_auxdata ):
    ''' Query documentation handles nonexistent files gracefully. '''
    with pytest.raises( _exceptions.ProcessorInavailability ):
        await module.query_content(
            mock_auxdata, '/nonexistent/path.inv', 'inventory' )


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


def test_800_validate_extraction_results_no_objects( ):
    ''' Validation passes when no objects are requested. '''
    results = [ ]
    requested_objects = [ ]
    # Should not raise any exception
    module._validate_extraction_results(
        results, requested_objects, 'test_processor', 'test_source' )


def test_801_validate_extraction_results_no_content( ):
    ''' Validation raises StructureIncompatibility when no content. '''
    results = [ ]
    requested_objects = [ { 'name': 'test_obj' } ]
    with pytest.raises( _exceptions.StructureIncompatibility ) as exc_info:
        module._validate_extraction_results(
            results, requested_objects, 'test_processor', 'test_source' )
    assert exc_info.value.processor_name == 'test_processor'
    assert exc_info.value.source == 'test_source'


def test_802_validate_extraction_results_meaningful_content( ):
    ''' Validation passes when meaningful content is extracted. '''
    results = [
        { 'signature': 'def example()', 'description': 'Example function' },
        { 'signature': 'class TestClass', 'description': 'Test class' },
    ]
    requested_objects = [
        { 'name': 'example' },
        { 'name': 'TestClass' },
    ]
    # Should not raise any exception
    module._validate_extraction_results(
        results, requested_objects, 'test_processor', 'test_source' )


def test_803_validate_extraction_results_low_success_rate( ):
    ''' Validation raises ContentExtractFailure when success rate too low. '''
    results = [
        { 'signature': '', 'description': '' },  # Empty content
        { 'signature': '', 'description': '' },  # Empty content
        { 'signature': 'def good()', 'description': 'Good function' },
    ]
    requested_objects = [
        { 'name': 'bad1' },
        { 'name': 'bad2' },
        { 'name': 'good' },
        { 'name': 'bad3' },
        { 'name': 'bad4' },
        { 'name': 'bad5' },
        { 'name': 'bad6' },
        { 'name': 'bad7' },
        { 'name': 'bad8' },
        { 'name': 'bad9' },
        { 'name': 'bad10' },  # 11 total objects, 1 meaningful = 9% < 10%
    ]
    with pytest.raises( _exceptions.ContentExtractFailure ) as exc_info:
        module._validate_extraction_results(
            results, requested_objects, 'test_processor', 'test_source' )
    assert exc_info.value.processor_name == 'test_processor'
    assert exc_info.value.source == 'test_source'
    assert exc_info.value.meaningful_results == 1
    assert exc_info.value.requested_objects == 11


def test_804_validate_extraction_results_edge_case_success_rate( ):
    ''' Validation passes when success rate exactly meets threshold. '''
    results = [
        { 'signature': 'def good()', 'description': '' },  # Meaningful
    ]
    requested_objects = [
        { 'name': 'good' },
        { 'name': 'bad1' },
        { 'name': 'bad2' },
        { 'name': 'bad3' },
        { 'name': 'bad4' },
        { 'name': 'bad5' },
        { 'name': 'bad6' },
        { 'name': 'bad7' },
        { 'name': 'bad8' },
        { 'name': 'bad9' },  # 10 total objects, 1 meaningful = 10% = threshold
    ]
    # Should not raise any exception
    module._validate_extraction_results(
        results, requested_objects, 'test_processor', 'test_source' )

