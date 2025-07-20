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
from unittest.mock import patch, Mock
from pathlib import Path
import datetime
import json
import tempfile

import sphinxmcps.xtnsmgr.cachemgr as module
from .test_utils import get_fake_extension_url


def test_000_cache_info_creation( ):
    ''' CacheInfo creates with required fields. '''
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


def test_010_cache_info_not_expired( ):
    ''' Recent cache entry is not expired. '''
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


def test_020_cache_info_expired( ):
    ''' Old cache entry is expired. '''
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


def test_030_cache_info_expired_edge_case( ):
    ''' Cache entry at exact TTL boundary is expired. '''
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


def test_100_calculate_cache_path_deterministic( ):
    ''' Cache path calculation is deterministic for same specification. '''
    spec = 'file:///path/to/package'
    path1 = module.calculate_cache_path( spec )
    path2 = module.calculate_cache_path( spec )
    assert path1 == path2


def test_110_calculate_cache_path_different_specs( ):
    ''' Different specifications produce different cache paths. '''
    spec1 = 'file:///path/to/package1'
    spec2 = 'file:///path/to/package2'
    path1 = module.calculate_cache_path( spec1 )
    path2 = module.calculate_cache_path( spec2 )
    assert path1 != path2


def test_120_calculate_cache_path_includes_platform( ):
    ''' Cache path includes platform-specific directory. '''
    spec = 'file:///path/to/package'
    path = module.calculate_cache_path( spec )
    platform_id = module.calculate_platform_id( )
    assert str( path ).endswith( platform_id )


def test_130_calculate_cache_path_structure( ):
    ''' Cache path has expected structure. '''
    spec = 'file:///path/to/package'
    path = module.calculate_cache_path( spec )
    parts = path.parts
    assert '.auxiliary' in parts
    assert 'caches' in parts
    assert 'extensions' in parts


def test_200_calculate_platform_id_format( ):
    ''' Platform ID has expected format. '''
    platform_id = module.calculate_platform_id( )
    parts = platform_id.split( '--' )
    assert len( parts ) == 3
    impl_version, os_name, cpu_arch = parts
    assert '-' in impl_version  # Contains implementation-version
    assert os_name.lower( ) == os_name  # Lowercase
    assert cpu_arch.lower( ) == cpu_arch  # Lowercase


def test_210_calculate_platform_id_includes_python_version( ):
    ''' Platform ID includes Python version. '''
    platform_id = module.calculate_platform_id( )
    import sys
    python_version = '.'.join( map( str, sys.version_info[ : 2 ] ) )
    assert python_version in platform_id


def test_220_calculate_platform_id_deterministic( ):
    ''' Platform ID calculation is deterministic. '''
    id1 = module.calculate_platform_id( )
    id2 = module.calculate_platform_id( )
    assert id1 == id2


def test_300_save_and_acquire_cache_info( ):
    ''' Cache info can be saved and retrieved. '''
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
        
        # Mock calculate_cache_path to return our temp directory
        with patch.object(
            module, 'calculate_cache_path', return_value = cache_path ):
            retrieved = module.acquire_cache_info( 'test-package' )
            assert retrieved is not None
            assert retrieved.specification == 'test-package'
            assert retrieved.ttl == 48
            assert retrieved.platform_id == 'test-platform'
            # Time comparison with tolerance for serialization precision
            time_diff = abs(
                ( retrieved.ctime - cache_time ).total_seconds( ) )
            assert time_diff < 1


def test_310_acquire_cache_info_nonexistent( ):
    ''' Non-existent cache returns None. '''
    result = module.acquire_cache_info( 'nonexistent-package' )
    assert result is None


def test_320_acquire_cache_info_invalid_json( ):
    ''' Invalid JSON metadata returns None with warning. '''
    with tempfile.TemporaryDirectory( ) as temp_dir:
        cache_path = Path( temp_dir )
        metadata_file = cache_path / '.cache_metadata.json'
        
        # Create invalid JSON
        with metadata_file.open( 'w' ) as f:
            f.write( '{ invalid json' )
        
        with patch.object(
            module, 'calculate_cache_path', return_value = cache_path ):
            result = module.acquire_cache_info( 'test-package' )
            assert result is None


def test_330_acquire_cache_info_missing_fields( ):
    ''' Missing required fields in metadata returns None. '''
    with tempfile.TemporaryDirectory( ) as temp_dir:
        cache_path = Path( temp_dir )
        metadata_file = cache_path / '.cache_metadata.json'
        
        # Create metadata missing required fields
        metadata = { 'package_spec': 'test-package' }  # Missing other fields
        with metadata_file.open( 'w' ) as f:
            json.dump( metadata, f )
        
        with patch.object(
            module, 'calculate_cache_path', return_value = cache_path ):
            result = module.acquire_cache_info( 'test-package' )
            assert result is None


def test_340_save_cache_info_creates_directories( ):
    ''' save_cache_info creates parent directories if needed. '''
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


def test_400_clear_package_cache_existing( ):
    ''' Clearing existing package cache returns True. '''
    with tempfile.TemporaryDirectory( ) as temp_dir:
        cache_path = Path( temp_dir )
        cache_path.mkdir( parents = True, exist_ok = True )
        ( cache_path / 'test_file.txt' ).touch( )
        
        with patch.object(
            module, 'calculate_cache_path', return_value = cache_path ):
            result = module.clear_package_cache( 'test-package' )
            assert result is True
            assert not cache_path.exists( )


