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
from . import importation as _importation
from . import installation as _installation
from .. import exceptions as _exceptions


_scribe = __.acquire_scribe( __name__ )


class CacheInfo( __.immut.DataclassObject ):
    ''' Information about cached extension package. '''

    specification: str
    location: __.Path
    ctime: __.datetime.datetime
    ttl: int # hours
    platform_id: str

    @property
    def is_expired( self ) -> bool:
        ''' Checks if cache entry has expired. '''
        return (
            __.datetime.datetime.now( ) - self.ctime
            > __.datetime.timedelta( hours = self.ttl )
        )


def calculate_cache_path( specification: str ) -> __.Path:
    ''' Calculates cache path for package specification. '''
    base_dir = __.Path( '.auxiliary/caches/extensions' )
    hasher = __.hashlib.sha256( )
    hasher.update( specification.encode( 'utf-8' ) )
    package_hash = hasher.hexdigest( )
    platform_id = calculate_platform_id( )
    return base_dir / package_hash / platform_id


def calculate_platform_id( ) -> str:
    ''' Calculates platform identifier for package cache paths.

        Format: {python_impl}-{python_ver}--{os_name}--{cpu_arch}

        Examples:
            cpython-3.10--linux--x86_64
            pypy-3.10-7.3--darwin--arm64
    '''
    implementation = __.sys.implementation.name
    version = '.'.join( map( str, __.sys.version_info[ : 2 ] ) )
    implementation_version = ''
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
        f"--{os_name}--{cpu_architecture}" )


def acquire_cache_info( specification: str ) -> CacheInfo | None:
    ''' Acquires cache information for a package, if it exists. '''
    cache_path = calculate_cache_path( specification )
    metadata_file = cache_path / '.cache_metadata.json'
    if not metadata_file.exists( ): return None
    try:
        with metadata_file.open( 'r', encoding = 'utf-8' ) as f:
            metadata = __.json.load( f )
        return CacheInfo(
            specification = metadata[ 'package_spec' ],
            ctime = __.datetime.datetime.fromisoformat(
                metadata[ 'installed_at' ]
            ),
            ttl = metadata[ 'ttl_hours' ],
            platform_id = metadata[ 'platform_id' ],
            location = cache_path )
    except ( __.json.JSONDecodeError, KeyError, ValueError ) as exc:
        _scribe.warning(
            f"Invalid cache metadata for {specification}: {exc}" )
        return None


def save_cache_info( cache_info: CacheInfo ) -> None:
    ''' Saves cache information to metadata file. '''
    metadata_file = cache_info.location / '.cache_metadata.json'
    metadata_file.parent.mkdir( parents = True, exist_ok = True )
    metadata: dict[ str, str | int ] = {
        'package_spec': cache_info.specification,
        'installed_at': cache_info.ctime.isoformat( ),
        'ttl_hours': cache_info.ttl,
        'platform_id': cache_info.platform_id
    }
    with metadata_file.open( 'w', encoding = 'utf-8' ) as f:
        __.json.dump( metadata, f, indent = 2 )


def cleanup_expired_caches( ttl: int = 24 ) -> None:
    ''' Removes expired cache entries. '''
    base_dir = __.Path( '.auxiliary/caches/extensions' )
    if not base_dir.exists( ): return
    for package_dir in base_dir.iterdir( ):
        if not package_dir.is_dir( ): continue
        for platform_dir in package_dir.iterdir( ):
            if not platform_dir.is_dir( ): continue
            metadata_file = platform_dir / '.cache_metadata.json'
            if not metadata_file.exists( ): continue
            try:
                with metadata_file.open( 'r', encoding = 'utf-8' ) as f:
                    metadata = __.json.load( f )
                installed_at = __.datetime.datetime.fromisoformat(
                    metadata[ 'installed_at' ] )
                cache_ttl = metadata.get( 'ttl_hours', ttl )
                if ( __.datetime.datetime.now( ) - installed_at
                     > __.datetime.timedelta( hours = cache_ttl )
                ):
                    _scribe.info( f"Removing expired cache: {platform_dir}" )
                    __.shutil.rmtree( platform_dir )
            except (
                KeyError, ValueError,
                __.json.JSONDecodeError,
                OSError,
            ) as exc:
                _scribe.warning(
                    f"Error processing cache {platform_dir}: {exc}" )


def clear_package_cache( specification: str ) -> bool:
    ''' Clears cache for specific package. Returns True if found. '''
    cache_path = calculate_cache_path( specification )
    if cache_path.exists( ):
        try:
            __.shutil.rmtree( cache_path )
        except OSError as exc:
            _scribe.error(
                f"Failed to clear cache for {specification}: {exc}" )
            return False
        else:
            _scribe.info( f"Cleared cache for package: {specification}" )
            return True
    return False


async def ensure_package( 
    specification: str 
) -> __.typx.Annotated[
    None,
    __.ddoc.Raises( 
        _exceptions.ExtensionInstallationError, 'Install fails.' 
    ),
    __.ddoc.Raises( _exceptions.ExtensionConfigError, 'Invalid spec.' )
]:
    ''' Ensure package is installed and importable. '''
    cache_info = acquire_cache_info( specification )
    if cache_info and not cache_info.is_expired:
        _scribe.debug( f"Using cached package: {specification}." )
        package_path = cache_info.location
    else:
        if cache_info and cache_info.is_expired:
            _scribe.debug( f"Clearing expired cache for: {specification}." )
            clear_package_cache( specification )
        package_path = await _installation.install_package( specification )
    _importation.add_package_to_import_path( package_path )


def invalidate( specification: str ) -> None:
    ''' Remove package from cache, forcing reinstall on next ensure. '''
    clear_package_cache( specification )
