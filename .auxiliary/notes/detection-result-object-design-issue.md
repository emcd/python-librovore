# Design Issue: Detection Results Should Be Structured Objects

## Issue Description

**Status**: 🔍 DESIGN ISSUE - Architecture inconsistency identified
**Date**: 2025-08-24
**Reporter**: Code Review Feedback Analysis

## Problem

Currently there is an architectural inconsistency in result types across the functions API:

- `query_inventory()` returns `InventoryQueryResult | ErrorResponse` (structured objects)  
- `query_content()` returns `ContentQueryResult | ErrorResponse` (structured objects)
- `detect()` returns `dict[ str, Any ] | ErrorResponse` (raw dictionary + structured errors)

This violates the principle of consistent data structures across the API.

## Current Implementation

```python
# functions.py
async def detect(...) -> dict[ str, Any ] | ErrorResponse:
    # Returns raw dictionary for success case
    return {
        'success': True,
        'source': location,
        'detections': detections,
        'detection_optimal': detection_optimal,
        'time_detection_ms': detection_time_ms
    }
```

## Proposed Solution

Create a structured `DetectionResult` dataclass in `results.py`:

```python
class DetectionResult( __.immut.DataclassObject ):
    ''' Detection results with processor selection and timing. '''
    
    source: str
    detections: list[Detection] 
    detection_optimal: Detection | None
    time_detection_ms: int
```

Update `functions.detect()` return type:
```python
async def detect(...) -> DetectionResult | ErrorResponse:
```

## Impact Analysis

**Breaking Change**: Yes - this would be a breaking change to the functions module API

**Benefits**:
- Consistent structured objects across all functions
- Type safety and IDE support 
- Self-formatting capabilities like other result types
- Better alignment with overall architecture

**Files Affected**:
- `sources/librovore/functions.py` - Update return type
- `sources/librovore/results.py` - Add DetectionResult class  
- `sources/librovore/cli.py` - Update render functions (minor)
- `sources/librovore/server.py` - Update MCP handlers (minor)

## Current Workaround

The CLI render functions currently handle the dictionary format with explicit checks and TODO comments marking the design inconsistency.

## Recommendation

This should be addressed in a future architecture enhancement release to maintain API consistency across the functions module.