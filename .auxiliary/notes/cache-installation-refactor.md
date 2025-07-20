# Cache-Installation Architecture Refactor

## Overview

This document outlines a refactoring of the extension manager (`xtnsmgr`) to make the cache responsible for package installation orchestration, eliminating the current split between cache management and installation logic.

## Current Architecture Problems

### Separation of Concerns Issues
- **Split Responsibility**: Cache manages metadata, installation handles actual package retrieval, processors orchestrates between them
- **Complex Orchestration**: Processors module must coordinate cache checks, installation, and import path management
- **Leaky Abstractions**: Callers need to understand cache hits/misses and handle installation explicitly

### Code Structure
```
processors.py:
  - Checks cache via cachemgr.acquire_cache_info()
  - Calls installation.install_packages_parallel() if needed
  - Calls isolation.add_to_import_path() for each result
  - Handles error cases from multiple sources

cachemgr.py:
  - Pure cache metadata management
  - No knowledge of how to populate cache

installation.py:
  - Package installation logic
  - No knowledge of cache integration
```

## Proposed Architecture

### Core Principle
**"Installation is fundamentally a cache-miss handler, not a separate concern."**

The cache should own the complete contract of "make this package importable", which includes:
1. Checking cache for existing installation
2. Installing package if not cached or expired
3. Adding package to sys.path (including .pth file processing)
4. Updating cache metadata

### Module Responsibilities

#### `cachemgr.py` - Enhanced Cache Manager
- **Primary Interface**: `async def ensure_package(specification: str) -> None`
- **Responsibility**: Ensure package is installed and importable
- **Delegates to**:
  - `importation.py` for sys.path and .pth management
  - `installation.py` for actual package installation
  - Existing cache metadata functions

#### `importation.py` - Import Path Management (renamed from `isolation.py`)
- **Responsibility**: Manage Python import system
- **Functions**:
  - `add_package_to_import_path(package_path: Path) -> None`
  - `process_pth_files(package_path: Path) -> None` (new)
  - `remove_package_from_import_path(package_path: Path) -> None`
  - `import_processor_module(module_name: str) -> types.ModuleType`
  - `cleanup_import_paths() -> None`

#### `installation.py` - Package Installation
- **Responsibility**: Pure package installation logic (unchanged interface)
- **Functions**: Current functions remain unchanged
- **Usage**: Called by cachemgr when cache miss occurs

#### `processors.py` - Simplified Orchestration
- **Responsibility**: Extension registration workflow
- **Simplified flow**:
  ```python
  for ext in external_extensions:
      await cachemgr.ensure_package(ext['package'])
  for ext in all_extensions:
      _register_processor(ext)
  ```

### New Interface Design

```python
# cachemgr.py
async def ensure_package( specification: str ) -> None:
    ''' Ensure package is installed and importable.

    Raises:
        ExtensionInstallationError: If installation fails
        ExtensionConfigError: If package specification is invalid
    '''

def invalidate( specification: str ) -> None:
    ''' Remove package from cache, forcing reinstall on next ensure_package. '''

# importation.py
def add_package_to_import_path( package_path: __.Path ) -> None:
    ''' Add package to sys.path and process any .pth files. '''

def process_pth_files( package_path: __.Path ) -> None:
    ''' Process .pth files in package directory to update sys.path. '''
```

## Migration Plan

### Phase 1: Rename and Enhance Importation Module
- [ ] Rename `isolation.py` to `importation.py`
- [ ] Add `process_pth_files()` function for .pth file handling
- [ ] Update `add_package_to_import_path()` to call `process_pth_files()`
- [ ] Update all imports throughout codebase

### Phase 2: Enhance Cache Manager
- [ ] Add `ensure_package()` method to cache manager
- [ ] Implement installation orchestration within `ensure_package()`
- [ ] Add dependency injection for installer function (optional, defaults to current)
- [ ] Ensure proper error handling and logging

### Phase 3: Simplify Processors Module
- [ ] Refactor `register_processors()` to use `cachemgr.ensure_package()`
- [ ] Remove direct calls to installation and importation modules
- [ ] Simplify error handling (cache manager handles installation errors)

### Phase 4: Add Convenience Method
- [ ] Add `invalidate()` method to cache manager
- [ ] Update cache cleanup functions to work with new interface

### Phase 5: Testing and Documentation
- [ ] Update tests to reflect new interfaces
- [ ] Verify .pth file processing works correctly
- [ ] Update documentation and docstrings

## Benefits

### Simplified Client Code
**Before:**
```python
cache_info = cachemgr.acquire_cache_info(spec)
if not cache_info or cache_info.is_expired:
    path = await installation.install_package(spec)
    cachemgr.save_cache_info(CacheInfo(...))
    isolation.add_to_import_path(path)
else:
    isolation.add_to_import_path(cache_info.location)
```

**After:**
```python
await cachemgr.ensure_package(spec)
```

### Better Separation of Concerns
- Cache owns "make package importable" contract
- Installation module remains focused on pure installation
- Importation module focuses on Python import system
- Processors module focuses on registration logic

### Improved Error Handling
- Single point for installation retry logic
- Consistent error types and messages
- Cache can implement fallback strategies

### Enhanced Testability
- Each module has clear, focused responsibility
- Easier to mock dependencies
- Installation logic can be tested independently via dependency injection

## Implementation Notes

### .pth File Processing
```python
def process_pth_files( package_path: __.Path ) -> None:
    ''' Process .pth files to update sys.path. '''
    for pth_file in package_path.glob( "*.pth" ):
        with pth_file.open( 'r', encoding = 'utf-8' ) as f:
            for line in f:
                line = line.strip( )
                if line and not line.startswith( '#' ):
                    if line.startswith( 'import ' ):
                        # Execute import statement
                        exec( line )
                    else:
                        # Add path to sys.path
                        path = package_path / line
                        if path.exists( ):
                            __.sys.path.insert( 0, str( path ) )
```

### Dependency Injection Pattern
```python
# Allow custom installer for testing
async def ensure_package(
    specification: str,
    installer: __.cabc.Callable[ [ str ], __.cabc.Awaitable[ __.Path ] ] = installation.install_package
) -> None:
    # Implementation uses provided installer function
```

## Risk Mitigation

### Backward Compatibility
- Keep existing functions in `cachemgr.py` during transition
- Deprecate old patterns gradually
- Ensure tests pass at each migration phase

### Rollback Strategy
- Each phase can be reverted independently
- Git commits structured to allow partial rollbacks
- Existing functionality preserved until full migration complete
