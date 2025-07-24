# URL Processing Anti-Pattern Analysis

## Current Anti-Pattern

The current code has **duplicated and inconsistent logic** for stripping `objects.inv` suffixes:

### 1. `_build_html_url()` (line 328)
```python
# TODO: Just pass in the base path instead of stripping suffixes.
path = normalized_source.path
if path.endswith( '/objects.inv' ):
    base_path = path[ :-12 ]           # Strip 12 chars
elif path.endswith( 'objects.inv' ):
    base_path = path[ :-11 ]           # Strip 11 chars  
else:
    base_path = path
normalized_base = base_path.rstrip( '/' ) + '/'
html_path = normalized_base + 'index.html'
```

### 2. `_build_searchindex_url()` (line 347)
```python
# TODO: Just pass in the base path instead of stripping suffixes.
path = normalized_source.path
if path.endswith( '/objects.inv' ):
    base_path = path[ :-12 ]           # EXACT SAME LOGIC
elif path.endswith( 'objects.inv' ):
    base_path = path[ :-11 ]           # EXACT SAME LOGIC
else:
    base_path = path
normalized_base = base_path.rstrip( '/' ) + '/'
searchindex_path = normalized_base + 'searchindex.js'
```

### 3. `_extract_base_url()` (line 457)
```python
url = normalize_inventory_source( source )
path = url.path.rstrip( '/objects.inv' )    # DIFFERENT APPROACH!
if not path.endswith( '/' ): path += '/'
```

## Problems with Current Approach

1. **Code Duplication**: Functions 1 & 2 have identical base path extraction logic
2. **Inconsistent Logic**: Function 3 uses simpler `rstrip()` vs. explicit length checks
3. **Multiple Responsibilities**: Each function does both "extract base" AND "build specific URL"
4. **TODO Comments**: The developers already identified this as problematic
5. **Maintenance Burden**: Changes to base URL logic need updates in multiple places

## Proposed Clean Architecture

### Core Insight: **Separate Base URL Extraction from Specific URL Construction**

```python
# Single responsibility: extract clean base URL from any source
def extract_base_url( source: str ) -> str:
    ''' Extract clean base documentation URL from any source. '''
    
# Simple builders that work from base URL  
def build_inventory_url( base_url: str ) -> str:
    ''' Build objects.inv URL from base URL. '''
    
def build_html_url( base_url: str ) -> str:
    ''' Build index.html URL from base URL. '''
    
def build_searchindex_url( base_url: str ) -> str:
    ''' Build searchindex.js URL from base URL. '''
    
def build_documentation_url( base_url: str, object_uri: str, object_name: str ) -> str:
    ''' Build documentation URL for specific object. '''
```

### Usage Pattern
```python
# Extract base URL once
base_url = extract_base_url( source )

# Build specific URLs as needed
inventory_url = build_inventory_url( base_url )
searchindex_url = build_searchindex_url( base_url )
doc_url = build_documentation_url( base_url, obj.uri, obj.name )
```

## Implementation Strategy

### Phase 1: Create Clean Base URL Function
```python
def extract_base_url( source: str ) -> str:
    ''' Extract clean base documentation URL from any source.
    
    Handles both inventory URLs and directory paths:
    - "https://docs.python.org/3/objects.inv" → "https://docs.python.org/3/"
    - "/path/to/docs/objects.inv" → "/path/to/docs/"
    - "/path/to/docs/" → "/path/to/docs/"
    '''
    normalized = normalize_inventory_source( source )
    path = normalized.path
    
    # Remove objects.inv suffix if present
    if path.endswith( '/objects.inv' ):
        path = path[:-12]  # Remove '/objects.inv'
    elif path.endswith( 'objects.inv' ):
        path = path[:-11]  # Remove 'objects.inv'
    
    # Ensure trailing slash
    if not path.endswith( '/' ):
        path += '/'
        
    return _urlparse.urlunparse(
        _urlparse.ParseResult(
            scheme=normalized.scheme, netloc=normalized.netloc, 
            path=path, params='', query='', fragment=''
        )
    )
```

### Phase 2: Create Simple URL Builders
```python
def build_inventory_url( base_url: str ) -> str:
    ''' Build objects.inv URL from base URL. '''
    return base_url.rstrip('/') + '/objects.inv'

def build_html_url( base_url: str ) -> str:
    ''' Build index.html URL from base URL. '''
    return base_url.rstrip('/') + '/index.html'

def build_searchindex_url( base_url: str ) -> str:
    ''' Build searchindex.js URL from base URL. '''
    return base_url.rstrip('/') + '/searchindex.js'

def build_documentation_url( base_url: str, object_uri: str, object_name: str ) -> str:
    ''' Build documentation URL for specific object. '''
    uri_with_name = object_uri.replace( '$', object_name )
    return f"{base_url.rstrip('/')}/{uri_with_name}"
```

### Phase 3: Update All Callers
Replace the complex functions with simple base URL + builder pattern.

## Benefits

1. **Single Responsibility**: Each function has one clear purpose
2. **No Code Duplication**: Base URL extraction logic exists once
3. **Consistent Logic**: All URL building uses same base URL approach
4. **Easier Testing**: Small, focused functions are easier to test
5. **Better Performance**: Extract base URL once, reuse for multiple URLs
6. **Clearer Intent**: Function names clearly indicate what URL they build

## Migration Impact

### Functions to Update:
- `SphinxProcessor.detect()` - use base URL + builders
- `_check_objects_inv()` - could work with inventory URL directly
- `_check_searchindex()` - use base URL + builder
- `_detect_theme()` - use base URL + builder
- All documentation extraction methods

### Functions to Remove:
- `_build_html_url()` - replace with `build_html_url(extract_base_url(...))`
- `_build_searchindex_url()` - replace with `build_searchindex_url(...)`
- Current `_extract_base_url()` - replace with cleaner version

This refactoring eliminates the anti-pattern while making the code more maintainable and testable.