# Structure Processor Enhancement Design (Phase 3)

## Overview

Structure processors extract documentation content from web pages based on inventory objects. However, they currently lack proper inventory-type awareness for URL construction and content extraction optimization. This enhancement implements capability advertisement and inventory-type filtering to ensure proper content extraction across all supported formats.

## Current Architecture Issues

### URL Construction Problems
```python
# Current approach - generic URL building
def derive_documentation_url(base_url: Any, obj_uri: str, obj_name: str) -> str:
    # Generic logic that may not work for all inventory types
```

### Missing Capability Filtering
```python
# Current approach - all objects sent to all structure processors
async def query_content(...):
    # No filtering based on structure processor capabilities
    documents = await extraction.extract_contents(auxdata, source, objects)
```

## Enhanced Architecture Design

### Structure Processor Capabilities

```python
class StructureProcessorCapabilities( __.immut.DataclassObject ):
    ''' Capability advertisement for structure processors. '''
    
    supported_inventory_types: frozenset[ str ]            # e.g., {'sphinx_objects_inv', 'mkdocs_search_index'}
    content_extraction_features: frozenset[ str ]          # e.g., {'signatures', 'descriptions', 'code_examples'}
    confidence_by_inventory_type: __.immut.Dictionary[ str, float ]  # Quality scores (0.0-1.0) for extraction success
    
    
    def get_confidence_for_type( self, inventory_type: str ) -> float:
        ''' Gets extraction confidence for inventory type.
        
            The confidence score (0.0-1.0) indicates how well this processor
            can extract content from the inventory type. Used for processor
            selection when multiple processors support the same type.
        '''
        # Implementation retrieves confidence score from mapping

class StructureDetection( Detection ):
    ''' Enhanced base class with capability advertisement. '''
    
    @__.typx.classmethod
    @__.typx.abc.abstractmethod
    def get_capabilities( cls ) -> StructureProcessorCapabilities:
        ''' Returns processor capabilities for filtering and selection.
        
            The content_extraction_features advertise what types of content this
            processor can reliably extract (signatures, descriptions, code_examples, 
            cross_references, etc.). This helps with processor selection and user
            expectations about extraction quality.
            
            The confidence_by_inventory_type scores (0.0-1.0) help select the best 
            processor when multiple processors support the same inventory type or
            when sites have multiple inventory formats available.
        '''
        # Subclasses implement to declare their inventory type support
    
    @__.typx.abc.abstractmethod
    async def extract_contents_typed(
        self,
        auxdata: ApplicationGlobals,
        source: str,
        objects: __.cabc.Sequence[ InventoryObject ], /, *,
        include_snippets: bool = True,
    ) -> tuple[ ContentDocument, ... ]:
        ''' Extracts content with full inventory object context. '''
        # Implementation performs inventory-type-aware content extraction
    
    def can_process_inventory_type( self, inventory_type: str ) -> bool:
        ''' Checks if processor can handle inventory type. '''
        # Implementation checks supported_inventory_types frozenset directly
        # return inventory_type in self.get_capabilities().supported_inventory_types
```

### Sphinx Structure Processor Enhancement

```python
class SphinxDetection( StructureDetection ):
    ''' Enhanced Sphinx structure processor with capability advertisement. '''
    
    @__.typx.classmethod
    def get_capabilities( cls ) -> StructureProcessorCapabilities:
        ''' Sphinx processor capabilities. '''
        # Implementation returns capabilities declaring:
        # - supported_inventory_types: {'sphinx_objects_inv'}
        # - content_extraction_features: {'signatures', 'descriptions', 'parameter_docs', 'return_docs', 'example_code', 'cross_references'}
        # - confidence_by_inventory_type: {'sphinx_objects_inv': 1.0}
    
    async def extract_contents_typed(
        self,
        auxdata: ApplicationGlobals, 
        source: str,
        objects: __.cabc.Sequence[ InventoryObject ], /, *,
        include_snippets: bool = True,
    ) -> tuple[ ContentDocument, ... ]:
        ''' Extracts content with inventory-type-aware URL construction. '''
        # Implementation filters objects to supported types (defensive programming)
        # Creates extraction tasks for each supported object
        # Uses inventory-type-aware URL construction via _build_sphinx_url
        # Gathers results asynchronously and filters successful extractions
        
    def _build_sphinx_url(
        self, base_url: __.typx.Any, obj: InventoryObject
    ) -> __.typx.Any:
        ''' Builds Sphinx-specific documentation URL. '''
        # Implementation handles Sphinx-specific URI patterns:
        # - URIs ending with '#$': replace $ with object name for anchor
        # - URIs ending with '$': replace $ with object name for module-level objects
        # - Uses urljoin for proper URL construction
```

### MkDocs Structure Processor Enhancement

