# Sphinx Processor Refactoring Plan

## Current State

**File**: `sources/sphinxmcps/processors/sphinx.py` (684 lines)
**Coverage**: 51% (168/369 statements missed, 146 branches, 13 branch parts)

The module handles all Sphinx-related functionality:
- Detection and metadata extraction 
- Inventory processing and filtering
- Documentation extraction and parsing
- HTML to markdown conversion
- URL normalization and management

## Function Inventory

| Line | Function | Lines | Category | Description |
|------|----------|-------|----------|-------------|
| 35   | `normalize_inventory_source` | ~30 | URLs | Parse and normalize inventory URLs |
| 66   | `SphinxProcessor` class | ~210 | Core | Main processor with 4 methods |
| 276  | `SphinxDetection` class | ~20 | Detection | Detection result dataclass |
| 296  | `_build_documentation_url` | ~10 | URLs | Build doc URLs from base + URI |
| 305  | `_calculate_relevance_score` | ~20 | Scoring | Calculate query relevance |
| 328  | `_build_html_url` | ~15 | URLs | Build HTML URL from objects.inv |
| 345  | `_build_searchindex_url` | ~15 | URLs | Build searchindex.js URL |
| 362  | `_check_objects_inv` | ~15 | Detection | Check if objects.inv exists |
| 378  | `_check_searchindex` | ~15 | Detection | Check if searchindex.js exists |
| 395  | `_collect_matching_objects` | ~20 | Filtering | Collect objects matching filters |
| 418  | `_create_term_matcher` | ~15 | Filtering | Create term matching function |
| 434  | `_detect_theme` | ~20 | Detection | Detect Sphinx theme |
| 455  | `_extract_base_url` | ~10 | URLs | Extract base URL from source |
| 466  | `_extract_content_snippet` | ~15 | Content | Extract content snippet |
| 483  | `_extract_inventory` | ~20 | Inventory | Extract sphobjinv inventory |
| 504  | `_extract_names_from_suggestions` | ~10 | Filtering | Extract names from fuzzy suggestions |
| 516  | `_fetch_html_content` | ~25 | Content | Fetch HTML from URL or file |
| 542  | `_filter_exact_and_regex_matching` | ~10 | Filtering | Filter with exact/regex |
| 556  | `_filter_fuzzy_matching` | ~15 | Filtering | Filter with fuzzy matching |
| 572  | `_filter_inventory` | ~15 | Filtering | Main inventory filtering |
| 590  | `_format_inventory_object` | ~15 | Formatting | Format object for output |
| 605  | `_html_to_markdown` | ~25 | Formatting | Convert HTML to markdown |
| 629  | `_parse_documentation_html` | ~40 | Content | Parse HTML content |
| 669  | `register` | ~15 | Registry | Create processor instance |

## SphinxProcessor Methods

| Method | Lines | Purpose |
|--------|-------|---------|
| `detect()` | ~35 | Source detection with confidence scoring |
| `extract_inventory()` | ~35 | Extract and filter inventory objects |
| `summarize_inventory()` | ~40 | Create human-readable inventory summary |
| `extract_documentation()` | ~35 | Extract docs for specific object |
| `query_documentation()` | ~60 | Query docs with relevance ranking |

## Functional Categories

### 1. Detection & Metadata (~100 lines)
- `SphinxDetection` class
- `SphinxProcessor.detect()`
- `_check_objects_inv()`, `_check_searchindex()`, `_detect_theme()`

### 2. URL Management (~70 lines) 
- `normalize_inventory_source()`
- `_build_html_url()`, `_build_searchindex_url()`
- `_build_documentation_url()`, `_extract_base_url()`

### 3. Inventory Processing (~150 lines)
- `SphinxProcessor.extract_inventory()`, `summarize_inventory()`
- `_extract_inventory()`, `_filter_inventory()`
- `_filter_exact_and_regex_matching()`, `_filter_fuzzy_matching()`
- `_collect_matching_objects()`, `_create_term_matcher()`
- `_format_inventory_object()`, `_extract_names_from_suggestions()`

### 4. Documentation Extraction (~120 lines)
- `SphinxProcessor.extract_documentation()`, `query_documentation()`
- `_fetch_html_content()`, `_parse_documentation_html()`
- `_calculate_relevance_score()`, `_extract_content_snippet()`

