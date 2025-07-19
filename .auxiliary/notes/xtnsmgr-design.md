# Extension Manager (xtnsmgr) Design Document

## Overview

The `xtnsmgr` (extension manager) module implements async, on-the-fly installation of external extension packages when the `package` field is present in extension configuration. It adapts concepts from isolated package management for our specific use case of loading extension processors.

## Architecture

### Module Structure
```
sources/sphinxmcps/xtnsmgr/
├── __init__.py          # Public API exports
├── __.py                # Internal imports rollup (like processors/__.py)
├── installation.py      # Async package installation with uv
├── cachemgr.py         # Cache management, TTL, platform ID
└── isolation.py        # Simple sys.path manipulation during import
```

### Design Principles

1. **No Complex Import Isolation**: Use standard Python import machinery with simple `sys.path` manipulation
2. **Parallel Async Installation**: Install multiple packages concurrently using `asyncio.gather` or `appcore.asyncf.gather_return_exceptions`
3. **TTL-Based Cache Management**: Automatic cache expiration with configurable TTL
4. **Configurable Retry Logic**: Exponential backoff with configurable max retries (default: 3)
5. **Natural Version Conflict Handling**: Let import conflicts surface for user resolution
6. **Platform-Specific Isolation**: Cache packages per platform to avoid binary compatibility issues

## Core Components

### 1. Installation Manager (`installation.py`)

**Key Functions:**
- `install_package(package_spec: str, *, max_retries: int = 3, cache_ttl_hours: int = 24) -> Path`
- `_install_with_uv(package_spec: str, target_path: Path) -> None`
- `_check_cache_validity(cache_path: Path, ttl_hours: int) -> bool`

**Implementation Details:**
- Uses `uv pip install --target {cache_path} {package_spec}` for isolated installation
- Implements exponential backoff retry logic (2^attempt seconds delay)
- Returns path to installed package for `sys.path` manipulation

**Key Implementation Details:**
- `ManagerAsync.install()` method using async subprocess execution
- Error handling with `PackageInstallFailure` exceptions

### 2. Cache Manager (`cachemgr.py`)

**Key Functions:**
- `calculate_cache_path(package_spec: str) -> Path`
- `calculate_platform_id() -> str`
- `cleanup_expired_caches(base_cache_dir: Path, ttl_hours: int = 24) -> None`
- `get_cache_info(package_spec: str) -> CacheInfo | None`

**Cache Structure:**
```
.auxiliary/caches/extensions/
├── {sha256(package_spec)}/
│   └── {platform_id}/
│       ├── .cache_metadata.json
│       └── {installed_packages}/
└── ...
```

**Platform ID Format:** `cpython-3.10--linux--x86_64`

**Cache Metadata:**
```json
{
    "package_spec": "sphinx-external-processor>=1.0.0",
    "installed_at": "2024-01-15T10:30:00Z",
    "ttl_hours": 24,
    "platform_id": "cpython-3.10--linux--x86_64"
}
```

**Key Implementation Details:**
- `calculate_cache_location()` using SHA256 hashing
- `calculate_platform_id()` for platform-specific isolation

### 3. Import Isolation (`isolation.py`)

**Key Functions:**
- `add_to_import_path(package_path: Path) -> None`
- `import_processor_module(module_name: str, package_path: Path) -> types.ModuleType`
- `cleanup_import_path() -> None`

**Implementation:**
- Simple `sys.path.insert(0, str(package_path))` during extension loading
- No complex import hooks - let standard Python machinery handle imports
- Version conflicts will surface naturally for user resolution

**Simplified Approach:**
- Uses basic `sys.path` manipulation instead of complex import hooks
- No need for `ImportContext`, `Registry`, or `Locator` complexity

### 4. Internal Imports (`__.py`)

**Rollup of frequently-used internals:**
```python
from .. import __ as _parent__
from ..exceptions import ExtensionInstallationError, ExtensionCacheError

# Re-export parent internals
Path = _parent__.Path
asyncf = _parent__.asyncf
# ... other common imports
```

## Integration with Configuration System

### Current Extension Config Format:
```toml
[[extensions]]
name = "sphinx"
enabled = true

[[extensions]]
name = "external_processor"
package = "sphinx-external-processor>=1.0.0"
enabled = true
arguments = { timeout = 30 }
```

### Loading Process:

1. **Parse Configuration**: `load_extensions_config()` returns list of extension configs
2. **Separate Extensions**: Split into builtin vs external based on `package` field presence
3. **Parallel Installation**: Use `asyncf.gather_return_exceptions()` to install all external packages concurrently
4. **Handle Installation Results**: Process success/failure for each installation
5. **Update Import Path**: Add successful installations to `sys.path` temporarily
6. **Load Processors**: Load both builtin and external processors using existing logic

