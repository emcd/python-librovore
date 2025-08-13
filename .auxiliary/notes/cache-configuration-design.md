# HTTP Cache Configuration Design Proposal

## Problem Analysis

### Current State
Librovore implements HTTP content caching to improve performance and reduce server load when accessing documentation sites. The current implementation uses hardcoded TTL values that cannot be configured by users, leading to several issues:

1. **Development Friction**: During development and testing, cached responses mask code improvements and bug fixes
2. **Inflexible Deployment**: Production deployments cannot tune cache behavior for their specific access patterns
3. **One-Size-Fits-All**: Different content types (robots.txt, inventory files, documentation pages) have different optimal cache lifetimes
4. **No Emergency Override**: No mechanism to bypass cache for debugging or testing scenarios

### Cache Architecture Overview
The system currently implements three distinct cache types:
- **ContentCache**: Caches GET request responses for documentation content
- **ProbeCache**: Caches HEAD request results for resource existence checks  
- **RobotsCache**: Caches robots.txt files with request delay management

Each cache type uses TTL-based expiration with memory management and LRU eviction policies.

## Proposed Solution: Hybrid Configuration Approach

### Primary Solution: TOML Configuration
Add cache configuration section to the general configuration file allowing granular control over cache behavior for different content types.

**Configuration Structure:**
```
[cache.content]
success-ttl = 3600      # Documentation pages (1 hour)
error-ttl = 30          # Failed requests (30 seconds)
memory-limit = 33554432 # 32MB memory limit

[cache.probe] 
success-ttl = 1800      # Resource existence checks (30 minutes)
error-ttl = 30          # Failed probes (30 seconds)
entries-max = 1000      # Maximum cached entries

[cache.robots]
ttl = 86400             # Robots.txt files (24 hours)
entries-max = 500       # Maximum cached entries
request-timeout = 5.0   # Request timeout in seconds
user-agent = "librovore/1.0"
```

**Key Design Principles:**
- Use TOML format consistent with existing configuration
- Avoid underscores in key names per project standards
- TTL values in seconds for precise control
- TTL of 0 disables caching for that content type
- Sensible defaults maintain current behavior when config absent

### Secondary Solution: CLI Override
Provide immediate cache bypass capability through command-line flags for debugging and testing scenarios.

**CLI Integration:**
- Add `--no-cache` flag to bypass all caching
- Add `--cache-ttl=N` flag to override TTL temporarily
- Flags apply only to current command execution
- Override configuration file settings when present

## Implementation Benefits

### Development Workflow
- Set `content-ttl = 0` in development configuration
- Eliminates cache-related debugging confusion
- Immediate feedback on code changes
- No need to remember command flags

### Production Deployment
- Tune cache lifetimes based on documentation update frequency
- Reduce server load with appropriate caching
- Different TTLs for different content stability levels
- Memory usage control for resource-constrained environments

### Operational Flexibility
- Emergency cache bypass for troubleshooting
- Per-deployment cache optimization
- A/B testing different cache strategies
- Gradual cache behavior migration

## Migration Strategy

### Backward Compatibility
- Maintain existing hardcoded defaults when configuration absent
- Graceful degradation if configuration file malformed
- No breaking changes to existing CLI interface

### Configuration Discovery
- Configuration loaded during cache initialization
- Runtime configuration updates not supported (restart required)
- Clear error messages for invalid TTL values
- Validation ensures non-negative TTL values

### CLI Integration Points
- Query-content and query-inventory commands gain cache flags
- MCP server operations respect configuration file settings
- Consistent cache behavior across all access patterns

## Implementation Architecture

### Current Implementation (Completed)
The cache configuration system has been successfully implemented with dependency injection:

**State Management**:
- `librovore.state.Globals` extends `appcore.Globals` with cache attributes
- Three cache instances: `content_cache`, `probe_cache`, `robots_cache`
- Created independently during application initialization via `cacheproxy.prepare()`

**Function Threading**:
- **CLI Functions**: All functions accept `auxdata: _state.Globals` parameter
- **MCP Server**: Uses closures to capture `auxdata` for tool functions  
- **Module Functions**: Functions like `retrieve_url(content_cache, robots_cache, url)` require explicit cache parameters
- **Processor Interface**: All processor methods accept `auxdata` parameter

**Configuration Structure**:
- **Separate TOML Tables**: `[cache.content]`, `[cache.probe]`, `[cache.robots]`
- **Granular Control**: Individual TTL, memory, and behavioral settings per cache type
- **Factory Methods**: Each cache class has `from_configuration()` class method

