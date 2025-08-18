# Librovore MCP Server Test Results & Issues

## Test Failures Summary

### Incompatible Documentation Sites

| Site | Tool | Parameters | Error | Analysis |
|------|------|------------|-------|----------|
| https://docs.pydantic.dev | query_inventory | term="BaseModel", results_max=3 | "No processor found to handle source: inventory" | ❌ No objects.inv (404) |
| https://docs.pydantic.dev | query_content | term="validation", results_max=3 | "No processor found to handle source: inventory" | ❌ No objects.inv (404) |
| https://docs.pydantic.dev | summarize_inventory | term="Field" | "No processor found to handle source: inventory" | ❌ No objects.inv (404) |
| https://requests.readthedocs.io | query_content | term="authentication", results_max=3 | "No processor found to handle source: inventory" | ⚠️ URL issue - use `/en/latest/` |
| https://starlette.readthedocs.io | query_inventory | term="request", results_max=3 | "No processor found to handle source: inventory" | ❌ No objects.inv (404) |

**URL Format Issue**: Requests documentation works correctly but requires the versioned URL:
- ❌ `https://requests.readthedocs.io/objects.inv` → 404 (tested by other Claude)
- ✅ `https://requests.readthedocs.io/en/latest/objects.inv` → 200 (confirmed working in previous tests)

**Root Cause Analysis**:
- **Pydantic, Starlette**: Pure MkDocs without mkdocstrings - no Sphinx object inventories
- **Requests**: ReadTheDocs site with proper inventory, but base URL redirects incorrectly

### Serialization Issues ✅ FIXED

| Site | Tool | Parameters | Error | Status |
|------|------|------------|-------|--------|
| https://docs.python.org | summarize_inventory | term="asyncio", group_by="domain" | "Unable to serialize unknown type: <class 'frigid.dictionaries.Dictionary'>" | ✅ Fixed in functions.py:410 |

**Root Cause**: The `_serialize_dataclass` function didn't handle `frigid.dictionaries.Dictionary` objects used by librovore's immutable data structures.

**Fix Applied**: Enhanced serialization function with:
- Added `hasattr(obj, 'items')` check to handle mapping-like objects 
- Renamed function to `serialize_for_json` and made it public
- Updated CLI to use the same serialization for JSON output
- Now properly converts `frigid.Dictionary` to regular Python `dict` before JSON serialization

**Verification**: ✅ Confirmed working with `hatch run librovore --display-format=JSON summarize-inventory https://docs.python.org/3/ asyncio --group-by=domain`

## Working Sites

### Excellent Support
- **Python Official Docs** (https://docs.python.org)
  - All tools work except summarize_inventory with group_by
  - Rich content extraction with code examples
  - Comprehensive inventory navigation

- **Flask Documentation** (https://flask.palletsprojects.com)
  - Full functionality across all tools
  - Detailed API documentation with parameters

- **FastAPI Documentation** (https://fastapi.tiangolo.com)  
  - Excellent MkDocs support (has object inventory)
  - Detailed parameter tables and source code
  - Complete function signatures

## Analysis

### MkDocs Compatibility
- **Works**: Sites with proper Sphinx object inventories (FastAPI)
- **Fails**: Sites without compatible inventory files (Pydantic, Starlette)
- **Pattern**: MkDocs support requires mkdocstrings or similar Sphinx-compatible inventory generation

### Documentation Generator Support
- **Sphinx**: Full support ✅
- **MkDocs + mkdocstrings**: Selective support (depends on configuration) ⚠️
- **Plain MkDocs**: No support ❌
- **ReadTheDocs variants**: Mixed results ⚠️

## Recommendations for Development

1. **Site Detection**: Consider adding site compatibility detection/warnings
2. **Error Handling**: Improve error messages to indicate missing object inventory
3. **Fallback Strategy**: For unsupported sites, could fall back to basic HTML parsing
4. **Serialization**: Fix Dictionary serialization issue in summarize_inventory with group_by

## Impact on Template Integration

The tool is valuable despite limitations:
- Covers major Python documentation sites (Python, Flask, FastAPI)
- Provides superior structured access compared to raw scraping
- Fills gap between curated (context7) and raw (firecrawl) approaches
- Worth including with clear usage guidelines about compatibility