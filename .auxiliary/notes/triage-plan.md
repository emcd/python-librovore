# Librovore Development Triage Plan

Based on comprehensive alpha testing feedback and analysis, this document outlines prioritized improvements for librovore development.

## High Priority - User Experience Improvements

### 1. Better Error Messages 🔥
**Current Issue**: Generic "No processor found to handle source: inventory" for all incompatible sites
**Improvement**: Provide specific, actionable error messages
**Implementation**:
- Check for `objects.inv` existence first (404 vs other errors)
- Specific messages:
  - "Site lacks Sphinx object inventory (objects.inv not found at {url})"
  - "Documentation site uses incompatible format (detected: MkDocs without mkdocstrings)"
  - "ReadTheDocs site requires versioned URL - try: {suggested_url}"
- **Files to modify**: `sources/librovore/exceptions.py`, error handling in CLI
- **Effort**: Low - enhance existing error handling
- **Impact**: Prevents user confusion, clearer troubleshooting

### 2. Site Compatibility Detection 🔥
**Current Issue**: Silent failure when sites lack required inventories
**Improvement**: Proactive compatibility assessment with user guidance
**Implementation**:
- Pre-flight inventory detection before attempting processing
- Helpful suggestions for common cases (ReadTheDocs URL patterns)
- Clear documentation about supported site types
- **Files to modify**: Detection pipeline, possibly new compatibility checker module
- **Effort**: Medium - new functionality but straightforward
- **Impact**: Better onboarding, clearer user expectations

## Medium Priority - Ecosystem Expansion

### 3. URL Resolution Intelligence ⚠️
**Issue**: ReadTheDocs sites need versioned URLs (`/en/latest/objects.inv`)
**Pattern**: Many RTD sites follow predictable URL patterns
**Improvement**: Intelligent URL pattern fallback
**Implementation**:
- Try common URL patterns before failing:
  - Base URL + `/objects.inv`
  - Base URL + `/en/latest/objects.inv`
  - Base URL + `/en/stable/objects.inv`
- Log attempted URLs for debugging
- **Files to modify**: URL resolution logic in inventory processors
- **Effort**: Medium - systematic URL pattern testing
- **Impact**: Expand working site coverage without architectural changes

### 4. MkDocs Detection Refinement ⚠️
**Current**: Binary detection (has inventory or doesn't)
**Issue**: MkDocs ecosystem fragmentation - some variants could work
**Improvement**: Better MkDocs variant classification
**Implementation**:
- Detect MkDocs + mkdocstrings (should work) vs plain MkDocs (won't work)
- Check for mkdocstrings indicators in HTML structure
- Provide specific guidance: "Site uses MkDocs - enable mkdocstrings to work with librovore"
- **Files to modify**: MkDocs detection logic, possibly new detector functions
- **Effort**: Medium - requires MkDocs ecosystem research
- **Impact**: Clearer user guidance on when to expect success

## Explicitly Not Recommended

### ❌ Fallback HTML Parsing
**Rationale**: Would undermine librovore's core value proposition of structured access
**Alternative**: Clear documentation about architectural scope and limitations
**Decision**: Maintain inventory-based approach as differentiator from generic scrapers

## Implementation Strategy

### Success Metrics
- Reduced user confusion in error scenarios
- Increased success rate for supported documentation types
- Clear user expectations about site compatibility
- Maintained architectural coherence and reliability

## Notes

- Architecture validation from testing confirms inventory-based approach is sound
- Current ecosystem coverage (Python, Flask, FastAPI, pytest, NumPy, pandas, Django, Panel) validates core use case
- Future expansion should maintain structured data principles while broadening compatibility
