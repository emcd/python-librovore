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
from . import exceptions as _exceptions


ProbeResponse: __.typx.TypeAlias = _generics.Result[ bool, Exception ]
ContentResponse: __.typx.TypeAlias = _generics.Result[ bytes, Exception ]


class CacheConfiguration( __.immut.DataclassObject ):
    ''' Configuration for HTTP cache behavior. '''

    contents_memory_max: int = 32 * 1024 * 1024  # 32 MiB for GET cache
    probe_entries_max: int = 1000  # Entry limit for HEAD cache
    error_ttl: float = 30.0     # 30 seconds
    network_error_ttl: float = 10.0  # 10 seconds
    success_ttl: float = 300.0  # 5 minutes


class CacheEntry( __.immut.DataclassObject ):
    ''' Cache entry base. '''

    timestamp: float
    ttl: float

    @property
    def extant( self ) -> bool:
        ''' Checks if cache entry has exceeded its TTL. '''
        return __.time.time( ) - self.timestamp > self.ttl


class ContentCacheEntry( CacheEntry ):
    ''' Cache entry for URL content with size tracking. '''

    response: ContentResponse
    headers: _httpx.Headers
    size_bytes: int

    @property
    def memory_usage( self ) -> int:
        ''' Calculates total memory usage including metadata. '''
        return self.size_bytes + 100  # Overhead estimate


class ProbeCacheEntry( CacheEntry ):
    ''' Cache entry for URL probe results. '''

    response: ProbeResponse


class ContentCache(
    __.immut.Object,
    instances_mutables = ( '_memory_total', '_request_mutexes' )
):
    ''' Cache manager for URL content (GET requests) with memory tracking. '''

    def __init__( self, configuration: CacheConfiguration ) -> None:
        self._cache: dict[ str, ContentCacheEntry ] = { }
        self._configuration = configuration
        self._memory_total = 0
        self._recency: __.collections.deque[ str ] = __.collections.deque( )
        self._request_mutexes: dict[ str, __.asyncio.Lock ] = { }

    async def access(
        self, url: str
    ) -> __.Absential[ tuple[ bytes, _httpx.Headers ] ]:
        ''' Retrieves cached content if valid. '''
        if url not in self._cache: return __.absent
        entry = self._cache[ url ]
        if entry.extant:
            self._remove( url )
            return __.absent
        self._record_access( url )
        return ( entry.response.extract( ), entry.headers )

    @__.ctxl.asynccontextmanager
    async def acquire_mutex_for( self, url: str ):
        ''' Acquires mutex for HTTP request deduplication. '''
        if url not in self._request_mutexes: # pragma: no branch
            self._request_mutexes[ url ] = __.asyncio.Lock( )
        mutex = self._request_mutexes[ url ]
        async with mutex:
            try: yield
            finally: self._request_mutexes.pop( url, None )

    def determine_ttl( self, response: ContentResponse ) -> float:
        ''' Determines appropriate TTL based on response type. '''
        if response.is_value( ):
            return self._configuration.success_ttl
        # TODO: Inspect exception type for more granular TTL
        return self._configuration.error_ttl

    async def store(
        self, url: str, response: ContentResponse,
        headers: _httpx.Headers, ttl: float
    ) -> None:
        ''' Stores content in cache with memory management. '''
        size_bytes = self._calculate_response_size( response )
        entry = ContentCacheEntry(
            response = response,
            headers = headers,
            timestamp = __.time.time( ),
            ttl = ttl,
            size_bytes = size_bytes )
        if old_entry := self._cache.get( url ):
            self._memory_total -= old_entry.memory_usage
        self._cache[ url ] = entry
        self._memory_total += entry.memory_usage
        self._record_access( url )
        self._evict_by_memory( )

    def _calculate_response_size( self, response: ContentResponse ) -> int:
        ''' Calculates memory footprint of cached response. '''
        if response.is_value( ):
            content = response.extract( )
            return len( content )
        return 100  # Conservative estimate for exception overhead

    def _evict_by_memory( self ) -> None:
        ''' Evicts LRU entries until memory usage is under limit. '''
        while (
            self._memory_total > self._configuration.contents_memory_max
            and self._recency
        ):
            lru_url = self._recency.popleft( )
            if lru_url in self._cache: # pragma: no branch
                entry = self._cache[ lru_url ]
                self._memory_total -= entry.memory_usage
                del self._cache[ lru_url ]
                _scribe.debug( f"Evicted cache entry: {lru_url}" )

    def _record_access( self, url: str ) -> None:
        ''' Updates LRU access order for given URL. '''
        with __.ctxl.suppress( ValueError ):
            self._recency.remove( url )
        self._recency.append( url )

    def _remove( self, url: str ) -> None:
        ''' Removes entry from cache and updates memory tracking. '''
        if entry := self._cache.pop( url, None ):
            self._memory_total -= entry.memory_usage
            with __.ctxl.suppress( ValueError ):
                self._recency.remove( url )


