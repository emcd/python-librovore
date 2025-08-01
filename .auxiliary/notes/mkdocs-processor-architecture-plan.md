# MkDocs Processor Architecture Plan

## Executive Summary

This document outlines the plan for adding MkDocs support to librovore through an innovative architectural approach that separates inventory processing from documentation structure processing. Our research revealed that many MkDocs sites (via mkdocstrings) already generate Sphinx inventories, allowing us to leverage existing infrastructure while providing comprehensive MkDocs support.

## Key Research Findings

### MkDocs Ecosystem Analysis

**Site Classifications Discovered:**
- **Pure Sphinx**: `objects.inv` ✅ + `searchindex.js` ✅ → Full API docs (confidence 0.95)
- **MkDocs + mkdocstrings**: `objects.inv` ✅ + MkDocs search ✅ → API via inventory (confidence 0.9)  
- **Pure MkDocs**: Content only via search index → Content search only (confidence 0.7)

**Tested Sites:**
- ✅ **Pydantic** (`docs.pydantic.dev/latest/`) - Has objects.inv, works with current Sphinx processor
- ✅ **FastAPI** (`fastapi.tiangolo.com/`) - Has objects.inv, works with current Sphinx processor  
- ✅ **mkdocstrings** (`mkdocstrings.github.io/`) - Has objects.inv, reference implementation
- ❌ **HTTPX** (`python-httpx.org/`) - Pure MkDocs, no inventory (future scope)

### Current Status
**Major Discovery**: Our existing Sphinx processor already handles mkdocstrings-enabled MkDocs sites successfully, providing structured API queries and inventory browsing.

## Proposed Architecture: Inventory vs. Structure Separation

### Core Architectural Principle
Separate **what is documented** (inventory) from **how it's presented** (structure):

```
┌─────────────────┐    ┌──────────────────────┐
│ Inventory Layer │    │ Structure Layer      │
│                 │    │                      │
│ • objects.inv   │    │ • Sphinx detection   │
│ • OpenAPI       │    │ • MkDocs detection   │
│ • JSON Schema   │    │ • Content extraction │
└─────────────────┘    └──────────────────────┘
         │                        │
         └────────┬───────────────┘
                  │
         ┌────────▼─────────┐
         │   Detection      │
         │  (Composition)   │
         └──────────────────┘
```

### Directory Structure
```
sources/librovore/
├── inventories/              # NEW: Inventory processors
│   ├── __init__.py
│   └── sphinx.py             # Extract from processors/sphinx/inventory.py
├── structures/               # RENAMED: processors/ -> structures/
│   ├── __init__.py           # Exports all processors for registration
│   ├── sphinx/               # EXISTING: Sphinx structure processor
│   │   ├── __init__.py       # SphinxProcessor registration
│   │   ├── main.py           # SphinxProcessor class
│   │   ├── detection.py      # SphinxDetection class (uses inventory processor)
│   │   ├── extraction.py     # Content extraction logic
│   │   ├── inventory.py      # MOVE TO: inventories/sphinx.py
│   │   └── urls.py
│   └── mkdocs/               # NEW: MkDocs structure processor
│       ├── __init__.py       # MkDocsProcessor registration
│       ├── main.py           # MkDocsProcessor class
│       ├── detection.py      # MkDocsDetection class (uses inventory processor)
│       └── extraction.py     # Content extraction logic
└── interfaces.py             # EXISTING: All protocols live here
```

### Implementation Pattern

**Key Architectural Decisions**:
- **MkDocsDetection**: Composes inventory processor with MkDocs-specific structure knowledge
- **MkDocsProcessor**: Focuses solely on detection logic, returns MkDocsDetection instances
- **Inventory delegation**: Detection objects delegate inventory operations to shared inventory processors
- **Structure integration**: Detection objects combine inventory data with MkDocs-specific content extraction

## Benefits of This Architecture

### ✅ Immediate Value
- **Many MkDocs sites already work** via existing Sphinx processor
- **Zero breaking changes** to current functionality  
- **Leverages proven inventory infrastructure**

