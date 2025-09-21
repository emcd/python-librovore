# Librovore MCP Server Test Results & Issues

## Content Query Issues

### Site Access Issues (2025-09-16)

**pytest docs** - https://docs.pytest.org/en/latest/
- Error: `403 Forbidden` on robots.txt, leading to "No Compatible Processor Found"
- Previously worked according to test list
- May be temporary access restriction or network-level blocking

**requests docs** - https://requests.readthedocs.io/en/latest/
- Error: `403 Forbidden` on robots.txt, leading to "No Compatible Processor Found"
- Previously worked according to test list
- May be temporary access restriction or network-level blocking

**Note**: These appear to be network/access issues rather than implementation problems, as:
- Other Sphinx sites (Python docs) work perfectly
- Error occurs at robots.txt fetch, before any processing logic
- Sites are listed as "expected to work" in test documentation

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
