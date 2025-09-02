# Content ID Feature Design

## Overview

Add content ID functionality to enable browse-then-extract workflows for documentation content. Users can first query with truncated results to see previews, then extract full content for specific objects using stable content identifiers.

## Design Decision

**Extend existing `query_content` interface** rather than adding a new `extract-content-by-id` function. This maintains interface simplicity while enabling the desired two-stage workflow.

## User Workflow

```bash
# Stage 1: Browse available content with previews
librovore query-content https://docs.python.org/3/ "pathlib" --lines-max 3

# Stage 2: Get full content for specific result
librovore query-content https://docs.python.org/3/ "pathlib" --content-id "cGF0aGxpYi5QYXRo" --lines-max 100
```

## Technical Implementation

### Content ID Strategy

Use **deterministic object identifier**: `base64(location + ":" + object_name)`

**Rationale:**
- **Stable**: Same object always has same ID regardless of query timing
- **Debuggable**: IDs can be decoded to understand what they reference
- **Efficient**: No expensive hashing, no state tracking required
- **Stateless**: Maintains librovore's stateless architecture

### Core Changes

1. **Extend ContentDocument**
   ```python
   class ContentDocument:
       content_id: str  # New field with deterministic ID
       # ... existing fields
   ```

2. **Extend query_content function**
   ```python
   async def query_content(
       # ... existing parameters
       content_id: Optional[str] = None,  # New parameter for content filtering
   ) -> ContentQueryResult:
   ```

3. **Interface Updates**
   - **CLI**: Add `--content-id` parameter to `QueryContentCommand`
   - **MCP**: Add `content_id` parameter to `_produce_query_content_function`

### Implementation Flow

- **Without content_id**: Generate content IDs for all results, return multiple `ContentDocument` objects
- **With content_id**: Decode ID, validate against location, return single matching `ContentDocument`
- **Error handling**: Invalid content IDs raise existing `ProcessorInavailability` exceptions

## Architectural Benefits

1. **Interface Simplicity**: No new functions/commands - extends existing `query_content`
2. **Stateless Design**: Content IDs are self-contained, no session storage required
3. **Dual Interface Compatibility**: Works identically for CLI and MCP server
4. **Self-Rendering Integration**: Content IDs automatically included in JSON/Markdown output
5. **Workflow Efficiency**: Enables natural browse-then-extract patterns

## Rejected Alternatives

- **New `extract-content-by-id` function**: Would proliferate interface complexity
- **Session-based IDs**: Requires state management and cleanup
- **Full content hashing**: Expensive computation for large documents
- **Result index numbers**: Fragile due to query execution order dependencies
- **`preview_lines` parameter**: Redundant with existing `lines_max` functionality

## Implementation Alignment

This design preserves librovore's core architectural principles:
- Maintains stateless operation model
- Extends rather than complicates existing interfaces
- Provides equivalent functionality across CLI/MCP interfaces
- Uses established parameter patterns (`lines_max`)
- Integrates with self-rendering result objects

The content ID feature transforms `query_content` from a simple search function into a flexible content navigation tool while maintaining full backward compatibility.