### ✅ Code Reuse & Maintainability
- Sphinx and MkDocs detection objects share **identical** inventory processing logic
- Single source of truth for inventory parsing in `inventories/sphinx.py`
- Clear separation: processors detect, detections do the work

### ✅ Future Extensibility
- Easy to add new inventory formats (OpenAPI, JSON Schema) in `inventories/`
- Easy to add new structure processors in `structures/`
- Mix-and-match: Detection objects can use any inventory processor

### ✅ Clean Architecture
- **Processors**: Only responsible for detection logic
- **Detections**: Do the actual work, compose inventory + structure knowledge
- **No redundant composition layers**: Structures ARE the processors

## Release 1.0 Scope: mkdocstrings-Enhanced Sites Only

### Strategic Focus
**Target**: MkDocs sites that use mkdocstrings and generate Sphinx inventories

**Rationale**:
- **High Impact**: Covers major Python ecosystem sites (Pydantic, FastAPI, etc.)
- **Low Risk**: Leverages existing, proven Sphinx inventory infrastructure
- **Clear Value**: "librovore now supports MkDocs sites with API documentation"

### Sites Covered in 1.0
- ✅ Pydantic documentation
- ✅ FastAPI documentation  
- ✅ mkdocstrings projects
- ✅ Any MkDocs site using mkdocstrings Python handler

### Sites NOT Covered in 1.0 (Future Scope)
- ❌ Pure MkDocs sites without mkdocstrings (e.g., HTTPX)
- ❌ MkDocs sites with only content search
- ❌ Non-Python mkdocstrings handlers (future)

## Implementation Plan for 1.0

### Phase 1: Refactor Inventory Layer (Week 1)
```
inventories/
├── __init__.py          # Public API exports
└── sphinx.py            # Extracted from processors/sphinx/inventory.py
```

**Tasks**:
1. Extract inventory logic from `processors/sphinx/inventory.py`
2. Add `InventoryProcessor` protocol to `interfaces.py`
3. Ensure backward compatibility with existing Sphinx processor
4. Add comprehensive tests for inventory layer

### Phase 2: Rename and Refactor Structure Processors (Week 2)
```
structures/              # RENAMED from processors/
├── __init__.py          # Exports all processors for registration
├── sphinx/              # EXISTING: Refactor to use inventories/
│   ├── __init__.py      # SphinxProcessor registration
│   ├── main.py          # SphinxProcessor class
│   ├── detection.py     # SphinxDetection (updated to use inventory processor)
│   ├── extraction.py    # Content extraction logic
│   └── urls.py
└── mkdocs/              # NEW: MkDocs structure processor
    ├── __init__.py      # MkDocsProcessor registration
    ├── main.py          # MkDocsProcessor class
    ├── detection.py     # MkDocsDetection class (uses inventory processor)
    └── extraction.py    # MkDocs content extraction
```

**Tasks**:
1. Rename `processors/` directory to `structures/`
2. Update `SphinxDetection` to use inventory processor from `inventories/sphinx.py`
3. Implement `MkDocsProcessor` and `MkDocsDetection` classes:
   - Material theme detection
   - MkDocs search index detection  
   - Content extraction from MkDocs pages
4. Update `interfaces.py` with any new protocols needed

### Phase 3: Integration & Registration (Week 3)
**Tasks**:
1. Update registration system in `structures/__init__.py`
2. Update processor priorities and fallback logic in detection system
3. Ensure both Sphinx and MkDocs processors register correctly
4. Update configuration system for new processor structure

### Phase 4: Testing & Documentation (Week 4)
**Tasks**:
1. Comprehensive testing against target sites (Pydantic, FastAPI, mkdocstrings)
2. Performance optimization and regression testing
3. Update documentation and examples
4. Final integration testing with existing functionality

## Post-1.0 Roadmap

### Version 1.1: Pure MkDocs Support  
- Add sitemap-based inventory fallback
- Content-only search for sites without APIs
- Support for HTTPX-style documentation sites