### Proposed Architecture Refinements

**Problem**: Current module functions require multiple cache parameters, creating parameter threading overhead:
```python
# Current API
await retrieve_url(auxdata.content_cache, auxdata.robots_cache, url)
await probe_url(auxdata.probe_cache, auxdata.robots_cache, url)
```

**Solution**: Object-oriented convenience methods with shared robots cache dependency:

**1. Robots Cache as Shared Dependency**
```python
# Proposed: Robots cache injected into other caches
content_cache = ContentCache(robots_cache=shared_robots, ...)
probe_cache = ProbeCache(robots_cache=shared_robots, ...)

# State object simplified
class Globals:
    content_cache: ContentCache  # Contains robots_cache internally
    probe_cache: ProbeCache      # Contains robots_cache internally
```

**2. Convenience Methods with UFCS**
```python
# Object-oriented API (primary)
await auxdata.content_cache.retrieve_url(url)
await auxdata.probe_cache.probe_url(url)

# Functional API (for UFCS style)
await retrieve_url(auxdata.content_cache, url)  # Simplified signature
await probe_url(auxdata.probe_cache, url)       # Simplified signature
```

**3. Implementation Strategy**
- **Lightweight Methods**: Convenience methods are thin wrappers around module functions
- **Backward Compatibility**: Keep module-level functions for UFCS and testing
- **Constructor Injection**: Pass robots cache to content/probe cache constructors
- **Consistent Configuration**: TOML structure remains unchanged

**Benefits**:
- **Reduced Parameter Threading**: Fewer parameters to pass through function chains
- **Better Encapsulation**: Robots compliance becomes internal cache concern
- **Object-Oriented Design**: More natural method dispatch on cache objects
- **UFCS Support**: Both `cache.method()` and `function(cache)` styles available
- **Cleaner Call Sites**: Less cognitive overhead at usage points

### Migration Path for Refinements

**Phase 1: Cache Constructor Changes**
1. **Add robots_cache parameter** to `ContentCache` and `ProbeCache` constructors
2. **Update cacheproxy.prepare()** to create shared robots cache first:
   ```python
   def prepare(auxdata: __.Globals) -> tuple[ContentCache, ProbeCache]:
       configuration = auxdata.configuration
       robots_cache = RobotsCache.from_configuration(configuration)
       content_cache = ContentCache.from_configuration(
           configuration, robots_cache=robots_cache)
       probe_cache = ProbeCache.from_configuration(
           configuration, robots_cache=robots_cache)
       return content_cache, probe_cache
   ```
3. **Update _state.Globals** to only contain `content_cache` and `probe_cache`

**Phase 2: Add Convenience Methods**
1. **Add lightweight wrapper methods** to cache classes:
   ```python
   class ContentCache:
       async def retrieve_url(self, url, **kwargs):
           return await retrieve_url(self, url, **kwargs)
   
   class ProbeCache:
       async def probe_url(self, url, **kwargs):
           return await probe_url(self, url, **kwargs)
   ```

**Phase 3: Simplify Module Functions**
1. **Remove robots_cache parameter** from module function signatures
2. **Access robots_cache** via `content_cache.robots_cache` or `probe_cache.robots_cache`
3. **Update all call sites** to use either new convenience methods or simplified function signatures

**Phase 4: Update Tests**
1. **Update test fixtures** to create caches with shared robots cache
2. **Migrate test calls** to use new API patterns
3. **Verify both method and function styles work correctly**

## Technical Considerations

### Cache Granularity
The solution provides content-type granularity rather than per-site or per-URL granularity. This balances configurability with complexity, addressing the most common use cases without over-engineering.

### Memory Management
Existing memory management and LRU eviction remain unchanged. The memory limit becomes configurable to support different deployment scenarios.

### Performance Impact
Configuration parsing occurs once during initialization. Runtime performance remains unchanged, with potential improvements from optimized TTL values.

## Success Criteria

### Functional Requirements
- Development environments can disable caching entirely
- Production environments can optimize cache lifetimes
- Emergency cache bypass available for troubleshooting
- Backward compatibility maintained

### Operational Requirements
- Configuration changes take effect on restart
- Invalid configurations provide clear error messages
- CLI overrides work consistently across commands
- Documentation reflects new configuration options

This design addresses the root cause of cache-related development friction while providing production-ready cache management capabilities.