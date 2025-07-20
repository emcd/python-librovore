''' Test utilities for extension manager testing. '''

import tempfile
from pathlib import Path
from unittest.mock import Mock
from contextlib import contextmanager

@contextmanager
def isolated_cache_directory():
    ''' Create isolated temporary cache directory for testing. '''
    with tempfile.TemporaryDirectory() as temp_dir:
        cache_path = Path( temp_dir )
        yield cache_path

def create_mock_uv_process( returncode=0, stdout=b'', stderr=b'' ):
    ''' Create mock subprocess for uv command testing. '''
    mock_process = Mock()
    mock_process.communicate.return_value = ( stdout, stderr )
    mock_process.returncode = returncode
    return mock_process

def get_fake_extension_url():
    ''' Get file:// URL for fake extension package. '''
    fake_extension_path = (
        Path( __file__ ).parent.parent / "fixtures" / "fake-extension" )
    return f"file://{fake_extension_path.absolute()}"

def get_broken_extension_url():
    ''' Get file:// URL for broken extension package. '''
    broken_extension_path = (
        Path( __file__ ).parent.parent / "fixtures" / "broken-extension" )
    return f"file://{broken_extension_path.absolute()}"

class MockTimeProvider:
    ''' Mock time provider for TTL testing. '''
    
    def __init__( self, initial_time ):
        self.current_time = initial_time
    
    def now( self ):
        return self.current_time
    
    def advance( self, delta ):
        self.current_time += delta