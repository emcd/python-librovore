# MCP Server UX Feedback

Based on exploration of the Sphinx MCP server during development of HTTP cache design document.

## Tool Experience Summary

Overall the MCP server worked well for retrieving documentation from https://emcd.github.io/python-appcore/stable/sphinx-html. The workflow was relatively smooth but revealed several areas for improvement.

## Interface Issues Encountered

### 1. Error Message Quality
**Issue**: The initial `query_documentation` call failed with `"error": "'domain'"` which was cryptic.
**Impact**: Had to guess what went wrong and try a different approach.
**Suggestion**: Provide clearer error messages like "Missing required parameter 'domain'" or "Invalid domain value: expected 'py', 'std', etc."

### 2. Domain Parameter Documentation
**Issue**: The `domain` parameter requirement wasn't clear from the initial failure.
**Impact**: Required experimentation to understand what domains are valid.
**Suggestion**: Either make domain optional with sensible defaults, or provide clearer documentation about valid domain values.

### 3. Documentation Formatting Issues
**Issue**: Extracted documentation had formatting problems - missing spaces in signatures like "classappcore.generics.Result" instead of "class appcore.generics.Result".
**Impact**: Reduced readability of extracted content.
**Suggestion**: Improve HTML-to-text conversion to preserve proper spacing.

### 4. Fuzzy Search Transparency
**Issue**: Using fuzzy matching with `extract_inventory` worked but it wasn't clear how the fuzzy threshold affects results.
**Impact**: Unclear whether threshold should be adjusted for better results.
**Suggestion**: Either provide fuzzy match scores in results or document threshold behavior better.

### 5. Multi-Step Discovery Workflow
**Issue**: Finding information required multiple sequential calls: `extract_inventory` → `extract_documentation` for each object.
**Impact**: More verbose than needed for exploratory research.
**Suggestion**: Consider a higher-level "explore topic" function that does inventory search + documentation extraction in one call.

## Positive Aspects

### 1. Inventory Search Effectiveness
The fuzzy search on inventory worked well for finding relevant objects like "Result", "Error", "Value" even with partial terms.

### 2. Documentation Extraction Accuracy
Once found, the `extract_documentation` calls returned relevant content with proper URLs and signatures.

### 3. Response Structure
The structured responses with object counts, filters applied, and organized results were helpful for understanding what was found.

## Suggested Improvements

### Short Term
1. Improve error messages with specific details about what's wrong
2. Fix documentation formatting issues (spacing in signatures)
3. Make domain parameter optional with reasonable defaults

### Medium Term  
1. Add fuzzy match scores to search results
2. Create combined "explore" function for common workflows
3. Add parameter validation with helpful suggestions

### Long Term
1. Consider caching frequently accessed documentation for performance
2. Add support for cross-referencing between related objects
3. Implement progressive search refinement (suggest narrowing/broadening searches)

## Implementation Notes

The server successfully demonstrated its value during the HTTP cache design process - being able to quickly look up `Result`, `Error`, and `Value` class details was exactly the kind of use case it should excel at. The core functionality is solid; the issues are primarily around polish and user experience.