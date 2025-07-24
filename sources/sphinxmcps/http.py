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


''' HTTP cache for documentation URL access. '''


from urllib.parse import ParseResult as _Url

import appcore.generics as _generics
import httpx as _httpx

from . import __


ProbeResponse: __.typx.TypeAlias = _generics.Result[ bool, Exception ]
ContentResponse: __.typx.TypeAlias = _generics.Result[ bytes, Exception ]


class CacheConfiguration( __.immut.DataclassObject ):
    ''' Configuration for HTTP cache behavior. '''

    success_ttl: float = 300.0  # 5 minutes
    error_ttl: float = 30.0     # 30 seconds
    network_error_ttl: float = 10.0  # 10 seconds
    probe_cache_entries_max: int = 1000  # Entry limit for HEAD cache
    content_cache_memory_max: int = 32 * 1024 * 1024  # 32 MiB for GET cache


class ContentCacheEntry( __.immut.DataclassObject ):
    ''' Cache entry for URL content with size tracking. '''

    response: ContentResponse
    timestamp: float
    ttl: float
    size_bytes: int

    @property
    def extant( self ) -> bool:
        ''' Checks if cache entry has exceeded its TTL. '''
        return __.time.time( ) - self.timestamp > self.ttl

    @property
    def memory_usage( self ) -> int:
        ''' Calculates total memory usage including metadata. '''
        return self.size_bytes + 100  # Overhead estimate


class ProbeCacheEntry( __.immut.DataclassObject ):
    ''' Cache entry for URL probe results. '''

    response: ProbeResponse
    timestamp: float
    ttl: float

    @property
    def extant( self ) -> bool:
        ''' Checks if cache entry has exceeded its TTL. '''
        return __.time.time( ) - self.timestamp > self.ttl


class _ProbeCache:
    ''' Cache manager for URL probe results (HEAD requests). '''

    def __init__( self, max_entries: int ) -> None:
        self._cache: dict[ str, ProbeCacheEntry ] = { }
        self._access_order: __.collections.deque[ str ] = (
            __.collections.deque( ) )
        self._max_entries = max_entries

    async def get( self, url_key: str ) -> __.Absential[ bool ]:
        ''' Retrieves cached probe result if valid. '''
        if url_key not in self._cache:
            return __.absent
        entry = self._cache[ url_key ]
        if entry.extant:
            self._remove( url_key )
            return __.absent
        self._record_access( url_key )
        return entry.response.extract( )

    async def store(
        self, url_key: str, response: ProbeResponse, ttl: float
    ) -> None:
        ''' Stores probe result in cache. '''
        entry = ProbeCacheEntry(
            response = response,
            timestamp = __.time.time( ),
            ttl = ttl )
        self._cache[ url_key ] = entry
        self._record_access( url_key )
        self._evict_by_count( )

    def _evict_by_count( self ) -> None:
        ''' Evicts oldest entries when cache exceeds max size. '''
        while len( self._cache ) > self._max_entries and self._access_order:
            lru_url = self._access_order.popleft( )
            if lru_url in self._cache:
                del self._cache[ lru_url ]

    def _record_access( self, url_key: str ) -> None:
        ''' Updates LRU access order for given URL. '''
        with __.ctxl.suppress( ValueError ):
            self._access_order.remove( url_key )
        self._access_order.append( url_key )

    def _remove( self, url_key: str ) -> None:
        ''' Removes entry from cache. '''
        self._cache.pop( url_key, None )
        with __.ctxl.suppress( ValueError ):
            self._access_order.remove( url_key )