### Integration Code Structure:
```python
async def load_and_register_processors():
    extensions = load_extensions_config(auxdata)
    
    # Separate builtin vs external
    builtin_extensions = [ext for ext in extensions if not ext.get('package')]
    external_extensions = [ext for ext in extensions if ext.get('package')]
    
    # Install external packages in parallel
    if external_extensions:
        install_results = await __.asyncf.gather_return_exceptions(*[
            xtnsmgr.install_package(ext['package']) 
            for ext in external_extensions
        ])
        
        # Process installation results and update sys.path
        for ext_config, result in zip(external_extensions, install_results):
            if isinstance(result, Exception):
                _scribe.error(f"Failed to install {ext_config['package']}: {result}")
                continue
            xtnsmgr.add_to_import_path(result)
    
    # Load all processors using existing logic
    for ext_config in extensions:
        if ext_config.get('package') and ext_config['name'] not in successful_installs:
            continue  # Skip failed installations
        
        # Use existing builtin/external loading logic
        module_path = _BUILTIN_PROCESSORS.get(ext_config['name'])
        if module_path:
            module = _import_processor_module(module_path)
        else:
            module = _import_external_processor_module(ext_config['name'])
        
        processor = module.register(ext_config.get('arguments'))
        processors[ext_config['name']] = processor
```

## Error Handling

### New Exception Types (in existing `exceptions.py`):
- `ExtensionInstallationError`: Package installation failures
- `ExtensionCacheError`: Cache-related issues
- `ExtensionVersionConflictError`: Import/version conflicts

### Error Scenarios:
1. **Installation Failure**: Log error, skip extension, continue with others
2. **Cache Corruption**: Clear cache entry, retry installation
3. **Import Conflicts**: Surface to user with clear error message
4. **Network Issues**: Retry with exponential backoff, then fail gracefully

## Configuration Options

### Global Configuration (in main config):
```toml
[extensions.cache]
ttl_hours = 24
max_retries = 3
cleanup_on_startup = true
max_cache_size_mb = 1000
```

### Per-Extension Configuration:
```toml
[[extensions]]
name = "custom_processor"
package = "my-sphinx-processor>=2.0.0"
cache_ttl_hours = 48  # Override global TTL
max_retries = 5       # Override global retries
```

## Performance Considerations

### Parallel Installation Benefits:
- Multiple packages install concurrently
- Reduces total startup time for multiple external extensions
- Network I/O doesn't block other installations

### Cache Optimization:
- Platform-specific caching prevents binary compatibility issues
- SHA256-based paths ensure deterministic cache locations
- TTL prevents stale packages while avoiding constant reinstalls

### Memory Management:
- Packages loaded into standard `sys.modules` (no duplication)
- Cache cleanup removes expired installations
- Configurable cache size limits prevent unbounded growth

## Future Enhancements

### Phase 2 Possibilities:
1. **Dependency Conflict Detection**: Analyze requirements before installation
2. **Cache Warming**: Pre-install commonly used extensions
3. **Extension Marketplace**: Registry of validated extensions
4. **Rollback Support**: Ability to revert to previous extension versions
5. **Health Checks**: Validate installed extensions periodically

### Advanced Import Isolation:
- Could upgrade to full import isolation in the future
- Would eliminate version conflicts entirely
- Could support more complex extension dependency trees

## Success Criteria

### Functional Requirements:
- ✅ Async parallel installation of external packages
- ✅ TTL-based cache management with automatic cleanup
- ✅ Configurable retry logic with exponential backoff
- ✅ Platform-specific isolation to prevent binary issues
- ✅ Graceful handling of installation failures
- ✅ Integration with existing extension configuration system

### Performance Requirements:
- Installation of 3 external packages should complete in parallel, not sequentially
- Cache hits should result in near-instantaneous loading
- Cache misses should not block other extension loading

### Reliability Requirements:
- Network failures should not prevent loading of other extensions
- Version conflicts should be reported clearly to users
- Cache corruption should be automatically detected and resolved

## Implementation Timeline

### Phase 1: Core Infrastructure
1. Create module structure with `__.py` rollup
2. Implement `cachemgr.py` with platform ID and cache paths
3. Implement `installation.py` with async uv integration
4. Add basic exception types to existing `exceptions.py`

### Phase 2: Integration
1. Implement `isolation.py` with simple sys.path manipulation
2. Update `xtnsapi.py` to use parallel installation
3. Add configuration schema for cache and retry settings
4. Integrate with existing extension loading logic

### Phase 3: Polish
1. Add comprehensive error handling and logging
2. Implement cache cleanup and TTL management
3. Add configuration validation and defaults
4. Create tests for installation and caching logic