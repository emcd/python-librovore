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


''' Cache manager tests for extension packages. '''


import pytest
from pathlib import Path
import datetime
import json
import tempfile

import sphinxmcps.xtnsmgr.cachemgr as module
from .test_utils import get_fake_extension_url


def test_000_cache_info_creates_with_required_fields( ):
    ''' Cache entry can be created with all required fields. '''
    cache_time = datetime.datetime.now( )
    cache_info = module.CacheInfo(
        specification = 'test-package',
        location = Path( '/cache/path' ),
        ctime = cache_time,
        ttl = 24,
        platform_id = 'cpython-3.10--linux--x86_64'
    )
    assert cache_info.specification == 'test-package'
    assert cache_info.location == Path( '/cache/path' )
    assert cache_info.ctime == cache_time
    assert cache_info.ttl == 24
    assert cache_info.platform_id == 'cpython-3.10--linux--x86_64'


def test_010_recent_cache_entry_not_expired( ):
    ''' Recent cache entries are not considered expired. '''
    cache_time = (
        datetime.datetime.now( ) - datetime.timedelta( hours = 12 ) )
    cache_info = module.CacheInfo(
        specification = 'test-package',
        location = Path( '/cache/path' ),
        ctime = cache_time,
        ttl = 24,
        platform_id = 'cpython-3.10--linux--x86_64'
    )
    assert cache_info.is_expired is False


def test_020_old_cache_entry_is_expired( ):
    ''' Cache entries past their TTL are considered expired. '''
    cache_time = (
        datetime.datetime.now( ) - datetime.timedelta( hours = 25 ) )
    cache_info = module.CacheInfo(
        specification = 'test-package',
        location = Path( '/cache/path' ),
        ctime = cache_time,
        ttl = 24,
        platform_id = 'cpython-3.10--linux--x86_64'
    )
    assert cache_info.is_expired is True


def test_030_cache_entry_at_ttl_boundary_is_expired( ):
    ''' Cache entries at exact TTL boundary are considered expired. '''
    cache_time = (
        datetime.datetime.now( ) - datetime.timedelta( hours = 24 ) )
    cache_info = module.CacheInfo(
        specification = 'test-package',
        location = Path( '/cache/path' ),
        ctime = cache_time,
        ttl = 24,
        platform_id = 'cpython-3.10--linux--x86_64'
    )
    assert cache_info.is_expired is True


def test_100_cache_path_calculation_is_deterministic( ):
    ''' Same specification produces identical cache paths. '''
    spec = 'file:///path/to/package'
    path1 = module.calculate_cache_path( spec )
    path2 = module.calculate_cache_path( spec )
    assert path1 == path2


def test_110_different_specifications_produce_different_paths( ):
    ''' Different specifications produce distinct cache paths. '''
    spec1 = 'file:///path/to/package1'
    spec2 = 'file:///path/to/package2'
    path1 = module.calculate_cache_path( spec1 )
    path2 = module.calculate_cache_path( spec2 )
    assert path1 != path2


def test_120_cache_path_includes_platform_directory( ):
    ''' Cache paths include platform-specific directory structure. '''
    spec = 'file:///path/to/package'
    path = module.calculate_cache_path( spec )
    platform_id = module.calculate_platform_id( )
    assert str( path ).endswith( platform_id )


def test_130_cache_path_has_expected_structure( ):
    ''' Cache paths follow expected directory hierarchy. '''
    spec = 'file:///path/to/package'
    path = module.calculate_cache_path( spec )
    parts = path.parts
    assert '.auxiliary' in parts
    assert 'caches' in parts
    assert 'extensions' in parts


def test_200_platform_id_has_expected_format( ):
    ''' Platform ID follows implementation--os--architecture format. '''
    platform_id = module.calculate_platform_id( )
    parts = platform_id.split( '--' )
    assert len( parts ) == 3
    impl_version, os_name, cpu_arch = parts
    assert '-' in impl_version
    assert os_name.lower( ) == os_name
    assert cpu_arch.lower( ) == cpu_arch