class _ContentCache:
    ''' Cache manager for URL content (GET requests) with memory tracking. '''

    def __init__( self, max_memory: int ) -> None:
        self._cache: dict[ str, ContentCacheEntry ] = { }
        self._access_order: __.collections.deque[ str ] = (
            __.collections.deque( ) )
        self._max_memory = max_memory
        self._total_memory = 0

    async def get( self, url_key: str ) -> __.Absential[ bytes ]:
        ''' Retrieves cached content if valid. '''
        if url_key not in self._cache:
            return __.absent
        entry = self._cache[ url_key ]
        if entry.extant:
            self._remove( url_key )
            return __.absent
        self._record_access( url_key )
        return entry.response.extract( )

    async def store(
        self, url_key: str, response: ContentResponse, ttl: float
    ) -> None:
        ''' Stores content in cache with memory management. '''
        size_bytes = self._calculate_response_size( response )
        entry = ContentCacheEntry(
            response = response,
            timestamp = __.time.time( ),
            ttl = ttl,
            size_bytes = size_bytes )
        if old_entry := self._cache.get( url_key ):
            self._total_memory -= old_entry.memory_usage
        self._cache[ url_key ] = entry
        self._total_memory += entry.memory_usage
        self._record_access( url_key )
        self._evict_by_memory( )

    def _calculate_response_size( self, response: ContentResponse ) -> int:
        ''' Calculates memory footprint of cached response. '''
        if response.is_value( ):
            content = response.extract( )
            return len( content )
        return 100  # Conservative estimate for exception overhead

    def _evict_by_memory( self ) -> None:
        ''' Evicts LRU entries until memory usage is under limit. '''
        while self._total_memory > self._max_memory and self._access_order:
            lru_url = self._access_order.popleft( )
            if lru_url in self._cache:
                entry = self._cache[ lru_url ]
                self._total_memory -= entry.memory_usage
                del self._cache[ lru_url ]
                _scribe.debug( f"Evicted cache entry: {lru_url}" )

    def _record_access( self, url_key: str ) -> None:
        ''' Updates LRU access order for given URL. '''
        with __.ctxl.suppress( ValueError ):
            self._access_order.remove( url_key )
        self._access_order.append( url_key )

    def _remove( self, url_key: str ) -> None:
        ''' Removes entry from cache and updates memory tracking. '''
        if entry := self._cache.pop( url_key, None ):
            self._total_memory -= entry.memory_usage
            with __.ctxl.suppress( ValueError ):
                self._access_order.remove( url_key )


_configuration_default = CacheConfiguration( )
_probe_cache = _ProbeCache( _configuration_default.probe_cache_entries_max )
_content_cache = _ContentCache(
    _configuration_default.content_cache_memory_max )
_request_locks: dict[ str, __.asyncio.Lock ] = { }
_scribe = __.acquire_scribe( __name__ )
_http_success_threshold = 400


async def probe_url(
    url: _Url, *,
    configuration: __.Absential[ CacheConfiguration ] = __.absent,
    timeout: float = 10.0,
) -> bool:
    ''' Cached HEAD request to check URL existence. '''
    if __.is_absent( configuration ):
        configuration = _configuration_default
    url_key = url.geturl( )
    cached_result = await _probe_cache.get( url_key )
    if not __.is_absent( cached_result ):
        return cached_result
    result = await _probe_url( url, timeout = timeout )
    ttl = _determine_ttl( result, configuration )
    await _probe_cache.store( url_key, result, ttl )
    return result.extract( )


async def retrieve_url(
    url: _Url, *,
    configuration: __.Absential[ CacheConfiguration ] = __.absent,
    timeout: float = 30.0,
    encoding: str = 'utf-8'
) -> str:
    ''' Cached GET request to fetch URL content. '''
    if __.is_absent( configuration ):
        configuration = _configuration_default
    url_key = url.geturl( )
    cached_result = await _content_cache.get( url_key )
    if not __.is_absent( cached_result ):
        return cached_result.decode( encoding )
    result = await _retrieve_url( url, timeout = timeout )
    ttl = _determine_ttl( result, configuration )
    await _content_cache.store( url_key, result, ttl )
    content_bytes = result.extract( )
    return content_bytes.decode( encoding )


def _determine_ttl(
    response: ProbeResponse | ContentResponse,
    configuration: CacheConfiguration
) -> float:
    ''' Determines appropriate TTL based on response type. '''
    if response.is_value( ):
        return configuration.success_ttl
    # TODO: Inspect exception type for more granular TTL
    return configuration.error_ttl


async def _probe_url( url: _Url, *, timeout: float ) -> ProbeResponse:
    ''' Makes HEAD request with deduplication. '''
    url_key = url.geturl( )
    if url_key not in _request_locks:
        _request_locks[ url_key ] = __.asyncio.Lock( )
    async with _request_locks[ url_key ]:
        try:
            async with _httpx.AsyncClient( ) as client:
                response = await client.head( url_key, timeout = timeout )
                return _generics.Value(
                    response.status_code < _http_success_threshold )
        except Exception as exc:
            _scribe.debug( f"HEAD request failed for {url_key}: {exc}" )
            return _generics.Error( exc )
        finally: _request_locks.pop( url_key, None )


async def _retrieve_url( url: _Url, *, timeout: float ) -> ContentResponse:
    ''' Makes GET request with deduplication. '''
    url_key = url.geturl( )
    if url_key not in _request_locks:
        _request_locks[ url_key ] = __.asyncio.Lock( )
    async with _request_locks[ url_key ]:
        try:
            async with _httpx.AsyncClient( ) as client:
                response = await client.get( url_key, timeout = timeout )
                response.raise_for_status( )
                return _generics.Value( response.content )
        except Exception as exc:
            _scribe.debug( f"GET request failed for {url_key}: {exc}" )
            return _generics.Error( exc )
        finally: _request_locks.pop( url_key, None )