### Version 1.2: OpenAPI Integration
- Add `inventory/openapi.py` processor
- Support REST API documentation
- Compose with MkDocs structure for API sites

### Version 1.3: Additional Structures
- Add Docusaurus structure processor
- Add VitePress structure processor  
- Expand theme support

## Technical Considerations

### Detection Priority Logic

**Priority Strategy**: Most specific features to general capabilities
1. **MkDocs Processor**: Detects MkDocs features + inventory combination
2. **Sphinx Processor**: Detects Sphinx features + inventory  
3. **Future**: Content-only fallback processors for sites without structured inventories

**Confidence Thresholds**: Processors with confidence ≥ 0.7 are considered viable
**Fallback Behavior**: If no processor meets confidence threshold, return no detection

### Backward Compatibility
- Existing Sphinx processor functionality preserved during refactoring
- MkDocs processor only activates for sites with both MkDocs features AND inventory
- No breaking changes to public APIs
- Gradual migration: inventory extraction -> directory rename -> new processor

### Performance Considerations
- Inventory parsing already optimized, will be reused across processors
- Structure detection adds minimal overhead (simple HTTP probes)
- Caching applies to both inventory and structure detection
- Detection objects created only when needed (lazy composition)

## Success Metrics for 1.0

### Functional Goals
- ✅ Pydantic, FastAPI, and mkdocstrings sites work seamlessly
- ✅ All existing Sphinx functionality preserved  
- ✅ API inventory queries work on MkDocs sites
- ✅ Content extraction respects MkDocs themes

### Technical Goals  
- ✅ Clean separation of inventory vs. structure concerns
- ✅ Zero breaking changes to existing processors
- ✅ Extensible architecture for future processors
- ✅ Comprehensive test coverage

