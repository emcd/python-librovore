# Structured Objects Implementation Plan

## Context

During CLI output format planning, we discussed transitioning from dictionary returns to structured dataclass objects in the functions module. After comprehensive analysis of the current architecture and inventory source variations, this change is **strongly recommended** as a foundation for future enhancements.

## Current State Analysis

Functions in `functions.py` return dictionaries with structured data:
- `query_inventory()` returns `dict[str, Any]`
- `query_content()` returns `dict[str, Any]` 
- `detect()` returns `dict[str, Any]`
- `summarize_inventory()` returns `str` (will change to `dict[str, Any]`)

### Schema Inconsistencies Identified

**Sphinx inventories** include:
- `_inventory_project`, `_inventory_version` 
- Rich object metadata (`domain`, `role`, `priority`)
- Standard Sphinx object structure

**MkDocs inventories** include:
- `_inventory_source` field
- Page-level objects with `content_preview`
- Limited metadata (synthetic `domain: 'page'`, `role: 'doc'`)

**Current problems:**
- No compile-time validation of result structure
- Runtime errors from missing/unexpected fields
- IDE tooling provides no assistance
- Difficult to add new inventory sources consistently

## Proposed Architecture

### Core Inventory Object Structure

```python
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Any, List

# Source type will be a simple string to support third-party extensions
# Examples: "sphinx_objects_inv", "mkdocs_search_index", "llms_txt"

@dataclass
class InventoryObject:
    """Universal inventory object with source attribution."""
    
    # Universal fields (always present)
    name: str  # Primary object name from inventory (e.g., "MyClass.method", "User Guide")
    uri: str  # Relative URI to object content (e.g., "/api/module.html#MyClass.method", "/guides/user/")
    source_type: str  # Inventory source identifier (e.g., "sphinx_objects_inv", "mkdocs_search_index")
    source_url: str  # URL to the inventory source itself (e.g., "https://docs.example.com/objects.inv")
    
    # Optional display enhancement
    display_name: Optional[str] = None  # Human-readable name if different from name (falls back to name)
    
    # Source-specific metadata (includes domain, role, priority, content_preview, etc.)
    specifics: dict[str, Any] = field(default_factory=dict)
    
    # Search/matching metadata
    relevance_score: float = 0.0
    match_reasons: list[str] = field(default_factory=list)
    
    @property
    def effective_display_name(self) -> str:
        """Returns display_name if available, otherwise falls back to name."""
        return self.display_name or self.name

@dataclass
class SearchMetadata:
    """Search operation metadata."""
    results_count: int
    results_max: int
    matches_total: Optional[int] = None
    search_time_ms: Optional[int] = None

@dataclass
class InventorySourceInfo:
    """Information about an inventory source."""
    source_type: str
    source_url: str
    processor_name: str
    confidence: float
    object_count: int

@dataclass
class InventoryQueryResult:
    """Complete result for inventory queries."""
    source: str
    query: str
    objects: list[InventoryObject]
    search_metadata: SearchMetadata
    inventory_sources: list[InventorySourceInfo]

@dataclass
class ContentQueryResult:
    """Complete result for content queries."""
    source: str
    query: str
    documents: list[ContentDocument]  # TBD structure
    search_metadata: SearchMetadata
```

## Benefits

- **Type safety**: Catch errors at development time
- **Source attribution**: Every object knows its provenance
- **Consistency**: Unified interface across inventory sources
- **Future-proof**: Easy to add new inventory sources
- **Multi-source ready**: Prepared for inventory merging strategies
- **Maintainability**: Clear contracts between layers
- **Tooling**: Better IDE support and refactoring capabilities

## Implementation Strategy

### Phase 1: Core Implementation
1. Add structured dataclass definitions to new `results.py` module
2. Update `processors.py` detection results to use structured objects
3. Convert `functions.py` to return structured objects
4. Update CLI and MCP server to handle structured objects

### Phase 2: Processor Integration
1. Update inventory processors to return `InventoryObject` instances
2. Implement source attribution in all processors
3. Comprehensive testing across all supported documentation formats

### Phase 3: Structure Processor Enhancement
1. Update structure processors to inspect inventory object sources and perform content URL mappings accordingly
2. Add capability advertisement for which inventory sources each structure processor supports
3. Update functions layer to filter inventory objects based on structure processor capabilities before forwarding for content extraction

## Implementation Notes

### Implementation Approach
```python
# In functions.py - direct implementation
async def query_inventory(...) -> InventoryQueryResult:
    # Structured implementation
    result = InventoryQueryResult(...)
    return result
```

### Processor Integration
Each inventory processor's `filter_inventory()` method should return `list[InventoryObject]` instead of `list[dict[str, Any]]`. Source attribution is added at the processor level:

```python
# In sphinx/detection.py
def format_inventory_object(objct) -> InventoryObject:
    return InventoryObject(
        name=objct.name,
        uri=objct.uri,
        source_type="sphinx_objects_inv",
        source_url=derive_inventory_url(base_url).geturl(),
        display_name=objct.dispname if objct.dispname != '-' else None,  # Falls back to name
        specifics={
            'domain': objct.domain,
            'role': objct.role,
            'priority': objct.priority,
            'inventory_project': inventory.project,
            'inventory_version': inventory.version,
        }
    )
```

## Decision

**APPROVED** - This is now a high-priority implementation item. The structured objects are a prerequisite for multiple inventory source support and provide immediate development benefits with manageable migration complexity.

## Implementation Status

**DESIGN COMPLETE** - Comprehensive design documents have been created:

1. **Structured Inventory Objects Design** (`documentation/architecture/designs/structured-inventory-objects.rst`)
   - Complete object model with `InventoryObject`, `SearchResult`, `ContentDocument`
   - Source attribution strategy and metadata handling
   - Backwards compatibility through enhanced serialization

2. **Inventory Processor Patterns** (`documentation/architecture/designs/inventory-processor-patterns.rst`)
   - Standardized implementation patterns for all inventory processors
   - Consistent detection, formatting, filtering, and error handling
   - Performance optimization and testing guidelines

3. **Results Module Design** (`documentation/architecture/designs/results-module-design.rst`)
   - Centralized module for all structured result objects
   - Type safety, validation, and serialization support
   - Integration patterns with existing modules

**READY FOR IMPLEMENTATION** - The design provides:
- Complete type definitions and interfaces
- Migration strategy with backwards compatibility
- Performance considerations and optimization patterns
- Testing and validation frameworks
- Integration guidance for all affected modules

## Success Criteria

- [ ] All functions in `functions.py` return structured objects
- [ ] MCP server JSON schema compatibility maintained
- [ ] CLI output format unchanged unless explicitly requested
- [ ] Full type safety in internal object handling
- [ ] Source attribution for all inventory objects
- [ ] Performance impact < 5% for single-source operations

## Dependencies

- Extension of `serialize_for_json()` function for new dataclass types
- Update to processor interfaces for structured returns
- Documentation updates for new object structure