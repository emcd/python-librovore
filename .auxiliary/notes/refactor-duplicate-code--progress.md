# Refactor Duplicate Code in Structure Processors - Progress

## Context and References

- **Implementation Title**: Refactor duplicate code from structure processors into shared modules
- **Start Date**: 2025-11-20
- **Reference Files**:
  - `.auxiliary/notes/issues.md` - Issue description for code duplication
  - `sources/librovore/structures/sphinx/urls.py` - Sphinx URL utilities (source of duplication)
  - `sources/librovore/structures/pydoctor/urls.py` - Pydoctor URL utilities (source of duplication)
  - `sources/librovore/structures/__.py` - Parent import namespace for all processors
  - `sources/librovore/structures/sphinx/__.py` - Sphinx import namespace
  - `sources/librovore/structures/pydoctor/__.py` - Pydoctor import namespace
- **Design Documents**: None
- **Session Notes**: See TodoWrite tracking

## Duplicate Code Identified

### Primary Duplication: normalize_base_url function
- **Location 1**: `sources/librovore/structures/sphinx/urls.py:31-55`
- **Location 2**: `sources/librovore/structures/pydoctor/urls.py:31-47`
- **Description**: Identical function that extracts clean base documentation URL from any source (URL, file path, or directory)
- **Complexity**: 25 lines of logic with URL parsing, path handling, and scheme validation
- **STATUS**: FIXED - Extracted to `sources/librovore/structures/urls.py`

### Secondary Duplication: from_source classmethod
- **Location 1**: `sources/librovore/structures/sphinx/detection.py:62-71`
- **Location 2**: `sources/librovore/structures/pydoctor/detection.py:55-64`
- **Location 3**: `sources/librovore/structures/mkdocs/detection.py:65-74`
- **Location 4**: `sources/librovore/structures/rustdoc/detection.py:56-65`
- **Description**: Identical classmethod implementation across all 4 Detection classes
- **Complexity**: 10 lines per class (40 lines total)
- **STATUS**: FIXED - Moved to `StructureDetection` base class in `sources/librovore/processors.py`

## Refactoring Strategy

### Approach
Create a shared `urls.py` module at `sources/librovore/structures/urls.py` containing common URL utilities, then import into `sources/librovore/structures/__.py` for distribution to all processors.

### Module Organization
- `sources/librovore/structures/urls.py` - New shared URL utilities module
  - `normalize_base_url` - Extracted from duplicate implementations
  - Type aliases and URL utility functions that are truly common

- `sources/librovore/structures/__.py` - Updated to export shared URL utilities
  - Add `from . import urls as _urls_common` (or similar pattern)
  - Export specific functions needed by processors

- Individual processor `__.py` files - Import from parent
  - Already using `from ..__ import *` pattern
  - Will automatically gain access to shared functions

### Implementation Plan

1. Create `sources/librovore/structures/urls.py` with shared URL utilities
2. Update `sources/librovore/structures/__.py` to export the shared utilities
3. Update `sources/librovore/structures/sphinx/urls.py` to use shared `normalize_base_url`
4. Update `sources/librovore/structures/pydoctor/urls.py` to use shared `normalize_base_url`
5. Remove duplicate code from processor-specific modules

## Design and Style Conformance Checklist
- [x] Module organization follows practices guidelines
- [x] Function signatures use wide parameter, narrow return patterns
- [x] Type annotations comprehensive with TypeAlias patterns
- [x] Exception handling follows Omniexception → Omnierror hierarchy
- [x] Naming follows nomenclature conventions
- [x] Immutability preferences applied
- [x] Code style follows formatting guidelines

## Implementation Progress Checklist
- [x] Create `sources/librovore/structures/urls.py` with `normalize_base_url`
- [x] Update `sources/librovore/structures/__.py` to export shared URL utilities
- [x] Update sphinx/urls.py to import and use shared normalize_base_url
- [x] Update pydoctor/urls.py to import and use shared normalize_base_url
- [x] Remove duplicate normalize_base_url implementations
- [x] Verify imports work correctly

## Quality Gates Checklist
- [x] Linters pass (`hatch --env develop run linters`)
- [x] Type checker passes
- [x] Tests pass (`hatch --env develop run testers`)
- [x] Code review ready

## Decision Log
- [2025-11-20] Create shared urls.py at structures level - This provides a natural location for common URL utilities that all structure processors can use
- [2025-11-20] Corrected import hierarchy - Processor __.py files should import from parent level using `from ..urls import *`, not the structures/__.py file importing sideways
- [2025-11-20] Use __.normalize_base_url directly - Callers should use `__.normalize_base_url()` instead of re-exporting through processor-specific urls.py modules
- [2025-11-20] Move from_source to base class - All four Detection classes had identical implementation, indicating this should be in the base StructureDetection class rather than duplicated in subclasses

## Handoff Notes

### Current State
**COMPLETED** - All refactoring work is done, verified, committed, and pushed.

**Commits:**
- f47a5b0: Initial normalize_base_url extraction (first attempt with incorrect import pattern)
- 26050d5: Fixed import patterns and extracted from_source to base class

**Implementation summary:**
1. **normalize_base_url duplication** (25 lines per processor):
   - Created `sources/librovore/structures/urls.py` with shared function
   - Updated processor __.py files (sphinx, pydoctor) to import `from ..urls import *`
   - Changed callers to use `__.normalize_base_url()` directly
   - Removed duplicate implementations from processor-specific urls.py files

2. **from_source duplication** (10 lines per class, 4 classes):
   - Moved identical implementation to `StructureDetection` base class
   - Removed duplicate methods from all 4 Detection subclasses
   - Prevents future implementation drift

**Quality verification:**
- All linters pass (ruff, isort, pyright) with 0 errors
- All 171 tests pass
- Code coverage maintained at 32%
- Total duplicate code eliminated: ~90 lines

### Next Steps
All refactoring complete. Future considerations:
- Monitor for additional duplication patterns that emerge
- Consider extracting other common utilities if patterns are discovered

### Implementation Details

**normalize_base_url refactoring:**
1. Created shared `sources/librovore/structures/urls.py` module
2. Updated processor __.py files to import `from ..urls import *`
3. Changed callers to use `__.normalize_base_url` instead of `_urls.normalize_base_url`
4. Removed duplicate implementations (25 lines per processor)
5. Followed correct import hierarchy with processor __.py files importing from parent level

**from_source refactoring:**
1. Identified identical implementation across all 4 Detection classes
2. Moved implementation to `StructureDetection` base class in `processors.py`
3. Removed duplicate implementations from all Detection subclasses
4. Eliminated 10 lines per class (40 lines total)
5. Prevents future implementation drift

### Context Dependencies
- Processor __.py files use `from ..__ import *` to import from parent module
- Processor __.py files use `from ..urls import *` to import shared URL utilities
- The normalize_base_url function is called as `__.normalize_base_url()` from main.py and extraction.py modules
- The from_source classmethod is inherited by all StructureDetection subclasses
- Function handles URL parsing, file path conversion, and scheme validation identically for all processors
