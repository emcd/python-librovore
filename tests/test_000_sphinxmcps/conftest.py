import shutil
from pathlib import Path
import pytest


@pytest.fixture( scope = 'session' )
def cached_inventories( tmp_path_factory ):
    '''
    Session-scoped fixture that copies inventory files to a temp directory.
    This improves test performance by avoiding repeated filesystem access.
    '''
    cache_dir = tmp_path_factory.mktemp( 'inventory_cache' )
    test_data_dir = Path( __file__ ).parent.parent / 'data' / 'inventories'
    
    if test_data_dir.exists( ):
        # Copy all inventory directories to cache
        for site_dir in test_data_dir.iterdir( ):
            if site_dir.is_dir( ):
                dest_dir = cache_dir / site_dir.name
                shutil.copytree( site_dir, dest_dir )
    
    return cache_dir


@pytest.fixture
def fake_fs_with_inventories( fs, cached_inventories ):
    '''
    Fixture that sets up pyfakefs with cached inventory files.
    Provides fast filesystem access for tests.
    '''
    # Create the test data directory structure in fake filesystem
    test_data_dir = Path( __file__ ).parent.parent / 'data' / 'inventories'
    fs.create_dir( test_data_dir )
    
    # Copy cached inventories to fake filesystem
    for site_dir in cached_inventories.iterdir( ):
        if site_dir.is_dir( ):
            dest_dir = test_data_dir / site_dir.name
            fs.create_dir( dest_dir )
            
            # Copy inventory files
            for file_path in site_dir.rglob( '*' ):
                if file_path.is_file( ):
                    relative_path = file_path.relative_to( site_dir )
                    dest_file = dest_dir / relative_path
                    file_stat = file_path.stat( )
                    fs.create_file( dest_file, st_size = file_stat.st_size )
                    fs.create_file( dest_file )
                    # Copy actual file content
                    with (
                        open( file_path, 'rb' ) as src,
                        fs.open( dest_file, 'wb' ) as dst
                    ):
                        dst.write( src.read( ) )
    
    return fs


def pytest_sessionfinish( session, exitstatus ):
    if exitstatus == 5:  # pytest exit code for "no tests collected"
        session.exitstatus = 0
