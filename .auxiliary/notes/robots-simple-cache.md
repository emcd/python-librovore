# Cache Interface Simplification Analysis

## Current Problem Pattern

Both `_check_robots_txt` and `_apply_request_delay` have this awkward pattern:

```python
try:
    parser = await cache.access(domain)
except RobotsTxtAccessFailure as exc:
    # handle gracefully
if is_absent(parser):
    try:
        parser = await _retrieve_robots_txt(client, cache, domain)
    except RobotsTxtAccessFailure as exc:
        # handle gracefully AGAIN
```

**Issues:**
- Duplicate exception handling per function
- Cache abstraction leaks (callers must handle cache miss)
- `absent` return values are essentially poor man's exceptions
- Violates "Tell, Don't Ask" principle

## Proposed Solution

**Pass `client` to `cache.access` and handle retrieval internally:**

```python
async def _check_robots_txt(url, *, client, cache):
    if url.scheme not in ('http', 'https'):
        return True

    domain = _extract_domain(url)
    try:
        parser = await cache.access_with_retrieval(domain, client)
    except _exceptions.RobotsTxtAccessFailure as exc:
        _scribe.warning(f"robots.txt access failed for {domain}: {exc.cause}. Proceeding without robots.txt validation.")
        return True

    try:
        return parser.can_fetch(cache.user_agent, url.geturl())
    except Exception as exc:
        _scribe.debug(f"robots.txt check failed: {exc}")
        return True
```

## Architectural Benefits

### 1. Single Responsibility
Cache becomes responsible for ensuring it can provide the requested resource, rather than exposing internal mechanics to callers.

### 2. Encapsulation
Internal cache mechanics (hit/miss/retrieval) are hidden. Callers just say "give me this" instead of "do you have this? if not, go get it."

### 3. Simplified Error Handling
Only one exception handling site per calling function instead of two.

### 4. Cleaner Abstractions
No more `absent` return values. Cache either returns a valid parser or raises an exception.

### 5. Consistent Semantics
All cache operations follow same pattern: return value or raise exception.

## Implementation Approaches

### Option A: New Method (Recommended)
```python
# In RobotsCache class:
async def access_with_retrieval(self, domain: str, client: _httpx.AsyncClient) -> _RobotFileParser:
    """Access cached parser or retrieve if not present. Always returns parser or raises."""
    try:
        return await self.access(domain)
    except _exceptions.RobotsTxtAccessFailure:
        raise  # Re-raise cached failures
    except:  # Cache miss or expired
        parser = await _retrieve_robots_txt(client, self, domain)
        if is_absent(parser):
            # Return permissive parser for "no robots.txt" case
            return _create_permissive_parser(domain)
        return parser
```

**Benefits**: Preserves existing API, adds cleaner interface

### Option B: Modify Existing Method
Change `access()` signature to accept optional client parameter.

**Benefits**: Single interface
**Drawbacks**: Breaking change, optional parameter complexity

### Option C: Separate Access/Retrieval Methods
Keep current `access()`, add separate `retrieve()` method, let callers choose.

**Benefits**: Explicit control
**Drawbacks**: Still requires caller coordination

## Edge Case Handling

### No robots.txt File (404/empty)
Cache should return a permissive parser that allows all access rather than returning `absent`.

### Retrieval vs Access Failures
- **Access failures** (cached 403, timeout): Should be re-raised to allow graceful degradation
- **Cache misses**: Should trigger retrieval
- **Retrieval failures**: Should be raised to caller

### Client Lifecycle
Client should be managed by caller since it may be reused across multiple cache operations.

## Recommendation

**Implement Option A** with a new `access_with_retrieval()` method:

1. **Non-breaking**: Preserves existing cache interface
2. **Clean**: Provides simplified interface for common use case
3. **Flexible**: Callers can still use fine-grained control if needed
4. **Testable**: Easy to test both old and new interfaces

This follows the principle of "make the common case simple, keep the complex case possible."

## Impact Assessment

### Code Reduction
- **Before**: ~8 lines per function (2 try/catch blocks + absent check)
- **After**: ~4 lines per function (1 try/catch block)
- **Net**: ~50% reduction in robots.txt handling code

### Maintainability
- Centralized cache-miss handling logic
- Single point of truth for retrieval semantics
- Easier to reason about error flows

### Performance
- No performance impact
- Potentially fewer allocations (no absent checks)

### Testing
- Easier to test single code path per function
- Cache behavior more isolated and testable

This architectural improvement aligns with SOLID principles and would significantly clean up the codebase.