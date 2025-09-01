# Librovore MCP Server Test Results & Issues

> **📋 Status**: Major issues resolved in v1.0a1. See `development-status.md` for current status summary.

## Test Failures Summary

### Remaining Incompatible Sites

| Site | Analysis | Recommendation |
|------|----------|----------------|
| https://starlette.readthedocs.io | Pure MkDocs without mkdocstrings - no object inventory | Enable mkdocstrings plugin or use alternative documentation tools |

## Analysis

### Root Cause Analysis  
Sites without Sphinx-compatible object inventories cannot be processed by librovore's structured approach.

**Compatibility Pattern**: 
- **Plain MkDocs**: No support (requires mkdocstrings plugin)
- **MkDocs + mkdocstrings**: Supported if properly configured
- **Sphinx**: Full support

## Interface Layer Issues (AOP Decorator Testing - 2025-08-31)


### MCP Server Issues

**MCP Response Sizes Significantly Larger Than Expected**
- **Problem**: MCP server content query responses are much larger than requested content limits
- **Expected**: Response sizes should respect content filtering and pagination parameters
- **Observed**: Content responses exceed 69,000+ tokens even with `results_max=1` and `include_snippets=false`
- **Test Case**: `mcp__librovore__query_content` with FastAPI documentation  
- **Impact**: MCP responses frequently exceed token limits, causing tool failures
- **Possible Causes**: 
  - Rich HTML-to-Markdown conversion creating verbose output
  - Lack of effective content truncation in structure processors
  - Missing content length estimation before response serialization

## Current Status Summary

### 🔄 Future Considerations
1. **Enhanced MkDocs Detection**: Better classification of MkDocs variants
2. **Documentation**: Clear usage guidelines about site compatibility
3. **Ecosystem Expansion**: Support for additional documentation formats
4. **CLI Format Consistency**: Fix CLI exception rendering to respect `--display-format` setting
5. **MCP Response Optimization**: Implement effective content truncation and size estimation

