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


''' Async package installation for extensions. '''


from . import __
from . import cachemgr as _cachemgr
from .. import exceptions as _exceptions


_scribe = __.acquire_scribe( __name__ )


async def install_package(
    package_spec: str, *,
    max_retries: int = 3,
    cache_ttl_hours: int = 24
) -> __.Path:
    ''' Install package asynchronously with retry logic.
    
        Returns path to installed package for sys.path manipulation.
    '''
    # Check if package is already cached and valid
    cache_info = _cachemgr.get_cache_info( package_spec )
    if cache_info and not cache_info.is_expired:
        _scribe.debug( f"Using cached package: {package_spec}" )
        return cache_info.cache_path
    
    # Clear expired cache if present
    if cache_info and cache_info.is_expired:
        _scribe.debug( f"Clearing expired cache for: {package_spec}" )
        _cachemgr.clear_package_cache( package_spec )
    
    # Install with retry logic
    for attempt in range( max_retries + 1 ):
        try:
            return await _install_with_uv( package_spec, cache_ttl_hours )
        except _exceptions.ExtensionInstallationError as exc:  # noqa: PERF203
            if attempt == max_retries:
                _scribe.error(
                    f"Failed to install {package_spec} after "
                    f"{max_retries + 1} attempts: {exc}"
                )
                raise
            
            # Exponential backoff
            delay = 2 ** attempt
            _scribe.warning(
                f"Installation attempt {attempt + 1} failed for "
                f"{package_spec}, retrying in {delay}s: {exc}"
            )
            await __.asyncio.sleep( delay )
    
    # This should never be reached, but satisfy type checker
    raise _exceptions.ExtensionInstallationError(
        package_spec, "Maximum retries exceeded"
    )


async def _install_with_uv( 
    package_spec: str, cache_ttl_hours: int 
) -> __.Path:
    ''' Install package using uv to isolated cache directory. '''
    cache_path = _cachemgr.calculate_cache_path( package_spec )
    cache_path.mkdir( parents = True, exist_ok = True )
    
    # Find uv executable
    try:
        import uv
        uv_executable = uv.find_uv_bin( )
    except ImportError as exc:
        raise _exceptions.ExtensionInstallationError(
            package_spec, f"uv not available: {exc}"
        ) from exc
    
    # Install package using uv
    command = [
        str( uv_executable ), 'pip',
        'install', '--target', str( cache_path ),
        package_spec
    ]
    
    _scribe.info( f"Installing {package_spec} to {cache_path}" )
    
    try:
        process = await __.asyncio.create_subprocess_exec(
            *command,
            stdout = __.asyncio.subprocess.PIPE,
            stderr = __.asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate( )
        
        if process.returncode != 0:
            raise _exceptions.ExtensionInstallationError(
                package_spec,
                f"uv install failed (exit {process.returncode}): "
                f"{stderr.decode( 'utf-8' )}"
            )
        
        # Save cache metadata on success
        cache_info = _cachemgr.CacheInfo(
            package_spec = package_spec,
            installed_at = __.datetime.datetime.now( ),
            ttl_hours = cache_ttl_hours,
            platform_id = _cachemgr.calculate_platform_id( ),
            cache_path = cache_path
        )
        _cachemgr.save_cache_info( cache_info )
        
        _scribe.info( f"Successfully installed {package_spec}" )
        return cache_path  # noqa: TRY300
        
    except __.asyncio.TimeoutError as exc:
        raise _exceptions.ExtensionInstallationError(
            package_spec, f"Installation timed out: {exc}"
        ) from exc
    except OSError as exc:
        raise _exceptions.ExtensionInstallationError(
            package_spec, f"Process execution failed: {exc}"
        ) from exc


async def install_packages_parallel(
    package_specs: list[ str ], *,
    max_retries: int = 3,
    cache_ttl_hours: int = 24
) -> list[ __.Path | Exception ]:
    ''' Install multiple packages in parallel using gather_async.
    
        Returns list of results - either Path objects for success or
        Exception objects for failures.
    '''
    if not package_specs:
        return [ ]
    
    install_tasks = [
        install_package(
            spec,
            max_retries = max_retries,
            cache_ttl_hours = cache_ttl_hours
        )
        for spec in package_specs
    ]
    
    _scribe.info( f"Installing {len( package_specs )} packages in parallel" )
    
    results = await __.asyncf.gather_async(
        *install_tasks,
        return_exceptions = True
    )
    
    # Log results
    successes = sum( 1 for result in results if isinstance( result, __.Path ) )
    failures = len( results ) - successes
    
    _scribe.info(
        f"Parallel installation completed: {successes} successful, "
        f"{failures} failed"
    )
    
    return list( results )