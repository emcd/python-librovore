# Exception Renderer Architecture Analysis

## Context

This document analyzes the proposal to add `render_as_json()` and `render_as_markdown()` methods directly to exception classes, eliminating the need for separate `ErrorResponse`/`ErrorInfo` objects and conversion functions in the business logic layer.

## Current State Assessment

### Hybrid Error Handling Pattern

The codebase currently uses a **hybrid approach** that's partially migrated toward structured error objects:

1. **Functions layer** (`functions.py`) catches `ProcessorInavailability` exceptions and converts them to `ErrorResponse` objects using helper functions like `_produce_processor_error_response()`
2. **CLI layer** (`cli.py`) catches broad `Exception` types, logs them, formats them via `_format_cli_exception()`, and exits with code 1
3. **MCP server** (`server.py`) uses structured error objects from functions and serializes them via `_results.serialize_for_json()`

### Structured Error Objects

- `ErrorInfo`: Basic error metadata (type, title, message, suggestion)
- `ErrorResponse`: Contextual wrapper with location/query plus `ErrorInfo`
- Both have proper `render_as_json()` methods
- `ErrorResponse` has `render_as_markdown()` method

## Alternative Analysis

### 1. Current Hybrid Approach (Status Quo)

**Pros:**
- Explicit error handling in function signatures
- Type-safe union returns (`InventoryResult | ErrorResponse`)
- MCP server gets structured objects directly
- Clear separation between exceptions (internal) and results (API)

**Cons:**
- Conversion overhead and complexity
- Duplicate error information (exception + `ErrorResponse`)
- Function signatures become verbose with union types
- Exception context can be lost in translation

### 2. Self-Rendering Exceptions (Proposed)

**Pros:**
- Natural Python exception flow
- Clean function signatures (no union types)
- Single source of truth for error information
- Consistent rendering across all catch points
- Eliminates conversion functions
- Exception retains full context and stack trace

**Cons:**
- Uncommon pattern (unfamiliarity)
- MCP server needs try/catch blocks
- Exceptions become part of public API contract
- Less explicit about what errors functions might raise

### 3. Result Pattern (Rust-style)

**Pros:**
- Explicit error handling requirements
- Type-safe at compile time
- Popular in functional programming
- No exceptions to catch

**Cons:**
- Very un-Pythonic
- Verbose usage patterns
- Significant refactoring required
- Mental overhead for all callers

## Recommendation: Self-Rendering Exceptions

The **self-rendering exceptions approach is optimal** for this specific architectural context.

### Architecture Fit

1. **MCP Requirements**: Server must return structured JSON. Having `render_as_json()` directly on exceptions is cleaner than any alternative.

2. **CLI Consistency**: Both CLI and MCP can use the same rendering methods, ensuring consistent error presentation.

3. **Function Complexity**: Business logic is already complex - eliminating error conversion reduces cognitive overhead.

## Implementation Strategy

### Base Exception Enhancement

```python
class Omnierror( Omniexception, Exception ):
    ''' Base for error exceptions with self-rendering capability. '''
    
    def render_as_json( self ) -> dict[ str, __.typx.Any ]:
        ''' Renders exception as JSON-compatible dictionary. '''
        return {
            'type': self.__class__.__name__.lower( ),
            'message': str( self ),
            **self._get_context_fields( )
        }
    
    def render_as_markdown(
        self, /, *,
        reveal_internals: bool = True,
    ) -> tuple[ str, ... ]:
        ''' Renders exception as Markdown lines for display. '''
        lines = [ f"## Error: {self.__class__.__name__}" ]
        lines.append( f"**Message:** {self}" )
        if reveal_internals:
            lines.extend( self._get_context_markdown( ) )
        return tuple( lines )
    
    def _get_context_fields( self ) -> dict[ str, __.typx.Any ]:
        ''' Extracts context fields for JSON rendering. '''
        return { k: v for k, v in self.__dict__.items( ) if not k.startswith( '_' ) }
    
    def _get_context_markdown( self ) -> list[ str ]:
        ''' Extracts context for Markdown rendering. '''
        return [ "**{key}:** {value}".format( key = k.title( ), value = v ) 
                for k, v in self._get_context_fields( ).items( ) ]
```

### Enhanced Specific Exceptions

```python
class ProcessorInavailability( Omnierror, RuntimeError ):
    ''' No processor found to handle source. '''

    def __init__(
        self,
        source: str,
        genus: __.Absential[ str ] = __.absent,
        query: __.Absential[ str ] = __.absent,
    ):
        self.source = source
        self.genus = genus  
        self.query = query
        message = f"No processor found to handle source: {source}"
        if not __.is_absent( genus ):
            message += f" (genus: {genus})"
        super( ).__init__( message )
    
    def render_as_json( self ) -> dict[ str, __.typx.Any ]:
        ''' Renders processor unavailability as JSON-compatible dictionary. '''
        return {
            'type': 'processor_unavailable',
            'title': 'No Compatible Processor Found',
            'message': str( self ),
            'source': self.source,
            'genus': self.genus if not __.is_absent( self.genus ) else None,
            'query': self.query if not __.is_absent( self.query ) else None,
            'suggestion': 'Verify the URL points to a supported documentation format.'
        }
```

### Clean CLI Pattern

```python
try:
    result = await _functions.query_inventory( ... )
except ( ProcessorInavailability, InventoryInaccessibility ) as exc:
    lines = exc.render_as_markdown( reveal_internals = True )  
    print( '\n'.join( lines ), file = stream )
    raise SystemExit( 1 )
except Exception as exc:  # Keep this safeguard for stdlib/third-party errors
    _scribe.error( "Unexpected error: %s", exc )
    print( f"❌ Internal error: {exc}", file = stream )
    raise SystemExit( 1 )
```

