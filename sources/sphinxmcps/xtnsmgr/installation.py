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


import uv as _uv

from . import __
from . import cachemgr as _cachemgr


_scribe = __.acquire_scribe( __name__ )


async def install_package(
    specification: str, *,
    max_retries: int = 3,
    cache_ttl: int = 24
) -> __.Path:
    ''' Installs package asynchronously with retry logic.

        Returns path to installed package for sys.path manipulation.
    '''
    cache_info = _cachemgr.acquire_cache_info( specification )
    if cache_info and not cache_info.is_expired:
        _scribe.debug( f"Using cached package: {specification}." )
        return cache_info.location
    if cache_info and cache_info.is_expired:
        _scribe.debug( f"Clearing expired cache for: {specification}." )
        _cachemgr.clear_package_cache( specification )
    for attempt in range( max_retries + 1 ):
        try:
            return await _install_with_uv( specification, cache_ttl )
        except __.ExtensionInstallationError as exc:  # noqa: PERF203
            if attempt == max_retries:
                _scribe.error(
                    f"Failed to install {specification} after "
                    f"{max_retries + 1} attempts: {exc}" )
                raise
            # Exponential backoff
            delay = 2 ** attempt
            _scribe.warning(
                f"Installation attempt {attempt + 1} failed for "
                f"{specification}, retrying in {delay}s: {exc}" )
            await __.asyncio.sleep( delay )
    raise __.ExtensionInstallationError(
        specification, "Maximum retries exceeded" )


async def _install_with_uv( specification: str, cache_ttl: int ) -> __.Path:
    ''' Installs package using uv to isolated cache directory. '''
    cache_path = _cachemgr.calculate_cache_path( specification )
    cache_path.mkdir( parents = True, exist_ok = True )
    try: uv_executable = _uv.find_uv_bin( )
    except ImportError as exc:
        raise __.ExtensionInstallationError(
            specification, f"uv not available: {exc}" ) from exc
    uv_exec_str: str = str( uv_executable )
    command: list[ str ] = [
        uv_exec_str, 'pip',
        'install', '--target', str( cache_path ),
        specification
    ]
    _scribe.info( f"Installing {specification} to {cache_path}." )
    try:
        process = await __.asyncio.create_subprocess_exec(
            *command,
            stdout = __.asyncio.subprocess.PIPE,
            stderr = __.asyncio.subprocess.PIPE )
    except OSError as exc:
        raise __.ExtensionInstallationError(
            specification, f"Process execution failed: {exc}" ) from exc
    try:
        stdout, stderr = await process.communicate( )
    except __.asyncio.TimeoutError as exc:
        raise __.ExtensionInstallationError(
            specification, f"Installation timed out: {exc}" ) from exc
    if process.returncode != 0:
        raise __.ExtensionInstallationError(
            specification,
            f"uv install failed (exit {process.returncode}): "
            f"{stderr.decode( 'utf-8' )}" )
    cache_info = _cachemgr.CacheInfo(
        specification = specification,
        ctime = __.datetime.datetime.now( ),
        ttl = cache_ttl,
        platform_id = _cachemgr.calculate_platform_id( ),
        location = cache_path )
    _cachemgr.save_cache_info( cache_info )
    _scribe.info( f"Successfully installed {specification}." )
    return cache_path


async def install_packages_parallel(
    specifications: __.cabc.Sequence[ str ], *,
    max_retries: int = 3,
    cache_ttl: int = 24
) -> __.cabc.Sequence[ __.Path ]:
    ''' Installs multiple packages in parallel using gather_async.

        Raises ExceptionGroup if any installations fail.
        Returns list of installation paths for successful installations.
    '''
    if not specifications: return [ ]
    installers = [
        install_package(
            spec, max_retries = max_retries, cache_ttl = cache_ttl )
        for spec in specifications ]
    count = len( specifications )
    _scribe.info( f"Installing {count} packages." )
    try:
        results = await __.asyncf.gather_async(
            *installers, error_message = "Failed to install packages." )
    except __.excg.ExceptionGroup as exc_group:
        # TODO: Log at top of propagation.
        # Log individual package installation errors
        for exc in exc_group.exceptions:
            _scribe.error( f"Package installation failed: {exc}." )
        raise
    else:
        _scribe.info( "Successfully installed all packages." )
        return results
