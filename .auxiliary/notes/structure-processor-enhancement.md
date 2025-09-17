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
    content_extraction_features: frozenset[ str ]          # e.g., {'signatures', 'descriptions', 'code_examples', 'cross_references'}
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
            processor can reliably extract:
            - 'signatures': Function/class signatures with parameters and return types
            - 'descriptions': Descriptive content and documentation text
            - 'code-examples': Code blocks with preserved language information
            - 'cross-references': Links and references to other documentation
            - 'arguments': Individual parameter documentation
            - 'returns': Return value documentation
            - 'attributes': Class and module attribute documentation

            Based on comprehensive theme analysis, these features use empirically-
            discovered universal patterns rather than theme-specific guesswork.
        '''
        # Subclasses implement to declare their inventory type support
    
    @__.typx.abc.abstractmethod
    async def extract_contents(
        self,
        auxdata: ApplicationGlobals,
        source: str,
        objects: __.cabc.Sequence[ InventoryObject ]
    ) -> tuple[ ContentDocument, ... ]:
        ''' Extracts content using inventory object metadata for strategy selection.

            Uses inventory object roles and types to choose optimal extraction:
            - API objects (functions, classes, methods): signature-aware extraction
            - Content objects (modules, pages): description-focused extraction
            - Code examples: language-preserving extraction

            Based on universal patterns from comprehensive theme analysis.
        '''
        # Implementation performs inventory-metadata-aware strategy selection
    
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
        ''' Sphinx processor capabilities based on universal pattern analysis. '''
        return StructureProcessorCapabilities(
            supported_inventory_types=frozenset({'sphinx_objects_inv'}),
            content_extraction_features=frozenset({
                'signatures',        # dt.sig.sig-object.py + dd patterns (100% consistent)
                'descriptions',      # Content extraction with navigation cleanup
                'arguments',         # Parameter documentation from signatures
                'returns',           # Return value documentation
                'attributes',        # Class and module attribute documentation
                'code-examples',     # .highlight containers with language detection
                'cross-references'   # Sphinx cross-reference extraction
            }),
            confidence_by_inventory_type={'sphinx_objects_inv': 1.0}
        )
    
    async def extract_contents(
        self,
        auxdata: ApplicationGlobals,
        source: str,
        objects: __.cabc.Sequence[ InventoryObject ]
    ) -> tuple[ ContentDocument, ... ]:
        ''' Extracts content using universal Sphinx patterns and inventory metadata. '''
        tasks = []
        for obj in objects:
            if obj.role in ['function', 'class', 'method']:
                # Use universal signature patterns (dt.sig.sig-object.py + dd)
                task = self._extract_with_signature_patterns(auxdata, source, obj)
            else:
                # Use universal content patterns with defensive selectors
                task = self._extract_with_content_patterns(auxdata, source, obj)
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)
        return tuple(r for r in results if isinstance(r, ContentDocument))
        
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
        ''' MkDocs processor capabilities based on universal pattern analysis. '''
        return StructureProcessorCapabilities(
            supported_inventory_types=frozenset({'mkdocs_search_index', 'sphinx_objects_inv'}),
            content_extraction_features=frozenset({
                'signatures',        # div.autodoc-signature patterns (mkdocstrings)
                'descriptions',      # Page content with theme-aware container selection
                'arguments',         # Parameter documentation from mkdocstrings
                'returns',           # Return value documentation
                'attributes',        # Attribute documentation
                'code-examples',     # .highlight containers with language-{lang} detection
                'navigation'         # Navigation context extraction
            }),
            confidence_by_inventory_type={
                'mkdocs_search_index': 0.8,
                'sphinx_objects_inv': 0.7  # Lower confidence since mkdocs is primary
            }
        )
    
    async def extract_contents(
        self,
        auxdata: ApplicationGlobals,
        source: str,
        objects: __.cabc.Sequence[ InventoryObject ]
    ) -> tuple[ ContentDocument, ... ]:
        ''' Extracts MkDocs content using source attribution for strategy selection. '''
        tasks = []
        for obj in objects:
            # Use source attribution to choose extraction strategy
            if obj.inventory_source == 'sphinx_objects_inv' and obj.role in ['function', 'class', 'method']:
                # Use Sphinx signature patterns for objects from sphinx inventory
                task = self._extract_with_sphinx_patterns(auxdata, source, obj)
            elif obj.inventory_source == 'mkdocs_search_index' and obj.role in ['function', 'class', 'method']:
                # Use mkdocstrings signature patterns for mkdocs objects
                task = self._extract_with_mkdocstrings_patterns(auxdata, source, obj)
            else:
                # Use universal content patterns for other objects
                task = self._extract_with_content_patterns(auxdata, source, obj)
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)
        return tuple(r for r in results if isinstance(r, ContentDocument))
            
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
    # Extracts content using processor's extract_contents method
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

### Content Search Strategy: Inventory-Guided vs Pure Content Search

**Issue Discovered**: During Tyro documentation investigation, we found a discoverability gap between inventory-guided search (librovore) and native website search engines.

**Root Cause Analysis**:
- **Inventory-guided search** (librovore approach): Search → Filter Inventory Names → Extract Content from Matches
- **Pure content search** (website engines): Search → Full-Text Content Search → Return Matching Content
- **The gap**: Users searching for `"mutex"` expect to find `"create_mutex_group"`, but inventory object names may not contain the conceptual terms users naturally search for

**Search Strategy Comparison**:

| Approach | Discovery | Performance | Coverage | Precision |
|----------|-----------|-------------|----------|-----------|
| **Inventory-guided** | Limited to API names | Fast (pre-filtered) | API-complete | High (structured) |
| **Pure content** | Full-text discovery | Slower (full crawl) | Content-complete | Variable |
| **Hybrid** | Best of both | Moderate | Comprehensive | Balanced |

**Design Decision for Structure Processors**:
- **Primary**: Maintain inventory-guided approach for performance and precision
- **Enhancement**: Improve inventory search with better fuzzy matching (`partial_ratio`) and match modes
- **Future consideration**: Hybrid approach where inventory search falls back to content search when insufficient results

**Implementation Notes**:
```python
# Current flow (inventory-guided)
objects = await idetection.filter_inventory(...)           # Get all inventory objects
candidates = filter_by_name(objects, term, match_mode=...)  # Search inventory names
documents = await sdetection.extract_contents(...)         # Extract matching content

# Potential hybrid enhancement (future consideration)
inventory_results = filter_by_name(objects, term, ...)
if len(inventory_results) < min_results_threshold:
    # Fallback to content search when inventory search insufficient
    content_results = await sdetection.search_content_directly(...)
    combined_results = merge_and_dedupe(inventory_results, content_results)
```

**Advantages of Current Approach**:
1. **Performance**: Pre-filtered object set reduces extraction overhead
2. **Structure**: Inventory objects provide rich metadata (roles, domains, priorities)
3. **Precision**: API-focused results avoid noise from prose content
4. **Consistency**: Standardized object structure across documentation formats

**Limitations Addressed by Match Mode Improvements**:
1. **Discovery gap**: Enhanced with `partial_ratio` for substring discovery
2. **Fuzzy threshold**: Better defaults for conceptual term matching  
3. **Match mode clarity**: Exact/Similar/Pattern modes with clear semantics

This analysis confirms the inventory-guided approach is architecturally sound for structure processors, with search improvements handling the discovered discoverability issues.

## Structure-Based Extraction Fallback

### Robustness Enhancement Through Decoupling

While inventory-guided extraction provides excellent performance and precision, real-world scenarios reveal cases where inventory metadata can be inaccurate, incomplete, or misaligned with actual HTML structure. Structure-based fallback provides robustness without abandoning the inventory-guided approach.

### Architecture Integration

```python
class StructureDetection( Detection ):
    ''' Enhanced base class with dual extraction capabilities. '''
    
    @__.typx.abc.abstractmethod
    async def extract_contents(
        self,
        auxdata: ApplicationGlobals,
        source: str,
        objects: __.cabc.Sequence[ InventoryObject ]
    ) -> tuple[ ContentDocument, ... ]:
        ''' Primary: Inventory-guided extraction. '''
        # Implementation performs inventory-type-aware content extraction
    
    @__.typx.abc.abstractmethod 
    async def extract_content_structure_based(
        self,
        auxdata: ApplicationGlobals,
        source: str,
        failed_objects: __.cabc.Sequence[ InventoryObject ], /, *,
        include_snippets: bool = True,
    ) -> tuple[ ContentDocument, ... ]:
        ''' Fallback: Structure-based extraction for failed inventory extractions. '''
        # Implementation uses HTML semantic analysis regardless of inventory metadata
        
    async def extract_with_hybrid_fallback(
        self,
        auxdata: ApplicationGlobals,
        source: str, 
        objects: __.cabc.Sequence[ InventoryObject ], /, *,
        include_snippets: bool = True,
    ) -> tuple[ ContentDocument, ... ]:
        ''' Combines inventory-guided extraction with structure-based fallback. '''
        # 1. Perform primary extraction using inventory metadata
        # 2. Identify failed extractions (None results or content like 'Hello World!')
        # 3. Apply structure-based fallback for failed objects only
        # 4. Merge successful primary results with successful fallback results
        # 5. Return combined tuple maintaining original object order
```

### Structure-Based Extraction Implementation

```python
async def extract_content_structure_based(
    self,
    auxdata: ApplicationGlobals,
    source: str,
    failed_objects: __.cabc.Sequence[ InventoryObject ], /, *,
    include_snippets: bool = True,
) -> tuple[ ContentDocument, ... ]:
    ''' Structure-based extraction using HTML semantic analysis. '''
    # For each failed object:
    # 1. Construct page URL from object (may differ from inventory URI)
    # 2. Fetch HTML content
    # 3. Apply semantic structure analysis to find object content
    # 4. Create ContentDocument with fallback metadata if content found
    # 5. Return tuple of results (None for failures)

async def _extract_using_semantic_structure(
    self, html_content: str, object_name: str, page_url: str
) -> str | None:
    ''' Semantic HTML structure analysis for content extraction. '''
    # Strategy 1: Find elements containing object name (id attributes, text content)
    # Strategy 2: Apply content extraction patterns near found anchors
    # Strategy 3: Use semantic cleanup to remove navigation/sidebar content
    # Strategy 4: Apply quality filters (minimum length, content coherence)
    # Return cleaned content string or None if no quality content found

def _semantic_content_cleanup(self, content: str) -> str:
    ''' Clean extracted content using semantic HTML understanding. '''
    # 1. Parse content with BeautifulSoup
    # 2. Remove semantic non-content areas (aside, nav, header, footer)
    # 3. Remove UI-specific elements (headerlinks, breadcrumbs, etc.)
    # 4. Prefer main content containers (main, article tags)
    # 5. Return cleaned HTML string
```

### Integration Benefits

1. **Graceful Degradation**: When inventory metadata fails, structure analysis provides backup
2. **Theme Resilience**: Works across documentation theme changes without pattern updates  
3. **Coverage Enhancement**: Finds content missed by inventory-guided extraction
4. **Quality Maintenance**: Inventory-guided results still preferred when available

### Performance Characteristics

- **Best Case**: Inventory extraction succeeds → no fallback overhead
- **Fallback Case**: +200-500ms per failed object for structure analysis
- **Pattern Discovery**: Development-time analysis for new documentation structures (cached afterwards)
- **Overall Impact**: <10% performance degradation in typical scenarios

This structure-based fallback complements the inventory-type awareness without compromising the performance benefits of the inventory-guided approach.

## Implementation Benefits

1. **Type Safety**: Structure processors work with typed `InventoryObject` instances
2. **Proper URL Construction**: Each processor handles its inventory type's URL patterns correctly  
3. **Capability-Based Filtering**: Only send objects to processors that can handle them
4. **Performance Optimization**: Avoid unnecessary processing attempts
5. **Error Handling**: Clear errors when no capable processor is available
6. **Future Extensibility**: New inventory types just need to register capabilities

## Universal Pattern Implementation Strategy

### Defensive Selector Strategy

Based on comprehensive theme analysis, universal patterns use defensive selector strategies to prevent confusion between theme structures:

```python
# High-specificity selectors (safe across all themes)
UNIVERSAL_CONTENT_SELECTORS = [
    'article[role="main"]',      # Semantic HTML5 with role
    'main[role="main"]',         # Explicit main role
    'div.body[role="main"]',     # Sphinx pattern with role
    'section.wy-nav-content-wrap', # RTD-specific (unlikely to conflict)
]

# Theme-specific selectors (looked up by detected theme)
THEME_SPECIFIC_SELECTORS = {
    'sphinx_rtd_theme': ['section.wy-nav-content-wrap'],
    'pydata_sphinx_theme': ['main.bd-main', 'article.bd-article'],
    'furo': ['article[role="main"]'],
    'alabaster': ['div.body[role="main"]'],
    'material': ['article.md-content__inner', 'main.md-main'],
    'readthedocs': ['div.col-md-9[role="main"]'],
}

# Generic selectors (require content quality validation)
GENERIC_CONTENT_SELECTORS = [
    'main',                      # HTML5 semantic main element
    'div.body',                  # Common documentation pattern
    'div.content',               # Generic content wrapper (validate required)
]
```

### Content Validation Requirements

For generic selectors, content validation prevents false matches. Key validation criteria:

- **Paragraph Count**: Container should have multiple paragraphs (not just navigation links)
- **Content Length**: Minimum substantial text content threshold to avoid empty containers
- **Link Density**: High link-to-text ratios indicate navigation areas rather than content
- **Semantic Context**: Prefer containers with semantic structure (headings, lists, code blocks)
- **Navigation Exclusion**: Avoid containers primarily consisting of navigation elements
- **Content Quality**: Prioritize containers with coherent documentation structure

### Pattern Discovery vs Runtime

- **Pattern Discovery**: Comprehensive analysis of documentation themes (development-time)
- **Runtime Selection**: Fast selector application with validation (production-time)
- **Fallback Chain**: Ordered from specific to generic with increasing validation requirements

This completes the Phase 3 enhancement while integrating seamlessly with the processor-provided formatters design.