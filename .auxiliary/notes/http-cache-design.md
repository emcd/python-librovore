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
```

#### 2. Cache Entry Structure
```python
class CacheEntry( __.immut.DataclassObject ):
    ''' HTTP response cache entry with TTL. '''
    
    response: __.cabc.Union[ bool, str, Exception ]  # HEAD bool, GET str, or cached error
    timestamp: float                                 # When cached  
    ttl: float                                      # Time to live in seconds
```

#### 3. Public API
```python
async def probe_url( 
    url: _Url, *, timeout: float = 10.0 
) -> bool:
    ''' Cached HEAD request to check URL existence. '''

async def retrieve_url( 
    url: _Url, *, timeout: float = 30.0 
) -> str:
    ''' Cached GET request to fetch URL content. '''
```

## Caching Strategy

### Cache Keys
- Use `url.geturl()` as cache key for consistency
- Separate namespaces for HEAD and GET requests

### TTL Configuration
- **Success responses**: 5 minutes (balance freshness vs efficiency)
- **Error responses**: 30 seconds (prevent retry storms, allow recovery)
- **Network errors**: 10 seconds (temporary issues may resolve quickly)

### Error Caching
- Cache common errors (404, 403, timeout) to prevent repeated failures
- Store exception objects in cache entries
- Re-raise original exceptions when serving from cache

## Implementation Details

### Request Deduplication
1. Check if URL already has active request (mutex exists and locked)
2. If so, wait for existing request to complete
3. If not, acquire mutex and make request
4. Store result in cache before releasing mutex

### Cache Expiration
- Check timestamp + TTL before serving cached responses
- Evict expired entries lazily (when accessed)
- No proactive cleanup initially (keep MVP simple)

### Error Handling
- Catch and cache `httpx` exceptions
- Cache `DocumentationInaccessibility` for failed requests
- Differentiate between client errors (4xx) and server errors (5xx) for TTL

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
    max_cache_size: int = 1000       # LRU eviction trigger
```

## Testing Strategy

### Unit Tests
- Cache hit/miss behavior
- TTL expiration handling
- Error caching and re-raising
- Concurrent request deduplication

### Integration Tests
- End-to-end processor detection with caching
- Performance comparison with/without cache
- Rate limiting avoidance verification

## LRU Eviction Strategy

### Implementation Approach
Use `collections.deque` to track access order for each cache:
- On cache hit: move URL to end of deque (`remove()` + `append()`)
- On cache miss: add URL to end of deque
- On eviction: remove from front of deque (least recently used)

### Eviction Logic
```python
def _evict_lru_entries( 
    cache: dict[ str, CacheEntry ],
    access_order: __.deque[ str ],
    max_size: int
) -> None:
    ''' Evicts least recently used entries when cache exceeds max size. '''
    while len( cache ) > max_size:
        if not access_order: break  # Safety check
        lru_url = access_order.popleft( )
        cache.pop( lru_url, None )  # May already be expired and removed
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

## Risks & Mitigations

### Stale Data
- **Risk**: Cached responses may become outdated
- **Mitigation**: Conservative 5-minute TTL balances freshness vs efficiency

### Memory Usage  
- **Risk**: Unbounded cache growth
- **Mitigation**: LRU eviction at configurable max size (default 1000 entries)

### Cache Coherency
- **Risk**: Different request types for same URL may be inconsistent
- **Mitigation**: Separate caches prevent HEAD/GET interference

## Success Criteria

- Zero 429 rate limiting errors during multi-processor detection
- <100ms response time for cached requests
- >90% cache hit rate for repeated URL access
- All existing tests continue passing after migration
- Memory usage remains bounded under normal operation