class ProbeCache(
    __.immut.Object, instances_mutables = ( '_request_mutexes', )
):
    ''' Cache manager for URL probe results (HEAD requests). '''

    def __init__( self, configuration: CacheConfiguration ) -> None:
        self._cache: dict[ str, ProbeCacheEntry ] = { }
        self._configuration = configuration
        self._recency: __.collections.deque[ str ] = __.collections.deque( )
        self._request_mutexes: dict[ str, __.asyncio.Lock ] = { }

    async def access( self, url: str ) -> __.Absential[ bool ]:
        ''' Retrieves cached probe result if valid. '''
        if url not in self._cache: return __.absent
        entry = self._cache[ url ]
        if entry.extant:
            self._remove( url )
            return __.absent
        self._record_access( url )
        return entry.response.extract( )

    @__.ctxl.asynccontextmanager
    async def acquire_mutex_for( self, url: str ):
        ''' Acquires mutex for HTTP request deduplication. '''
        if url not in self._request_mutexes: # pragma: no branch
            self._request_mutexes[ url ] = __.asyncio.Lock( )
        mutex = self._request_mutexes[ url ]
        async with mutex:
            try: yield
            finally: self._request_mutexes.pop( url, None )

    def determine_ttl( self, response: ProbeResponse ) -> float:
        ''' Determines appropriate TTL based on response type. '''
        if response.is_value( ):
            return self._configuration.success_ttl
        # TODO: Inspect exception type for more granular TTL
        return self._configuration.error_ttl

    async def store(
        self, url: str, response: ProbeResponse, ttl: float
    ) -> None:
        ''' Stores probe result in cache. '''
        entry = ProbeCacheEntry(
            response = response,
            timestamp = __.time.time( ),
            ttl = ttl )
        self._cache[ url ] = entry
        self._record_access( url )
        self._evict_by_count( )

    def _evict_by_count( self ) -> None:
        ''' Evicts oldest entries when cache exceeds max size. '''
        while (
            len( self._cache ) > self._configuration.probe_entries_max
            and self._recency
        ):
            lru_url = self._recency.popleft( )
            if lru_url in self._cache: # pragma: no branch
                del self._cache[ lru_url ]

    def _record_access( self, url: str ) -> None:
        ''' Updates LRU access order for given URL. '''
        with __.ctxl.suppress( ValueError ):
            self._recency.remove( url )
        self._recency.append( url )

    def _remove( self, url: str ) -> None:
        ''' Removes entry from cache. '''
        self._cache.pop( url, None )
        with __.ctxl.suppress( ValueError ):
            self._recency.remove( url )


_configuration_default = CacheConfiguration( )
_http_success_threshold = 400
_content_cache_default = ContentCache( _configuration_default )
_probe_cache_default = ProbeCache( _configuration_default )
_scribe = __.acquire_scribe( __name__ )


async def probe_url(
    url: _Url, *,
    cache: ProbeCache = _probe_cache_default,
    duration_max: float = 10.0,
    client_factory: __.cabc.Callable[ [ ], _httpx.AsyncClient ] = (
        _httpx.AsyncClient ),
) -> bool:
    ''' Cached HEAD request to check URL existence. '''
    match url.scheme:
        case '' | 'file':
            return __.Path( url.path ).exists( )
        case 'http' | 'https':
            url_s = url.geturl( )
            result = await cache.access( url_s )
            if not __.is_absent( result ): return result
            result = await _probe_url(
                url, duration_max = duration_max,
                cache = cache, client_factory = client_factory )
            ttl = cache.determine_ttl( result )
            await cache.store( url_s, result, ttl )
            return result.extract( )
        case _: return False


async def retrieve_url(
    url: _Url, *,
    cache: ContentCache = _content_cache_default,
    duration_max: float = 30.0,
    client_factory: __.cabc.Callable[ [ ], _httpx.AsyncClient ] = (
        _httpx.AsyncClient ),
) -> bytes:
    ''' Cached GET request to fetch URL content as bytes. '''
    match url.scheme:
        case '' | 'file':
            location = __.Path( url.path )
            try: return location.read_bytes( )
            except Exception as exc:
                raise _exceptions.DocumentationInaccessibility(
                    url.geturl( ), exc ) from exc
        case 'http' | 'https':
            url_s = url.geturl( )
            result = await cache.access( url_s )
            if not __.is_absent( result ):
                content_bytes, _ = result
                return content_bytes
            result, headers = await _retrieve_url(
                url, duration_max = duration_max,
                cache = cache, client_factory = client_factory )
            ttl = cache.determine_ttl( result )
            await cache.store( url_s, result, headers, ttl )
            return result.extract( )
        case _:
            raise _exceptions.DocumentationInaccessibility(
                url.geturl( ),
                ValueError( f"Unsupported scheme: {url.scheme}" ) )


