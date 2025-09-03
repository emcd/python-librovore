.. vim: set fileencoding=utf-8:
.. -*- coding: utf-8 -*-
.. +--------------------------------------------------------------------------+
   |                                                                          |
   | Licensed under the Apache License, Version 2.0 (the "License");          |
   | you may not use this file except in compliance with the License.         |
   | You may obtain a copy of the License at                                  |
   |                                                                          |
   |     http://www.apache.org/licenses/LICENSE-2.0                           |
   |                                                                          |
   | Unless required by applicable law or agreed to in writing, software      |
   | distributed under the License is distributed on an "AS IS" BASIS,        |
   | WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. |
   | See the License for the specific language governing permissions and      |
   | limitations under the License.                                           |
   |                                                                          |
   +--------------------------------------------------------------------------+


*******************************************************************************
Results Module Design
*******************************************************************************

Overview
===============================================================================

The results module provides a centralized collection of structured dataclass 
objects representing search results, inventory objects, and content documents. 
This module serves as the foundation for type-safe operations across all 
interface layers while maintaining clean separation between data representation 
and business logic.

Design Principles
===============================================================================

Architectural Foundation
-------------------------------------------------------------------------------

**Centralized Type Definitions**
  All result-related dataclasses reside in a single module to ensure consistency 
  and prevent circular dependencies between processor, search, and function 
  modules.

**Immutable Data Structures**
  All result objects inherit from ``__.immut.DataclassObject`` following project 
  practices for thread safety and predictable behavior in concurrent operations.

**Universal Object Interface**
  All inventory processors return ``InventoryObject`` instances rather than 
  format-specific dictionaries, providing type safety and enabling consistent 
  search operations across different inventory formats.

**Complete Source Attribution**
  Every result object includes complete provenance information enabling 
  debugging, caching optimization, and future multi-source operations without 
  requiring separate tracking mechanisms.

**Clean Separation of Concerns**
  Inventory objects represent pure documentation metadata without search-specific 
  fields. Search results wrap inventory objects with relevance scoring. This 
  separation allows inventory objects to be reused across different search 
  contexts and enables search-independent operations.

**Self-Rendering Object Architecture**
  All result objects implement standardized rendering methods for different 
  output formats, encapsulating domain-specific formatting knowledge within 
  the objects themselves rather than external formatting functions.

Core Object Definitions
===============================================================================

Universal Inventory Object
-------------------------------------------------------------------------------

.. code-block:: python

    class InventoryObject( __.immut.DataclassObject ):
        ''' Universal inventory object with complete source attribution.
        
            Represents a single documentation object from any inventory source
            with standardized fields, format-specific metadata container, and
            self-formatting capabilities where each processor creates objects
            that know how to render their own specifics data.
        '''
        
        # Universal identification fields
        name: __.typx.Annotated[
            str, __.ddoc.Doc( "Primary object identifier from inventory source." ) ]
        uri: __.typx.Annotated[
            str, __.ddoc.Doc( "Relative URI to object documentation content." ) ]
        inventory_type: __.typx.Annotated[
            str, __.ddoc.Doc( "Inventory format identifier (e.g., sphinx_objects_inv)." ) ]
        location_url: __.typx.Annotated[
            str, __.ddoc.Doc( "Complete URL to inventory location for attribution." ) ]
        
        # Optional display enhancement
        display_name: __.typx.Annotated[
            __.typx.Optional[ str ], 
            __.ddoc.Doc( "Human-readable name if different from name." ) ] = None
        
        # Format-specific metadata container
        specifics: __.typx.Annotated[
            __.immut.Dictionary[ str, __.typx.Any ],
            __.ddoc.Doc( "Format-specific metadata (domain, role, priority, etc.)." ) 
        ] = __.dcls.field( default_factory = __.immut.Dictionary )
        
        
        @property
        def effective_display_name( self ) -> str:
            ''' Returns display_name if available, otherwise falls back to name. '''
        
        # Self-formatting capabilities (processor-provided formatters)
        def render_as_json( self ) -> __.immut.Dictionary[ str, __.typx.Any ]:
            ''' Renders complete object as JSON-compatible dictionary. '''
        
        def render_as_markdown(
            self, /, *,
            reveal_internals: __.typx.Annotated[
                bool,
                __.ddoc.Doc( '''
                    Controls whether implementation-specific details (internal field names, 
                    version numbers, priority scores) are included. When False, only 
                    user-facing information is shown.
                ''' )
            ] = True,
        ) -> tuple[ str, ... ]:
            ''' Renders complete object as Markdown lines for display. ''''
        

