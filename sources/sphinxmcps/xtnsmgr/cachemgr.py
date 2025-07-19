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


''' Cache management for extension packages. '''


from . import __


_scribe = __.acquire_scribe( __name__ )


class CacheInfo( __.immut.DataclassObject ):
    ''' Information about a cached extension package. '''

    package_spec: str
    installed_at: __.datetime.datetime
    ttl_hours: int
    platform_id: str
    cache_path: __.Path

    @property
    def is_expired( self ) -> bool:
        ''' Check if cache entry has expired based on TTL. '''
        return (
            __.datetime.datetime.now( ) - self.installed_at
            > __.datetime.timedelta( hours = self.ttl_hours )
        )


def calculate_cache_path( package_spec: str ) -> __.Path:
    ''' Calculate cache path for a package specification. '''
    # Base cache directory
    base_dir = __.Path( '.auxiliary/caches/extensions' )
    
    # Create SHA256 hash of package spec for deterministic path
    hasher = __.hashlib.sha256( )
    hasher.update( package_spec.encode( 'utf-8' ) )
    package_hash = hasher.hexdigest( )
    
    # Platform-specific subdirectory
    platform_id = calculate_platform_id( )
    
    return base_dir / package_hash / platform_id


def calculate_platform_id( ) -> str:
    ''' Calculate platform identifier for package cache paths.

        Format: {python_impl}-{python_ver}--{os_name}--{cpu_arch}

        Examples:
            cpython-3.10--linux--x86_64
            pypy-3.10-7.3--darwin--arm64
    '''
    implementation = __.sys.implementation.name
    version = '.'.join( map( str, __.sys.version_info[ : 2 ] ) )
    implementation_version = ''
    
    # Add implementation-specific version info
    match implementation:
        case 'pypy':
            implementation_version = '-' + '.'.join(
                map( str, __.sys.pypy_version_info[ : 2 ] ) ) # pyright: ignore
        case 'graalpy':
            # TODO: Add GraalVM version when available
            pass
        case _:
            pass
    
    os_name = __.platform.system( ).lower( )
    cpu_architecture = __.platform.machine( ).lower( )
    
    return (
        f"{implementation}-{version}{implementation_version}"
        f"--{os_name}--{cpu_architecture}"
    )


def get_cache_info( package_spec: str ) -> CacheInfo | None:
    ''' Get cache information for a package if it exists. '''
    cache_path = calculate_cache_path( package_spec )
    metadata_file = cache_path / '.cache_metadata.json'
    
    if not metadata_file.exists( ):
        return None
    
    try:
        with metadata_file.open( 'r', encoding = 'utf-8' ) as f:
            metadata = __.json.load( f )
        
        return CacheInfo(
            package_spec = metadata[ 'package_spec' ],
            installed_at = __.datetime.datetime.fromisoformat(
                metadata[ 'installed_at' ]
            ),
            ttl_hours = metadata[ 'ttl_hours' ],
            platform_id = metadata[ 'platform_id' ],
            cache_path = cache_path
        )
    except ( __.json.JSONDecodeError, KeyError, ValueError ) as exc:
        _scribe.warning(
            f"Invalid cache metadata for {package_spec}: {exc}"
        )
        return None


def save_cache_info( cache_info: CacheInfo ) -> None:
    ''' Save cache information to metadata file. '''
    metadata_file = cache_info.cache_path / '.cache_metadata.json'
    metadata_file.parent.mkdir( parents = True, exist_ok = True )
    
    metadata: dict[ str, str | int ] = {
        'package_spec': cache_info.package_spec,
        'installed_at': cache_info.installed_at.isoformat( ),
        'ttl_hours': cache_info.ttl_hours,
        'platform_id': cache_info.platform_id
    }
    
    with metadata_file.open( 'w', encoding = 'utf-8' ) as f:
        __.json.dump( metadata, f, indent = 2 )


def cleanup_expired_caches( ttl_hours: int = 24 ) -> None:
    ''' Remove expired cache entries. '''
    base_dir = __.Path( '.auxiliary/caches/extensions' )
    if not base_dir.exists( ):
        return
    
    for package_dir in base_dir.iterdir( ):
        if not package_dir.is_dir( ):
            continue
        
        for platform_dir in package_dir.iterdir( ):
            if not platform_dir.is_dir( ):
                continue
            
            metadata_file = platform_dir / '.cache_metadata.json'
            if not metadata_file.exists( ):
                continue
            
            try:
                with metadata_file.open( 'r', encoding = 'utf-8' ) as f:
                    metadata = __.json.load( f )
                
                installed_at = __.datetime.datetime.fromisoformat(
                    metadata[ 'installed_at' ]
                )
                cache_ttl = metadata.get( 'ttl_hours', ttl_hours )
                
                if ( __.datetime.datetime.now( ) - installed_at
                     > __.datetime.timedelta( hours = cache_ttl ) ):
                    _scribe.info( f"Removing expired cache: {platform_dir}" )
                    __.subprocess.run(
                        [ 'rm', '-rf', str( platform_dir ) ],
                        check = True
                    )
                
            except ( __.json.JSONDecodeError, KeyError, ValueError,
                    __.subprocess.CalledProcessError ) as exc:
                _scribe.warning( 
                    f"Error processing cache {platform_dir}: {exc}" )


def clear_package_cache( package_spec: str ) -> bool:
    ''' Clear cache for a specific package. Returns True if found. '''
    cache_path = calculate_cache_path( package_spec )
    
    if cache_path.exists( ):
        try:
            __.subprocess.run(
                [ 'rm', '-rf', str( cache_path ) ],
                check = True
            )
        except __.subprocess.CalledProcessError as exc:
            _scribe.error( f"Failed to clear cache for {package_spec}: {exc}" )
            return False
        else:
            _scribe.info( f"Cleared cache for package: {package_spec}" )
            return True
    
    return False