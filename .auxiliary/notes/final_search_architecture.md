# Final Search Architecture Plan

## Current State After Initial Refactor

✅ **Completed Initial Refactor:**
- Centralized search logic in `SearchEngine` with rapidfuzz
- Eliminated `ProcessorFilters` class - now using direct dicts  
- Updated `query_content` to use centralized architecture
- All tests passing

## Proposed Final Architecture

### Clean Separation: Search Behaviors vs Processor Filters

**Current Interim State:**
```python
# Still using wrapper class
filters = Filters(
    universal=UniversalFilters(match_mode=MatchMode.Fuzzy, fuzzy_threshold=70),
    processor_filters={'domain': 'py', 'role': 'function'}
)
await query_inventory(source, query, filters=filters)
```

**Proposed Final State:**
```python
# Direct, clean separation
search_behaviors = SearchBehaviors(match_mode=MatchMode.Fuzzy, fuzzy_threshold=70)
filters = {'domain': 'py', 'role': 'function'}  # Simple dict
await query_inventory(source, query, search_behaviors=search_behaviors, filters=filters)
```

### Key Changes

#### 1. Rename and Simplify
- **Rename**: `UniversalFilters` → `SearchBehaviors` (clearer distinction from inventory filters)
- **Eliminate**: `Filters` wrapper class entirely (no backward compatibility needed)
- **Rename**: `extra_filters` parameter → `filters` (since `search_behaviors` is separate)

#### 2. Function Signatures
```python
# Old approach (interim):
async def query_inventory(
    source: str, query: str, 
    filters: Filters = Filters()
) -> dict[str, Any]: ...

# New approach (final):
async def query_inventory(
    source: str, query: str,
    search_behaviors: SearchBehaviors = SearchBehaviors(),
    filters: dict[str, Any] = {}
) -> dict[str, Any]: ...
```

#### 3. MCP Server Interface
```python
# Clean tool signatures
async def query_inventory(
    source: str,
    query: str, /, *,
    search_behaviors: SearchBehaviors = SearchBehaviors(),
    filters: dict[str, Any] = {}
) -> dict[str, Any]:
    """
    Search inventory with clean separation:
    - search_behaviors: How to search (fuzzy, exact, regex, thresholds)  
    - filters: What to filter (domain, role, priority - processor-specific)
    """
```

#### 4. Processor Interface
```python
class Processor:
    async def extract_inventory(
        self, source: str, /, *,
        filters: dict[str, Any] = {},  # Renamed from extra_filters
        details: InventoryQueryDetails = InventoryQueryDetails.Documentation,
    ) -> dict[str, Any]: ...
```

### Benefits of Final Architecture

#### 1. **Conceptual Clarity**
- `SearchBehaviors`: "HOW to search" (fuzzy vs exact, thresholds)
- `filters`: "WHAT to filter" (domain-specific criteria)
- No confusion about where parameters belong

#### 2. **Simplicity**
- No wrapper classes or complex nested objects
- Direct parameters make function calls obvious
- Easier for new processors to understand

#### 3. **Flexibility**
- Easy to add new search behaviors without changing processor interface
- Simple dict for filters allows any processor-specific parameters
- Clean foundation for future enhancements

#### 4. **Testing**
- Search behaviors tested independently from inventory filtering
- Processor filtering tested independently from search matching  
- Clear boundaries for unit testing

### Implementation Steps

#### Phase 1: Rename and Restructure (30 min)
1. **Rename** `UniversalFilters` → `SearchBehaviors`
2. **Update** all imports and references
3. **Remove** `Filters` wrapper class entirely
4. **Update** tests to use direct `SearchBehaviors` construction

#### Phase 2: Update Function Signatures (45 min)  
1. **Modify** `query_inventory()` to take separate parameters
2. **Update** `query_content()` similarly
3. **Rename** `extra_filters` → `filters` in processor interface
4. **Update** all call sites

#### Phase 3: Clean Up and Test (15 min)
1. **Remove** legacy property methods
2. **Run** full test suite
3. **Update** any remaining references

### Final API Examples

#### Simple Usage
```python
# Fuzzy search for "inventory" in Python domain
result = await query_inventory(
    "https://docs.python.org",
    "inventory", 
    search_behaviors=SearchBehaviors(match_mode=MatchMode.Fuzzy),
    filters={'domain': 'py'}
)
```

#### Advanced Usage  
```python
# Exact search with multiple filters
result = await query_inventory(
    "https://sphinx-doc.org", 
    "Document",
    search_behaviors=SearchBehaviors(match_mode=MatchMode.Exact),
    filters={'domain': 'py', 'role': 'class', 'priority': '1'}
)
```

#### MCP Tool Interface
```python
# Clean MCP tool signature
@tool
async def query_inventory(
    source: str,
    query: str,
    match_mode: str = "fuzzy",
    fuzzy_threshold: int = 50,
    domain: str = "",
    role: str = "",
    priority: str = ""
) -> dict[str, Any]:
    """Search documentation inventory."""
    search_behaviors = SearchBehaviors(
        match_mode=MatchMode(match_mode),
        fuzzy_threshold=fuzzy_threshold
    )
    filters = {k: v for k, v in {
        'domain': domain, 'role': role, 'priority': priority
    }.items() if v}
    return await functions.query_inventory(source, query, search_behaviors, filters)
```

### Migration Strategy

Since this is not a released project:
- **No backward compatibility needed**
- **Clean break** from current interim architecture  
- **Direct migration** to final state
- **Update all code and tests** in single sprint

This final architecture provides a clean, intuitive separation that will serve the project well as new processors are added.