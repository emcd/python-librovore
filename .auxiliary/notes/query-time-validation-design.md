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
from . import __

class StructureProcessFailure( __.Omnierror ):
    ''' Structure processor failed to complete processing. '''

class ContentExtractFailure( StructureProcessFailure ):
    ''' Failed to extract meaningful content from documentation. '''

class ThemeDetectFailure( StructureProcessFailure ):
    ''' Theme detection failed during processing. '''

# Separate from failures - compatibility issues
class StructureIncompatibility( __.Omnierror ):
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

### Validation Function
```python
_SUCCESS_RATE_MINIMUM = 0.1

def _validate_extraction_results(
    results: __.cabc.Sequence[ __.cabc.Mapping[ str, __.typx.Any ] ],
    requested_objects: __.cabc.Sequence[ __.cabc.Mapping[ str, __.typx.Any ] ],
    processor_name: str,
    source: str
) -> None:
    ''' Validates that extraction results contain meaningful content. '''
    if not requested_objects: return
    if not results:
        raise StructureIncompatibility(
            f"No content extracted by {processor_name} from {source}. "
            f"The documentation structure may be incompatible with this processor." )
    meaningful_results = 0
    for result in results:
        signature = result.get( 'signature', '' ).strip( )
        description = result.get( 'description', '' ).strip( )
        if signature or description: meaningful_results += 1
    success_rate = meaningful_results / len( requested_objects )
    if success_rate < _SUCCESS_RATE_MINIMUM:
        raise ContentExtractFailure(
            f"Processor {processor_name} extracted mostly empty content from {source}. "
            f"Got {meaningful_results} meaningful results from {len( requested_objects )} requested objects. "
            f"This may indicate incompatible theme or documentation structure." )
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

Design approved. Implementation pending based on Layer 1 effectiveness. If Layer 1 confidence thresholds prove insufficient to prevent empty result problems, this validation approach should be implemented.

## Related Documents

- `.auxiliary/notes/layer2-validation-attempt.md` - Documents the reverted detection-time approach
- `sources/librovore/detection.py:33` - Layer 1 confidence threshold implementation