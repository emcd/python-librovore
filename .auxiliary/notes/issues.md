# Librovore Issues and Enhancement Opportunities

## Silent Filter Failures

**Issue:** When users apply filters that don't match any objects, the system silently returns unfiltered results without warning or error.

**Examples:**
- Filtering `domain=py` on a pure MkDocs site (which uses `domain=page`)
- Using filter values that don't exist in the inventory
- Applying Sphinx-specific filters to MkDocs inventories

**Current Behavior:**
```bash
# Pure MkDocs site with domain=page for all objects
hatch run librovore query-inventory https://www.python-httpx.org/ httpx --filters domain=py
# Returns: All 24 results (filter silently ignored)
```

**Impact:**
- Users may not realize their filter didn't work
- Confusing when expecting filtered results but getting everything
- Makes it hard to distinguish "no matches" from "filter didn't apply"

**Mitigation:**
- The `--summarize` feature partially helps by showing actual domain values
- Users can see `domain: page (100%)` and realize this isn't a Sphinx site

**Potential Solutions:**
1. **Strict mode**: Error when filter doesn't match any objects
2. **Warning**: Display warning but continue with unfiltered results
3. **Metadata**: Add `filters_applied` vs `filters_ignored` to search metadata
4. **Validation**: Pre-validate filters against processor capabilities before querying

**Discovered:** 2025-10-20 during summary feature testing
**Priority:** Medium (UX improvement, not a critical bug)