**Universal Fields**
- ``name``: Primary object identifier from inventory location
- ``uri``: Relative URI to object documentation content  
- ``inventory_type``: Format identifier (e.g., "sphinx_objects_inv", "mkdocs_search_index")
- ``location_url``: Complete URL to inventory location for debugging and caching

**Format-Specific Metadata**
- ``specifics``: Immutable dictionary containing processor-specific fields
- Sphinx objects include: ``domain``, ``role``, ``priority``, ``inventory_project``, ``inventory_version``
- MkDocs objects include: ``object_type`` (content previews handled by structure processors)

Search Result Objects
-------------------------------------------------------------------------------

.. code-block:: python

    class SearchResult( __.immut.DataclassObject ):
        ''' Search result with inventory object and match metadata. '''
        
        inventory_object: __.typx.Annotated[
            InventoryObject, __.ddoc.Doc( "Matched inventory object with metadata." ) ]
        score: __.typx.Annotated[
            float, __.ddoc.Doc( "Search relevance score (0.0-1.0)." ) ]
        match_reasons: __.typx.Annotated[
            tuple[ str, ... ],
            __.ddoc.Doc( "Detailed reasons for search match." ) ]
        
        @classmethod
        def from_inventory_object(
            cls,
            inventory_object: InventoryObject, *,
            score: float,
            match_reasons: __.cabc.Sequence[ str ],
        ) -> __.typx.Self:
            ''' Creates search result from inventory object with scoring. '''

Content and Documentation Objects
-------------------------------------------------------------------------------

.. code-block:: python

    class ContentDocument( __.immut.DataclassObject ):
        ''' Documentation content with extracted metadata and content identification. '''
        
        inventory_object: __.typx.Annotated[
            InventoryObject, __.ddoc.Doc( "Location inventory object for this content." ) ]
        content_id: __.typx.Annotated[
            str, __.ddoc.Doc( "Deterministic identifier for content retrieval." ) ]
        description: __.typx.Annotated[
            str, __.ddoc.Doc( "Extracted object description or summary." ) ] = ''
        documentation_url: __.typx.Annotated[
            str, __.ddoc.Doc( "Complete URL to full documentation page." ) ] = ''
        
        # Structure processor metadata
        extraction_metadata: __.typx.Annotated[
            __.immut.Dictionary[ str, __.typx.Any ],
            __.ddoc.Doc( "Metadata from structure processor extraction." ) 
        ] = __.dcls.field( default_factory = __.immut.Dictionary )
        
        @property
        def has_meaningful_content( self ) -> bool:
            ''' Returns True if document contains useful extracted content. '''
        
        def render_as_json( self ) -> __.immut.Dictionary[ str, __.typx.Any ]:
            ''' Renders complete document as JSON-compatible dictionary. '''
        
        def render_as_markdown(
            self, /, *,
            reveal_internals: bool = True,
        ) -> tuple[ str, ... ]:
            ''' Renders complete document as Markdown lines for display. ''''

Content Identification System
-------------------------------------------------------------------------------

The content ID system enables browse-then-extract workflows by providing stable identifiers for documentation content objects. Content IDs are deterministic identifiers that allow users to first query with truncated results for previews, then extract full content for specific objects.

**Content ID Generation Strategy**

Content IDs use deterministic object identification: ``base64(location + ":" + object_name)``

**Design Benefits:**

- **Stateless Architecture**: Content IDs are self-contained, requiring no session storage
- **Stable Identification**: Same object always generates same ID regardless of query timing
- **Human-Debuggable**: IDs can be decoded to understand referenced objects
- **Performance**: No expensive computation or state tracking required

**Usage Pattern:**

.. code-block:: python

    # Stage 1: Browse with previews - generates content IDs for all results
    preview_result = await query_content(
        auxdata, location, term, lines_max = 5 )
    
    # Stage 2: Extract full content using content ID from preview
    full_result = await query_content(
        auxdata, location, term, 
        content_id = preview_result.documents[0].content_id,
        lines_max = 100 )

