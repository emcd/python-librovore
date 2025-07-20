# Extension Manager (xtnsmgr) - Complete Implementation

## Overview

The `xtnsmgr` (extension manager) module provides a comprehensive system for loading, installing, and managing extension processors with **cache-driven package management**. The key architectural insight is that **"Installation is fundamentally a cache-miss handler, not a separate concern."**

## Current Implementation Status: ✅ COMPLETE

All phases of the extension manager have been successfully implemented and tested.

## Architecture

### Module Structure
```
sources/sphinxmcps/xtnsmgr/
├── __init__.py           # Public API exports
├── __.py                 # Internal imports rollup
├── cachemgr.py          # Cache management with ensure_package() orchestration
├── configuration.py      # Extension configuration loading and validation
├── importation.py       # Import path and .pth file processing
├── installation.py      # Async package installation with uv
└── processors.py        # Simplified processor loading and registration
```

### Core Design Principles

1. **Cache-Driven Package Management**: Cache manager orchestrates complete "make package importable" workflow
2. **Separation of Concerns**: Each module has focused, single responsibility
3. **Async Parallel Operations**: Multiple packages install concurrently 
4. **TTL-Based Cache Management**: Automatic cache expiration with configurable TTL
5. **Comprehensive .pth Support**: Proper handling of .pth files with encoding, security, and platform considerations
6. **Natural Import Resolution**: Standard Python import machinery with sys.path manipulation

## Core Components

### 1. Cache Manager (`cachemgr.py`) - **IMPLEMENTED**

**Primary Interface:**
```python
async def ensure_package( specification: str ) -> None:
    ''' Ensure package is installed and importable. '''

def invalidate( specification: str ) -> None:
    ''' Remove package from cache, forcing reinstall on next ensure. '''
```

**Key Features:**
- **Complete Workflow Orchestration**: Handles cache check → install → import path setup
- **Proper Exception Documentation**: Uses `__.ddoc.Raises` with actual exception classes
- **Dependency Injection Ready**: Clean module-level imports for testability
- **TTL Management**: Automatic cache expiration and cleanup

### 2. Import Management (`importation.py`) - **IMPLEMENTED** 

**Primary Interface:**
```python
def add_package_to_import_path( package_path: __.Path ) -> None:
    ''' Add package to sys.path and process any .pth files. '''

def process_pth_files( package_path: __.Path ) -> None:
    ''' Process .pth files with proper encoding, hidden file detection, and security. '''
```

**Key Features:**
- **Comprehensive .pth Processing**: Handles UTF-8-BOM, locale fallbacks, hidden file detection
- **Cross-Platform Support**: Proper hidden file detection for Darwin, Windows, Linux
- **Security Considerations**: Safe exec() usage with proper error handling
- **Standard Import Machinery**: Uses `__.types` and private import aliases

### 3. Installation Manager (`installation.py`) - **IMPLEMENTED**

**Key Features:**
- **Async uv Integration**: Uses `uv pip install --target` for isolated installation
- **Retry Logic**: Exponential backoff with configurable max retries (default: 3)
- **Parallel Installation**: Multiple packages install concurrently via `gather_async`
- **Proper Error Handling**: ExceptionGroup support with individual error logging

### 4. Configuration Management (`configuration.py`) - **IMPLEMENTED**

**Key Features:**
- **Extension Validation**: Comprehensive validation of extension configurations
- **Type Safety**: Proper type annotations and casting
- **Filtering Functions**: Built-in vs external extension separation
- **Argument Extraction**: Clean interface for extension-specific arguments

### 5. Processor Management (`processors.py`) - **IMPLEMENTED**

**Dramatically Simplified Architecture:**

**Before (Complex Orchestration):**
```python
# ~15 lines of cache check → install → import path → error handling
cache_info = cachemgr.acquire_cache_info(spec)
if not cache_info or cache_info.is_expired:
    path = await installation.install_package(spec)
    cachemgr.save_cache_info(CacheInfo(...))
    importation.add_package_to_import_path(path)
else:
    importation.add_package_to_import_path(cache_info.location)
```

**After (Cache-Driven):**
```python
# ~3 lines total
for specification in specifications:
    await cachemgr.ensure_package(specification)
```

## Configuration Integration

### Extension Configuration Format:
```toml
[[extensions]]
name = "sphinx"
enabled = true

[[extensions]]
name = "external_processor"
package = "sphinx-external-processor>=1.0.0"
enabled = true
[extensions.arguments]
timeout = 30
```

### Loading Process:
1. **Parse Configuration**: Extract and validate extension configurations
2. **Separate Extensions**: Built-in vs external based on `package` field
3. **Ensure External Packages**: Cache-driven installation and import path setup
4. **Register All Processors**: Unified registration for built-in and external

## Cache Architecture

