# Search Logic Centralization Plan

## Overview

Centralize fuzzy/regex/exact matching logic in the engine to eliminate duplication across processor implementations and prepare for adding new processors (MkDocs, etc.). This includes migrating from unmaintained `fuzzywuzzy` (via sphobjinv) to `rapidfuzz` for better performance and maintenance.

## Current Architecture Issues

### 1. Search Logic Duplication
- **Current**: Each processor implements its own search matching logic
- **Problem**: Will require reimplementing fuzzy/regex/exact matching for each new processor
- **Impact**: Code duplication, inconsistent behavior, maintenance burden

### 2. Dependency on Unmaintained Library
- **Current**: Using `sphobjinv.suggest()` which depends on `fuzzywuzzy` 
- **Problem**: `fuzzywuzzy` is unmaintained and slower than `rapidfuzz`
- **Impact**: Performance bottleneck, security/maintenance risk

### 3. Mixed Responsibilities
- **Current**: Processors handle both domain-specific filtering (domain, role, priority) AND universal search matching (fuzzy, regex, exact)
- **Problem**: Violates separation of concerns, makes testing complex
- **Impact**: Harder to add new processors, inconsistent search behavior

## Proposed Architecture

### Clear Separation of Concerns

```
┌─────────────────────────────────────────────────────────────┐
│                    ENGINE LEVEL                             │
│  - Universal search matching (fuzzy, regex, exact)         │
│  - Search scoring and ranking                               │
│  - Search term preprocessing                                │
│  - Match mode logic (MatchMode enum)                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 PROCESSOR LEVEL                             │
│  - Domain-specific filtering (domain, role, priority)      │
│  - Inventory extraction and parsing                        │
│  - Source-specific logic (Sphinx vs MkDocs vs ...)        │
└─────────────────────────────────────────────────────────────┘
```

### New Search Module

Create `sources/sphinxmcps/search.py`:

```python
class SearchEngine:
    """Centralized search engine for all processors."""
    
    async def filter_objects(
        self,
        objects: list[InventoryObject],
        query: str,
        match_mode: MatchMode,
        fuzzy_threshold: int = 50,
    ) -> list[ScoredObject]:
        """Apply universal search matching to objects."""
        
    async def score_relevance(
        self,
        objects: list[InventoryObject], 
        query: str,
    ) -> list[ScoredObject]:
        """Score objects by relevance to query."""
```

## Implementation Plan

### Single Sprint Implementation (4 hours)

#### 1. Add rapidfuzz Dependency and Prune Environment
- **Add** `rapidfuzz` to pyproject.toml dependencies  
- **Run** `hatch env prune` to rebuild environment with new dependency
- **Remove** dependency on sphobjinv's suggest() method

#### 2. Restructure Filters DTO
- **Split** current `Filters` into:
  - `UniversalFilters` (match_mode, fuzzy_threshold) - handled by engine
  - `ProcessorFilters` (processor-specific filters like domain, role, priority)
- **Update** all references to use new filter structure

#### 3. Create Centralized Search Engine
- **Create** `sources/sphinxmcps/search.py` module
- **Implement** search engine with rapidfuzz integration
- **Support** exact, regex, and fuzzy matching modes
- **Add** relevance scoring and ranking

#### 4. Update Processor Interface
- **Modify** `Processor.extract_inventory()` to accept `extra_filters: dict[str, Any]`
- **Remove** hardcoded domain-specific parameters from interface
- **Update** SphinxProcessor to use `extra_filters` dictionary approach

#### 5. Update Functions Layer
- **Modify** `query_inventory()` to orchestrate search:
  1. Extract raw inventory using processor-specific filters
  2. Apply universal search matching at engine level
  3. Score and rank results
  4. Return formatted results
- **Remove** search logic from business functions

#### 6. Clean Up SphinxProcessor
- **Remove** search matching logic from `processors/sphinx/inventory.py`
- **Remove** unused helper functions (`extract_names_from_suggestions`, `filter_fuzzy_matching`)
- **Simplify** inventory filtering to only handle processor-specific concerns

#### 7. Update Tests
- **Migrate** existing tests to new search API
- **Update** test fixtures to use new filter structure
- **Ensure** no regression in search functionality

## Benefits

### For Current Implementation
- **Performance**: rapidfuzz is significantly faster than fuzzywuzzy
- **Maintenance**: Remove dependency on unmaintained library
- **Consistency**: Uniform search behavior across all tools
- **Testing**: Easier to test search logic in isolation

### For Future Processors  
- **Simplicity**: New processors don't need to implement search logic
- **Consistency**: All processors get same high-quality search automatically
- **Focus**: Processors can focus on their domain-specific concerns
- **Speed**: Faster time-to-implement for new processors

### For Users
- **Performance**: Faster search responses, especially for fuzzy matching
- **Reliability**: More robust and maintained dependencies
- **Consistency**: Same search experience across different documentation types

## Success Criteria

- **Architecture**: Clean separation between processor-specific and universal logic
- **Consistency**: Identical search results across all match modes  
- **Simplicity**: New processor implementation requires minimal search-related code
- **Quality**: No regression in search relevance or accuracy
- **Extensibility**: Easy foundation for adding MkDocs processor

## Risk Mitigation

- **Compatibility**: Maintain identical API surface during transition
- **Quality**: Thorough testing to ensure no search regression

## Future Extensions

This architecture enables:
- **MkDocs Processor**: Can focus on MkDocs-specific parsing without reimplementing search
- **Advanced Search**: Easy to add features like boolean queries, phrase matching
- **Search Analytics**: Centralized location to add search metrics and logging
- **Custom Scoring**: Easy to experiment with different relevance algorithms

---

**Status**: Planning phase - ready for implementation  
**Priority**: High - blocks MkDocs processor development  
**Timeline**: Single 4-hour sprint  
**Dependencies**: rapidfuzz documentation (if needed)