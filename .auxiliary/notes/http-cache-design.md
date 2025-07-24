# HTTP Cache Module Design

## Problem Statement

As the processor ecosystem grows, multiple processors will probe the same documentation URLs during detection. This creates several problems:
- **Rate limiting risk**: Multiple simultaneous requests to same URLs can trigger 429 responses
- **Inefficiency**: Redundant network requests for identical resources
- **Inconsistency**: Different processors may get different responses due to timing

## Solution Overview

Create a shared HTTP cache module that mediates all external URL access with:
- Request deduplication via async mutexes
- Response caching with TTL expiration
- Error response caching to prevent retry storms
- Separate cache entries for different HTTP methods

## Architecture

### Module Location
`sources/sphinxmcps/http.py`

### Core Components

#### 1. Cache Storage
```python
# Separate caches for different request types
_head_cache: dict[ str, CacheEntry ] = { }
_get_cache: dict[ str, CacheEntry ] = { }

# Per-URL locks to prevent concurrent requests
_request_locks: dict[ str, __.asyncio.Lock ] = { }

# LRU tracking for cache eviction
_head_access_order: __.deque[ str ] = __.deque( )
_get_access_order: __.deque[ str ] = __.deque( )

# Global memory usage tracking
_total_cache_memory: int = 0
_memory_lock: __.asyncio.Lock = __.asyncio.Lock( )
```

#### 2. Cache Entry Structure
```python
from appcore.generics import Result, Value, Error

class CacheEntry( __.immut.DataclassObject ):
    ''' HTTP response cache entry with Result wrapper and size tracking. '''
    
    response: Result[ __.cabc.Union[ bool, str ], Exception ]  # Wrapped response
    timestamp: float                                           # When cached  
    ttl: float                                                # Time to live in seconds
    size_bytes: int                                           # Memory footprint in bytes

    @property 
    def memory_footprint( self ) -> int:
        ''' Calculate total memory usage including metadata. '''
        return self.size_bytes + 100  # Add overhead for cache entry metadata

    @property
    def is_expired( self ) -> bool:
        ''' Check if cache entry has exceeded its TTL. '''
        return __.time.time( ) - self.timestamp > self.ttl
```

#### 3. Public API
```python
async def probe_url( 
    url: _Url, *, timeout: float = 10.0 
) -> bool:
    ''' Cached HEAD request to check URL existence.
    
    Returns:
        bool: True if URL is accessible, False otherwise
        
    Raises:
        Original exception from cached Error result
    '''

async def retrieve_url( 
    url: _Url, *, timeout: float = 30.0 
) -> str:
    ''' Cached GET request to fetch URL content.
    
    Returns:
        str: Response content from successful request
        
    Raises:
        Original exception from cached Error result
    '''
```

## Caching Strategy

### Cache Keys
- Use `url.geturl()` as cache key for consistency
- Separate namespaces for HEAD and GET requests

### TTL Configuration
- **Success responses**: 5 minutes (balance freshness vs efficiency)
- **Error responses**: 30 seconds (prevent retry storms, allow recovery)
- **Network errors**: 10 seconds (temporary issues may resolve quickly)

### Error Caching with Result Types
- Cache common errors (404, 403, timeout) as `Error(exception)` instances
- Use `Result.is_error()` to identify cached failures
- Re-raise original exceptions via `Result.extract()` when serving from cache
- Error results maintain type safety while preserving exception details

## Implementation Details

### Request Deduplication
1. Check if URL already has active request (mutex exists and locked)
2. If so, wait for existing request to complete
3. If not, acquire mutex and make request
4. Wrap response in `Value(response)` or exception in `Error(exception)`
5. Store Result in cache before releasing mutex

### Cache Expiration
- Check timestamp + TTL before serving cached responses
- Evict expired entries lazily (when accessed)
- No proactive cleanup initially (keep MVP simple)

### Error Handling with Result Types
- Catch `httpx` and `DocumentationInaccessibility` exceptions
- Wrap caught exceptions in `Error(exception)` for caching
- Use `Result.is_error()` to check for cached failures before serving
- Differentiate between client errors (4xx) and server errors (5xx) for TTL
- `Result.extract()` automatically re-raises the original exception

## Migration Path

### Phase 1: Implement Core Cache
- Create `http.py` module with basic caching
- Implement `probe_url` and `retrieve_url` functions
- Add comprehensive tests

### Phase 2: Update Processors
- Migrate `detection.probe_url` to use cached version
- Migrate `extraction.retrieve_url` to use cached version
- Update all processor imports

### Phase 3: Remove Duplicated Code
- Remove old probe/retrieve functions from submodules
- Clean up unused imports

## Configuration Options