```python
class MkDocsDetection( StructureDetection ):
    ''' Enhanced MkDocs structure processor. '''
    
    @__.typx.classmethod
    def get_capabilities( cls ) -> StructureProcessorCapabilities:
        ''' MkDocs processor capabilities. '''
        # Implementation returns capabilities declaring:
        # - supported_inventory_types: {'mkdocs_search_index'}
        # - content_extraction_features: {'page_content', 'headings', 'navigation'}
        # - confidence_by_inventory_type: {'mkdocs_search_index': 0.8}
    
    async def extract_contents_typed(
        self,
        auxdata: ApplicationGlobals,
        source: str, 
        objects: __.cabc.Sequence[ InventoryObject ], /, *,
        include_snippets: bool = True,
    ) -> tuple[ ContentDocument, ... ]:
        ''' Extracts MkDocs content with type awareness. '''
        # Implementation filters to MkDocs-compatible objects
        # Creates MkDocs-specific extraction tasks
        # Uses _build_mkdocs_url for proper URL construction
        # Returns tuple of successfully extracted documents
            
    def _build_mkdocs_url(
        self, base_url: __.typx.Any, obj: InventoryObject
    ) -> __.typx.Any:
        ''' Builds MkDocs-specific documentation URL. '''
        # Implementation normalizes MkDocs URI patterns:
        # - Ensures URI starts with '/'
        # - Adds trailing '/' for directory-style URIs without extensions
        # - Uses urljoin for proper URL construction
```

### Functions Layer Integration

```python
# Enhanced functions.py integration
async def query_content(
    auxdata: ApplicationGlobals,
    location: str,
    term: str, /, *,
    # ... other parameters from existing signature
) -> ContentResult:
    ''' Enhanced content query with structure processor capability filtering. '''
    # Implementation performs existing inventory query
    # NEW: Filters inventory objects by structure processor capabilities
    # Selects structure processor with highest detection confidence
    # Extracts content using processor's extract_contents_typed method
    # Returns ContentQueryResult with proper error propagation

async def _filter_objects_by_structure_capabilities(
    auxdata: ApplicationGlobals,
    location: str,
    objects: __.cabc.Sequence[ InventoryObject ],
) -> tuple[ InventoryObject, ... ]:
    ''' Filters inventory objects by structure processor capabilities. '''
    # Implementation groups objects by inventory type
    # Queries each available processor's capabilities via get_capabilities()
    # Filters to objects with capable processors
    # Logs debug messages for unsupported inventory types
    # Returns tuple of compatible objects

async def _select_best_structure_processor(
    auxdata: ApplicationGlobals,
    location: str, 
    objects: __.cabc.Sequence[ InventoryObject ],
) -> StructureDetection:
    ''' Selects best structure processor for the given objects. '''
    # Implementation uses existing structure processor detection system
    # Selects processor with highest detection confidence (not by inventory type)
    # Filters inventory objects by selected processor's capabilities
    # Raises ProcessorInavailability if no capable processor found

async def _get_available_structure_processors(
    auxdata: ApplicationGlobals, location: str
) -> tuple[ StructureDetection, ... ]:
    ''' Gets available structure processors for location. '''
    # Implementation uses existing processor discovery mechanism
    # Instantiates available structure processor classes
    # Returns tuple of processor instances with their capabilities

# Pseudo-code showing confidence scoring in practice:
#
# Current functions.py flow:
#   objects = await idetection.filter_inventory(...)           # Get all inventory objects
#   candidates = filter_by_name(objects, term)[...results_max * 3]  # Search and limit
#   sdetection = await detect_structure(...)                   # Get single structure processor  
#   documents = await sdetection.extract_contents(...candidates)    # Extract with whatever processor was found
#
# Enhanced flow with capability filtering:
#   objects = await idetection.filter_inventory(...)           # Get all inventory objects  
#   candidates = filter_by_name(objects, term)[...results_max * 3]  # Search and limit
#   sdetection = await detect_structure(...)                   # Get single best structure processor by detection confidence
#
#   # NEW: Filter candidates by selected processor's capabilities
#   processor_capabilities = sdetection.get_capabilities()
#   compatible_candidates = [
#       candidate for candidate in candidates 
#       if candidate.inventory_type in processor_capabilities.supported_inventory_types
#   ]
#   
#   if compatible_candidates:
#       documents = await sdetection.extract_contents_typed(
#           auxdata, location, compatible_candidates[:results_max]
#       )
#   else:
#       # Return error response using existing error propagation
#       return ErrorResponse( location = location, query = term, error = ErrorInfo( ... ) )
#
# This approach handles:
# 1. Structure processor selection by detection confidence (existing system)
# 2. Inventory object filtering by processor capabilities (new enhancement)
# 3. Clear error handling when no compatible objects exist
```

## Integration with Processor-Provided Formatters

The two enhancements complement each other perfectly:

### Clear Separation of Concerns
- **Structure processors**: Handle content extraction and URL construction based on inventory types
- **Display formatters**: Handle presentation of inventory object specifics for CLI/JSON output

### Capability System Alignment
- **Structure processor capabilities**: Declare which inventory types they can extract content from
- **Formatter capabilities**: Declare which inventory types they can format for display

### Discovery Pattern
```python
# Both systems use capability-based discovery without external registration
sphinx_capabilities = SphinxDetection.get_capabilities()
inventory_object.render_specifics_markdown()  # Self-formatting without external lookup
```

## Design Decisions

### Rejected: Processor Registration System

No registration system is needed - processors are discovered through the existing detection system and their capabilities are queried dynamically via the `get_capabilities()` method. This avoids additional configuration and maintains the current discovery patterns.

## Implementation Benefits

1. **Type Safety**: Structure processors work with typed `InventoryObject` instances
2. **Proper URL Construction**: Each processor handles its inventory type's URL patterns correctly  
3. **Capability-Based Filtering**: Only send objects to processors that can handle them
4. **Performance Optimization**: Avoid unnecessary processing attempts
5. **Error Handling**: Clear errors when no capable processor is available
6. **Future Extensibility**: New inventory types just need to register capabilities

This completes the Phase 3 enhancement while integrating seamlessly with the processor-provided formatters design.