async def retrieve_url_as_text(
    url: _Url, *,
    cache: ContentCache = _content_cache_default,
    duration_max: float = 30.0,
    charset_default: str = 'utf-8',
    client_factory: __.cabc.Callable[ [ ], _httpx.AsyncClient ] = (
        _httpx.AsyncClient ),
) -> str:
    ''' Cached GET request to fetch URL content as text. '''
    match url.scheme:
        case '' | 'file':
            location = __.Path( url.path )
            # TODO? Use preferred fs encoding instead of default charset.
            try: return location.read_text( encoding = charset_default )
            except Exception as exc:
                raise _exceptions.DocumentationInaccessibility(
                    url.geturl( ), exc ) from exc
        case 'http' | 'https':
            url_s = url.geturl( )
            result = await cache.access( url_s )
            if not __.is_absent( result ):
                content_bytes, headers = result
                _validate_textual_content( headers, url_s )
                charset = _extract_charset_from_headers(
                    headers, charset_default )
                return content_bytes.decode( charset )
            result, headers = await _retrieve_url(
                url, duration_max = duration_max,
                cache = cache, client_factory = client_factory )
            ttl = cache.determine_ttl( result )
            await cache.store( url_s, result, headers, ttl )
            content_bytes = result.extract( )
            _validate_textual_content( headers, url_s )
            charset = _extract_charset_from_headers(
                headers, charset_default )
            return content_bytes.decode( charset )
        case _:
            raise _exceptions.DocumentationInaccessibility(
                url.geturl( ),
                ValueError( f"Unsupported scheme: {url.scheme}" ) )


def _extract_charset_from_headers(
    headers: _httpx.Headers, default: str
) -> str:
    ''' Extracts charset from Content-Type header. '''
    content_type = headers.get( 'content-type', '' )
    if isinstance( content_type, str ) and ';' in content_type:
        _, _, params = content_type.partition( ';' )
        if 'charset=' in params:
            charset = params.split( 'charset=' )[ -1 ].strip( )
            return charset.strip( '"\'' )
    return default


def _extract_mimetype_from_headers( headers: _httpx.Headers ) -> str:
    ''' Extracts mimetype from Content-Type header. '''
    content_type = headers.get( 'content-type', '' )
    if isinstance( content_type, str ) and ';' in content_type:
        mimetype, _, _ = content_type.partition( ';' )
        return mimetype.strip( )
    return content_type


def _is_textual_mimetype( mimetype: str ) -> bool:
    ''' Checks if mimetype represents textual content. '''
    return (
        mimetype.startswith( 'text/' ) or mimetype in (
            'application/ecmascript',
            'application/javascript',
            'application/json',
            'application/ld+json',
            'application/xml',
            'application/yaml',
            'application/x-yaml',
            'image/svg+xml',
        )
    )


async def _probe_url(
    url: _Url, *, duration_max: float,
    cache: ProbeCache,
    client_factory: __.cabc.Callable[ [ ], _httpx.AsyncClient ]
) -> ProbeResponse:
    ''' Makes HEAD request with deduplication. '''
    url_s = url.geturl( )
    async with cache.acquire_mutex_for( url_s ):
        try:
            async with client_factory( ) as client:
                response = await client.head( url_s, timeout = duration_max )
                return _generics.Value(
                    response.status_code < _http_success_threshold )
        except Exception as exc:
            _scribe.debug( f"HEAD request failed for {url_s}: {exc}" )
            return _generics.Error( exc )


async def _retrieve_url(
    url: _Url, *, duration_max: float,
    cache: ContentCache,
    client_factory: __.cabc.Callable[ [ ], _httpx.AsyncClient ]
) -> tuple[ ContentResponse, _httpx.Headers ]:
    ''' Makes GET request with deduplication. '''
    url_s = url.geturl( )
    async with cache.acquire_mutex_for( url_s ):
        try:
            async with client_factory( ) as client:
                response = await client.get( url_s, timeout = duration_max )
                response.raise_for_status( )
                return (
                    _generics.Value( response.content ),
                    response.headers )
        except Exception as exc:
            _scribe.debug( f"GET request failed for {url_s}: {exc}" )
            return _generics.Error( exc ), _httpx.Headers( )


def _validate_textual_content( headers: _httpx.Headers, url: str ) -> None:
    ''' Validates that content is textual based on mimetype. '''
    mimetype = _extract_mimetype_from_headers( headers )
    if mimetype and not _is_textual_mimetype( mimetype ):
        raise _exceptions.HttpContentTypeInvalidity(
            url, mimetype, "text decoding" )