**Interface Integration:**

The content_id parameter extends the existing query_content function:

- **Without content_id**: Returns multiple ContentDocument objects with content IDs populated
- **With content_id**: Filters to single matching ContentDocument with full content
- **Error Handling**: Invalid content IDs raise ProcessorInavailability exceptions

This design transforms query_content from a simple search function into a flexible content navigation tool while maintaining complete backward compatibility and stateless operation.

Query Metadata Objects
===============================================================================

Search and Operation Metadata
-------------------------------------------------------------------------------

.. code-block:: python

    class SearchMetadata( __.immut.DataclassObject ):
        ''' Search operation metadata and performance statistics. '''
        
        results_count: __.typx.Annotated[
            int, __.ddoc.Doc( "Number of results returned to user." ) ]
        results_max: __.typx.Annotated[
            int, __.ddoc.Doc( "Maximum results requested by user." ) ]
        matches_total: __.typx.Annotated[
            __.typx.Optional[ int ], 
            __.ddoc.Doc( "Total matching objects before limit applied." ) ] = None
        search_time_ms: __.typx.Annotated[
            __.typx.Optional[ int ],
            __.ddoc.Doc( "Search execution time in milliseconds." ) ] = None
        
        @property
        def results_truncated( self ) -> bool:
            ''' Returns True if results were limited by results_max. '''
        
        def render_as_json( self ) -> __.immut.Dictionary[ str, __.typx.Any ]:
            ''' Renders search metadata as JSON-compatible dictionary. ''''

    class InventoryLocationInfo( __.immut.DataclassObject ):
        ''' Information about detected inventory location and processor. '''
        
        inventory_type: __.typx.Annotated[
            str, __.ddoc.Doc( "Inventory format type identifier." ) ]
        location_url: __.typx.Annotated[
            str, __.ddoc.Doc( "Complete URL to inventory location." ) ]
        processor_name: __.typx.Annotated[
            str, __.ddoc.Doc( "Name of processor handling this location." ) ]
        confidence: __.typx.Annotated[
            float, __.ddoc.Doc( "Detection confidence score (0.0-1.0)." ) ]
        object_count: __.typx.Annotated[
            int, __.ddoc.Doc( "Total objects available in this inventory." ) ]
        
        def render_as_json( self ) -> __.immut.Dictionary[ str, __.typx.Any ]:
            ''' Renders location info as JSON-compatible dictionary. '''

Detection Result Objects
-------------------------------------------------------------------------------

.. code-block:: python

    class Detection( __.immut.DataclassObject ):
        ''' Processor detection information with confidence scoring. '''
        
        processor_name: __.typx.Annotated[
            str, __.ddoc.Doc( "Name of the processor that can handle this location." ) ]
        confidence: __.typx.Annotated[
            float, __.ddoc.Doc( "Detection confidence score (0.0-1.0)." ) ]
        processor_type: __.typx.Annotated[
            str, __.ddoc.Doc( "Type of processor (inventory, structure)." ) ]
        detection_metadata: __.typx.Annotated[
            __.immut.Dictionary[ str, __.typx.Any ],
            __.ddoc.Doc( "Processor-specific detection metadata." ) 
        ] = __.dcls.field( default_factory = __.immut.Dictionary )

    class DetectionsResult( __.immut.DataclassObject ):
        ''' Detection results with processor selection and timing metadata. '''
        
        source: __.typx.Annotated[
            str, __.ddoc.Doc( "Primary location URL for detection operation." ) ]
        detections: __.typx.Annotated[
            tuple[ Detection, ... ],
            __.ddoc.Doc( "All processor detections found for location." ) ]
        detection_optimal: __.typx.Annotated[
            __.typx.Optional[ Detection ],
            __.ddoc.Doc( "Best detection result based on confidence scoring." ) ]
        time_detection_ms: __.typx.Annotated[
            int, __.ddoc.Doc( "Detection operation time in milliseconds." ) ]
        
        def render_as_json( self ) -> __.immut.Dictionary[ str, __.typx.Any ]:
            ''' Renders detection results as JSON-compatible dictionary. '''
        
        def render_as_markdown(
            self, /, *,
            reveal_internals: bool = True,
        ) -> tuple[ str, ... ]:
            ''' Renders detection results as Markdown lines for display. ''''

