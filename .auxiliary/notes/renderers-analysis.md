# Renderers Analysis: Domain-Specific Rendering and Architectural Alignment

## Current State Assessment

### Architecture Gap Identified

The results module design document clearly specifies self-rendering object methods, but implementation is incomplete:

**Documented Design Elements:**
- `InventoryObject.render_specifics_markdown(*, show_technical: bool = True)` → `tuple[str, ...]`
- `InventoryObject.render_specifics_json()` → `__.immut.Dictionary[str, __.typx.Any]`
- Object-specific `to_json_dict()` methods with domain knowledge
- `serialize_for_json()` delegates to object-specific methods

**Missing Complete Method Specifications:**
The design shows `InventoryObject` rendering methods but doesn't specify the complete interface for all result objects. These objects also need rendering methods:

- `ContentQueryResult` 
- `InventoryQueryResult`
- `ErrorResponse`
- `DetectionsResult` (for survey-processors)
- `InventoryLocationInfo`
- `SearchMetadata`

**Gap**: The design document should explicitly state that **all major result objects** implement both `render_as_markdown()` and `render_as_json()` methods, not just `InventoryObject`.

### Current CLI Anti-Pattern

The existing CLI functions violate the documented architecture:
- `_render_inventory_query_result_json()` uses generic `_results.serialize_for_json()`
- `_render_content_query_result_json()` uses generic `_results.serialize_for_json()` 
- Objects don't self-format, CLI formats them externally

## JSON Rendering Functions Duplication Analysis

### High Duplication
- `_render_inventory_summary_json()` and `_render_survey_processors_json()` are identical
- Both just call `serialize_for_json()` + `json.dumps()`

### Moderate Duplication  
- `_render_detect_result_json()` and `_render_inventory_query_result_json()` share ErrorResponse handling pattern
- Common pattern: check for ErrorResponse → call generic serializer

### Unique Logic
- `_render_content_query_result_json()` has special truncation logic
- `_render_error_json()` specialized for error formatting

## Proposed Solution

### Phase 1: Complete Object Method Implementation
- Add missing `render_as_markdown()` and `render_as_json()` methods to all major result objects
- Migrate business logic from CLI rendering functions into object methods  
- Update `serialize_for_json()` to properly delegate to object methods

### Phase 2: Extract Presentation Logic
- Create `renderers/` subpackage with `__.py` import hub (not `base.py`)
- Move CLI-specific concerns (truncation, error formatting, display helpers) to renderers
- Update CLI to call object methods + presentation coordinators

## Renderers Subpackage Structure

```
renderers/
├── __.py           # Common utilities (import cascade pattern)
├── json.py         # JSON presentation coordination  
└── markdown.py     # Markdown presentation coordination
```

### Renderers Role Clarification
Based on the design document, renderers should be **presentation coordinators**, not **business logic containers**:

- **Objects handle domain logic**: `result.render_as_json()`
- **Renderers handle presentation**: formatting, truncation, CLI-specific display concerns
- **Example**: `_truncate_query_content()` belongs in renderers because it's presentation logic

## Work Involved

### Phase 1: Complete Object Method Implementation
- Add missing `render_as_markdown()` and `render_as_json()` methods to all major result objects
- Migrate business logic from CLI rendering functions into object methods
- Update `serialize_for_json()` to properly delegate to object methods

### Phase 2: Extract Presentation Logic
- Create `renderers/` subpackage with `__.py` import hub
- Move CLI-specific concerns (truncation, error formatting, display helpers) to renderers
- Update CLI to call object methods + presentation coordinators

## Caveats and Concerns

**Design Consistency**: Current implementation completely bypasses the documented self-rendering architecture. Phase 1 is essential before any consolidation.

**Method Interface Standardization**: Need to define consistent signatures across all result objects (e.g., should all objects support `show_technical` parameter?).

**Circular Dependencies**: Renderers must not import business logic - only presentation utilities and the objects themselves.

## Next Steps

1. Designer should update results module design document to specify complete rendering interface for all result objects
2. Implement missing object rendering methods per updated design
3. Extract presentation logic to renderers subpackage
4. Update CLI to use object methods + presentation coordinators

The architectural vision in the design document is sound, but there's a significant implementation gap that needs addressing before any consolidation or extraction work.