# Explore Function Design

## Context

Based on UX feedback in `mcp-server-ux-feedback.md`, issue #5 identified a need for a combined "explore topic" function to streamline the common workflow of:
1. `extract_inventory` → find relevant objects  
2. `extract_documentation` → get details for each object

This reduces the multi-step discovery process that requires sequential calls.

## Context7 Comparison

Context7 provides a similar pattern with two functions:
- `resolve-library-id`: Library search across multiple libraries
- `get-library-docs`: Topic-focused documentation retrieval with code snippets

Their `get-library-docs` takes a `topic` parameter and returns relevant code snippets and documentation for a specific library. Our `explore` function is similar but focuses on exploring objects within a single Sphinx documentation source rather than across multiple libraries.

Key differences:
- Context7: Cross-library search → topic docs within one library
- Our approach: Object search → documentation extraction within one source
- Context7: Returns code snippets + docs
- Our approach: Returns object metadata + structured documentation

## Interface Design

```python
async def explore(
    source: SourceArgument,
    query: str, /, *,
    domain: DomainFilter = __.absent,
    role: RoleFilter = __.absent,
    priority: PriorityFilter = __.absent,
    match_mode: _interfaces.MatchMode = _interfaces.MatchMode.Fuzzy,
    fuzzy_threshold: int = 50,
    max_objects: int = 5,
    include_sections: SectionFilter = __.absent,  # signature, description
    include_documentation: bool = True,
) -> dict[ str, __.typx.Any ]:
    ''' 
    Explores objects related to a query by combining inventory search 
    with documentation extraction.
    
    This function streamlines the common workflow of searching inventory
    for relevant objects and then extracting detailed documentation for
    each match. It handles errors gracefully by separating successful
    results from failed extractions.
    '''
```

## Return Structure Design

```python
{
    "project": "project-name",
    "version": "1.0.0", 
    "query": "searched_query",
    "search_metadata": {
        "object_count": 3,
        "max_objects": 5,
        "filters": { "domain": "py", "match_mode": "fuzzy", ... }
    },
    "documents": [
        {
            "name": "Result", 
            "role": "class",
            "domain": "py",
            "uri": "...",
            "fuzzy_score": 95,  # Only present for fuzzy searches
            "documentation": {  # Only if include_documentation=True
                "signature": "class Result[T, E]",
                "description": "Detailed docs...",
                "url": "full_url"
            }
        }
    ],
    "errors": [
        {
            "name": "SomeClass",
            "domain": "py", 
            "error": "Documentation extraction failed: Object not found"
        }
    ]
}
```

## Design Decisions

1. **Parameter naming**: `query` (Latin-derived) instead of `topic` for consistency
2. **Max objects limit**: `max_objects` parameter to control performance and prevent overwhelming results
3. **Error handling**: Separate `documents` and `errors` arrays to handle partial failures gracefully
4. **Documentation sections**: Reuse existing `include_sections` from `extract_documentation` (signature, description)
5. **Implementation pattern**: Function → CLI → MCP server (standard pattern for testing)

## Open Questions

### Interface Complexity
The function has 8 parameters, which approaches the complexity threshold. Consider bundling filter parameters into a DTO:

```python
# Current approach
async def explore(
    source: SourceArgument,
    query: str, /, *,
    domain: DomainFilter = __.absent,
    role: RoleFilter = __.absent,
    priority: PriorityFilter = __.absent,
    match_mode: _interfaces.MatchMode = _interfaces.MatchMode.Fuzzy,
    fuzzy_threshold: int = 50,
    max_objects: int = 5,
    include_sections: SectionFilter = __.absent,
    include_documentation: bool = True,
)

# Potential DTO approach
async def explore(
    source: SourceArgument,
    query: str, /, *,
    filters: ExploreFilters = ExploreFilters(),
    max_objects: int = 5,
    include_sections: SectionFilter = __.absent,
    include_documentation: bool = True,
)
```

**Considerations**:
- How does Pydantic surface DTOs in JSON Schema for MCP tools?
- Does bundling improve or complicate the CLI experience?
- Trade-off between parameter count and nested complexity

### Status
- HTML formatting: ✅ Completed
- Fuzzy search transparency: ✅ Completed  
- Explore function: 📋 Designed, pending implementation