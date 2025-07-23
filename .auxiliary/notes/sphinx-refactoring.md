# Sphinx Processor Refactoring Plan

## Current State

The `processors/sphinx.py` module is currently 683 lines and handles all Sphinx-related functionality:
- Detection and metadata extraction 
- Inventory processing and filtering
- Documentation extraction and parsing
- HTML to markdown conversion
- URL normalization and management

**Coverage**: 51% (168/369 statements missed, 146 branches, 13 branch parts)

## Refactoring Goals

1. **Break into logical subpackage** - Organize by functional areas
2. **Improve testability** - Smaller, focused modules are easier to test comprehensively
3. **Enhance maintainability** - Clearer separation of concerns
4. **Follow project guidelines** - Keep modules under 600 lines, functions under 30 lines

## Proposed Subpackage Structure

```
processors/
└── sphinx/
    ├── __init__.py          # Public API exports
    ├── detection.py         # SphinxProcessor.detect() and SphinxDetection
    ├── inventory.py         # Inventory extraction, filtering, and processing
    ├── documentation.py     # Documentation extraction and HTML parsing  
    ├── formatting.py        # HTML to markdown conversion utilities
    └── urls.py             # URL normalization and construction utilities
```

## Module Breakdown

### detection.py (~150 lines)
- `SphinxProcessor.detect()` method
- `SphinxDetection` dataclass  
- `_check_objects_inv()`, `_check_searchindex()`, `_detect_theme()` functions
- URL building for detection (`_build_html_url`, `_build_searchindex_url`)

### inventory.py (~200 lines)
- `SphinxProcessor.extract_inventory()` and `summarize_inventory()` methods
- `_extract_inventory()`, `_filter_inventory()` functions
- Filtering functions: `_filter_exact_and_regex_matching()`, `_filter_fuzzy_matching()`
- Helper functions: `_collect_matching_objects()`, `_create_term_matcher()`, `_format_inventory_object()`

### documentation.py (~150 lines)
- `SphinxProcessor.extract_documentation()` and `query_documentation()` methods
- `_fetch_html_content()`, `_parse_documentation_html()` functions
- URL and content utilities: `_extract_base_url()`, `_build_documentation_url()`
- Relevance scoring: `_calculate_relevance_score()`, `_extract_content_snippet()`

### formatting.py (~80 lines)
- `_html_to_markdown()` function
- HTML parsing and conversion utilities
- Text cleanup and formatting functions

### urls.py (~100 lines)
- `normalize_inventory_source()` function (moved from current location)
- URL construction and manipulation utilities
- Path and scheme handling functions

## Migration Strategy

1. **Phase 1**: Create subpackage structure and move functions
2. **Phase 2**: Update imports and maintain backward compatibility
3. **Phase 3**: Add comprehensive tests for each module
4. **Phase 4**: Optimize and refactor individual modules

## Testing Strategy

Each module should achieve >90% coverage:
- **detection.py**: Test all detection paths, theme detection, error handling
- **inventory.py**: Test filtering modes, edge cases, malformed inventories  
- **documentation.py**: Test HTML parsing, query scoring, content extraction
- **formatting.py**: Test markdown conversion edge cases
- **urls.py**: Test URL normalization, scheme handling, path resolution

## Backward Compatibility

Maintain full backward compatibility by:
- Re-exporting all public APIs from `__init__.py`
- Keeping `SphinxProcessor` class interface identical
- Preserving all function signatures and return types
- Ensuring no changes to MCP tool interfaces

## Success Criteria

- [ ] All modules under 200 lines
- [ ] >90% test coverage for each module
- [ ] All existing tests continue to pass
- [ ] Linters report no violations
- [ ] Clear separation of concerns between modules
- [ ] Improved code organization and readability