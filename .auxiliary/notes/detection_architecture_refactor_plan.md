# Detection Architecture Refactor Plan

## Overview

Refactor the processor architecture to eliminate duplicate theme detection by making Detection objects the primary interface, with processors serving as lightweight detectors only.

## Current Problems

1. **Duplicate theme detection**: Theme detected in `detection.py` but re-detected in `extraction.py`
2. **Lost metadata**: Detection metadata (theme, capabilities) not passed to extraction functions
3. **Stateless processors**: Processors carry no state but act as heavy interfaces

## Proposed Architecture

### 1. Function Signature Changes

**functions.py** - Add optional processor_name parameter:
```python
async def query_content(
    source: str, query: str, /, *,
    processor_name: __.Absential[ str ] = __.absent,  # NEW
    search_behaviors: _interfaces.SearchBehaviors = _search_behaviors_default,
    filters: __.cabc.Mapping[ str, __.typx.Any ] = _filters_default,
    include_snippets: bool = True,
    results_max: int = 10,
) -> dict[ str, __.typx.Any ]:

async def query_inventory(
    source: str, query: str, /, *,
    processor_name: __.Absential[ str ] = __.absent,  # NEW
    search_behaviors: _interfaces.SearchBehaviors = _search_behaviors_default,
    filters: __.cabc.Mapping[ str, __.typx.Any ] = _filters_default,
    details: _interfaces.InventoryQueryDetails = _interfaces.InventoryQueryDetails.Documentation,
    results_max: int = 5,
) -> dict[ str, __.typx.Any ]:

async def summarize_inventory(
    source: str, query: str = '', /, *,
    processor_name: __.Absential[ str ] = __.absent,  # NEW
    search_behaviors: _interfaces.SearchBehaviors = _search_behaviors_default,
    filters: __.cabc.Mapping[ str, __.typx.Any ] = _filters_default,
    group_by: __.typx.Optional[ str ] = None,
) -> str:
```

### 2. Detection System Changes

**detection.py** - Replace all_detections with processor_name:
```python
async def detect(
    source: str,
    processor_name: __.Absential[ str ] = __.absent,  # replaces all_detections
) -> dict[ str, __.typx.Any ]:
    # If processor_name specified, return only that detection
    # If absent, return best detection
    # Cache structure: source -> (processor_name -> detection)
```


### 3. Detection Method Dispatch

**SphinxDetection class** - Add business logic methods:
```python
class SphinxDetection(__.Detection):
    async def extract_documentation_for_objects(
        self, source: str, objects: __.cabc.Sequence[ __.cabc.Mapping[ str, __.typx.Any ] ], /, *,
        include_snippets: bool = True,
    ) -> list[ dict[ str, __.typx.Any ] ]:
        # Use self.theme, self.normalized_source etc.
        return await _extraction.extract_documentation_for_objects(
            source, objects, 
            theme = self.theme,
            include_snippets = include_snippets
        )
    
    async def extract_filtered_inventory(
        self, source: str, /, *,
        filters: __.cabc.Mapping[ str, __.typx.Any ] = _filters_default,
        details: __.InventoryQueryDetails = __.InventoryQueryDetails.Documentation,
    ) -> list[ dict[ str, __.typx.Any ] ]:
        # Direct call to module function
        return await _inventory.extract_filtered_inventory(
            source, filters = filters, details = details
        )
```

### 4. Module-Level Function Refactoring

**processors/sphinx/extraction.py** - Make functions accept theme parameter:
```python
async def extract_documentation_for_objects(
    source: str, 
    objects: __.cabc.Sequence[ __.cabc.Mapping[ str, __.typx.Any ] ], /, *,
    theme: __.Absential[ str ] = __.absent,
    include_snippets: bool = True,
) -> list[ dict[ str, __.typx.Any ] ]:
    # Implementation using theme parameter directly
    # Remove _detect_theme_from_html() function

def parse_documentation_html(
    content: str, 
    element_id: str, *, 
    theme: __.Absential[ str ] = __.absent
) -> dict[ str, str ]:
    # Use provided theme, no auto-detection
```

**processors/sphinx/inventory.py** - Module-level functions:
```python
async def extract_filtered_inventory(
    source: str, /, *,
    filters: __.cabc.Mapping[ str, __.typx.Any ] = _filters_default,
    details: __.InventoryQueryDetails = __.InventoryQueryDetails.Documentation,
) -> list[ dict[ str, __.typx.Any ] ]:
    # Move logic from SphinxProcessor.extract_filtered_inventory
```

### 5. Processor Simplification

**SphinxProcessor class** - Becomes lightweight detector:
```python
class SphinxProcessor(__.Processor):
    name: str = 'sphinx'
    
    @property
    def capabilities(self) -> __.ProcessorCapabilities:
        # Keep capabilities for registration
    
    async def detect(self, source: str) -> __.Detection:
        # Keep detection logic only
        # Remove all extract_* methods
```

## Implementation Steps

### Phase 1: Infrastructure Changes
1. **Update function signatures** in `functions.py` to accept `processor_name`
2. **Modify detect() function** in `detection.py` to use `processor_name` instead of `all_detections`
3. **Update functions.py** to call `detect()` directly for getting detection objects

### Phase 2: Detection Method Addition  
4. **Add business methods to SphinxDetection** class
5. **Create module-level functions** in extraction.py and inventory.py
6. **Update extraction functions** to accept theme parameter

### Phase 3: Processor Simplification
7. **Remove business methods from SphinxProcessor**
8. **Update function calls** to use detection.method() instead of processor.method()
9. **Remove duplicate theme detection** from extraction.py

### Phase 4: Testing & Cleanup
10. **Test all entry points** with both explicit and auto processor selection
11. **Update any remaining references** to old processor methods
12. **Remove dead code** from refactored modules

## Files to Modify

- `sources/sphinxmcps/functions.py` - Function signatures, detection usage
- `sources/sphinxmcps/detection.py` - detect() function signature  
- `sources/sphinxmcps/processors/sphinx/detection.py` - SphinxDetection methods
- `sources/sphinxmcps/processors/sphinx/main.py` - SphinxProcessor simplification
- `sources/sphinxmcps/processors/sphinx/extraction.py` - Module functions, remove theme detection
- `sources/sphinxmcps/processors/sphinx/inventory.py` - Module functions

## Benefits

1. **Eliminates duplicate theme detection** - theme flows from detection to extraction
2. **Cleaner architecture** - detection objects become primary interface
3. **Better separation of concerns** - processors are detectors, detections do business logic
4. **Flexible processor selection** - explicit or automatic processor choice
5. **Rich metadata flow** - all detection metadata available to business logic

## Potential Risks

1. **Testing complexity** - need to test both processor_name specified and auto-detected paths
2. **Migration complexity** - many file changes required

## Notes

- Use `__.absent` consistently for optional parameters
- Follow existing code patterns and style guidelines (space padding, wide argument types)
- Ensure linter compliance throughout refactor
- No backward compatibility concerns since project not yet released