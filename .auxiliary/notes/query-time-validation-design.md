# Query-Time Validation Design Discussion

## Background

After implementing Layer 1 confidence thresholds (50% minimum), we discussed implementing Layer 2 validation. An initial attempt at detection-time validation was reverted due to design flaws. This document captures the refined design approach for query-time validation.

## Problem Analysis

The core issue is not extraction failures that raise exceptions, but **successful extractions that return empty or meaningless results**. Examples:
- Sphinx processor on MkDocs site returns results with empty signatures/descriptions
- Processor on unsupported theme extracts nothing useful but reports "success"
- Users receive poor experience with no clear indication of incompatibility

## Design Decision: Query-Time Validation

**Approach**: Validate actual extraction results rather than pre-validate during detection.

**Rationale**:
- Detection remains fast and lightweight (Layer 1 confidence thresholds only)
- Validation occurs when actually needed, not speculatively
- No circular dependencies between structure and inventory detection
- Clear error messages when problems are discovered

## Exception Hierarchy

Based on project nomenclature guidelines:

```python
class StructureProcessFailure( Omnierror ):
    ''' Structure processor failed to complete processing. '''

class ContentExtractFailure( StructureProcessFailure ):
    ''' Failed to extract meaningful content from documentation. '''

class ThemeDetectFailure( StructureProcessFailure ):
    ''' Theme detection failed during processing. '''

class StructureIncompatibility( Omnierror ):
    ''' Documentation structure incompatible with processor. '''
```

## Implementation Strategy

### Integration Point
Validate in `sources/librovore/functions.py:query_content()` after content extraction (around line 101-107).

### Current Flow
```python
# Extract content as normal
contents = await sdetection.extract_contents(
    auxdata, source, candidates, include_snippets = include_snippets )

# Process results
contents_by_relevance = sorted(
    contents, key = lambda x: x.get( 'relevance_score', 0.0 ), reverse = True )
```

### Enhanced Flow
```python
# Extract content as normal
contents = await sdetection.extract_contents(
    auxdata, source, candidates, include_snippets = include_snippets )

# Validate extraction results
_validate_extraction_results(
    contents, candidates, sdetection.processor.name, source )

# Process results
contents_by_relevance = sorted(
    contents, key = lambda x: x.get( 'relevance_score', 0.0 ), reverse = True )
```

## Key Benefits

1. **Performance**: Detection remains fast, validation only when needed
2. **Actionable Errors**: Clear messages about what went wrong and why
3. **No Circular Dependencies**: Structure validation independent of inventory detection
4. **Fail Fast**: Problems discovered before returning poor results to users
5. **Future Extensibility**: Could enable fallback to alternative processors

## User Experience Improvement

**Current**: Silent failures or generic errors when extraction produces empty results
**Proposed**: Clear, actionable messages:
- "No content extracted by sphinx from https://docs.example.com. The documentation structure may be incompatible with this processor."
- "Processor sphinx extracted mostly empty content from https://docs.example.com. Got 1 meaningful results from 10 requested objects. This may indicate incompatible theme or documentation structure."

## Discussion Outcomes

1. **Exception naming**: Use `StructureProcessFailure`, `ContentExtractFailure`, `ThemeDetectFailure` (not compound names)
2. **Validation approach**: Check actual results rather than pre-validation sampling
3. **Integration point**: Validate in `query_content` after extraction, not during detection
4. **Success threshold**: 10% minimum meaningful results (configurable)
5. **Error vs warning**: Low success rates should be errors, not warnings with partial results

## Status

**IMPLEMENTED** ✅

The query-time validation system has been successfully implemented and integrated:

### Implementation Details

- **Exception hierarchy**: Added to `sources/librovore/exceptions.py`
  - `StructureIncompatibility`: For completely empty extraction results
  - `StructureProcessFailure`: Base for processing failures  
  - `ContentExtractFailure`: For low success rates (< 10%)
  - `ThemeDetectFailure`: For theme detection issues

- **Validation function**: `_validate_extraction_results()` in `sources/librovore/functions.py`
  - 10% minimum success rate threshold (`_SUCCESS_RATE_MINIMUM = 0.1`)
  - Checks for meaningful content (non-empty signatures or descriptions)
  - Validates after content extraction in `query_content()`

- **Integration point**: Line 126-127 in `sources/librovore/functions.py:query_content()`
  - Validates extraction results before processing for relevance ranking
  - Provides clear error messages for incompatible processors

### Testing

Comprehensive test coverage added to `tests/test_000_librovore/test_300_functions.py`:
- Tests for no objects requested (passes validation)
- Tests for empty content extraction (raises `StructureIncompatibility`)
- Tests for meaningful content (passes validation)
- Tests for low success rates (raises `ContentExtractFailure`)
- Tests for edge cases at exactly 10% threshold

### Quality Assurance

- ✅ All tests pass (273/273)
- ✅ All linters pass (Ruff, Vulture, Pyright)
- ✅ Code coverage improved for exceptions module (58% → 68%)
- ✅ Follows project practices and style guidelines

## Related Documents

- `.auxiliary/notes/layer2-validation-attempt.md` - Documents the reverted detection-time approach
- `sources/librovore/detection.py:33` - Layer 1 confidence threshold implementation
