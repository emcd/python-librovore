# Pydoctor Inventory Processor Implementation Progress

## Context and References

- **Implementation Title**: Add Pydoctor inventory processor support
- **Start Date**: 2025-11-19
- **Reference Files**:
  - `.auxiliary/notes/pydoctor-rustdoc.md` - Comprehensive structure analysis
  - `.auxiliary/notes/pydoctor-rustdoc-outstanding-questions.md` - Confirms research complete
  - `sources/librovore/inventories/sphinx/` - Reference implementation pattern
  - `sources/librovore/interfaces.py` - Processor interfaces
  - `sources/librovore/processors.py` - Base processor classes
  - `sources/librovore/results.py` - Result structures
- **Design Documents**: None - following established Sphinx processor pattern
- **Session Notes**: See TodoWrite items in current session

## Design and Style Conformance Checklist

- [x] Module organization follows practices guidelines
- [x] Function signatures use wide parameter, narrow return patterns
- [x] Type annotations comprehensive with TypeAlias patterns
- [x] Exception handling follows Omniexception → Omnierror hierarchy
- [x] Naming follows nomenclature conventions
- [x] Immutability preferences applied
- [x] Code style follows formatting guidelines

## Implementation Progress Checklist

### Package Structure
- [x] `sources/librovore/inventories/pydoctor/__.py` - Import rollup
- [x] `sources/librovore/inventories/pydoctor/__init__.py` - Package init with register()
- [x] `sources/librovore/inventories/pydoctor/detection.py` - Detection logic
- [x] `sources/librovore/inventories/pydoctor/main.py` - Main processor class

### Core Implementation
- [x] `PydoctorInventoryDetection` class with searchindex.json detection
- [x] `filter_inventory()` function for extracting objects from searchindex.json
- [x] `PydoctorInventoryObject` class for rendering specifics
- [x] `PydoctorInventoryProcessor` class with capabilities and detect()
- [x] Registration function to add to inventory_processors registry

### Integration
- [x] Processor registered in `data/configuration/general.toml`
- [ ] Detection tested with Dulwich and Twisted reference sites (deferred to future testing)
- [x] Inventory extraction from searchindex.json format
- [x] Qualified name parsing (e.g., `dulwich.repo.Repo`)

## Quality Gates Checklist

- [x] Linters pass (`hatch --env develop run linters`)
- [x] Type checker passes
- [x] Tests pass (`hatch --env develop run testers`)
- [x] Code review ready

## Decision Log

- [2025-11-19] Use searchindex.json as primary inventory source - Analysis shows this is Pydoctor's standard search index format with qualified names
- [2025-11-19] Follow Sphinx processor pattern - Established pattern works well for inventory processors
- [2025-11-19] Defer HTML index fallback - Focus on searchindex.json parsing first, add HTML index fallback later if needed
- [2025-11-19] Use pyright ignore comments for JSON parsing - Dynamic JSON data from searchindex requires runtime type checks, so pyright ignore comments used for type narrowing issues

## Implementation Details

### Pydoctor Inventory Format

Based on analysis in `pydoctor-rustdoc.md`:

**Primary source**: `searchindex.json` (Lunr.js format)
- Location: `{base_url}/searchindex.json`
- Format: Lunr.js search index with vector-based scoring
- Fields: `name`, `names`, `qname` (qualified name)
- Qualified names like: `dulwich.repo.Repo`, `twisted.internet.reactor`

**Detection markers**:
- Presence of `searchindex.json` at base URL
- Optional: Check for `<meta name="generator" content="pydoctor">` in HTML
- CSS files: `apidocs.css`, `pydoctor.js`

**Extraction strategy**:
1. Fetch `searchindex.json` from `{base_url}/searchindex.json`
2. Parse Lunr.js index format (JSON with fieldVectors)
3. Extract qualified names from field vectors
4. Map to module/class/function structure based on naming conventions
5. Return as `InventoryObject` instances with pydoctor-specific metadata

### Module Organization

Following Sphinx processor pattern:
- `__.py` - Imports rollup from parent `inventories/__`
- `__init__.py` - Exports main class and register() function
- `detection.py` - Detection logic and inventory extraction
- `main.py` - Main processor class with capabilities

## Handoff Notes

### Current State
- **Implemented**: Complete Pydoctor inventory processor with searchindex.json support
  - Package structure (__.py, __init__.py, detection.py, main.py)
  - Detection logic using searchindex.json presence
  - Inventory extraction from Lunr.js format
  - Object type inference from qualified names
  - PydoctorInventoryObject with specifics rendering
  - Registration in configuration
- **Not Implemented**: Integration tests with live Dulwich/Twisted sites

### Next Steps
1. Add integration tests with real Pydoctor documentation sites
2. Consider adding HTML index fallback for sites without searchindex.json
3. Add more detailed object type detection (methods, properties, etc.)

### Known Issues
- Object type inference is basic (module/class/function based on naming)
- URI generation assumes standard pattern (qname.replace('.', '/') + '.html')
- No validation of searchindex.json schema version

### Context Dependencies
- Requires HTTP client access to fetch searchindex.json
- Pydoctor search index format is Lunr.js-based (vector format)
- Need to handle potential URL variations (http/https, trailing slashes)
- Should gracefully handle missing searchindex.json
