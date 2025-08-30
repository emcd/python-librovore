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
        ''' Documentation content with extracted metadata and snippets. '''
        
        inventory_object: __.typx.Annotated[
            InventoryObject, __.ddoc.Doc( "Location inventory object for this content." ) ]
        signature: __.typx.Annotated[
            str, __.ddoc.Doc( "Extracted function/class signature." ) ] = ''
        description: __.typx.Annotated[
            str, __.ddoc.Doc( "Extracted object description or summary." ) ] = ''
        content_snippet: __.typx.Annotated[
            str, __.ddoc.Doc( "Relevant content excerpt for search context." ) ] = ''
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

.. code-block:: python

    class ErrorInfo( __.immut.DataclassObject ):
        ''' Structured error information for processor failures. '''
        
        type: __.typx.Annotated[
            str, __.ddoc.Doc( "Error type identifier (e.g., 'processor_unavailable')." ) ]
        title: __.typx.Annotated[
            str, __.ddoc.Doc( "Human-readable error title." ) ]
        message: __.typx.Annotated[
            str, __.ddoc.Doc( "Detailed error description." ) ]
        suggestion: __.typx.Annotated[
            __.typx.Optional[ str ],
            __.ddoc.Doc( "Suggested remediation steps." ) ] = None

    class ErrorResponse( __.immut.DataclassObject ):
        ''' Error response wrapper maintaining query context. '''
        
        location: __.typx.Annotated[
            str, __.ddoc.Doc( "Primary location URL for failed query." ) ]
        query: __.typx.Annotated[
            str, __.ddoc.Doc( "Search term or query string that failed." ) ]
        error: __.typx.Annotated[
            ErrorInfo, __.ddoc.Doc( "Detailed error information." ) ]
        
        def render_as_json( self ) -> __.immut.Dictionary[ str, __.typx.Any ]:
            ''' Renders error response as JSON-compatible dictionary. '''
        
        def render_as_markdown(
            self, /, *,
            reveal_internals: bool = True,
        ) -> tuple[ str, ... ]:
            ''' Renders error response as Markdown lines for display. '''

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
        
        def render_as_json( self ) -> __.immut.Dictionary[ str, __.typx.Any ]:
            ''' Renders content query result as JSON-compatible dictionary. '''
        
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

The functions module uses structured result objects for all operations:

.. code-block:: python

    # functions.py - Union return types for proper error propagation
    InventoryResult: __.typx.TypeAlias = InventoryQueryResult | ErrorResponse
    ContentResult: __.typx.TypeAlias = ContentQueryResult | ErrorResponse
    DetectionsResultUnion: __.typx.TypeAlias = DetectionsResult | ErrorResponse
    ProcessorsSurveyResultUnion: __.typx.TypeAlias = ProcessorsSurveyResult | ErrorResponse

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
    ) -> InventoryResult:
        ''' Returns structured inventory query results or error information. '''

    async def query_content(
        auxdata: __.ApplicationGlobals,
        location: __.typx.Annotated[ str, __.ddoc.Fname( 'location argument' ) ],
        term: str, /, *,
        processor_name: __.Absential[ str ] = __.absent,
        search_behaviors: __.SearchBehaviors = _search_behaviors_default,
        filters: __.cabc.Mapping[ str, __.typx.Any ] = _filters_default,
        include_snippets: bool = True,
        results_max: int = 10,
    ) -> ContentResult:
        ''' Returns structured content query results or error information. '''

    async def detect(
        auxdata: __.ApplicationGlobals,
        location: __.typx.Annotated[ str, __.ddoc.Fname( 'location argument' ) ], /, *,
        processor_name: __.Absential[ str ] = __.absent,
        processor_types: __.cabc.Sequence[ str ] = ( 'inventory', 'structure' ),
    ) -> DetectionsResultUnion:
        ''' Returns structured detection results with processor selection and timing. '''

    async def survey_processors(
        auxdata: __.ApplicationGlobals, /, 
        genus: __.interfaces.ProcessorGenera,
        name: __.typx.Optional[ str ] = None,
    ) -> ProcessorsSurveyResultUnion:
        ''' Returns structured survey results listing available processors and capabilities. '''

