# Librovore MCP Server Test Results & Issues

## Content Query Issues


### Content Extraction Issues (2025-09-21)

**HTTPX sparse results** - https://www.python-httpx.org/
- Issue: Minimal content extraction (only document titles, no rich content)
- Cause: Pure MkDocs without mkdocstrings, limited structured content in search index
- Impact: Functional but not ideal for comprehensive documentation queries
- Status: Expected behavior, but worth monitoring for pattern improvements

**Python docs missing built-in functions** - https://docs.python.org/3/
- Issue: Query for "print" returns C API functions but not built-in print() function
- Impact: Users may not find the most relevant/expected documentation
- Possible causes: Inventory filtering, search term matching, or object type prioritization
- Status: Functional but could benefit from improved relevance ranking

**robots.txt 403 blocking queries completely** - https://docs.pytest.org/en/latest/
- Issue: When robots.txt returns 403 Forbidden, queries fail completely instead of proceeding
- Impact: Sites with restrictive robots.txt policies are completely unusable
- Expected behavior: Queries should proceed anyway when robots.txt is inaccessible (403, 404, etc.)
- Current behavior: Shows clear error message but stops all processing
- Status: REGRESSION - queries used to work despite robots.txt issues
- Added: 2025-01-27

## 2025-01-26 - emcd-appcore CLI Framework Research - RESOLVED

**Status**: RESOLVED - Found comprehensive examples and implementation patterns in appcore source code.

**Note**: This was not a Librovore issue - the examples and patterns were available in the main documentation page and especially in the source code at `../python-appcore/sources/appcore/introspection.py`, which serves as a complete reference implementation.