### Cache Structure:
```
.auxiliary/caches/extensions/
├── {sha256(package_spec)}/
│   └── {platform_id}/
│       ├── .cache_metadata.json
│       └── {installed_packages}/
```

### Platform ID Format: 
`cpython-3.10--linux--x86_64`

### Cache Metadata:
```json
{
    "package_spec": "sphinx-external-processor>=1.0.0",
    "installed_at": "2024-01-15T10:30:00Z",
    "ttl_hours": 24,
    "platform_id": "cpython-3.10--linux--x86_64"
}
```

## Benefits Achieved

### 1. Simplified Client Code
- **Processors module**: Reduced from complex orchestration to simple `ensure_package()` calls
- **Single Responsibility**: Each module has clear, focused purpose
- **Better Error Handling**: Centralized installation retry logic and error management

### 2. Enhanced Testability
- **Dependency Injection**: Clean module-level imports allow easy mocking
- **Isolated Concerns**: Each module can be tested independently
- **Clear Interfaces**: Well-defined function signatures and responsibilities

### 3. Improved Performance
- **Parallel Installation**: Multiple packages install concurrently
- **Efficient Caching**: Platform-specific caching prevents binary compatibility issues
- **Smart Cache Management**: TTL prevents stale packages while avoiding constant reinstalls

### 4. Robust .pth File Support
- **Proper Encoding**: UTF-8-BOM support with locale fallbacks
- **Cross-Platform**: Hidden file detection across operating systems
- **Security**: Safe execution of import statements with error containment
- **Standards Compliance**: Follows Python site.py implementation patterns

## Error Handling

### Exception Types:
- `ExtensionInstallationError`: Package installation failures
- `ExtensionConfigError`: Configuration validation issues

### Error Scenarios:
1. **Installation Failure**: Individual package failures don't block others
2. **Cache Corruption**: Automatic cache invalidation and retry
3. **Import Conflicts**: Clear error messages for version conflicts
4. **Network Issues**: Retry with exponential backoff, graceful degradation

## Implementation History

### Phase 1: Rename and Enhance Import Management ✅
- Renamed `isolation.py` → `importation.py` for semantic clarity
- Added comprehensive .pth file processing with security and platform considerations
- Updated all imports and references throughout codebase

### Phase 2: Cache Manager Enhancement ✅  
- Added `ensure_package()` method with complete workflow orchestration
- Proper exception documentation using `__.ddoc.Raises` with actual exception classes
- Clean module-level imports for better testability

### Phase 3: Processor Simplification ✅
- Replaced complex `_install_packages()` with simple `_ensure_external_packages()`
- Eliminated direct installation and import path orchestration
- Reduced processor loading logic from ~15 lines to ~3 lines per package

### Phase 4: Convenience Methods ✅
- Added `invalidate()` method for clean cache management interface

### Phase 5: Testing and Documentation ✅
- All tests pass with new architecture (117/117 tests passing)
- Proper code style compliance and linting
- Documentation updated to reflect current implementation

## Future Enhancements

### Potential Improvements:
1. **Dependency Conflict Detection**: Analyze requirements before installation
2. **Cache Warming**: Pre-install commonly used extensions
3. **Health Checks**: Validate installed extensions periodically
4. **Advanced Import Isolation**: Full import isolation for complex dependency trees

### Plugin Marketplace Integration:
- Registry of validated extensions
- Extension compatibility checks
- Community extension discovery

## Success Metrics

### Functional Requirements: ✅ ALL COMPLETE
- ✅ Async parallel installation of external packages
- ✅ TTL-based cache management with automatic cleanup  
- ✅ Configurable retry logic with exponential backoff
- ✅ Platform-specific isolation preventing binary issues
- ✅ Graceful handling of installation failures
- ✅ Integration with existing extension configuration system
- ✅ Comprehensive .pth file processing
- ✅ Cache-driven package management with single responsibility

### Performance Requirements: ✅ ACHIEVED
- ✅ Parallel installation reduces total startup time
- ✅ Cache hits result in near-instantaneous loading
- ✅ Cache misses don't block other extension loading
- ✅ Simplified processor logic improves maintainability

### Reliability Requirements: ✅ VERIFIED
- ✅ Network failures don't prevent loading of other extensions
- ✅ Version conflicts reported clearly to users  
- ✅ Cache corruption automatically detected and resolved
- ✅ All 117 tests pass, ensuring backward compatibility

## Integration with Plugin Architecture

The xtnsmgr seamlessly integrates with the plugin architecture documented in `plugin-architecture.md`:

- **External Plugin Loading**: Supports Phase 3 requirements for external plugin installation
- **Configuration Integration**: Handles Phase 4 TOML `[[extensions]]` parsing
- **Plugin Registry**: Works with existing plugin registration system
- **Performance**: Enables async loading required for responsive MCP server

The extension manager provides the foundational infrastructure for the complete plugin ecosystem while maintaining simplicity and reliability.