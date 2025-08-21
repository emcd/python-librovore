# Librovore MCP Server Test Results & Issues

> **📋 Status**: Major issues resolved in v1.0a1. See `development-status.md` for current status summary.

## Test Failures Summary

### URL Pattern Issues ✅ RESOLVED

| Site | Status | Resolution |
|------|--------|------------|
| https://requests.readthedocs.io | ✅ **WORKING** | Automatic URL pattern extension discovers `/en/latest/` path |
| https://docs.pydantic.dev | ✅ **WORKING** | Automatic URL pattern extension discovers `/latest/` path |

**Fix Applied**: Universal URL pattern extension system (v1.0a1) automatically discovers working documentation URLs:
- Tries common patterns: `/en/latest/`, `/latest/`, `/en/stable/`, `/stable/`, etc.
- Transparent URL resolution returns working URLs to users
- Redirects cache eliminates repeated pattern probing

### Remaining Incompatible Sites

| Site | Analysis | Recommendation |
|------|----------|----------------|
| https://starlette.readthedocs.io | Pure MkDocs without mkdocstrings - no object inventory | Enable mkdocstrings plugin or use alternative documentation tools |

**Root Cause**: Sites without Sphinx-compatible object inventories cannot be processed by librovore's structured approach.

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

## Current Status Summary

### ✅ Completed Improvements
1. **✅ Site Detection**: Universal URL pattern extension with automatic discovery
2. **✅ Error Handling**: Structured, actionable error messages implemented
3. **✅ Serialization**: Fixed Dictionary serialization for all JSON output
4. **✅ URL Resolution**: Transparent working URL discovery and caching

### 🔄 Future Considerations
1. **Enhanced MkDocs Detection**: Better classification of MkDocs variants
2. **Documentation**: Clear usage guidelines about site compatibility
3. **Ecosystem Expansion**: Support for additional documentation formats

## Impact on Template Integration

The tool is valuable despite limitations:
- Covers major Python documentation sites (Python, Flask, FastAPI)
- Provides superior structured access compared to raw scraping
- Fills gap between curated (context7) and raw (firecrawl) approaches
- Worth including with clear usage guidelines about compatibility