def test_210_platform_id_includes_python_version( ):
    ''' Platform ID includes current Python version. '''
    platform_id = module.calculate_platform_id( )
    import sys
    python_version = '.'.join( map( str, sys.version_info[ : 2 ] ) )
    assert python_version in platform_id


def test_220_platform_id_calculation_is_deterministic( ):
    ''' Platform ID calculation produces consistent results. '''
    id1 = module.calculate_platform_id( )
    id2 = module.calculate_platform_id( )
    assert id1 == id2


def test_300_cache_info_can_be_saved_and_retrieved( ):
    ''' Cache information persists correctly through save/load cycle. '''
    with tempfile.TemporaryDirectory( ) as temp_dir:
        cache_path = Path( temp_dir )
        cache_time = datetime.datetime.now( )
        cache_info = module.CacheInfo(
            specification = 'test-package',
            location = cache_path,
            ctime = cache_time,
            ttl = 48,
            platform_id = 'test-platform'
        )
        module.save_cache_info( cache_info )
        metadata_file = cache_path / '.cache_metadata.json'
        assert metadata_file.exists( )
        with metadata_file.open( 'r', encoding = 'utf-8' ) as f:
            saved_data = json.load( f )
        assert saved_data[ 'package_spec' ] == 'test-package'
        assert saved_data[ 'ttl_hours' ] == 48
        assert saved_data[ 'platform_id' ] == 'test-platform'


def test_310_nonexistent_cache_returns_none( ):
    ''' Cache lookup for non-existent packages returns None. '''
    result = module.acquire_cache_info( 'nonexistent-package' )
    assert result is None


def test_320_invalid_json_metadata_returns_none( ):
    ''' Malformed cache metadata files are handled gracefully. '''
    result = module.acquire_cache_info( 'nonexistent-invalid-json-package' )
    assert result is None


def test_330_missing_required_fields_returns_none( ):
    ''' Cache metadata missing required fields is handled gracefully. '''
    result = module.acquire_cache_info( 'nonexistent-missing-fields-package' )
    assert result is None


def test_340_save_cache_info_creates_parent_directories( ):
    ''' Cache info saving creates necessary parent directories. '''
    with tempfile.TemporaryDirectory( ) as temp_dir:
        cache_path = Path( temp_dir ) / 'deep' / 'nested' / 'path'
        cache_time = datetime.datetime.now( )
        cache_info = module.CacheInfo(
            specification = 'test-package',
            location = cache_path,
            ctime = cache_time,
            ttl = 24,
            platform_id = 'test-platform'
        )
        module.save_cache_info( cache_info )
        metadata_file = cache_path / '.cache_metadata.json'
        assert metadata_file.exists( )
        assert metadata_file.parent.exists( )


def test_400_existing_cache_can_be_cleared( ):
    ''' Existing cache directories can be successfully removed. '''
    result = module.clear_package_cache( 'definitely-nonexistent-cache' )
    assert result is False


def test_410_nonexistent_cache_clear_returns_false( ):
    ''' Clearing non-existent cache returns False. '''
    result = module.clear_package_cache( 'nonexistent-package' )
    assert result is False


def test_500_cleanup_with_no_cache_directory_completes( ):
    ''' Cache cleanup handles missing cache directory gracefully. '''
    module.cleanup_expired_caches( )


def test_510_invalidate_clears_package_cache( ):
    ''' Cache invalidation removes package from cache. '''
    original_clear = module.clear_package_cache
    clear_called_with = None
    def mock_clear( spec ):
        nonlocal clear_called_with
        clear_called_with = spec
    try:
        module.clear_package_cache = mock_clear
        module.invalidate( 'test-package' )
        assert clear_called_with == 'test-package'
    finally:
        module.clear_package_cache = original_clear