Processor Survey Result Objects
-------------------------------------------------------------------------------

.. code-block:: python

    class ProcessorInfo( __.immut.DataclassObject ):
        ''' Information about a processor and its capabilities. '''
        
        processor_name: __.typx.Annotated[
            str, __.ddoc.Doc( "Name of the processor for identification." ) ]
        processor_type: __.typx.Annotated[
            str, __.ddoc.Doc( "Type of processor (inventory, structure)." ) ]
        capabilities: __.typx.Annotated[
            __.interfaces.ProcessorCapabilities,
            __.ddoc.Doc( "Complete capability description for processor." ) ]
        
        def render_as_json( self ) -> __.immut.Dictionary[ str, __.typx.Any ]:
            ''' Renders processor info as JSON-compatible dictionary. '''
        
        def render_as_markdown(
            self, /, *,
            reveal_internals: bool = True,
        ) -> tuple[ str, ... ]:
            ''' Renders processor info as Markdown lines for display. '''

    class ProcessorsSurveyResult( __.immut.DataclassObject ):
        ''' Survey results listing available processors and capabilities. '''
        
        genus: __.typx.Annotated[
            __.interfaces.ProcessorGenera, 
            __.ddoc.Doc( "Processor genus that was surveyed (inventory or structure)." ) ]
        filter_name: __.typx.Annotated[
            __.typx.Optional[ str ],
            __.ddoc.Doc( "Optional processor name filter applied to survey." ) ] = None
        processors: __.typx.Annotated[
            tuple[ ProcessorInfo, ... ],
            __.ddoc.Doc( "Available processors matching survey criteria." ) ]
        survey_time_ms: __.typx.Annotated[
            int, __.ddoc.Doc( "Survey operation time in milliseconds." ) ]
        
        def render_as_json( self ) -> __.immut.Dictionary[ str, __.typx.Any ]:
            ''' Renders survey results as JSON-compatible dictionary. '''
        
        def render_as_markdown(
            self, /, *,
            reveal_internals: bool = True,
        ) -> tuple[ str, ... ]:
            ''' Renders survey results as Markdown lines for display. ''''

Error Handling Objects
-------------------------------------------------------------------------------

The error handling architecture supports both structured error responses for API boundaries and self-rendering exceptions for natural Python exception flow. This dual approach enables clean function signatures while maintaining structured error information across interface layers.

**Self-Rendering Exception Base Classes**

.. code-block:: python

    class Omniexception( __.immut.Object, BaseException ):
        ''' Base for all exceptions raised by package API. '''

    class Omnierror( Omniexception, Exception ):
        ''' Base for error exceptions with self-rendering capability. '''
        
        @__.abc.abstractmethod
        def render_as_json( self ) -> __.immut.Dictionary[ str, __.typx.Any ]:
            ''' Renders exception as JSON-compatible dictionary. '''
        
        @__.abc.abstractmethod  
        def render_as_markdown( self ) -> tuple[ str, ... ]:
            ''' Renders exception as Markdown lines for display. '''

**Domain-Specific Self-Rendering Exceptions**

.. code-block:: python

    class ProcessorInavailability( Omnierror, RuntimeError ):
        ''' No processor found to handle source. '''

        def __init__(
            self,
            source: __.typx.Annotated[
                str, __.ddoc.Doc( "Source URL that could not be processed." ) ],
            genus: __.Absential[ str ] = __.absent,
            query: __.Absential[ str ] = __.absent,
        ): ...

        def render_as_json( self ) -> __.immut.Dictionary[ str, __.typx.Any ]:
            ''' Renders processor unavailability as JSON-compatible dictionary. '''

    class InventoryInaccessibility( Omnierror, RuntimeError ):
        ''' Inventory location cannot be accessed. '''

        def __init__(
            self,
            location: __.typx.Annotated[
                str, __.ddoc.Doc( "Inventory location URL." ) ],
            cause: __.typx.Annotated[
                __.typx.Optional[ BaseException ],
                __.ddoc.Doc( "Underlying exception that caused inaccessibility." )
            ] = None,
        ): ...

    class InventoryInvalidity( Omnierror, ValueError ):
        ''' Inventory data format is invalid or corrupted. '''

        def __init__(
            self,
            location: __.typx.Annotated[
                str, __.ddoc.Doc( "Inventory location URL." ) ],
            details: __.typx.Annotated[
                str, __.ddoc.Doc( "Description of invalidity." )
            ],
        ): ...


