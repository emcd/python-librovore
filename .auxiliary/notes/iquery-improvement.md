# Inventory Query Search Mode Improvements

## Problem Statement

Investigation of the Tyro documentation discoverability issue revealed a fundamental problem with our inventory search match modes:

1. **Exact mode**: Currently performs substring matching (unexpected behavior)
2. **Fuzzy mode**: Default 50% threshold is too restrictive for discovery use cases
3. **Search failure**: Query `"mutex"` returns 0 results with default Fuzzy, but 6 results with Exact/Regex

## Root Cause Analysis

**Fuzzy similarity scores for "mutex" query:**
- `tyro.conf.create_mutex_group`: **30%** (below 50% threshold)
- `tyro.conf._mutex_group`: **37%** (below 50% threshold)  
- `example-14_mutex`: **48%** (below 50% threshold)
- `tyro._fields.FieldDefinition.mutex_group`: **22%** (below 50% threshold)

**All mutex objects score below the default 50% fuzzy threshold**, causing the search failure. The current fuzzy search is optimized for typo tolerance, not substring discovery.

## Design Options Considered

### Option 1: New Match Mode
Add dedicated `Substring` match mode:
- **Exact**: Only perfect matches
- **Substring**: Substring matching with relevance ordering
- **Fuzzy**: Typo tolerance (keep current threshold)
- **Regex**: Pattern matching (unchanged)

**Pros:** Clear semantics, predictable behavior  
**Cons:** More complexity, users need to learn new mode

### Option 2: Mode-Specific Flags  
Configuration flags like:
- `--exact-includes-substrings`
- `--fuzzy-includes-substrings`  
- `--case-sensitive` (default: false for case-insensitive)

**Pros:** Flexible, backward compatible  
**Cons:** Flag explosion, complex UX

### Option 3: Hybrid Fuzzy Search
Enhance Fuzzy mode with multi-stage scoring:

```python
def enhanced_similar_search(objects, term, fuzzy_threshold=50, contains_term=False, case_sensitive=False):
    results = []
    term_compare = term if case_sensitive else term.lower()
    
    for obj in objects:
        name_compare = obj.name if case_sensitive else obj.name.lower()
        
        # Stage 1: Exact match (100% score)
        if name_compare == term_compare:
            score = 1.0
            reason = 'exact match'
        
        # Stage 2: Substring matches (if --contains-term enabled)  
        elif contains_term and term_compare in name_compare:
            if name_compare.startswith(term_compare):
                score = 0.9
                reason = 'starts with term'
            else:
                score = 0.8  
                reason = 'contains term'
        
        # Stage 3: Enhanced fuzzy matching with partial_ratio for discovery
        else:
            # Use partial_ratio for needle-in-haystack substring discovery
            partial_score = rapidfuzz.fuzz.partial_ratio(term_compare, name_compare)
            
            # Use regular ratio for typo/misspelling detection  
            regular_score = rapidfuzz.fuzz.ratio(term_compare, name_compare)
            
            # Take the higher score for best discovery
            ratio = max(partial_score, regular_score)
            
            if ratio >= fuzzy_threshold:
                score = ratio / 100.0
                score_type = 'partial' if partial_score > regular_score else 'fuzzy'
                reason = f'{score_type} match ({ratio}%)'
            else:
                continue  # Skip low-scoring matches
                
        results.append(SearchResult(obj, score, [reason]))
    
    return sorted(results, key=lambda r: r.score, reverse=True)
```

**Pros:** Single mode handles discovery + typo tolerance  
**Cons:** Complex behavior, harder to predict

### Option 4: Semantic Restructure
Rename modes for clarity:
- **Exact**: Perfect matches only
- **Contains**: Substring matching with relevance ordering  
- **Similar**: Fuzzy/typo tolerance
- **Pattern**: Regex matching

**Pros:** Clear names, intuitive behavior  
**Cons:** Breaking change, requires migration


## Updated Recommendation Based on Feedback

### Final Approach: Option 3 + Option 4 Names + Option 2 Flag

1. **Rename match modes** with cleaner semantics:
   - **Exact**: Perfect matches only
   - **Similar**: Enhanced fuzzy with `partial_ratio` for discovery
   - **Pattern**: Regex matching (unchanged)

2. **Add flags for enhanced control**:
   - `--contains-term`: Applies to Exact and Similar modes for explicit substring matching
   - `--case-sensitive`: Enable case-sensitive matching (default: false)

3. **Enhanced fuzzy matching with dual scoring**:
   - `partial_ratio()` for substring discovery: `"mutex"` → `"create_mutex_group"` = 83%
   - `ratio()` for typo/misspelling detection: `"mutx"` → `"mutex"` (uses indel detection)
   - Take `max(partial_score, regular_score)` for best results
   - `partial_ratio` handles needle-in-haystack, `ratio` handles typos

4. **Default to Similar mode** for best user experience

## Files to Modify
- `sources/librovore/search.py`: Core search implementation, add partial_ratio
- `sources/librovore/interfaces.py`: Rename Fuzzy→Similar in MatchMode enum  
- `sources/librovore/server.py`: Add `--contains-term` and `--case-sensitive` flags, update CLI handling
- `sources/librovore/results.py`: Rename `query` field to `term`
- Tests: Update existing tests, add partial_ratio test cases

## Issues Found: Remaining "query" Usage
The following signatures still use "query" instead of "term":
- `sources/librovore/search.py:35`: `def filter_by_name(objects, query: str, ...)`
- `sources/librovore/results.py:380,460`: Result objects contain `query` field  
- `sources/librovore/exceptions.py:446`: `query_location` parameter

These should be updated to use "term" for consistency.

## Breaking Changes (Acceptable in Alpha)
- **Exact** mode becomes truly exact (no more substring matching)
- **Fuzzy** mode renamed to **Similar** with enhanced partial_ratio
- `--contains-term` flag required for substring behavior  
- Default mode changes to **Similar** for better discovery