# Command Consolidation Plan

## Decision Summary

**Consolidate from 4 tools to 2 tools:** `explore` + `query-documentation`

## Rationale

### Current Tool Overlap Analysis

**Before consolidation (4 tools):**
- `extract-inventory`: Object list with metadata, no docs
- `extract-documentation`: Single object → full documentation  
- `query-documentation`: Content search within documentation text
- `explore`: Inventory search → optional documentation for multiple objects

**Functional overlap identified:**
- `explore` with exact object name produces identical results to `extract-documentation`
- `explore` with `--no-include-documentation` provides better functionality than `extract-inventory` (fuzzy scoring, rich metadata, error handling)

### Final Tool Set (2 tools)

**1. `explore`** - Unified inventory-based discovery
- **Replaces:** `extract-inventory` and `extract-documentation`
- **Use cases:**
  - Find objects by name/pattern (fuzzy matching with scores)
  - Get documentation for specific objects (exact match)
  - Inventory browsing with optional docs
- **Benefits:** Rich filtering, error handling, fuzzy scoring, flexible output

**2. `query-documentation`** - Content-based search within documentation
- **Unique functionality:** Searches within documentation text content
- **Specialized features:** Content snippets, relevance scoring, text matching
- **Use case:** "Find docs containing concept X" vs "Get docs for object X"

### Benefits of Consolidation

1. **Token efficiency**: 50% reduction in tools = more context window for documentation
2. **Reduced LLM confusion**: Clear separation of concerns eliminates overlapping functionality
3. **Better UX**: `explore` provides superior experience vs tools it replaces
4. **Maintenance**: Less code duplication, single source of truth for inventory operations

### Test Results Confirming Equivalence

**extract-documentation:**
```json
{
  "object_name": "appcore.generics.Result",
  "url": "https://...",
  "signature": "classappcore.generics.Result(*posargs,**nomargs)¶",
  "description": "Bases:Protocol,Generic[T,E]Either a value..."
}
```

**explore with exact match:**
```json
{
  "documents": [{
    "name": "appcore.generics.Result",
    "documentation": {
      "object_name": "appcore.generics.Result", 
      "url": "https://...",
      "signature": "classappcore.generics.Result(*posargs,**nomargs)¶",
      "description": "Bases:Protocol,Generic[T,E]Either a value..."
    }
  }]
}
```

**Result**: Identical documentation content, but `explore` provides additional metadata (search stats, error handling, etc.)

## Implementation Plan

1. ✅ Move `Filters` DTO to `interfaces` module
2. Remove deprecated commands: `extract-inventory`, `extract-documentation`
3. Update MCP server tool registration to reflect new minimal set
4. Update documentation and examples

## Migration Guide for Users

**Old → New command mappings:**

```bash
# Extract inventory → explore without docs
extract-inventory --domain py --term Result
→ explore --query Result --domain py --no-include-documentation

# Extract documentation → explore with exact match  
extract-documentation --object-name "appcore.generics.Result"
→ explore --query "appcore.generics.Result" --match-mode Exact --max-objects 1

# Query documentation → unchanged
query-documentation --query "error handling"
→ query-documentation --query "error handling"
```

## Decision Date

2025-07-26 - Committed with UX improvements milestone (commit 7c3c00d)