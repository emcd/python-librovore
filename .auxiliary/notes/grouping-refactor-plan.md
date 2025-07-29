# Processor-Agnostic Grouping for summarize_inventory

## Problem
Current `summarize_inventory` function calls `_group_documents_by_domain`, which assumes all processors have a Sphinx-specific "domain" concept. This violates our processor-agnostic architecture.

## Proposed Solution

### 1. Add Group-By Parameter
- `summarize_inventory(source, query='', group_by: str | None = None, ...)`
- `group_by` should correspond to a processor-specific filter key
- Examples: `"domain"` for Sphinx, `"category"` for other processors, `None` for no grouping

### 2. New InventoryQueryDetails Enum Variant
- Add `InventoryQueryDetails.Labels` to ensure processors return grouping labels
- This guarantees that objects include all fields necessary for requested grouping
- Processors must include complete metadata for grouping operations

### 3. Generic Grouping Logic
- Replace `_group_documents_by_domain` with `_group_documents_by_field(documents, field_name)`
- Handle cases where objects don't have the requested grouping field
- Fallback strategies: default group name, skip grouping, or error

### 4. Processor Capability Advertisement
- Consider extending `ProcessorCapabilities` to advertise available grouping fields
- This allows clients to discover valid `group_by` values per processor
- Could be derived from existing `supported_filters` list

## Implementation Flow
1. User calls `summarize_inventory(source, group_by="domain")`
2. Function validates `group_by` against processor capabilities (optional)
3. Calls processor with `details=InventoryQueryDetails.Labels` to ensure labels
4. Applies universal search matching as usual
5. Uses generic `_group_documents_by_field(documents, "domain")` for grouping
6. Formats summary with processor-appropriate grouping

## Benefits
- Maintains processor-agnostic architecture
- Allows flexible grouping per processor type
- Backward compatible (group_by=None for flat summaries)
- Extensible for future processor implementations

## Edge Cases to Handle
- Processor doesn't support requested grouping field
- Objects missing the grouping field value
- Empty groups after filtering/search
- Non-string grouping values