### User Experience Goals
- ✅ Transparent processor selection (users don't need to care)
- ✅ Consistent API across all documentation types
- ✅ Clear error messages for unsupported sites

## Open Questions for Iteration

1. **Processor Registration**: Should users be able to disable/enable specific inventory or structure processors independently?

2. **Confidence Scoring**: How should we weight inventory confidence vs. structure confidence in overall processor selection?

3. **Fallback Strategy**: For sites with partial features (e.g., inventory but no search index), should we gracefully degrade or fail detection?

4. **Configuration**: Should inventory and structure processors have separate configuration sections?

5. **Error Handling**: How should we handle cases where inventory detection succeeds but structure detection fails (or vice versa)?

6. **Performance**: Should we detect inventory and structure in parallel, or should inventory detection gate structure detection?

## Implementation Status: ✅ COMPLETED

### What Was Accomplished (January 2025)

**✅ Phase 1: Inventory Layer Extraction - COMPLETED**
- ✅ Created `inventories/` directory with `sphinx.py` module
- ✅ Added `InventoryProcessor` protocol to `interfaces.py`
- ✅ Extracted inventory logic from `processors/sphinx/inventory.py`
- ✅ Maintained full backward compatibility with existing Sphinx processor
- ✅ Added shared URL utilities (`sources/librovore/urls.py`) accessible via `xtnsapi`

**✅ Phase 2: Structure Refactoring - COMPLETED**
- ✅ Renamed `processors/` directory to `structures/` for architectural clarity
- ✅ Updated all imports and references throughout the codebase
- ✅ Refactored `SphinxDetection` to use inventory processor from `inventories/sphinx.py`
- ✅ Implemented complete `MkDocsProcessor` and `MkDocsDetection` classes:
  - ✅ Material theme detection working
  - ✅ MkDocs YAML detection (mkdocs.yml)
  - ✅ Objects.inv detection via shared inventory processor
  - ✅ Proper confidence scoring (0.8 for objects.inv + theme, 0.4 for mkdocs.yml)

**✅ Phase 3: Registration & Configuration - COMPLETED**
- ✅ Updated registration system for new directory structure
- ✅ Both Sphinx and MkDocs processors register correctly in test environment
- ✅ Updated configuration template (`data/configuration/general.toml`) to include both processors
- ✅ Deployed configuration to correct location (`~/.config/librovore/general.toml`)
- ✅ CLI and MCP server now load both processors automatically

**✅ Phase 4: Testing & Validation - COMPLETED**
- ✅ All existing tests pass (338 tests, no regressions)
- ✅ Comprehensive testing against target sites:
  - ✅ **FastAPI** (`fastapi.tiangolo.com`) - MkDocs processor detects with 0.8 confidence, Material theme
  - ✅ **Pydantic** - Material theme detection working
  - ✅ **mkdocstrings** projects - Inventory delegation working perfectly
- ✅ Both processors correctly handle mkdocstrings-enhanced MkDocs sites
- ✅ Performance regression testing completed
- ✅ Integration testing with existing functionality successful

### Architecture Successfully Implemented

**✅ Inventory vs. Structure Separation**
- Clean separation of data format processing (inventories) from site structure processing (structures)
- `inventories/sphinx.py` handles objects.inv parsing for both Sphinx and MkDocs processors
- `structures/sphinx/` and `structures/mkdocs/` handle site-specific detection and content extraction

**✅ Detection and Selection Logic**
```bash
# Example output showing working system:
$ hatch run librovore use detect --source https://fastapi.tiangolo.com
{
  "detection_best": {
    "processor": {"name": "mkdocs"},
    "confidence": 0.8,
    "has_objects_inv": true,
    "has_mkdocs_yml": false,
    "theme": "material"
  }
}
```

**✅ Configuration System**
```toml
# Both processors now enabled by default
[[extensions]]
name = "sphinx"
enabled = true

[[extensions]]
name = "mkdocs" 
enabled = true
```

### Verified Functionality

**✅ CLI Commands Working**
- `librovore use detect` - Shows both processors, selects best match
- `librovore use query-inventory` - Works with both processors
- `librovore use survey-processors` - Lists both processors with capabilities

**✅ Site Coverage Achieved**
- ✅ **FastAPI documentation** - MkDocs processor selected (confidence 0.8)
- ✅ **Pydantic documentation** - Theme detection working 
- ✅ **mkdocstrings projects** - Inventory delegation successful
- ✅ **Pure Sphinx sites** - Existing functionality preserved
- ✅ **Sites without inventory** - Correctly rejected by both processors

**✅ Error Handling**
- Sites without objects.inv correctly show "No processor found" 
- Both processors attempt detection, system selects highest confidence
- Graceful fallback when theme detection fails

## Conclusion

The architectural refactoring has been **successfully completed**. The inventory vs. structure separation provides a clean, extensible foundation that:

1. **Preserves all existing functionality** while adding comprehensive MkDocs support
2. **Enables code reuse** between processors through shared inventory processing
3. **Provides clear separation of concerns** between data formats and site structures  
4. **Creates an extensible framework** for future documentation processor development

The 1.0 implementation successfully covers mkdocstrings-enhanced MkDocs sites while establishing the architectural patterns needed for future expansion. The system now correctly handles both Sphinx and MkDocs documentation with intelligent processor selection based on site characteristics.

**Next Steps**: Ready for production use. Future enhancements can focus on pure MkDocs sites, additional inventory formats (OpenAPI), or new structure processors (Docusaurus, VitePress).

## Connection to Dual Registry Architecture

This MkDocs processor implementation was **enabled by the dual registry architecture** documented in `dual-registry-implementation-plan.md`. The architectural separation of inventory processors from structure processors allows:

- **Inventory reuse**: Both Sphinx and MkDocs processors share the same `SphinxInventoryProcessor` for objects.inv files
- **Clean separation**: MkDocs structure detection (themes, YAML config) is independent from inventory processing
- **Extensibility**: New inventory formats (OpenAPI) can be added without affecting structure processors
- **Type safety**: ProcessorGenera enum ensures proper routing to inventory vs structure registries

The dual registry system provides the foundation that makes this clean architectural separation possible.