# Librovore MCP Server Test Results & Issues

## Formatting Issues

### Content ID Spacing
- **Issue**: In content query results, the `Content ID` metadata appears immediately after the content text without a blank line separator
- **Impact**: Poor visual separation between content and metadata in Rich markdown display
- **Example**: Content ends with `...final` then immediately shows `**URL:** https://...` 
- **Fix needed**: Add blank line before metadata section in content result rendering
- **Location**: Likely in `sources/librovore/results.py` in the `ContentQueryResult.render_as_markdown()` method