### 5. Content Formatting (~50 lines)
- `_html_to_markdown()`
- HTML parsing and conversion utilities

### 6. Registry (~15 lines)
- `register()` function

## Refactoring Goals

1. **Break into logical subpackage** - Organize by functional areas
2. **Improve testability** - Smaller, focused modules are easier to test comprehensively
3. **Enhance maintainability** - Clearer separation of concerns
4. **Follow project guidelines** - Keep modules under 600 lines, functions under 30 lines

## Proposed Subpackage Structure

```
processors/sphinx/
├── __init__.py           # Re-export SphinxProcessor, register()
├── core.py              # SphinxProcessor class (~150 lines)
├── detection.py         # SphinxDetection + detection functions (~100 lines)
├── urls.py              # URL manipulation functions (~70 lines)  
├── inventory.py         # Inventory processing (~150 lines)
├── extraction.py        # Documentation extraction (~120 lines)
└── conversion.py        # HTML to markdown conversion (~50 lines)
```

## Module Breakdown

### core.py (~150 lines)
- `SphinxProcessor` class with all 5 methods
- Main processor coordination and method delegation

### detection.py (~100 lines)
- `SphinxDetection` dataclass  
- `_check_objects_inv()`, `_check_searchindex()`, `_detect_theme()` functions
- Detection-related utilities

### urls.py (~70 lines)
- `normalize_inventory_source()` function
- `_build_html_url()`, `_build_searchindex_url()`, `_build_documentation_url()`
- `_extract_base_url()` and URL construction utilities
- Path and scheme handling functions

### inventory.py (~150 lines)
- `_extract_inventory()`, `_filter_inventory()` functions
- Filtering functions: `_filter_exact_and_regex_matching()`, `_filter_fuzzy_matching()`
- Helper functions: `_collect_matching_objects()`, `_create_term_matcher()`, `_format_inventory_object()`
- `_extract_names_from_suggestions()` function

### extraction.py (~120 lines)
- `_fetch_html_content()`, `_parse_documentation_html()` functions
- Relevance scoring: `_calculate_relevance_score()`, `_extract_content_snippet()`
- Documentation parsing and content extraction utilities

### conversion.py (~50 lines)
- `_html_to_markdown()` function
- HTML parsing and conversion utilities
- Text cleanup and formatting functions

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

## URL Processing Anti-Pattern Resolution

### Current Problem
The code has **duplicated and inconsistent logic** for URL manipulation:

1. `_build_html_url()` and `_build_searchindex_url()` have **identical** base path extraction logic
2. `_extract_base_url()` uses **different approach** (rstrip vs explicit length checks)  
3. **TODO comments** in code acknowledge this as problematic
4. Each function does both "extract base" AND "build specific URL" (multiple responsibilities)

### Proposed Clean Architecture

**Core Insight**: Separate base URL extraction from specific URL construction

```python
# Single responsibility functions
def extract_base_url( source: str ) -> str:
    ''' Extract clean base documentation URL from any source. '''

def build_inventory_url( base_url: str ) -> str:
def build_html_url( base_url: str ) -> str:  
def build_searchindex_url( base_url: str ) -> str:
def build_documentation_url( base_url: str, object_uri: str, object_name: str ) -> str:
```

**Usage Pattern**:
```python
# Extract once, reuse multiple times
base_url = extract_base_url( source )
inventory_url = build_inventory_url( base_url )
searchindex_url = build_searchindex_url( base_url )
```

### Benefits
- **Eliminates code duplication** - base URL logic exists once
- **Consistent approach** - all URL building uses same base
- **Single responsibility** - each function has clear purpose  
- **Better performance** - extract base URL once, reuse
- **Easier testing** - small, focused functions

### Impact on Subpackage Design
This URL refactoring should be done **before** the subpackage split to:
1. Reduce the code that needs to be moved
2. Simplify the `urls.py` module design
3. Eliminate anti-pattern debt in the new architecture

## Success Criteria

- [ ] All modules under 200 lines
- [ ] >90% test coverage for each module
- [ ] All existing tests continue to pass
- [ ] Linters report no violations
- [ ] Clear separation of concerns between modules
- [ ] Improved code organization and readability
- [ ] URL anti-pattern eliminated with clean base URL + builder pattern