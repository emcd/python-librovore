# Processor-Provided Formatters Design

## Overview

Rather than maintaining a central semantic field registry that requires constant updates, we implement **processor-provided formatters** where each inventory processor provides formatting intelligence for its own `specifics` fields. This approach co-locates domain knowledge with the processors that create it, making the system truly extensible and maintainable.

## Core Principle

> **Each processor knows best how to present its own data.**

Sphinx processors understand `domain`, `role`, and `priority` semantics. MkDocs processors understand `content_preview` and page-based organization. Future processors will have their own field semantics that we cannot predict centrally.

## Architecture Design

### Enhanced InventoryObject Methods

```python
class InventoryObject( __.immut.DataclassProtocol ):
    ''' Enhanced with self-formatting capabilities. '''
    
    # ... existing fields ...
    
    def render_specifics_markdown(
        self, /, *, 
        show_technical: __.typx.Annotated[
            bool, 
            __.ddoc.Doc( 
                'Controls whether implementation-specific details (internal field names, '
                'version numbers, priority scores) are included. When False, only '
                'user-facing information is shown.' 
            )
        ] = True,
    ) -> tuple[ str, ... ]:
        ''' Renders specifics as Markdown lines for CLI display. '''
        # Implementation knows how to render its own specifics without external lookup
        
    def render_specifics_json( self ) -> __.immut.Dictionary[ str, __.typx.Any ]:
        ''' Renders specifics for JSON output. '''
        # Implementation returns raw specifics data as immutable dictionary
        
    def get_compact_display_fields( self ) -> tuple[ tuple[ str, str ], ... ]:
        ''' Gets priority fields for compact display as (label, value) pairs. '''
        # Implementation selects most important fields for brief display
```

### Implementation Approach

`InventoryObject` instances know how to render their own specifics without external dependencies. Each inventory processor creates objects that inherently understand their own data format and rendering requirements.

#### Sphinx Inventory Objects
```python
# Sphinx processors create objects that understand Sphinx-specific rendering
def render_specifics_markdown( 
    self, /, *, 
    show_technical: __.typx.Annotated[ bool, __.ddoc.Doc( '...' ) ] = True 
) -> tuple[ str, ... ]:
    ''' Renders Sphinx inventory specifics as Markdown lines. '''
    # Implementation shows role and domain information directly
    # Uses Sphinx terminology (role, domain, priority) that users understand
    # Includes source attribution and priority when show_technical=True
        
def get_compact_display_fields( self ) -> tuple[ tuple[ str, str ], ... ]:
    ''' Gets Sphinx priority fields for compact display. '''
    # Implementation prioritizes role information  
    # Shows domain when non-Python or when contextually relevant
```

#### MkDocs Inventory Objects
```python
# MkDocs processors create objects that understand page-based rendering
def render_specifics_markdown( 
    self, /, *, 
    show_technical: __.typx.Annotated[ bool, __.ddoc.Doc( '...' ) ] = True 
) -> tuple[ str, ... ]:
    ''' Renders MkDocs inventory specifics as Markdown lines. '''
    # Implementation emphasizes document/page nature
    # Shows navigation context and page hierarchy when available
        
def get_compact_display_fields( self ) -> tuple[ tuple[ str, str ], ... ]:
    ''' Gets MkDocs priority fields for compact display. '''
    # Implementation consistently shows document type and page structure
```

### CLI Integration

```python
# CLI integration becomes dramatically simplified
def _append_inventory_metadata(
    lines: __.cabc.MutableSequence[ str ], invobj: __.cabc.Mapping[ str, __.typx.Any ]
) -> None:
    ''' Appends inventory metadata using object self-formatting. '''
    # Implementation creates InventoryObject from dict representation
    # Calls object's render_specifics_markdown method
    # Extends lines list with formatted results

def _append_content_description(
    lines: __.cabc.MutableSequence[ str ], 
    document: __.cabc.Mapping[ str, __.typx.Any ], 
    inventory_object: __.cabc.Mapping[ str, __.typx.Any ],
) -> None:
    ''' Appends content description with standard fallbacks. '''
    # Implementation tries description, then content_snippet
    # Uses consistent fallback chain across all inventory types
```

## Implementation Benefits

### 1. True Extensibility
- New inventory processors create objects that know how to render themselves
- No core code changes required for new inventory formats
- Rendering logic evolves with the objects that contain the data

### 2. Domain Knowledge Co-location  
- Objects understand their own field semantics without external dependencies
- No knowledge duplication between processors and separate formatters
- Data and presentation logic evolve together

### 3. Type Safety
- Each processor creates appropriately typed objects
- No dynamic type checking or registry lookups required
- Compile-time validation of rendering capabilities

### 4. Maintainability
- Clear separation: objects handle their own presentation
- No external registries or configuration to maintain
- Self-contained, independently testable rendering logic

### 5. User Experience
- Consistent interface (all objects implement same methods)
- Format-appropriate presentation without external configuration
- Context-aware formatting (show_technical parameter)

## Migration Strategy

### Phase 1: Infrastructure
1. Implement `SpecificsFormatter` interface and registry
2. Add formatting methods to `InventoryObject`
3. Create built-in formatters for Sphinx and MkDocs

### Phase 2: Integration
1. Update CLI to use object formatting methods
2. Modify JSON serialization to use `render_specifics_json()`
3. Update processors to register their formatters

### Phase 3: Enhancement
1. Add context support for different display modes
2. Implement semantic field mapping where useful
3. Add user configuration for formatting preferences

This approach provides a clean, extensible solution that respects the principle of co-locating domain knowledge with the code that creates it.