## Migration Benefits

1. **Immediate Cleanup**: Remove all `_produce_*_error_response()` functions
2. **Simplified Functions**: Clean return types, natural exception flow  
3. **Consistent Errors**: Same rendering everywhere, no information loss
4. **Future-Proof**: Easy to add new context fields to exceptions

## Architectural Justification

While the self-rendering exception pattern is uncommon, it's **architecturally sound** because:

- Exceptions already carry context data
- Multiple output formats are needed (inherently a presentation concern)
- Error handling is already structured (not generic `Exception` catching)
- Python's duck typing makes this natural
- Pattern is more common in web frameworks where exceptions need to render as HTTP responses

This approach will eliminate significant complexity from the current hybrid system while maintaining all benefits of structured error reporting.

## AOP Enhancement: Decorator Pattern Integration

### Refined Proposal: Self-Rendering Exceptions + AOP Decorators

The self-rendering exception approach can be enhanced with **Aspect-Oriented Programming (AOP)** using decorators to handle the cross-cutting concern of exception catching and rendering. This creates perfect separation between business logic and error handling.

### MCP Server Implementation (Very Clean)

```python
def intercept_errors( func ):
    ''' Intercepts package exceptions and renders them as JSON for MCP. '''
    async def wrapper( *args, **kwargs ):
        try:
            return await func( *args, **kwargs )
        except Omnierror as exc:
            return exc.render_as_json( )
        # Let other exceptions bubble up for FastMCP to handle
    return wrapper

@intercept_errors
async def query_inventory_mcp( location: str, term: str, ... ):
    ''' Searches object inventory by name with fuzzy matching. '''
    # Pure business logic, no error handling clutter
    return await _functions.query_inventory( auxdata, location, term, ... )
```

This creates **exceptionally clean** MCP functions with pure business logic and zero error handling boilerplate.

### CLI Implementation (Parameterized Decorator)

```python
def intercept_errors( stream, display_format ):
    ''' Creates decorator to intercept package exceptions and render for CLI. '''
    def decorator( func ):
        async def wrapper( *args, **kwargs ):
            try:
                return await func( *args, **kwargs )
            except Omnierror as exc:
                if display_format == DisplayFormat.JSON:
                    output = __.json.dumps( exc.render_as_json( ), indent = 2 )
                else:
                    lines = exc.render_as_markdown( reveal_internals = True )
                    output = '\n'.join( lines )
                print( output, file = stream )
                raise SystemExit( 1 )
            except Exception as exc:  # Keep safeguard for stdlib/third-party errors
                _scribe.error( "Unexpected error: %s", exc )
                print( f"❌ Internal error: {exc}", file = stream )
                raise SystemExit( 1 )
        return wrapper
    return decorator

# Usage in CLI command:
async def __call__( self, auxdata, display, display_format ):
    stream = await display.provide_stream( )
    
    @intercept_errors( stream, display_format )
    async def execute( ):
        return await _functions.query_inventory(
            auxdata, self.location, self.term,
            search_behaviors = self.search_behaviors,
            filters = self.filters,
            results_max = self.results_max,
            details = self.details )
    
    result = await execute( )
    # Handle successful result rendering here
```

The **parameterized decorator with closure** approach is preferred over a handler class because:
- **Functional simplicity** - Straightforward closure pattern that captures context
- **Less overhead** - No need to instantiate handler classes for each command  
- **Familiar pattern** - Standard Python decorator with closure, well-understood
- **Inline clarity** - Context capture happens where it's needed

### Major Benefits of AOP Enhancement

#### 1. Perfect AOP Separation
- Exception handling becomes a true cross-cutting concern
- Business logic functions are completely pure
- Single responsibility principle fully achieved

#### 2. Exceptional DRY (Don't Repeat Yourself)
- Error handling logic written **exactly once** per interface layer
- No duplication of try/catch blocks across functions
- Consistent error behavior guaranteed

#### 3. Business Logic Clarity
```python
# Before: cluttered with error handling
async def query_inventory( ... ) -> InventoryResult | ErrorResponse:
    try:
        detection = await _detection.detect_inventory( ... )
    except ProcessorInavailability as exc:
        return _produce_processor_error_response( ... )
    # ... more business logic

# After: pure business logic
async def query_inventory( ... ) -> InventoryQueryResult:  # Clean signature!
    detection = await _detection.detect_inventory( ... )  # Natural flow
    # ... pure business logic
```

#### 4. Function Signatures Become Beautiful
No more `Union[SuccessType, ErrorResponse]` - just clean return types that represent success cases.

#### 5. Maintainability Excellence
- Change error handling behavior in one place
- Add new error types to decorator, automatically applies everywhere
- Easy testing of error presentation variations

### Three-Layer Architecture

**Self-rendering exceptions + AOP decorators** creates optimal separation:

1. **Business Layer**: Pure logic with natural exceptions
2. **Exception Classes**: Self-contained presentation logic (render methods)
3. **Interface Decorators**: Cross-cutting concern handling (catch and delegate)

Each layer has exactly one responsibility, creating extraordinarily clean architecture.

## Final Recommendation: Combined Approach

**Combine self-rendering exceptions with AOP decorators** for the optimal solution:

- Exceptions handle their own presentation (render methods)
- Decorators handle the cross-cutting concern (catching + rendering)  
- Business logic becomes completely pure
- Interface layers get consistent behavior with zero duplication

This represents one of the cleanest error handling approaches for systems requiring multiple output formats, providing exceptional maintainability and architectural clarity.