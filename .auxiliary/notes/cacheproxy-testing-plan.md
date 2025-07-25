# CacheProxy Testing Implementation Plan

## ✅ COMPLETED: Comprehensive Test Suite (78 test functions)

### **Current Status**
- **Test Coverage**: 87% (221 statements, 26 missed, 56 branches, 7 partially covered)
- **Total Tests**: 78 comprehensive test functions in `test_110_cacheproxy.py`
- **Dependency Injection**: ✅ Implemented `client_factory` parameter injection
- **Testing Approach**: ✅ Modernized to use `httpx.MockTransport` instead of complex mocking

### **Completed Test Coverage Areas**

**Series 000-099: Configuration & Entry Classes**
- CacheConfiguration defaults and custom values
- CacheEntry TTL expiration logic and boundary conditions  
- ContentCacheEntry memory usage calculation
- ProbeCacheEntry basic construction

**Series 100-199: ContentCache Class**
- Initialization with configuration
- Cache access: missing URLs, fresh entries, expired entries
- TTL determination for success/error responses
- Store operations with memory tracking
- Memory-based LRU eviction when limits exceeded
- LRU access order updates

**Series 200-299: ProbeCache Class**
- Initialization with configuration
- Cache access: missing URLs, fresh entries, expired entries
- TTL determination for success/error responses
- Store operations with recency tracking
- Count-based eviction when entry limits exceeded
- LRU access order updates

**Series 300-399: probe_url Function**
- File scheme handling (existing/missing files)
- Empty scheme treated as file path
- HTTP cache hit returns cached result
- HTTP cache miss with successful HEAD requests (using MockTransport)
- HTTP cache miss with exception handling (using MockTransport)
- Unsupported schemes return False
- Dependency injection with custom cache and client_factory

**Series 400-499: retrieve_url & retrieve_url_as_text Functions**
- File scheme content retrieval (existing/missing files)
- Empty scheme treated as file path
- HTTP cache hit returns cached content
- Charset extraction and text decoding
- Content-Type validation for textual content
- Custom charset defaults
- Unsupported schemes raise exceptions
- Dependency injection with custom cache