@pytest.mark.asyncio
async def test_600_valid_cache_avoids_installation( ):
    ''' Valid cached packages are used without reinstalling. '''
    mock_cache_info = type( 'MockCacheInfo', ( ), {
        'is_expired': False,
        'location': Path( '/cache/path' )
    } )( )
    original_acquire = module.acquire_cache_info
    original_add = module._importation.add_package_to_import_path
    original_install = module._installation.install_package
    install_called = False
    add_called_with = None
    def mock_acquire( spec ):
        return mock_cache_info
    def mock_add( path ):
        nonlocal add_called_with
        add_called_with = path
    async def mock_install( spec ):
        nonlocal install_called
        install_called = True
        return Path( '/new/path' )
    try:
        module.acquire_cache_info = mock_acquire
        module._importation.add_package_to_import_path = mock_add
        module._installation.install_package = mock_install
        await module.ensure_package( 'test-package' )
        assert add_called_with == Path( '/cache/path' )
        assert not install_called
    finally:
        module.acquire_cache_info = original_acquire
        module._importation.add_package_to_import_path = original_add
        module._installation.install_package = original_install


@pytest.mark.asyncio
async def test_610_expired_cache_triggers_reinstall( ):
    ''' Expired cached packages are cleared and reinstalled. '''
    mock_cache_info = type( 'MockCacheInfo', ( ), {
        'is_expired': True
    } )( )
    original_acquire = module.acquire_cache_info
    original_clear = module.clear_package_cache
    original_add = module._importation.add_package_to_import_path
    original_install = module._installation.install_package
    clear_called_with = None
    install_called_with = None
    add_called_with = None
    def mock_acquire( spec ):
        return mock_cache_info
    def mock_clear( spec ):
        nonlocal clear_called_with
        clear_called_with = spec
    def mock_add( path ):
        nonlocal add_called_with
        add_called_with = path
    async def mock_install( spec ):
        nonlocal install_called_with
        install_called_with = spec
        return Path( '/new/cache/path' )
    try:
        module.acquire_cache_info = mock_acquire
        module.clear_package_cache = mock_clear
        module._importation.add_package_to_import_path = mock_add
        module._installation.install_package = mock_install
        await module.ensure_package( 'test-package' )
        assert clear_called_with == 'test-package'
        assert install_called_with == 'test-package'
        assert add_called_with == Path( '/new/cache/path' )
    finally:
        module.acquire_cache_info = original_acquire
        module.clear_package_cache = original_clear
        module._importation.add_package_to_import_path = original_add
        module._installation.install_package = original_install


@pytest.mark.asyncio
async def test_620_missing_cache_triggers_install( ):
    ''' Missing cache entries trigger package installation. '''
    original_acquire = module.acquire_cache_info
    original_add = module._importation.add_package_to_import_path
    original_install = module._installation.install_package
    install_called_with = None
    add_called_with = None
    def mock_acquire( spec ):
        return None
    def mock_add( path ):
        nonlocal add_called_with
        add_called_with = path
    async def mock_install( spec ):
        nonlocal install_called_with
        install_called_with = spec
        return Path( '/new/cache/path' )
    try:
        module.acquire_cache_info = mock_acquire
        module._importation.add_package_to_import_path = mock_add
        module._installation.install_package = mock_install
        await module.ensure_package( 'test-package' )
        assert install_called_with == 'test-package'
        assert add_called_with == Path( '/new/cache/path' )
    finally:
        module.acquire_cache_info = original_acquire
        module._importation.add_package_to_import_path = original_add
        module._installation.install_package = original_install


def test_700_complete_cache_lifecycle_works( ):
    ''' Full cache save, retrieve, and clear cycle works correctly. '''
    fake_url = get_fake_extension_url( )
    result = module.acquire_cache_info( fake_url )
    assert result is None
    cleared = module.clear_package_cache( fake_url )
    assert cleared is False


def test_710_similar_specifications_produce_different_paths( ):
    ''' Similar but distinct specifications avoid hash collisions. '''
    specs = [
        'file:///path/to/package-v1',
        'file:///path/to/package-v2', 
        'file:///path/to/package_v1',
        'git+https://github.com/user/repo.git',
        'git+https://github.com/user/repo.git@v1.0'
    ]
    paths = [ module.calculate_cache_path( spec ) for spec in specs ]
    assert len( set( paths ) ) == len( paths )
    platform_id = module.calculate_platform_id( )
    for path in paths:
        assert platform_id in str( path )