Complete Query Results
-------------------------------------------------------------------------------

.. code-block:: python

    class InventoryQueryResult( __.immut.DataclassObject ):
        ''' Complete result structure for inventory queries. '''
        
        location: __.typx.Annotated[
            str, __.ddoc.Doc( "Primary location URL for this query." ) ]
        query: __.typx.Annotated[
            str, __.ddoc.Doc( "Search term or query string used." ) ]
        objects: __.typx.Annotated[
            tuple[ InventoryObject, ... ],
            __.ddoc.Doc( "Inventory objects matching search criteria." ) ]
        search_metadata: __.typx.Annotated[
            SearchMetadata, __.ddoc.Doc( "Search execution and result metadata." ) ]
        inventory_locations: __.typx.Annotated[
            tuple[ InventoryLocationInfo, ... ],
            __.ddoc.Doc( "Information about inventory locations used." ) ]
        
        def render_as_json( self ) -> __.immut.Dictionary[ str, __.typx.Any ]:
            ''' Renders inventory query result as JSON-compatible dictionary. '''
        
        def render_as_markdown(
            self, /, *,
            reveal_internals: bool = True,
        ) -> tuple[ str, ... ]:
            ''' Renders inventory query result as Markdown lines for display. '''

    class ContentQueryResult( __.immut.DataclassObject ):
        ''' Complete result structure for content queries. '''
        
        location: __.typx.Annotated[
            str, __.ddoc.Doc( "Primary location URL for this query." ) ]
        query: __.typx.Annotated[
            str, __.ddoc.Doc( "Search term or query string used." ) ]
        documents: __.typx.Annotated[
            tuple[ ContentDocument, ... ],
            __.ddoc.Doc( "Documentation content for matching objects." ) ]
        search_metadata: __.typx.Annotated[
            SearchMetadata, __.ddoc.Doc( "Search execution and result metadata." ) ]
        inventory_locations: __.typx.Annotated[
            tuple[ InventoryLocationInfo, ... ],
            __.ddoc.Doc( "Information about inventory locations used." ) ]
        
        def render_as_json(
            self, /, *,
            lines_max: __.typx.Optional[ int ] = None,
        ) -> __.immut.Dictionary[ str, __.typx.Any ]:
            ''' Renders content query result as JSON-compatible dictionary with optional content truncation. '''
        
        def render_as_markdown(
            self, /, *,
            reveal_internals: bool = True,
            lines_max: __.typx.Annotated[
                __.typx.Optional[ int ],
                __.ddoc.Doc( "Maximum lines to display per content result." )
            ] = None,
        ) -> tuple[ str, ... ]:
            ''' Renders content query result as Markdown lines for display. '''

Processor Integration Design
===============================================================================

Enhanced Base Classes
-------------------------------------------------------------------------------

The processor layer integrates with structured objects through updated return types:

.. code-block:: python

    # processors.py - Enhanced base class
    class InventoryDetection( Detection ):
        ''' Enhanced base class returning structured objects. '''

        @__.abc.abstractmethod
        async def filter_inventory(
            self,
            auxdata: __.ApplicationGlobals,
            location: str, /, *,
            filters: __.cabc.Mapping[ str, __.typx.Any ],
            details: __.InventoryQueryDetails = (
                __.InventoryQueryDetails.Documentation ),
        ) -> tuple[ InventoryObject, ... ]:
            ''' Returns structured inventory objects instead of dictionaries. '''

Processor Object Formatting
-------------------------------------------------------------------------------

Each processor provides consistent object formatting:

.. code-block:: python

    # Sphinx processor formatting
    def format_inventory_object(
        sphinx_object: __.typx.Any,
        inventory: __.typx.Any,
        location_url: str,
    ) -> InventoryObject:
        ''' Formats Sphinx inventory object with complete attribution. '''
        
        return InventoryObject(
            name = sphinx_object.name,
            uri = sphinx_object.uri,
            inventory_type = 'sphinx_objects_inv',
            location_url = location_url,
            display_name = (
                sphinx_object.dispname 
                if sphinx_object.dispname != '-' 
                else None ),
            specifics = __.immut.Dictionary(
                domain = sphinx_object.domain,
                role = sphinx_object.role,
                priority = sphinx_object.priority,
                inventory_project = inventory.project,
                inventory_version = inventory.version ) )

    # MkDocs processor formatting  
    def format_inventory_object(
        mkdocs_document: __.cabc.Mapping[ str, __.typx.Any ],
        location_url: str,
    ) -> InventoryObject:
        ''' Formats MkDocs search index document with attribution. '''
        
        typed_doc = dict( mkdocs_document )
        location = str( typed_doc.get( 'location', '' ) )
        title = str( typed_doc.get( 'title', '' ) )
        
        return InventoryObject(
            name = title,
            uri = location,
            inventory_type = 'mkdocs_search_index',
            location_url = location_url,
            specifics = __.immut.Dictionary(
                domain = 'page',
                role = 'doc', 
                priority = '1',
                object_type = 'page' ) )

Functions Layer Integration
===============================================================================

Enhanced Business Logic Functions
-------------------------------------------------------------------------------

The functions module provides clean business logic functions using natural exception flow with self-rendering exceptions:

.. code-block:: python

    # functions.py - Clean signatures with exception-based error handling
    async def query_inventory(
        auxdata: __.ApplicationGlobals,
        location: __.typx.Annotated[ str, __.ddoc.Fname( 'location argument' ) ],
        term: str, /, *,
        processor_name: __.Absential[ str ] = __.absent,
        search_behaviors: __.SearchBehaviors = _search_behaviors_default,
        filters: __.cabc.Mapping[ str, __.typx.Any ] = _filters_default,
        details: __.InventoryQueryDetails = (
            __.InventoryQueryDetails.Documentation ),
        results_max: int = 5,
    ) -> InventoryQueryResult:
        ''' Returns structured inventory query results. Raises domain exceptions on error. '''

    async def query_content(
        auxdata: __.ApplicationGlobals,
        location: __.typx.Annotated[ str, __.ddoc.Fname( 'location argument' ) ],
        term: str, /, *,
        processor_name: __.Absential[ str ] = __.absent,
        search_behaviors: __.SearchBehaviors = _search_behaviors_default,
        filters: __.cabc.Mapping[ str, __.typx.Any ] = _filters_default,
        content_id: __.Absential[ str ] = __.absent,
        results_max: int = 10,
        lines_max: __.typx.Optional[ int ] = None,
    ) -> ContentQueryResult:
        ''' Returns structured content query results. When content_id provided, returns single matching document. Raises domain exceptions on error. '''

    async def detect(
        auxdata: __.ApplicationGlobals,
        location: __.typx.Annotated[ str, __.ddoc.Fname( 'location argument' ) ], /, *,
        processor_name: __.Absential[ str ] = __.absent,
        processor_types: __.cabc.Sequence[ str ] = ( 'inventory', 'structure' ),
    ) -> DetectionsResult:
        ''' Returns structured detection results with processor selection and timing. '''

    async def survey_processors(
        auxdata: __.ApplicationGlobals, /, 
        genus: __.interfaces.ProcessorGenera,
        name: __.typx.Optional[ str ] = None,
    ) -> ProcessorsSurveyResult:
        ''' Returns structured survey results listing available processors and capabilities. '''


Error Handling Patterns
-------------------------------------------------------------------------------

The system uses **self-rendering exceptions** for natural Python error flow with clean function signatures and consistent error presentation across interface layers.

**Self-Rendering Exception Pattern**

Functions use natural exception flow with domain-specific self-rendering exceptions:

.. code-block:: python

    # Business logic functions with clean signatures
    async def query_inventory(
        auxdata: __.ApplicationGlobals,
        location: str,
        term: str, /, *,
        search_behaviors: __.SearchBehaviors = _search_behaviors_default,
        filters: __.cabc.Mapping[ str, __.typx.Any ] = _filters_default,
        details: __.InventoryQueryDetails = __.InventoryQueryDetails.Documentation,
        results_max: int = 5,
    ) -> InventoryQueryResult:
        ''' Returns structured inventory query results. Raises domain exceptions on error. '''

    # Processor layer raises self-rendering exceptions
    class SphinxInventoryProcessor:
        async def query_inventory( 
            self, filters: __.cabc.Mapping[ str, __.typx.Any ], 
            details: __.InventoryQueryDetails 
        ) -> tuple[ __.InventoryObject, ... ]:
            try:
                inventory = extract_inventory( base_url )
                return tuple( format_objects( inventory, filters ) )
            except ConnectionError as exc:
                raise InventoryInaccessibility( location = url, cause = exc )
            except ParseError as exc:
                raise InventoryInvalidity( location = url, details = str( exc ) )

**Interface Layer Exception Handling**

Interface layers use Aspect-Oriented Programming (AOP) patterns with decorators:

.. code-block:: python

    # MCP Server - Exception interception decorator signature
    def intercept_errors( func ) -> __.cabc.Callable:
        ''' Intercepts package exceptions and renders them as JSON for MCP. '''

    @intercept_errors
    async def query_inventory_mcp( location: str, term: str, ... ):
        ''' Searches object inventory by name with fuzzy matching. '''

    # CLI Layer - Parameterized exception handling decorator signature
    def intercept_errors( 
        stream: __.typx.TextIO, 
        display_format: __.DisplayFormat 
    ) -> __.cabc.Callable:
        ''' Creates decorator to intercept package exceptions and render for CLI. '''


Search Engine Integration
===============================================================================

Enhanced Search Result Objects
-------------------------------------------------------------------------------

.. code-block:: python

    # search.py - Enhanced to work with structured objects
    def filter_by_name(
        objects: __.cabc.Sequence[ InventoryObject ],
        term: str, /, *,
        match_mode: __.MatchMode = __.MatchMode.Fuzzy,
        fuzzy_threshold: int = 50,
    ) -> tuple[ SearchResult, ... ]:
        ''' Enhanced search filtering returning structured results. '''

Self-Rendering Architecture
-------------------------------------------------------------------------------

**Universal Rendering Interface**
All structured result objects implement standardized rendering methods:

.. code-block:: python

    # Universal rendering interface for all result objects
    def render_as_json( self ) -> __.immut.Dictionary[ str, __.typx.Any ]:
        ''' Renders object as JSON-compatible immutable dictionary. '''
        
    def render_as_markdown( 
        self, /, *, 
        reveal_internals: bool = True 
    ) -> tuple[ str, ... ]:
        ''' Renders object as Markdown lines for CLI display. '''

**Domain-Specific Rendering Implementation**
Each object encapsulates its own formatting logic:

.. code-block:: python

    # InventoryObject rendering example
    def render_as_json( self ) -> __.immut.Dictionary[ str, __.typx.Any ]:
        ''' Returns JSON-compatible dictionary with domain knowledge. '''
        result = __.immut.Dictionary(
            name = self.name,
            uri = self.uri,
            inventory_type = self.inventory_type,
            location_url = self.location_url,
            display_name = self.display_name,
            effective_display_name = self.effective_display_name,
        )
        # Merge with domain-specific formatting logic
        return result.union( self.specifics )
    
    def render_as_markdown( 
        self, /, *, reveal_internals: bool = True 
    ) -> tuple[ str, ... ]:
        ''' Returns Markdown lines using processor-specific formatting. '''
        lines = [ f"### `{self.effective_display_name}`" ]
        # Domain-specific formatting logic implemented by processors
        return tuple( lines )

Validation and Type Safety
===============================================================================

Object Validation Strategy
-------------------------------------------------------------------------------

Validation of result objects is implemented at object initialization
through ``__post_init__`` methods when validation is needed. This ensures
that invalid objects cannot be constructed and provides fail-fast behavior
with guaranteed valid state.

Objects own their validity invariants through initialization-time validation
rather than relying on external validation functions.

Module Organization
===============================================================================

File Structure and Imports
-------------------------------------------------------------------------------