### Cache Settings (injectable via arguments)
```python
class HttpCacheConfig( __.immut.DataclassObject ):
    ''' Configuration for HTTP cache behavior. '''
    
    success_ttl: float = 300.0       # 5 minutes
    error_ttl: float = 30.0          # 30 seconds  
    network_error_ttl: float = 10.0  # 10 seconds
    max_memory_bytes: int = 32 * 1024 * 1024  # 32 MiB default
    max_cache_entries: int = 1000    # Fallback entry limit
```

## Testing Strategy

### Unit Tests
- Cache hit/miss behavior with Result types
- TTL expiration handling  
- Error caching with `Error(exception)` wrapping
- Result extraction and exception re-raising
- Concurrent request deduplication
- Memory tracking accuracy for Value/Error results
- Memory-based eviction behavior
- Type safety validation for Result[bool, Exception] vs Result[str, Exception]

### Integration Tests
- End-to-end processor detection with caching
- Performance comparison with/without cache
- Rate limiting avoidance verification
- Memory usage under load

## LRU Eviction Strategy

### Implementation Approach
Use `collections.deque` to track access order for each cache:
- On cache hit: move URL to end of deque (`remove()` + `append()`)
- On cache miss: add URL to end of deque
- On eviction: remove from front of deque (least recently used)

### Memory-Based Eviction Logic
```python
def _calculate_response_size( response: Result[ __.cabc.Union[ bool, str ], Exception ] ) -> int:
    ''' Calculate memory footprint of cached Result. '''  
    if response.is_value( ):
        value = response.extract( )
        match value:
            case bool( ):
                return 1  # Minimal for boolean
            case str( content ):
                return len( content.encode( 'utf-8' ) )
            case _:
                return 8  # Default object overhead
    else:
        # For Error results, estimate exception string size without extracting
        # (extracting would raise the exception)
        return 100  # Conservative estimate for exception overhead

def _create_cache_entry(
    response: Result[ __.cabc.Union[ bool, str ], Exception ],
    ttl: float
) -> CacheEntry:  
    ''' Create cache entry with proper size calculation. '''
    return CacheEntry(
        response = response,
        timestamp = __.time.time( ),
        ttl = ttl,
        size_bytes = _calculate_response_size( response )
    )

async def _evict_by_memory( 
    cache: dict[ str, CacheEntry ],
    access_order: __.deque[ str ],
    max_memory: int
) -> None:
    ''' Evicts LRU entries until memory usage is under limit. '''
    global _total_cache_memory
    async with _memory_lock:
        while _total_cache_memory > max_memory and access_order:
            lru_url = access_order.popleft( )
            if entry := cache.pop( lru_url, None ):
                _total_cache_memory -= entry.memory_footprint
```

### Access Tracking
```python
def _record_cache_access( url: str, access_order: __.deque[ str ] ) -> None:
    ''' Updates LRU access order for given URL. '''
    try: access_order.remove( url )  # O(n) but bounded by cache size
    except ValueError: pass  # URL not in deque yet
    access_order.append( url )
```

### Performance Considerations
- `deque.remove()` is O(n) but cache size is bounded (1000 entries)
- Cache lookups remain O(1)
- Eviction only triggers when cache exceeds limit
- Trade-off: simple implementation vs optimal performance

## Future Enhancements

### Advanced LRU Optimizations (Post-MVP)
- Replace deque with doubly-linked list for O(1) access updates
- Implement `functools.lru_cache`-style decorator approach
- Add cache hit/miss rate metrics

### Advanced Features
- Cache persistence across restarts
- Cache warming for common URLs
- Configurable per-domain rate limiting
- Circuit breaker for consistently failing domains

## Benefits

1. **Performance**: Eliminates redundant network requests during detection
2. **Reliability**: Prevents rate limiting from simultaneous requests  
3. **Consistency**: All processors see identical responses for same URLs
4. **Scalability**: Efficient resource usage as processor count grows
5. **Robustness**: Error caching prevents cascading failures
6. **Type Safety**: Result types provide compile-time guarantees for error handling
7. **Functional Programming**: Clean separation of success/error paths with Result API
8. **Memory Efficiency**: Byte-based eviction handles variable response sizes

## Risks & Mitigations

### Stale Data
- **Risk**: Cached responses may become outdated
- **Mitigation**: Conservative 5-minute TTL balances freshness vs efficiency

### Memory Usage  
- **Risk**: Unbounded cache growth
- **Mitigation**: Memory-based LRU eviction at configurable limit (default 32 MiB)

### Cache Coherency
- **Risk**: Different request types for same URL may be inconsistent
- **Mitigation**: Separate caches prevent HEAD/GET interference

## Success Criteria

- Zero 429 rate limiting errors during multi-processor detection
- <100ms response time for cached requests
- >90% cache hit rate for repeated URL access
- All existing tests continue passing after migration
- Memory usage remains bounded under normal operation