# Structured Objects Discussion

## Context

During CLI output format planning, we discussed transitioning from dictionary returns to structured dataclass objects in the functions module.

## Current State

Functions in `functions.py` return dictionaries with structured data:
- `query_inventory()` returns `dict[str, Any]`
- `query_content()` returns `dict[str, Any]` 
- `detect()` returns `dict[str, Any]`
- `summarize_inventory()` returns `str` (will change to `dict[str, Any]`)

## Proposed Change

Replace dictionary returns with structured dataclasses:

```python
@dataclasses.dataclass
class InventoryQueryResult:
    project: str
    version: str
    query: str
    documents: list[InventoryDocument]
    search_metadata: SearchMetadata
    source: str
```

## Benefits

- **Type safety**: Catch errors at development time
- **Consistency**: Already using dataclasses elsewhere (DetectionsForLocation)
- **Maintainability**: Clear contracts between layers
- **Tooling**: Better IDE support and refactoring capabilities
- **Validation**: Built-in data validation

## Decision

**DEFERRED** - Focus on CLI output formatting first. Structured objects represent a significant architectural change that should be planned carefully after current CLI improvements are complete.

## Implementation Notes

When implemented, use phased transition: add structured classes alongside current dict returns, then migrate command by command to avoid breaking changes.