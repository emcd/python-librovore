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
```python
# structures/mkdocs/detection.py
class MkDocsDetection(__.Detection):
    def __init__(self, processor, confidence, source, **kwargs):
        super().__init__(processor=processor, confidence=confidence)
        self.source = source
        # Inventory processor attached to detection (where the work happens)
        self.inventory_processor = SphinxInventoryProcessor()
        # Structure-specific attributes
        self.has_mkdocs_search = kwargs.get('has_mkdocs_search', False)
        self.mkdocs_theme = kwargs.get('mkdocs_theme')
    
    async def filter_inventory(self, source, *, filters, details):
        # Delegate to inventory processor
        return await self.inventory_processor.filter_inventory(
            source, filters=filters, details=details)
    
    async def extract_contents(self, source, objects, *, include_snippets):
        # Use MkDocs structure knowledge + inventory data
        return await self._extract_mkdocs_content(
            source, objects, include_snippets=include_snippets)

# structures/mkdocs/main.py  
class MkDocsProcessor(__.Processor):
    name: str = 'mkdocs'
    
    async def detect(self, source: str) -> MkDocsDetection:
        # Detection logic - processor only does detection
        has_inventory = await self._check_inventory(source)
        has_mkdocs = await self._check_mkdocs_features(source)
        
        if has_inventory and has_mkdocs:
            return MkDocsDetection(
                processor=self, 
                confidence=0.9,
                source=source,
                has_mkdocs_search=True,
                mkdocs_theme=detected_theme
            )
        # ... more detection logic
```

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
```python
async def determine_optimal_processor(source):
    # Priority: Most specific features -> General
    processors_to_try = [
        ('mkdocs', MkDocsProcessor),      # MkDocs features + inventory
        ('sphinx', SphinxProcessor),      # Sphinx features + inventory  
        # Future: ('content', ContentProcessor),   # Content-only fallback
    ]
    
    for name, processor_class in processors_to_try:
        detection = await processor_class().detect(source) 
        if detection.confidence >= 0.7:
            return detection
    
    return None  # No suitable processor found
```

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

## Conclusion

This architectural approach provides a clean, extensible foundation for comprehensive documentation ecosystem support. By separating inventory processing from structure processing, we enable code reuse, maintain clear separation of concerns, and create a framework that can easily accommodate future documentation formats and site structures.

The 1.0 focus on mkdocstrings-enhanced sites provides immediate, high-value functionality while establishing the architectural patterns needed for future expansion. This approach minimizes risk while maximizing impact for the Python documentation ecosystem.