# Sphinx Extension Refactoring Implementation Plan

## Overview

This document outlines the implementation plan for refactoring the current Sphinx-specific code in `functions.py` into the new plugin architecture. The goal is to move Sphinx-specific functionality into the `processors/sphinx.py` processor while maintaining backward compatibility.

## Current State Analysis

The `functions.py` file is currently **heavily Sphinx-specific** (~65% of the code):
- **65% Sphinx-specific functionality** (inventory processing, HTML parsing, sphobjinv usage)
- **25% Generic/reusable functionality** (content processing, URL handling)
- **10% Public API/wrapper functions** (should remain for compatibility)

## Architecture Benefits

This refactoring will:
1. **Enable multi-format support** - Core functions become format-agnostic
2. **Maintain backward compatibility** - Public API functions remain unchanged
3. **Improve modularity** - Each processor owns its specific logic
4. **Reduce coupling** - Core functions no longer depend on sphobjinv
5. **Enable better testing** - Processors can be tested independently

## Phase 1: Create Sphinx Processor Methods

### 1.1 Add inventory processing methods to `SphinxProcessor`

```python
# In processors/sphinx.py
class SphinxProcessor:
    async def extract_inventory(self, source: str, **kwargs) -> dict
    async def summarize_inventory(self, source: str, **kwargs) -> str
    async def extract_documentation(self, source: str, object_name: str, **kwargs) -> dict
    async def query_documentation(self, source: str, query: str, **kwargs) -> list
```

### 1.2 Move Sphinx-specific helper methods

**Functions to move from `functions.py` to `SphinxProcessor`:**

**Core Sphinx Inventory Processing:**
- `_extract_inventory()` - Direct sphobjinv.Inventory usage
- `_filter_inventory()` - Sphinx object filtering
- `_collect_matching_objects()` - Sphinx-specific object collection
- `_create_term_matcher()` - Sphinx object matching logic
- `_filter_exact_and_regex_matching()` - Sphinx filtering implementations
- `_filter_fuzzy_matching()` - Uses sphobjinv.suggest()
- `_extract_names_from_suggestions()` - Parses sphobjinv format
- `_format_inventory_object()` - Formats sphobjinv objects

**Sphinx Documentation Processing:**
- `extract_documentation()` - Sphinx HTML extraction
- `query_documentation()` - Sphinx documentation querying
- `_extract_base_url()` - Sphinx inventory URL handling
- `_build_documentation_url()` - Sphinx URL construction
- `_parse_documentation_html()` - Sphinx HTML structure parsing
- `_fetch_html_content()` - HTTP fetching (Sphinx-specific implementation)

## Phase 2: Update Core Functions to Delegate

### 2.1 Update `functions.py` public API functions

```python
async def extract_inventory(source: str, **kwargs) -> dict:
    """Extract inventory - delegates to appropriate processor."""
    detection_result = await detect_source(source)
    if not detection_result:
        raise InventoryInaccessibility(f"No processor found for source: {source}")
    
    processor_name = detection_result['detector_name']
    processor = xtnsapi.processors[processor_name]
    return await processor.extract_inventory(source, **kwargs)
```

### 2.2 Apply similar pattern to

- `summarize_inventory()`
- `extract_documentation()`
- `query_documentation()`

### 2.3 Keep in Core Functions

**Generic Content Processing:**
- `_calculate_relevance_score()` - Generic relevance algorithm
- `_extract_content_snippet()` - Generic snippet extraction
- `_html_to_markdown()` - Generic HTML conversion

**Public API Functions (as thin wrappers):**
- `extract_inventory()` - Delegate to appropriate processor
- `summarize_inventory()` - Delegate to appropriate processor
- `normalize_inventory_source()` - Generic URL/path normalization

**Type Aliases:**
- Keep most type aliases for public API consistency
- Move Sphinx-specific types to processor

## Phase 3: Move Dependencies and Update Imports

### 3.1 Move sphinx-specific dependencies

- `sphobjinv` imports move to `processors/sphinx.py`
- `BeautifulSoup` imports move to `processors/sphinx.py`
- Update `pyproject.toml` if needed

### 3.2 Update imports throughout codebase

- Remove sphobjinv imports from `functions.py`
- Update any direct imports of moved functions

## Phase 4: Update Tests

### 4.1 Update integration tests

- Test that delegation works correctly
- Test that detection → processor selection → processing pipeline works

### 4.2 Add processor-specific tests

- Test sphinx processor methods directly
- Test error handling when no processor found

### 4.3 Update function tests

- Ensure they still work with the delegation approach
- Mock the detection system if needed

## Phase 5: Update CLI and Server

### 5.1 Update CLI commands

- Ensure they work with the new delegation approach
- May need to handle processor registration timing

### 5.2 Update MCP server

- Ensure MCP tools work with delegation
- Test that processor registration happens correctly

## Implementation Details

### Error Handling Strategy
- If no processor detected: raise clear error about unsupported format
- If processor detected but processing fails: let processor-specific errors bubble up
- Maintain existing error types for backward compatibility

### Testing Strategy
- Keep existing integration tests working
- Add new tests for processor-specific functionality
- Test the delegation mechanism explicitly

### Backward Compatibility
- All existing function signatures remain unchanged
- All existing error types remain available
- Existing CLI commands continue to work

### Migration Path
1. Implement processor methods
2. Update delegation in functions.py
3. Move internal functions to processor
4. Update tests
5. Clean up unused imports

## Success Criteria

- [ ] All existing tests continue to pass
- [ ] CLI commands work unchanged
- [ ] MCP server functionality unchanged
- [ ] New processor methods work correctly
- [ ] Delegation mechanism works properly
- [ ] Dependencies properly isolated
- [ ] Code coverage maintained
- [ ] Documentation updated

## Next Steps

1. Begin Phase 1 implementation
2. Create processor methods in sphinx.py
3. Test processor methods work correctly
4. Move to Phase 2 delegation implementation