.. code-block:: python

    # results.py - Core results module
    from . import __

    # Core result objects
    class InventoryObject( __.immut.DataclassObject ): ...
    class SearchResult( __.immut.DataclassObject ): ...
    class ContentDocument( __.immut.DataclassObject ): ...

    # Metadata objects  
    class SearchMetadata( __.immut.DataclassObject ): ...
    class InventoryLocationInfo( __.immut.DataclassObject ): ...

    # Complete query results
    class InventoryQueryResult( __.immut.DataclassObject ): ...
    class ContentQueryResult( __.immut.DataclassObject ): ...
    class DetectionsResult( __.immut.DataclassObject ): ...
    
    # Survey results
    class ProcessorInfo( __.immut.DataclassObject ): ...
    class ProcessorsSurveyResult( __.immut.DataclassObject ): ...


    # Serialization support
    def serialize_for_json( ... ): ...

    # Type aliases (at end to avoid forward references)
    InventoryObjects: __.typx.TypeAlias = __.cabc.Sequence[ InventoryObject ]
    SearchResults: __.typx.TypeAlias = __.cabc.Sequence[ SearchResult ]
    ContentDocuments: __.typx.TypeAlias = __.cabc.Sequence[ ContentDocument ]
    

.. code-block:: python

    # exceptions.py - Self-rendering exception hierarchy
    from . import __

    # Base exception hierarchy
    class Omniexception( __.immut.Object, BaseException ): ...
    class Omnierror( Omniexception, Exception ): ...

    # Domain-specific exceptions with self-rendering capabilities
    class ProcessorInavailability( Omnierror, RuntimeError ): ...
    class InventoryInaccessibility( Omnierror, RuntimeError ): ...
    class InventoryInvalidity( Omnierror, ValueError ): ...
    class ContentInaccessibility( Omnierror, RuntimeError ): ...
    class ContentInvalidity( Omnierror, ValueError ): ...

Presentation Layer Integration
===============================================================================

CLI and Renderers Integration
-------------------------------------------------------------------------------

The self-rendering architecture enables clean separation between business logic 
and presentation concerns:

**Presentation vs Business Logic Separation**
- **Objects handle domain logic**: ``result.render_as_json()``
- **CLI coordinators handle presentation**: truncation, formatting, display helpers
- **MCP server uses objects directly**: no CLI-specific presentation layer

**Direct Self-Rendering Architecture**
Objects handle all presentation directly through self-rendering methods, eliminating
the need for external presentation coordination layers.

Integration Benefits
===============================================================================

**Clean Function Signatures**
- Natural exception flow eliminates verbose union return types  
- Business logic functions have clean success-case signatures
- Type annotations reflect actual success types without error boilerplate
- Function signatures become more readable and maintainable

**Type Safety and IDE Support**
- Compile-time validation of object structure and field access
- Full IDE autocompletion and refactoring support  
- Static analysis capabilities for detecting field usage
- Exception type hierarchy provides structured error catching patterns

**Self-Rendering Architecture**
- Exceptions handle their own presentation logic through render methods
- Objects encapsulate format-specific knowledge within themselves  
- Clean separation between business logic and presentation concerns
- Consistent error display across CLI and MCP interfaces without duplication

**Aspect-Oriented Error Handling**
- Interface layers use decorators for cross-cutting error handling concerns
- Business logic remains pure with no error marshaling overhead
- Single point of error presentation control per interface layer
- Exception handling behavior easily modified without touching business functions

**Domain-Specific Rendering**
- Processors provide domain expertise through object rendering methods
- Extensible rendering without modifying CLI or interface layers
- Complete error context preservation from point of failure to presentation
- Self-contained formatting logic reduces coupling between layers

**Complete Source Attribution**
- Full provenance tracking for every inventory object
- Enhanced debugging capabilities with location-specific metadata
- Foundation for future multi-source aggregation capabilities
- Exception objects maintain complete failure context

**Consistency and Maintainability**  
- Unified interface across all inventory processor types
- Clear separation between universal and format-specific data
- Predictable object structure for interface layers
- Error handling complexity isolated to exception classes and decorators

**Performance and Scalability**
- Immutable objects enable safe concurrent access
- Structural sharing reduces memory overhead
- Efficient serialization for network transmission
- Exception-based flow avoids creating error objects for success cases
- Domain-specific rendering optimizations contained within objects

This results module design provides a robust foundation for type-safe operations 
across all system components while maintaining clean architectural boundaries 
and enabling future enhancements through structured object capabilities and 
self-rendering architecture.