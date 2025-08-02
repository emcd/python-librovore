# Cache Configuration Refactor Plan

## Overview

Replace the shared `CacheConfiguration` object with class-specific attributes using inheritance. This eliminates the "god object" anti-pattern and provides cleaner encapsulation.

## Current Architecture Issues

- **God Object**: `CacheConfiguration` contains 9 fields, only 1 truly shared across all cache types  
- **Unused Field**: `network_error_ttl` is completely unused
- **Namespace Pollution**: Fields like `contents_memory_max`, `robots_ttl` require prefixes
- **Coupling**: All caches depend on fields they don't use
- **Indirection**: `self._configuration.error_ttl` instead of `self.error_ttl`

## Proposed Architecture

### Base Cache Class
```python
class Cache:
    error_ttl: float = 30.0
    success_ttl: float = 300.0
    
    def __init__(self, *, error_ttl: float = None, success_ttl: float = None):
        if error_ttl is not None: self.error_ttl = error_ttl
        if success_ttl is not None: self.success_ttl = success_ttl
        self._request_mutexes: dict[str, asyncio.Lock] = {}
```

### Specific Cache Classes
```python
class ContentCache(Cache):
    memory_max: int = 32 * 1024 * 1024
    
    def __init__(self, *, memory_max: int = None, **base_kwargs):
        super().__init__(**base_kwargs)
        if memory_max is not None: self.memory_max = memory_max
        # ... existing initialization

class ProbeCache(Cache):
    entries_max: int = 1000
    
    def __init__(self, *, entries_max: int = None, **base_kwargs):
        super().__init__(**base_kwargs)
        if entries_max is not None: self.entries_max = entries_max
        # ... existing initialization

class RobotsCache(Cache):
    entries_max: int = 500
    ttl: float = 3600.0
    request_timeout: float = 5.0
    user_agent: str = 'librovore/1.0'
    
    def __init__(self, *, entries_max: int = None, ttl: float = None, 
                 request_timeout: float = None, user_agent: str = None, 
                 **base_kwargs):
        super().__init__(**base_kwargs)
        if entries_max is not None: self.entries_max = entries_max
        if ttl is not None: self.ttl = ttl
        if request_timeout is not None: self.request_timeout = request_timeout
        if user_agent is not None: self.user_agent = user_agent
        # ... existing initialization
```

## Implementation Changes

### Files to Modify

1. **`sources/librovore/cacheproxy.py`**
   - Remove `CacheConfiguration` class entirely
   - Update `Cache` base class with shared attributes
   - Add specific attributes to each cache class
   - Update all `self._configuration.field` → `self.field`
   - Update module-level defaults: `_content_cache_default = ContentCache()`

2. **`tests/test_000_librovore/test_110_cacheproxy.py`**
   - Remove configuration object tests (`test_000_*`, `test_001_*`)
   - Update cache constructor calls throughout
   - Replace config assertions with attribute assertions

### Change Categories

#### Removed Entirely
- All `CacheConfiguration` instantiation
- Configuration validation tests
- The unused `network_error_ttl` field

#### Constructor Updates
```python
# Before
config = module.CacheConfiguration(contents_memory_max=1024)
cache = module.ContentCache(config)

# After  
cache = module.ContentCache(memory_max=1024)
```

#### Assertion Updates
```python
# Before
assert cache._configuration.contents_memory_max == 1024

# After
assert cache.memory_max == 1024
```

#### Default Cache Updates
```python
# Before
cache = module.ContentCache(module.CacheConfiguration())

# After
cache = module.ContentCache()
```

## Test Impact Analysis

### Tests Affected: 107 lines across multiple categories

1. **Configuration Tests (2 tests)**: Remove entirely
2. **Cache Initialization Tests (15+ tests)**: Update constructor calls
3. **Custom Configuration Tests (25+ tests)**: Use constructor parameters
4. **Dependency Injection Tests (10+ tests)**: Pass parameters instead of config
5. **Default Usage Tests (50+ tests)**: Remove config parameter

### Test Migration Strategy

1. **Remove obsolete tests**: Configuration validation tests
2. **Update constructor patterns**: Replace config object with parameters
3. **Update assertions**: Direct attribute access instead of config indirection
4. **Simplify fixtures**: Remove `default_config` fixture, update cache fixtures

## Benefits

### Architectural
- **Clear Ownership**: Each cache owns its specific configuration
- **Reduced Coupling**: No cross-cache configuration dependencies  
- **Better Encapsulation**: Direct attribute access instead of indirection
- **Cleaner Namespace**: Remove prefixes (`memory_max` vs `contents_memory_max`)

### Code Quality
- **Fewer Lines**: Eliminate configuration object and validation
- **Direct Access**: `self.error_ttl` vs `self._configuration.error_ttl`
- **Type Safety**: Class attributes have clear ownership
- **Maintainability**: Changes to one cache don't affect others

### Testing
- **Simpler Setup**: `ContentCache(memory_max=1024)` vs config object creation
- **Clearer Intent**: Parameters show exactly what's being customized
- **Better Isolation**: Test individual cache behaviors independently

## Implementation Timeline

1. **Update `cacheproxy.py`**: Implement new class hierarchy
2. **Update test file**: Migrate all 107 affected lines
3. **Run full test suite**: Ensure no regressions
4. **Update delay injection**: Add delay function parameter to base class
5. **Commit changes**: Single atomic change with all updates

## Risk Mitigation

- **Full test coverage**: All existing test behaviors preserved
- **No gradual migration**: Clean break, no legacy compatibility
- **Atomic change**: Single commit with both implementation and tests
- **Clear documentation**: Updated class docstrings and attribute documentation

This refactor eliminates architectural debt while maintaining all existing functionality and test coverage.