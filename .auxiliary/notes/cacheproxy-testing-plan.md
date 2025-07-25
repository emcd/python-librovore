# CacheProxy Testing Implementation Plan

## Current Status

### ✅ COMPLETED: Comprehensive cacheproxy testing (63 test functions in test_110_cacheproxy.py):

**Configuration & Entry Classes** (Series 000):
- CacheConfiguration defaults and custom values
- CacheEntry TTL expiration logic and boundary conditions
- ContentCacheEntry memory usage calculation
- ProbeCacheEntry basic construction

**ContentCache Class** (Series 100):
- Initialization with configuration
- Cache access: missing URLs, fresh entries, expired entries
- TTL determination for success/error responses
- Store operations with memory tracking
- Memory-based LRU eviction when limits exceeded
- LRU access order updates

**ProbeCache Class** (Series 200):
- Initialization with configuration
- Cache access: missing URLs, fresh entries, expired entries
- TTL determination for success/error responses
- Store operations with recency tracking
- Count-based eviction when entry limits exceeded
- LRU access order updates

**probe_url Function** (Series 300):
- File scheme handling (existing/missing files)
- Empty scheme treated as file path
- HTTP cache hit returns cached result
- HTTP cache miss makes request and caches result
- HTTP 404 responses return False
- Unsupported schemes return False

