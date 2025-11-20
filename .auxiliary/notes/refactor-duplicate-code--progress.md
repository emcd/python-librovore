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

### Secondary Duplication Candidates

1. **URL derivation pattern** - Both processors have `derive_*_url` functions that follow similar patterns
   - `derive_html_url` (sphinx) vs `derive_index_url` (pydoctor) - essentially the same
   - `derive_documentation_url` - exists in both but with different signatures

2. **Detection try-except pattern** - Both `main.py` files have similar try-except blocks around `normalize_base_url`

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
- [2025-11-20] Create shared urls.py at structures level - This provides a natural location for common URL utilities that all structure processors can use, following the existing import pattern via __.py
- [2025-11-20] Use noqa: F401 for re-exports - The normalize_base_url function is imported into processor-specific urls.py modules for re-export to other modules that import urls. Used `# noqa: F401` to indicate this is an intentional re-export pattern.
- [2025-11-20] Use wildcard import in structures/__.py - Following the existing pattern, used `from .urls import *` to make shared URL utilities available to all structure processors via their `__.py` imports.

## Handoff Notes

### Current State
**COMPLETED** - All refactoring work is done and verified.

Implementation summary:
- Created `sources/librovore/structures/urls.py` with shared `normalize_base_url` function
- Updated `sources/librovore/structures/__.py` to export shared URL utilities via wildcard import
- Refactored `sphinx/urls.py` and `pydoctor/urls.py` to import and re-export the shared function
- Removed duplicate implementations (25 lines of identical code per processor)
- All linters pass (ruff, isort, pyright)
- All 171 tests pass
- Code coverage maintained

### Next Steps
1. Commit changes with descriptive message
2. Push to the designated branch
3. Consider future enhancements:
   - Extract other common URL utilities if more duplication is found
   - Look for similar duplication patterns in other processor modules

### Implementation Details
The refactoring successfully eliminated the duplicate `normalize_base_url` function by:
1. Creating a new shared module at the structures level
2. Leveraging the existing `__.py` import pattern where each processor imports `from ..__ import *`
3. Using re-export pattern in processor-specific urls.py modules to maintain backward compatibility

### Context Dependencies
- The __.py import pattern automatically makes shared utilities available to all processors
- The normalize_base_url function is called via `_urls.normalize_base_url()` from main.py and extraction.py modules
- The function handles URL parsing, file path conversion, and scheme validation identically for all processors
