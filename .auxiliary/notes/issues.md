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