def test_410_clear_package_cache_nonexistent( ):
    ''' Clearing non-existent package cache returns False. '''
    with patch.object(
        module, 'calculate_cache_path',
        return_value = Path( '/nonexistent/path' )
    ):
        result = module.clear_package_cache( 'nonexistent-package' )
        assert result is False


def test_420_clear_package_cache_permission_error( ):
    ''' Permission error during cache clear returns False. '''
    with patch.object(
        module, 'calculate_cache_path', return_value = Path( '/fake/path' )
    ), patch.object(
        module.__.shutil, 'rmtree',
        side_effect = OSError( "Permission denied" )
    ):
        result = module.clear_package_cache( 'test-package' )
        assert result is False


def test_500_cleanup_expired_caches_no_directory( ):
    ''' Cleanup with no cache directory completes successfully. '''
    with patch.object(
        module.__, 'Path',
        return_value = Mock( exists = Mock( return_value = False ) )
    ):
        module.cleanup_expired_caches( )  # Should not raise


def test_510_invalidate_calls_clear_cache( ):
    ''' Invalidate function calls clear_package_cache. '''
    with patch.object( module, 'clear_package_cache' ) as mock_clear:
        module.invalidate( 'test-package' )
        mock_clear.assert_called_once_with( 'test-package' )


@pytest.mark.asyncio
async def test_600_ensure_package_cache_hit( ):
    ''' Ensure package uses cache when available and valid. '''
    mock_cache_info = Mock( )
    mock_cache_info.is_expired = False
    mock_cache_info.location = Path( '/cache/path' )
    
    with patch.object(
        module, 'acquire_cache_info', return_value = mock_cache_info
    ), patch.object(
        module._importation, 'add_package_to_import_path'
    ) as mock_add, patch.object(
        module._installation, 'install_package'
    ) as mock_install:
        
        await module.ensure_package( 'test-package' )
        
        mock_add.assert_called_once_with( Path( '/cache/path' ) )
        mock_install.assert_not_called( )


@pytest.mark.asyncio
async def test_610_ensure_package_expired_cache( ):
    ''' Ensure package clears expired cache and reinstalls. '''
    mock_cache_info = Mock( )
    mock_cache_info.is_expired = True
    cache_path = Path( '/new/cache/path' )
    
    with patch.object(
        module, 'acquire_cache_info', return_value = mock_cache_info
    ), patch.object(
        module, 'clear_package_cache'
    ) as mock_clear, patch.object(
        module._installation, 'install_package', return_value = cache_path
    ) as mock_install, patch.object(
        module._importation, 'add_package_to_import_path'
    ) as mock_add:
        
        await module.ensure_package( 'test-package' )
        
        mock_clear.assert_called_once_with( 'test-package' )
        mock_install.assert_called_once_with( 'test-package' )
        mock_add.assert_called_once_with( cache_path )


@pytest.mark.asyncio
async def test_620_ensure_package_no_cache( ):
    ''' Ensure package installs when no cache exists. '''
    cache_path = Path( '/new/cache/path' )
    
    with patch.object(
        module, 'acquire_cache_info', return_value = None
    ), patch.object(
        module._installation, 'install_package', return_value = cache_path
    ) as mock_install, patch.object(
        module._importation, 'add_package_to_import_path'
    ) as mock_add:
        
        await module.ensure_package( 'test-package' )
        
        mock_install.assert_called_once_with( 'test-package' )
        mock_add.assert_called_once_with( cache_path )


def test_700_full_cache_cycle( ):
    ''' Complete cache save, retrieve, and clear cycle. '''
    fake_url = get_fake_extension_url( )
    
    with tempfile.TemporaryDirectory( ) as temp_dir, patch.object(
        module, 'calculate_cache_path', return_value = Path( temp_dir )
    ):
        # Save cache info
        cache_time = datetime.datetime.now( )
        cache_info = module.CacheInfo(
            specification = fake_url,
            location = Path( temp_dir ),
            ctime = cache_time,
            ttl = 24,
            platform_id = module.calculate_platform_id( )
        )
        module.save_cache_info( cache_info )
        
        # Retrieve cache info
        retrieved = module.acquire_cache_info( fake_url )
        assert retrieved is not None
        assert retrieved.specification == fake_url
        assert not retrieved.is_expired
        
        # Clear cache
        result = module.clear_package_cache( fake_url )
        assert result is True
        
        # Verify cache is gone
        retrieved_after_clear = module.acquire_cache_info( fake_url )
        assert retrieved_after_clear is None


def test_710_cache_path_collision_resistance( ):
    ''' Different but similar specifications produce different paths. '''
    specs = [
        'file:///path/to/package-v1',
        'file:///path/to/package-v2', 
        'file:///path/to/package_v1',
        'git+https://github.com/user/repo.git',
        'git+https://github.com/user/repo.git@v1.0'
    ]
    
    paths = [ module.calculate_cache_path( spec ) for spec in specs ]
    
    # All paths should be unique
    assert len( set( paths ) ) == len( paths )
    
    # All paths should include platform ID
    platform_id = module.calculate_platform_id( )
    for path in paths:
        assert platform_id in str( path )