Error Handling Patterns
-------------------------------------------------------------------------------

The system uses **exception-based error handling at the processor level** with 
**structured error marshaling at the functions boundary**. This approach maintains 
clean processor implementations while providing structured APIs for CLI and MCP consumers.

**Processor Layer**: Raises domain-specific exceptions for clear error semantics:

.. code-block:: python

    # Processors raise exceptions directly
    class SphinxInventoryProcessor:
        async def query_inventory( 
            self, filters: __.cabc.Mapping[ str, __.typx.Any ], 
            details: __.InventoryQueryDetails 
        ) -> tuple[ __.InventoryObject, ... ]:
            try:
                inventory = extract_inventory( base_url )
                return tuple( format_objects( inventory, filters ) )
            except ConnectionError as exc:
                raise InventoryInaccessibility( url, cause = exc )
            except ParseError as exc:
                raise InventoryInvalidity( url, cause = exc )

**Functions Layer**: Catches exceptions and marshals to structured responses:

.. code-block:: python

    # functions.py - Exception marshaling to structured responses
    async def query_inventory( ... ) -> InventoryResult:
        try:
            detection = await detect_inventory( auxdata, location, ... )
            objects = await detection.query_inventory( filters = filters, ... )
            return InventoryQueryResult(
                location = location, query = term, objects = objects, ... )
        except ProcessorInavailability as exc:
            return ErrorResponse(
                location = location, query = term,
                error = ErrorInfo( type = 'processor_unavailable', ... ) )
        except InventoryInaccessibility as exc:
            return ErrorResponse(
                location = location, query = term,
                error = ErrorInfo( type = 'inventory_inaccessible', ... ) )

**Consumer Layer**: Uses isinstance checks or pattern matching on structured results:

.. code-block:: python

    # CLI/MCP consumers handle structured responses
    result = await query_inventory( auxdata, location, term )
    if isinstance( result, ErrorResponse ):
        logger.error( f"Query failed: {result.error.message}." )
        return format_error_response( result )
    
    # At this point, result is InventoryQueryResult
    return format_success_response( result.objects )

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

    # Error handling objects
    class ErrorInfo( __.immut.DataclassObject ): ...
    class ErrorResponse( __.immut.DataclassObject ): ...

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
    
    # Union types for error propagation
    InventoryResult: __.typx.TypeAlias = InventoryQueryResult | ErrorResponse  
    ContentResult: __.typx.TypeAlias = ContentQueryResult | ErrorResponse
    DetectionsResultUnion: __.typx.TypeAlias = DetectionsResult | ErrorResponse
    ProcessorsSurveyResultUnion: __.typx.TypeAlias = ProcessorsSurveyResult | ErrorResponse

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

**Type Safety and IDE Support**
- Compile-time validation of object structure and field access
- Full IDE autocompletion and refactoring support  
- Static analysis capabilities for detecting field usage
- Union types provide exhaustive pattern matching with type narrowing
- `match` statements with object unpacking enable clean error handling

**Domain-Specific Rendering**
- Objects encapsulate format-specific knowledge within themselves
- Processors provide domain expertise through object rendering methods
- Clean separation between data representation and presentation logic
- Extensible rendering without modifying CLI or interface layers

**Complete Source Attribution**
- Full provenance tracking for every inventory object
- Enhanced debugging capabilities with location-specific metadata
- Foundation for future multi-source aggregation capabilities

**Consistency and Maintainability**  
- Unified interface across all inventory processor types
- Clear separation between universal and format-specific data
- Predictable object structure for interface layers
- Self-contained formatting logic reduces coupling

**Performance and Scalability**
- Immutable objects enable safe concurrent access
- Structural sharing reduces memory overhead
- Efficient serialization for network transmission
- Domain-specific rendering optimizations contained within objects

This results module design provides a robust foundation for type-safe operations 
across all system components while maintaining clean architectural boundaries 
and enabling future enhancements through structured object capabilities and 
self-rendering architecture.