**Utility Functions** (Series 400):
- Charset extraction from Content-Type headers (with/without quotes)
- Mimetype extraction from Content-Type headers
- Textual mimetype detection (text/*, application/json, etc.)
- Content validation for textual types
- Error handling for missing headers

**Current Test Coverage**: 80% (221 statements, 43 missed, 56 branches, 9 partially covered)

### ❌ COVERAGE GAPS IDENTIFIED (Lines requiring tests for 100% coverage):

**Missing Lines Analysis** (coverage report --show-missing):
- **Line 132**: Exception size estimation branch in ContentCache._calculate_response_size()
- **Line 141->136**: Memory eviction loop continuation (empty recency queue edge case)
- **Line 155->exit**: ContentCache._remove() early return (entry not found)
- **Line 205->200**: ProbeCache eviction loop continuation (empty recency queue edge case)
- **Lines 242-245**: HTTP scheme cache miss path in probe_url()
- **Lines 268-272**: HTTP scheme cache miss path in retrieve_url()
- **Lines 303-313**: HTTP scheme cache miss path in retrieve_url_as_text()
- **Line 325->328**: Charset extraction branch when no semicolon in Content-Type
- **Lines 360-372**: _probe_url() HTTP HEAD request implementation
- **Lines 379-393**: _retrieve_url() HTTP GET request implementation

**Coverage Gap Categories**:

1. **HTTP Request Functions** (Lines 360-372, 379-393):
   - _probe_url() HEAD requests with success/error responses
   - _retrieve_url() GET requests with content retrieval
   - Request deduplication via mutex handling
   - Exception handling and error wrapping
   - HTTP status code handling

2. **Public HTTP Functions** (Lines 242-245, 268-272, 303-313):
   - probe_url() HTTP scheme cache miss scenarios
   - retrieve_url() HTTP scheme cache miss scenarios  
   - retrieve_url_as_text() HTTP scheme cache miss scenarios
   - Integration with private HTTP functions

3. **Edge Case Branches**:
   - ContentCache._calculate_response_size() exception handling (Line 132)
   - Memory eviction with empty recency queue (Line 141->136)
   - ProbeCache eviction with empty recency queue (Line 205->200)
   - ContentCache._remove() with missing entry (Line 155->exit)
   - Content-Type header without semicolon (Line 325->328)

**Required Test Additions** (~15-20 functions needed for 100% coverage):

**Series 500: HTTP Integration Tests**
- test_500_probe_url_http_cache_miss_success() - Lines 242-245, 360-372
- test_510_probe_url_http_cache_miss_failure() - Exception handling in _probe_url()
- test_520_retrieve_url_http_cache_miss_success() - Lines 268-272, 379-393
- test_530_retrieve_url_http_cache_miss_failure() - Exception handling in _retrieve_url()
- test_540_retrieve_url_as_text_http_cache_miss_success() - Lines 303-313
- test_550_retrieve_url_as_text_http_cache_miss_failure() - Exception handling

**Series 600: Edge Case Coverage**
- test_600_content_cache_calculate_response_size_exception() - Line 132
- test_610_content_cache_evict_empty_recency_queue() - Line 141->136
- test_620_content_cache_remove_missing_entry() - Line 155->exit
- test_630_probe_cache_evict_empty_recency_queue() - Line 205->200
- test_640_extract_charset_no_semicolon() - Line 325->328

**Series 700: HTTP Request Deduplication**
- test_700_probe_url_concurrent_requests_deduplication()
- test_710_retrieve_url_concurrent_requests_deduplication()
- test_720_request_mutex_cleanup_after_completion()

**Series 800: HTTP Error Conditions**
- test_800_probe_url_http_timeout_exception()
- test_810_retrieve_url_http_connection_error()
- test_820_retrieve_url_http_status_error()

## HTTPX Mocking Context

### MockTransport Usage Pattern

HTTPX provides `MockTransport` for testing HTTP interactions without network calls:

```python
def mock_handler(request):
    # Inspect request.method, request.url, request.headers
    return httpx.Response(status_code, json=data, headers=headers)

transport = httpx.MockTransport(mock_handler)
client = httpx.Client(transport=transport)
```

### Key Mocking Strategies for CacheProxy

1. **Status Code Testing**: Return different HTTP status codes (200, 404, 500) to test success/error paths

2. **Content-Type Headers**: Mock various Content-Type headers for charset detection and mimetype validation

3. **Request Inspection**: Verify that cache proxy makes expected HEAD vs GET requests

4. **Timeout Simulation**: Use handler functions that raise `httpx.TimeoutException` or `httpx.ConnectError`

5. **Response Content**: Return different content sizes to test memory-based eviction

### Domain-Specific Mocking

Since cacheproxy handles different URL schemes:
- **File scheme**: Use `pyfakefs` (already available in test infrastructure)
- **HTTP/HTTPS schemes**: Use `httpx.MockTransport`
- **Unsupported schemes**: Direct testing without mocking

### Request Deduplication Testing

The cacheproxy module uses `_request_mutexes` for deduplication. Testing this requires:
- Concurrent async calls to same URL
- Verification that only one actual HTTP request is made
- Proper mutex cleanup after requests complete

## Testing Infrastructure Notes

- Project uses `pyfakefs` for filesystem operations (available via `fs` fixture)
- Async tests marked with `@pytest.mark.asyncio`
- Mock objects created with `unittest.mock.Mock(spec=ClassName)` for type safety
- Time mocking via `patch.object(module.__.time, 'time', return_value=timestamp)`
- Project follows numbered test organization (000-999 series within modules)

## Test Coverage Goals

**Target**: 100% line and branch coverage for cacheproxy module
**Current Coverage**: 80% (221 statements, 43 missed, 56 branches, 9 partially covered)
**Achievement**: 63 comprehensive test functions completed

**Completed Coverage Areas**:
- ✅ Cache manager classes and their core operations (Series 100-200)
- ✅ Configuration handling and TTL logic (Series 000)
- ✅ File scheme probing functionality (Series 300)
- ✅ Utility functions for content handling (Series 400)

**Remaining Coverage Gaps** (20% to achieve 100%):
- ❌ HTTP scheme cache miss paths in public functions (Lines 242-245, 268-272, 303-313)
- ❌ Private HTTP request functions (_probe_url, _retrieve_url) (Lines 360-372, 379-393)
- ❌ Edge case branches in cache management and utility functions
- ❌ Request deduplication and mutex handling
- ❌ HTTP error conditions and timeouts

**Strategy for Completion**:
- Focus testing on the 17 specific test functions identified above
- Use httpx.MockTransport for HTTP request simulation
- Target the exact missing lines revealed by coverage analysis
- Ensure branch coverage for conditional statements

**DEPENDENCY INJECTION REQUIRED FOR 100% COVERAGE**:

The remaining 20% coverage gap exists because private functions `_probe_url` (lines 360-372) and `_retrieve_url` (lines 379-393) hardcode `httpx.AsyncClient()` creation, making them untestable without monkey-patching (which violates immutable module design).

**Required Changes for Testability**:

Add optional `client_factory` parameter to public functions:

```python
async def probe_url(
    url: _Url, *,
    cache: ProbeCache = _probe_cache_default,
    duration_max: float = 10.0,
    client_factory: Callable[[], _httpx.AsyncClient] = _httpx.AsyncClient,
) -> bool:

async def retrieve_url(
    url: _Url, *,
    cache: ContentCache = _content_cache_default,
    duration_max: float = 30.0,
    client_factory: Callable[[], _httpx.AsyncClient] = _httpx.AsyncClient,
) -> bytes:

async def retrieve_url_as_text(
    url: _Url, *,
    cache: ContentCache = _content_cache_default,
    duration_max: float = 30.0,
    charset_default: str = 'utf-8',
    client_factory: Callable[[], _httpx.AsyncClient] = _httpx.AsyncClient,
) -> str:
```

Then modify private functions to accept client from factory:
```python
async def _probe_url(
    url: _Url, *, duration_max: float, client_factory: Callable[[], _httpx.AsyncClient]
) -> ProbeResponse:
    # Use client_factory() instead of _httpx.AsyncClient()
```

This allows tests to inject `lambda: httpx.AsyncClient(transport=mock_transport)` to achieve 100% coverage while maintaining dependency injection principles.