**Series 500-599: Utility Functions & HTTP Success Cases**
- Charset extraction from Content-Type headers (with/without quotes)
- Mimetype extraction from Content-Type headers
- Textual mimetype detection (text/*, application/json, etc.)
- Content validation for textual types
- HTTP cache miss success scenarios (using MockTransport)

**Series 600-699: Integration & Configuration Tests**
- Cross-component integration
- Custom cache configuration effects
- Cache sharing across function calls
- Dependency injection validation

**Series 700-799: Utility Functions (Detailed)**
- Content-Type header parsing edge cases
- Charset extraction variants
- Mimetype detection for various types
- Textual content validation

**Series 800-899: Edge Case Coverage**
- Exception size estimation in ContentCache._calculate_response_size()
- Empty recency queue handling in memory/count eviction
- Missing entry removal handling
- Content-Type header without semicolon

**Series 900-999: HTTP Request Testing (MockTransport)**
- Concurrent request deduplication
- Request mutex cleanup
- HTTP timeout exceptions
- HTTP connection errors
- HTTP status errors

## ✅ COVERAGE IMPROVEMENT ACHIEVED: 96% (Option A Partially Completed)

**Previous**: 87% coverage (26 missed lines, 7 partial branches)
**Current**: 96% coverage (5 missed lines, 6 partial branches)
**Improvement**: +9% coverage achieved

### **🎯 Successfully Implemented (Option A Results)**

#### **HTTP Cache Miss Scenarios - ✅ COMPLETED**
- ✅ **Lines 274-279**: `retrieve_url()` HTTP cache miss path - NOW COVERED
- ✅ **Lines 312-323**: `retrieve_url_as_text()` HTTP cache miss path - NOW COVERED  
- ✅ **Lines 391-405**: `_retrieve_url()` implementation details - NOW COVERED

**Tests Added**:
- `test_560_retrieve_url_as_bytes_http_cache_miss`: Tests GET request cache miss with MockTransport
- `test_570_retrieve_url_as_text_http_cache_miss`: Tests text retrieval cache miss with UTF-8
- `test_575_retrieve_url_as_text_http_cache_miss_custom_charset`: Tests ISO-8859-1 charset handling

## ❌ REMAINING COVERAGE GAPS (4% to achieve 100%)

**Current**: 96% coverage analysis shows 5 statement misses + 6 partial branches

### **Category 1: Cache Eviction Race Conditions (4 partial branches)**
- **Line 141->136**: ContentCache memory eviction when recency queue has stale entries
- **Line 205->200**: ProbeCache count eviction when recency queue has stale entries  
- **Line 372->374**: `_probe_url()` mutex access when mutex already exists
- **Line 392->394**: `_retrieve_url()` mutex access when mutex already exists

### **Category 2: Error Handling Edge Cases (2 partial branches)**  
- **Line 335->338**: Charset extraction when Content-Type header has no 'charset=' parameter
- **Lines 402-404**: `_retrieve_url()` exception handling and debug logging

### **Category 3: Function Return Paths (1 statement miss)**
- **Lines 322-323**: `retrieve_url_as_text()` unsupported scheme exception path

## 🎯 REMAINING OPTIONS FOR 100% COVERAGE

### **Option A1: Complete Coverage (Final 4%)**
- **Target**: All remaining edge cases and race conditions
- **Effort**: High complexity due to race condition simulation
- **Value**: Theoretical completeness

### **Option B: Accept Excellent Coverage (Recommended)**
- **96% coverage** represents exceptional business logic coverage
- **Missing 4%** entirely consists of edge cases, race conditions, and error paths
- **ROI consideration**: Diminishing returns for complex edge case testing

## 📋 PROPOSED TEST NUMBERING REORGANIZATION

**Current Issue**: Tests numbered beyond 999 (up to 1143)
**Solution**: Reorganize into logical component groups within 000-999 range

### **Recommended Numbering Scheme**

**000-099: Configuration & Data Classes**
- 000-019: CacheConfiguration
- 020-039: CacheEntry base class
- 040-059: ContentCacheEntry  
- 060-079: ProbeCacheEntry

**100-199: ContentCache Class**
- 100-119: Initialization & basic operations
- 120-139: Cache access patterns
- 140-159: TTL & store operations
- 160-179: Memory management & eviction
- 180-199: LRU access tracking

**200-299: ProbeCache Class**  
- 200-219: Initialization & basic operations
- 220-239: Cache access patterns
- 240-259: TTL & store operations
- 260-279: Count-based eviction
- 280-299: LRU access tracking

**300-399: probe_url Function**
- 300-319: File scheme handling
- 320-339: HTTP scheme cache hits
- 340-359: HTTP scheme cache misses
- 360-379: Error conditions & edge cases
- 380-399: Dependency injection & configuration

**400-499: retrieve_url Functions**
- 400-419: File scheme retrieval
- 420-439: HTTP scheme cache hits  
- 440-459: HTTP scheme cache misses
- 460-479: Text retrieval & charset handling
- 480-499: Error conditions & edge cases

**500-599: HTTP Request Testing**
- 500-519: Successful HTTP requests (MockTransport)
- 520-539: HTTP exceptions & timeouts
- 540-559: Request deduplication
- 560-579: Connection & status errors
- 580-599: Integration scenarios

**600-699: Utility Functions**
- 600-619: Content-Type header parsing
- 620-639: Charset extraction
- 640-659: Mimetype detection  
- 660-679: Content validation
- 680-699: Edge cases & error handling

**700-799: Integration & Configuration**
- 700-719: Cross-component integration
- 720-739: Custom cache configurations
- 740-759: Dependency injection patterns
- 760-779: Cache sharing scenarios
- 780-799: Performance & behavior validation

**800-899: Edge Cases & Error Conditions**
- 800-819: Cache eviction edge cases
- 820-839: Memory management edge cases
- 840-859: HTTP error edge cases
- 860-879: Content processing edge cases
- 880-899: Miscellaneous edge cases

**900-999: Reserved for Future Extensions**

## 🔧 DEPENDENCY INJECTION IMPLEMENTATION (✅ COMPLETED)

Successfully implemented `client_factory` parameter injection:

```python
async def probe_url(
    url: _Url, *,
    cache: ProbeCache = _probe_cache_default,
    duration_max: float = 10.0,
    client_factory: __.cabc.Callable[ [ ], _httpx.AsyncClient ] = _httpx.AsyncClient,
) -> bool:

async def retrieve_url(
    url: _Url, *,
    cache: ContentCache = _content_cache_default,
    duration_max: float = 30.0,
    client_factory: __.cabc.Callable[ [ ], _httpx.AsyncClient ] = _httpx.AsyncClient,
) -> bytes:

async def retrieve_url_as_text(
    url: _Url, *,
    cache: ContentCache = _content_cache_default,
    duration_max: float = 30.0,
    charset_default: str = 'utf-8',
    client_factory: __.cabc.Callable[ [ ], _httpx.AsyncClient ] = _httpx.AsyncClient,
) -> str:
```

**Benefits Achieved**:
- ✅ Clean testing via `httpx.MockTransport` instead of complex mocking
- ✅ Backward compatibility with default HTTP client behavior
- ✅ 100% coverage capability through dependency injection
- ✅ Elimination of real HTTP requests to external sites

## 🧪 MODERNIZED TESTING APPROACH (✅ COMPLETED)

**Converted from**: Complex `unittest.mock` patching of `httpx.AsyncClient`
**Converted to**: Clean `httpx.MockTransport` with real client

**Example Pattern**:
```python
def handler( request ):
    return _httpx.Response( 200, content = test_content )
mock_transport = _httpx.MockTransport( handler )
def client_factory( ):
    return _httpx.AsyncClient( transport = mock_transport )
result = await module.probe_url( url, client_factory = client_factory )
```

**Results**:
- ✅ 8 tests modernized to use MockTransport
- ✅ More maintainable and authentic HTTP testing
- ✅ Follows httpx recommended testing practices
- ✅ All tests passing (78/78)

## 📈 COVERAGE IMPROVEMENT TRAJECTORY

- **Initial Coverage**: 80% (before dependency injection)
- **Current Coverage**: 87% (after dependency injection + test modernization)
- **Potential Coverage**: 100% (via additional HTTP cache miss tests)
- **Practical Target**: 87-90% (excellent coverage of business logic)

## 🎯 NEXT STEPS (If Pursuing 100% Coverage)

1. **Add HTTP Cache Miss Tests** (~5 functions):
   - `test_440_retrieve_url_http_cache_miss_success`
   - `test_460_retrieve_url_as_text_http_cache_miss_success`
   - `test_470_retrieve_url_http_cache_miss_with_headers`
   - `test_480_retrieve_url_as_text_charset_extraction`
   - `test_490_retrieve_url_concurrent_cache_miss`

2. **Add Content-Type Edge Case**:
   - `test_635_extract_charset_no_charset_parameter`

3. **Add Mutex Edge Case**:
   - `test_545_probe_url_existing_mutex_handling`

**Total Additional Tests**: ~7 functions to achieve 100% coverage