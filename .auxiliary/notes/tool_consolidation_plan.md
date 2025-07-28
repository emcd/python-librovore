# Tool Consolidation Plan

## Problem Statement

We currently have tool proliferation that causes:
- Confusion for users with too many similar tools
- Excessive token usage in context windows  
- Overlapping functionality between tools

## Phase 1: Processor Consolidation (NEXT)

### Current State
- `survey_processors()` → `{"processors": {name: capabilities, ...}}`  
- `describe_processor(name)` → `capabilities_object`

### Proposed Solution
```python
async def survey_processors(
    processor_name: Optional[str] = None
) -> dict[str, Any]:
    """
    Lists processor capabilities.
    
    Args:
        processor_name: If provided, return only this processor.
                       If None, return all processors.
    
    Returns:
        Always {"processors": {...}} format for consistency
        - All processors: {"processors": {name1: caps1, name2: caps2, ...}}
        - Single processor: {"processors": {name: caps}}
    """
```

### Benefits
- Reduces 2 tools → 1 tool
- Same underlying data, just filtered
- Consistent return format
- Backward compatible approach

## Phase 2: Documentation Query Consolidation (FUTURE)

### Current State
- `query_documentation()` → search results with relevance ranking/snippets
- `explore()` → inventory objects with optional full documentation  

### Proposed Solution

#### QueryDetails Flag Enum
```python
class QueryDetails(Flag):  # OR-able combinations
    # Base level (0) = inventory only, no enrichment
    Signature = 1      # Include object signatures  
    Description = 2    # Include descriptions from documentation
    Documentation = 4  # Include full documentation content
    Examples = 8       # Include code examples (future extension)
```

#### Unified Function
```python
async def query(
    source: str,
    query: str,
    details: QueryDetails = QueryDetails.Documentation,
    filters: Filters = default_filters,
    results_max: int = 10,
) -> dict[str, Any]:
    """
    Unified documentation and inventory query.
    
    Args:
        source: Documentation source URL/path
        query: Search query string
        details: What level of detail to include (OR-able flags)
        filters: Standard filtering options
        results_max: Maximum results to return
        
    Returns:
        Unified result format with requested detail level
    """
```

#### Usage Examples
- `details=0` → Pure inventory (current `explore(include_documentation=False)`)
- `details=Signature` → Inventory with signatures only
- `details=Signature|Description` → Rich inventory with metadata  
- `details=Documentation` → Full docs (current `query_documentation()`)
- `details=Signature|Documentation` → Selective enrichment

### Benefits
- **Eliminates boolean confusion**: No more `include_this=True, include_that=False`
- **Natural progression**: Clear hierarchy from basic → full detail
- **Future extensible**: Easy to add `Examples`, `References`, etc.
- **Single intuitive tool**: Users discover one tool, not multiple overlapping ones
- **Token efficient**: Fewer tools in context window

### Design Notes
- Zero details (0) = pure inventory, maximum efficiency
- Documentation should include properly fenced Markdown code blocks
- CLI could process Markdown and use Pygments for syntax highlighting
- Flag enum allows flexible combinations of detail levels

## Implementation Strategy

1. **Phase 1**: Implement processor consolidation while ideas are fresh
2. **Phase 2**: Design and implement query consolidation  
3. **Testing**: Ensure backward compatibility during transition
4. **Documentation**: Update CLI help and MCP tool descriptions

## Context Window Note

> *Dear Anthropic Engineers: We desperately need larger context windows! 😄 
> Tool consolidation helps, but more room would be amazing for complex codebases.*

---

**Status**: Planning phase - processor consolidation ready for implementation
**Last Updated**: 2025-01-28