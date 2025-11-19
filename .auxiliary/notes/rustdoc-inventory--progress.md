# Rustdoc Inventory Processor Implementation - Progress Tracking

## Context and References

- **Implementation Title**: Rustdoc inventory processor for librovore
- **Start Date**: 2025-11-19
- **Reference Files**:
  - `.auxiliary/notes/pydoctor-rustdoc.md` - Comprehensive Rustdoc structure analysis
  - `.auxiliary/notes/pydoctor-rustdoc-outstanding-questions.md` - Confirms research complete
  - `sources/librovore/inventories/sphinx/` - Reference inventory processor implementation
  - `sources/librovore/inventories/mkdocs/` - Alternative reference implementation
  - `sources/librovore/interfaces.py` - InventoryProcessor protocol definition
  - `sources/librovore/inventories/__init__.py` - Base classes and utilities
- **Design Documents**:
  - Analysis documents confirm all reconnaissance complete
  - Detection via `<meta name="generator" content="rustdoc">` and custom elements
  - Inventory extraction from "All Items" HTML page (`/{crate}/all.html`)
- **Session Notes**: See TodoWrite items in current session

## Design and Style Conformance Checklist

- [ ] Module organization follows practices guidelines (imports, type aliases, private constants, public classes, helpers)
- [ ] Function signatures use wide parameter, narrow return patterns
- [ ] Type annotations comprehensive with TypeAlias patterns
- [ ] Exception handling follows Omniexception → Omnierror hierarchy
- [ ] Naming follows nomenclature conventions
- [ ] Immutability preferences applied (tuple, frozenset, immut.Dictionary)
- [ ] Code style follows formatting guidelines (spacing, quotes, docstrings)
- [ ] Documentation uses narrative mood, triple single-quotes

## Implementation Progress Checklist

### Core Module Structure
- [ ] `sources/librovore/inventories/rustdoc/__init__.py` - Package initialization
- [ ] `sources/librovore/inventories/rustdoc/__.py` - Internal imports rollup
- [ ] `sources/librovore/inventories/rustdoc/detection.py` - Rustdoc site detection
- [ ] `sources/librovore/inventories/rustdoc/main.py` - Main processor class

### Detection Implementation
- [ ] RustdocInventoryDetection class
- [ ] from_source classmethod for detection logic
- [ ] filter_inventory method for filtering objects
- [ ] Meta tag detection (`<meta name="generator" content="rustdoc">`)
- [ ] Custom element detection (`<rustdoc-topbar>`, `<rustdoc-toolbar>`)
- [ ] CSS file detection (`rustdoc-*.css`)

### Inventory Extraction
- [ ] derive_inventory_url function (for all.html)
- [ ] extract_inventory function (parse HTML page)
- [ ] filter_inventory function (apply filters)
- [ ] RustdocInventoryObject class with specifics rendering
- [ ] format_inventory_object function
- [ ] Item type mapping (struct, enum, trait, fn, macro, etc.)

### Processor Implementation
- [ ] RustdocInventoryProcessor class
- [ ] capabilities property
- [ ] detect method
- [ ] Supported filters definition

### Integration
- [ ] Register processor in inventory registry
- [ ] Add to __init__.py exports if needed

## Quality Gates Checklist

- [ ] Linters pass (`hatch --env develop run linters`)
- [ ] Type checker passes (Pyright via linters)
- [ ] Tests pass (`hatch --env develop run testers`)
- [ ] Code review ready

## Decision Log

- **2025-11-19** - Use "All Items" HTML page as primary inventory source
  - Rationale: Most complete and reliable source compared to sidebar-items.js files
  - Alternative considered: Crawling per-module sidebar-items files
  - Trade-off: HTML parsing is more robust than assembling from multiple JS files

- **2025-11-19** - Follow Sphinx processor architecture pattern
  - Rationale: Established pattern in codebase, proven design
  - Modules: detection.py, main.py, __.py structure

## Handoff Notes

### Current State
- **Completed**: Environment setup, coding standards review, tracking file creation
- **In Progress**: Beginning implementation
- **Not Started**: Actual code implementation

### Next Steps
1. Create directory structure for rustdoc processor
2. Implement __.py with imports rollup
3. Implement detection.py with Rustdoc detection logic
4. Implement main.py with inventory extraction from all.html
5. Register processor
6. Run quality assurance
7. Test with reference sites (Rust std, serde, tokio)

### Known Issues
- None yet - beginning implementation

### Context Dependencies
- Rustdoc uses "All Items" page at `/{crate}/all.html` for complete inventory
- Detection markers: `<meta name="generator" content="rustdoc">`, `<rustdoc-topbar>` custom element
- Item types to support: struct, enum, trait, fn (function), macro, mod (module), const, type
- Need to handle versioned resource files (e.g., `sidebar-items1.84.0.js`)
- HTML structure is highly consistent across Rustdoc versions
