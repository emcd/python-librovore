# MkDocs Inventory Processor Design Sketch

## Overview

Design for a new MkDocs inventory processor to handle `search_index.json` files as inventory sources, enabling sites like HTTPX (pure MkDocs without mkdocstrings) to work with librovore's inventory-based architecture.

## Current Architecture Context

- **Existing MkDocs Structure Processor**: Handles content extraction from MkDocs HTML pages
- **Proposed MkDocs Inventory Processor**: Will handle `search_index.json` as an inventory source
- **Inventory-First Approach**: All operations require inventory detection before proceeding to content operations

## MkDocs Search Index as Inventory

### Data Structure
```json
{
  "config": {
    "lang": ["en"],
    "separator": "[\\s\\-]+",
    "pipeline": ["stopWordFilter", "stemmer"]
  },
  "docs": [
    {
      "location": "api/",
      "title": "Developer Interface",
      "text": "Full documentation content..."
    },
    {
      "location": "quickstart/",
      "title": "Quickstart",
      "text": "Getting started content..."
    }
  ]
}
```

### Inventory Mapping
- **Object URI**: `location` field (e.g., "api/", "quickstart/")
- **Object Name**: `title` field (e.g., "Developer Interface", "Quickstart")
- **Rich Content**: `text` field (embedded documentation content)

## Detection Strategy

### Probe Paths
1. `/search/search_index.json` (confirmed for HTTPX)
2. `/search_index.json` (alternative common path)
3. `/assets/search/search_index.json` (potential Material theme variant)

### Detection Logic
- Attempt after standard Sphinx inventory detection fails
- Validate JSON structure (requires `docs` array with `location`/`title` fields)
- Cache parsed inventory for subsequent operations

## Dual-Purpose Usage

### Query-Inventory Operations
- **Search**: Filter `docs` array by `title` and `location` fields
- **Fuzzy Matching**: Apply existing fuzzy search to object names (titles)
- **Result Format**: Return inventory objects with URI (`location`) and display name (`title`)

### Query-Content Integration
- **Option 1**: Use embedded `text` field directly from inventory
- **Option 2**: Use `location` to guide content extraction from actual pages
- **Hybrid**: Prefer embedded text, fall back to page fetching for enhanced content

## Multiple Inventory Handling

### Scenario: Site with Both `objects.inv` and `search_index.json`

**Challenges:**
- Different object granularities (API symbols vs documentation pages)
- Potential overlap or complementary coverage
- User expectation management

**Strategy Options:**
1. **Precedence Order**: Prefer Sphinx `objects.inv` when available, fall back to MkDocs search index
2. **Merged Inventory**: Combine both sources into unified inventory (with source tagging)
3. **User Selection**: Allow users to specify preferred inventory source
4. **Automatic Selection**: Use heuristics to choose most appropriate source based on query type

**Recommended Approach**: Start with **Precedence Order** (Sphinx first) for simplicity, with future extensibility for merging.

## Implementation Architecture

### New Components
- **MkDocsInventoryProcessor**: Inherit from base inventory processor
- **Detection Logic**: Add to existing processor detection pipeline
- **Inventory Cache**: Store parsed `search_index.json` data
- **Query Interface**: Implement standard inventory query methods

### Integration Points
- **Detection Pipeline**: Add MkDocs inventory detection after Sphinx
- **Functions Layer**: No changes needed (uses generic inventory interface)
- **Structure Processor**: Coordinate with existing MkDocs structure processor

## Benefits

### User Experience
- Sites like HTTPX become fully supported instead of rejected
- Consistent inventory-based workflow across all documentation types
- Natural progression: inventory → filtered content

### Technical
- Maintains architectural consistency (inventory-first approach)
- Leverages existing caching and query infrastructure
- Clean separation between inventory and content operations

## Open Questions

1. **Content Strategy**: Should we prefer embedded `text` or fetch actual pages?
2. **Multiple Inventories**: How aggressively should we merge vs choose between sources?
3. **Performance**: How do we handle large search indices efficiently?
4. **Compatibility**: Are there MkDocs variants that structure search indices differently?

## Next Steps

1. Formal design review with system architect
2. Prototype implementation of MkDocs inventory processor
3. Testing with HTTPX and other pure MkDocs sites
4. Multiple inventory handling strategy refinement