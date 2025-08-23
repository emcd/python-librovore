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
Inventory Processors Architecture
*******************************************************************************

Overview
===============================================================================

Inventory processors extract and provide object inventories from documentation 
sources, enabling discovery and search operations across different documentation 
formats. These processors form the foundation of librovore's inventory-based 
architecture, converting format-specific inventory data into universal 
``InventoryObject`` instances.

**Role in librovore architecture**: Inventory processors serve as the primary 
interface between external documentation sources and librovore's search and 
discovery operations. They enable format-agnostic inventory operations while 
maintaining complete source attribution and metadata preservation.

**Relationship to structure processors**: Inventory processors discover and 
enumerate documentation objects, while structure processors extract content 
from those objects. The two processor types work together through capability-based 
filtering to ensure inventory objects are only sent to compatible structure 
processors.

**Universal object interface principles**: All inventory processors return 
``InventoryObject`` instances regardless of source format, providing type safety, 
consistent search operations, and multi-source aggregation capabilities. The 
universal interface isolates format differences within processor implementations 
while enabling uniform operations across all inventory types.

Architecture Patterns
===============================================================================

Universal Inventory Object Interface
-------------------------------------------------------------------------------

**Decision**: All inventory processors return ``InventoryObject`` instances 
rather than format-specific dictionaries.

**Rationale**: Provides type safety, enables consistent search operations, 
and supports multi-source aggregation capabilities. The universal interface 
isolates format differences within processor implementations.

**Impact**: Processors become responsible for complete source attribution 
and metadata normalization, while search and ranking operations work 
uniformly across all inventory types.

The universal interface follows a consistent dataflow pattern across all 
processor types:

.. code-block:: text

    External Inventory Source
              │
              ▼
    ┌─────────────────────┐
    │   Detection Phase   │ ◄─── Confidence scoring
    └─────────────────────┘      URL derivation
              │
              ▼
    ┌─────────────────────┐
    │   Loading Phase     │ ◄─── Raw data retrieval
    └─────────────────────┘      Format validation
              │
              ▼
    ┌─────────────────────┐
    │  Transformation     │ ◄─── Format-specific parsing
    │       Phase         │      Universal object creation
    └─────────────────────┘
              │
              ▼
    ┌─────────────────────┐
    │   Filtering Phase   │ ◄─── Criteria application
    └─────────────────────┘      Results ranking
              │
              ▼
    Universal InventoryObject Collection

Source Attribution Strategy
-------------------------------------------------------------------------------

**Decision**: Every inventory object includes complete provenance information 
including processor type, location URL, and format-specific metadata.

**Rationale**: Enables debugging, caching optimization, and future multi-source 
operations. Complete attribution allows the system to understand object 
origins without maintaining separate tracking mechanisms.

**Impact**: Processors must provide consistent metadata extraction and URL 
normalization. Format-specific details are preserved in the ``specifics`` 
container without affecting universal operations.

Source attribution includes:
- **Processor identification**: Clear identification of the processor type that created the object
- **Location attribution**: Complete URL tracking for cache management and debugging
- **Format metadata preservation**: Format-specific details maintained in structured containers
- **Provenance tracking**: Full chain of custody from source to object creation

Confidence-Based Detection
-------------------------------------------------------------------------------

**Decision**: Processor detection uses numerical confidence scores rather than 
boolean availability checks.

**Rationale**: Allows graceful handling of edge cases where multiple processors 
might partially support a documentation source. Provides foundation for 
processor precedence and quality assessment.

**Impact**: Detection algorithms must provide meaningful confidence 
differentiation. The detection system can make informed choices when multiple 
processors are available for a source.

Confidence scoring methodology:
- **High confidence (0.9+)**: Well-structured inventories with substantial content and clear format indicators
- **Medium confidence (0.7+)**: Valid inventories meeting minimum structural requirements
- **Low confidence (0.5+)**: Partial or potentially problematic inventories that may still be usable
- **Below threshold**: Malformed, empty, or incompatible inventories rejected from consideration

Error Handling Patterns
-------------------------------------------------------------------------------

**Consistent Error Categories**: All processors handle standard error types with 
uniform reporting and graceful degradation:

- **Accessibility Errors**: Network failures, missing resources, permission denials
- **Format Errors**: Invalid inventory structure, parsing failures, unsupported versions  
- **Configuration Errors**: Invalid filter parameters, unsupported operations
- **System Errors**: Unexpected failures, resource exhaustion

**Quality Assurance Patterns**: Multi-stage validation from raw data through final 
object creation ensures data integrity and provides detailed error context for 
debugging inventory processing issues.

Performance Characteristics
-------------------------------------------------------------------------------

**Detection Caching**: Detection results are cached with appropriate TTL values 
to avoid repeated expensive operations while maintaining data freshness for 
dynamic documentation sources.

**Inventory Caching**: Raw inventory data caching at the processor level reduces 
external service load while ensuring consistent object creation across multiple 
filter operations.

**Object Caching**: Formatted inventory objects may be cached when processing 
large inventories with repeated filter operations to improve response times.

**Scalability Considerations**: Processors implement streaming parsing for large 
inventories, pagination support for query results, and memory-efficient object 
creation patterns to handle documentation sites of varying sizes.

Processor-Provided Formatters System
===============================================================================

Self-Contained Object Approach
-------------------------------------------------------------------------------

The processor-provided formatters design implements **self-contained inventory objects** 
where each inventory processor creates objects that provide formatting intelligence 
for their own ``specifics`` fields. This approach co-locates domain knowledge with 
the processors that create it, making the system truly extensible and maintainable.

**Core Principle**: Each processor knows best how to present its own data. Sphinx 
processors understand ``domain``, ``role``, and ``priority`` semantics. MkDocs 
processors understand ``content_preview`` and page-based organization. Other 
processors have their own field semantics that cannot be predicted centrally.

**Architectural Foundation**:
- **Self-Contained Objects**: Inventory objects provide their own rendering methods without external dependencies
- **Domain Knowledge Co-location**: Objects understand their own field semantics and presentation requirements
- **Extensibility Without Core Changes**: New inventory processors create objects that inherently know how to render themselves

Domain Knowledge Co-location
-------------------------------------------------------------------------------

Domain knowledge remains with the processors and objects that understand the data:

- **Format Expertise**: Processors understand their source format's semantics and conventions
- **Presentation Logic**: Objects know how to render their specific data appropriately
- **Evolution Together**: Data structures and presentation logic evolve in tandem
- **No External Dependencies**: Objects render themselves without requiring external formatting registries

Interface Specifications
-------------------------------------------------------------------------------

The ``InventoryObject`` class provides self-formatting capabilities through methods 
that each processor implements to render format-specific data. See the 
`results-module-design` document for complete interface specifications.

.. code-block:: python

    class InventoryObject( __.immut.DataclassObject ):
        ''' Universal inventory object with self-formatting capabilities. '''
        
        def render_specifics_markdown( 
            self, /, *, 
            show_technical: __.typx.Annotated[ bool, __.ddoc.Doc( '...' ) ] = True 
        ) -> tuple[ str, ... ]:
            ''' Renders specifics as Markdown lines for CLI display. '''
            
        def render_specifics_json( self ) -> dict[ str, __.typx.Any ]:
            ''' Renders specifics as JSON-serializable dictionary. '''
            
        def get_compact_display_fields( self ) -> tuple[ tuple[ str, str ], ... ]:
            ''' Gets priority fields for compact display formats. '''

CLI and JSON Integration Patterns
-------------------------------------------------------------------------------

The CLI layer integrates with self-formatting objects through standardized interfaces:

.. code-block:: python

    # CLI integration signatures
    def _append_inventory_metadata(
        lines: __.cabc.MutableSequence[ str ], 
        inventory_object: __.cabc.Mapping[ str, __.typx.Any ]
    ) -> None:
        ''' Appends inventory metadata using object self-formatting. '''
        
    def _append_content_description(
        lines: __.cabc.MutableSequence[ str ], 
        document: __.cabc.Mapping[ str, __.typx.Any ], 
        inventory_object: __.cabc.Mapping[ str, __.typx.Any ],
    ) -> None:
        ''' Appends content description with standard fallbacks. '''

Serialization supports self-formatting objects:

.. code-block:: python

    # Serialization signatures
    def serialize_for_json( obj: __.typx.Any ) -> __.typx.Any:
        ''' Serialization supporting self-formatting objects. '''
        
    def _serialize_dataclass_for_json( obj: __.typx.Any ) -> dict[ str, __.typx.Any ]:
        ''' Serializes dataclass objects using render_specifics_json when available. '''

Example Implementation Patterns
-------------------------------------------------------------------------------

Each processor creates objects that understand format-specific rendering:

**Sphinx-specific rendering**: Sphinx inventory objects implement rendering that 
shows role and domain information directly, uses Sphinx terminology that users 
understand, and includes source attribution and priority when technical details 
are requested.

**MkDocs-specific rendering**: MkDocs inventory objects implement rendering that 
emphasizes document/page nature, shows navigation context and page hierarchy 
when available, and consistently displays document type and page structure.

Detection and Discovery
===============================================================================

Detection Interface Contracts
-------------------------------------------------------------------------------

All inventory processors implement standardized detection interfaces that provide 
consistent behavior across different inventory formats:

.. code-block:: python

    class InventoryDetection( Detection ):
        ''' Base class for inventory processor detection. '''
        
        @__.typx.abc.abstractmethod
        async def detect_async(
            self,
            location: str, /, *,
            auxdata: __.state.Globals
        ) -> DetectionResult:
            ''' Detects inventory availability with confidence scoring. '''
            
        @__.typx.abc.abstractmethod  
        def format_inventory_object(
            self,
            source_data: __.typx.Any,
            location_url: str, /, *,
            auxiliary_data: __.typx.Optional[ __.typx.Any ] = None,
        ) -> InventoryObject:
            ''' Formats source data into inventory object with self-formatting capabilities. '''

**Detection Contract**: Async detection returning confidence-scored results with 
optional caching of preliminary inventory data for performance optimization.

**Object Creation Contract**: Unified object creation interface that converts 
format-specific source data into universal inventory objects with complete 
attribution and self-formatting capabilities.

Confidence Scoring Methodology
-------------------------------------------------------------------------------

Confidence scoring provides consistent assessment of inventory source quality 
and processor compatibility:

**Scoring Factors**:
- **Structural Validity**: Well-formed inventory data matching expected format patterns
- **Content Quality**: Sufficient object count and metadata richness for useful operations
- **Format Indicators**: Clear markers indicating the expected inventory format
- **Accessibility**: Reliable access to inventory data without errors or restrictions

**Consistency Requirements**: All processors use equivalent confidence scales and 
assessment criteria to ensure reliable processor selection across different 
inventory formats.

**Calibration Standards**: Regular validation against known good and problematic 
inventory sources ensures confidence scores remain meaningful and comparable.

Processor Selection Patterns
-------------------------------------------------------------------------------

The detection system provides optimal processor selection based on confidence 
scores and capability matching:

**Selection Algorithm**:
1. **Confidence Ranking**: Primary selection based on detection confidence scores
2. **Capability Matching**: Secondary filtering based on required operation capabilities  
3. **Performance Characteristics**: Consideration of processor performance profiles
4. **Precedence Rules**: Explicit precedence handling for overlapping processor capabilities

**Multi-Processor Scenarios**: When multiple processors detect inventory sources, 
the system applies consistent selection logic while maintaining user experience 
predictability.

Cache Integration Strategy
-------------------------------------------------------------------------------

Caching strategy optimizes performance while maintaining data freshness:

**Detection Result Caching**: Confidence-scored detection results cached with 
TTL management to avoid repeated expensive detection operations.

**Preliminary Data Caching**: Detection processes may cache preliminary inventory 
data when it can be reused for subsequent processing operations.

**Cache Invalidation**: TTL expiration and explicit invalidation triggers ensure 
cached data remains current with source changes.

**Memory Management**: Cache size limits and LRU eviction policies prevent 
memory exhaustion during extended operation periods.

Error Handling for Detection Failures
-------------------------------------------------------------------------------

Robust error handling ensures graceful degradation when detection fails:

**Error Categories**:
- **Network Errors**: Connection failures, timeouts, DNS resolution problems
- **Authentication Errors**: Permission denied, credential failures, access restrictions
- **Format Errors**: Unexpected inventory structure, parsing failures, version incompatibilities
- **Resource Errors**: Memory exhaustion, disk space issues, system resource limitations

**Recovery Strategies**: Automatic retry with exponential backoff, graceful degradation 
to alternative processors, and comprehensive error logging for debugging support.

Base Interfaces and Protocols
===============================================================================

InventoryDetection Abstract Base Class
-------------------------------------------------------------------------------

The ``InventoryDetection`` abstract base class provides the foundation for all 
inventory processor implementations:

.. code-block:: python

    class InventoryDetection( Detection ):
        ''' Base class providing unified inventory processor interface. '''
        
        @property
        @__.typx.abc.abstractmethod
        def processor_class( self ) -> type[ InventoryProcessor ]:
            ''' Returns the processor class for this detection result. '''
            
        @property  
        @__.typx.abc.abstractmethod
        def capabilities( self ) -> __.immut.Dictionary[ str, __.typx.Any ]:
            ''' Returns processor capability information. '''

Universal Interface Contracts
-------------------------------------------------------------------------------

All inventory processors implement identical interface contracts to ensure 
consistent behavior and interoperability:

**Detection Interface**: Standardized async detection with confidence scoring, 
capability advertisement, and optional preliminary data caching.

**Processing Interface**: Consistent inventory acquisition, query operations, 
and filtering capabilities across all processor implementations.

**Object Creation Interface**: Unified object formatting method signatures that 
create self-formatting inventory objects with complete source attribution.

Core Processing Methods
-------------------------------------------------------------------------------

All inventory processors implement standardized processing methods:

.. code-block:: python

    class InventoryProcessor( __.abc.ABC ):
        ''' Base class for inventory processors. '''
        
        @__.typx.abc.abstractmethod
        async def acquire_inventory(
            self
        ) -> __.immut.Dictionary[ str, InventoryObject ]:
            ''' Returns mapping of object URI to inventory object. '''
            
        @__.typx.abc.abstractmethod
        async def query_inventory(
            self,
            term: str, *,
            search_behaviors: SearchBehaviors = SearchBehaviors( ),
            filters: __.cabc.Mapping[ str, __.typx.Any ] = __.immut.Dictionary( ),
            results_max: int = 10
        ) -> __.cabc.Sequence[ SearchResult ]:
            ''' Provides search over inventory objects with filtering support. '''

**Contract Specifications**:
- ``acquire_inventory`` returns complete inventory as mapping from URI to inventory object
- ``query_inventory`` provides fuzzy/exact/regex search with configurable behaviors
- Search results include relevance scoring and match reason tracking
- Filtering support accommodates format-specific metadata and characteristics

format_inventory_object Unified Signature
-------------------------------------------------------------------------------

The unified ``format_inventory_object`` signature ensures consistent object creation 
across all processor implementations:

.. code-block:: python

    @__.typx.abc.abstractmethod
    def format_inventory_object(
        self,
        source_data: __.typx.Any,
        location_url: str, /, *,
        auxiliary_data: __.typx.Optional[ __.typx.Any ] = None,
    ) -> InventoryObject:
        ''' Formats source data into inventory object with self-formatting capabilities.
        
            Args:
                source_data: Format-specific source data (Sphinx object, MkDocs document, etc.)
                location_url: Complete URL to inventory location for attribution
                auxiliary_data: Additional context data (inventory metadata, etc.)
        '''

**Parameter Standardization**: Consistent parameter names, types, and semantics 
across all processor implementations eliminate interface confusion.

**Type Safety**: Strong typing ensures compile-time validation of processor 
implementations and caller code.

**Extensibility**: Optional auxiliary data parameter provides extension point 
for processor-specific enhancements without breaking interface compatibility.

Capability Advertisement Patterns
-------------------------------------------------------------------------------

Processors advertise their capabilities through standardized metadata:

.. code-block:: python

    class ProcessorCapabilities( __.immut.DataclassObject ):
        ''' Processor capability advertisement. '''
        
        supported_inventory_types: frozenset[ str ]
        supported_filters: frozenset[ str ]  
        performance_characteristics: __.immut.Dictionary[ str, __.typx.Any ]
        operational_constraints: __.immut.Dictionary[ str, __.typx.Any ]

**Capability Discovery**: Dynamic capability discovery enables system adaptation 
to available processors and their operational characteristics.

**Filter Advertisement**: Processors advertise supported filter types, enabling 
validation of user requests before processing begins.

**Performance Profiles**: Capability information includes performance characteristics 
for operation planning and resource allocation.

Validation and Type Safety
-------------------------------------------------------------------------------

Strong validation ensures system reliability and provides clear error feedback:

**Interface Validation**: Compile-time and runtime validation of processor 
implementations against abstract base class contracts.

**Data Validation**: Multi-stage validation from raw inventory data through 
final object creation with detailed error context.

**Type Safety**: Comprehensive type annotations enable static analysis and 
provide clear interface contracts for processor implementers.

**Error Propagation**: Structured error handling with detailed context information 
supports debugging and system monitoring.

Implementation Outline
===============================================================================

Processor-Specific Data Source Handling Patterns
-------------------------------------------------------------------------------

Inventory processors handle diverse data source formats through specialized 
parsing and validation strategies:

**Data Source Diversity**: Processors accommodate various inventory formats including 
binary files, JSON documents, XML structures, and custom text formats.

**Parsing Strategies**: Format-appropriate parsing techniques including streaming 
parsers for large files, validation schemas for structured data, and error 
recovery mechanisms for malformed inputs.

**Performance Optimization**: Memory-efficient processing techniques including 
lazy loading, incremental parsing, and selective data extraction based on 
query requirements.

Format-Specific Object Creation Strategies
-------------------------------------------------------------------------------

Object creation strategies vary by inventory format while maintaining universal 
output consistency:

**Metadata Normalization**: Translation of format-specific metadata into universal 
object fields while preserving format-specific details in structured containers.

**Attribution Strategies**: Consistent source attribution patterns that capture 
complete provenance information including processor type, source location, and 
format-specific identifiers.

**Self-Formatting Integration**: Object creation includes formatting method 
implementation that understands format-specific semantics and presentation 
requirements.

Detection Methodology and Validation Approaches
-------------------------------------------------------------------------------

Detection implementations use format-appropriate validation and confidence 
assessment techniques:

**Probe Strategies**: Sequential or parallel probing of standard and alternative 
inventory locations using format-specific URL patterns.

**Validation Criteria**: Format-appropriate structural validation including 
schema compliance, content quality assessment, and compatibility verification.

**Confidence Calibration**: Consistent confidence scoring based on validation 
results, content quality metrics, and format-specific quality indicators.

Content Integration and Search Patterns
-------------------------------------------------------------------------------

Integration with search and content systems through standardized interfaces:

**Search Integration**: Universal object interfaces enable format-agnostic 
search operations while preserving format-specific search capabilities through 
metadata containers.

**Content Coordination**: Capability-based filtering ensures inventory objects 
are only processed by compatible structure processors for content extraction.

**Multi-Source Coordination**: Source attribution enables tracking and coordination 
across multiple inventory sources for comprehensive documentation coverage.

Performance Optimization Strategies
-------------------------------------------------------------------------------

Performance optimization approaches tailored to inventory processing characteristics:

**Caching Strategies**: Multi-level caching including detection results, raw 
inventory data, and formatted objects with appropriate TTL management.

**Lazy Loading**: Deferred processing of inventory data until required by 
specific operations to minimize initial load times.

**Batch Processing**: Efficient batch operations for large inventory processing 
tasks with memory management and progress tracking.

Scalability and Extension Considerations
-------------------------------------------------------------------------------

Design patterns support system scalability and future enhancement:

**Memory Management**: Bounded memory usage through streaming processing, 
pagination, and selective data loading based on operational requirements.

**Processor Extensibility**: Clear extension points for new inventory formats 
through abstract base class implementation and capability advertisement.

**Configuration Management**: Flexible configuration systems supporting 
processor-specific parameters and operational tuning.

Example Implementation Skeletons
-------------------------------------------------------------------------------

**Sphinx Processor Outline**:
- ``objects.inv`` binary file handling with decompression and parsing
- Domain/role semantic understanding for object categorization
- Priority-based object ranking and presentation
- Cross-reference resolution for documentation linking
- Theme-independent inventory processing

**MkDocs Processor Outline**:
- ``search_index.json`` file handling with page-level extraction
- Content preview generation from embedded text
- Navigation context extraction from page hierarchy
- Alternative format support for theme-specific variations
- Hybrid content strategy coordination

Extension Points and Future Processors
===============================================================================

Plugin Architecture Patterns
-------------------------------------------------------------------------------

Consistent processor interfaces enable third-party inventory processors through 
well-defined extension patterns:

**Interface Compliance**: New processors implement standard abstract base classes 
with consistent method signatures and behavioral contracts.

**Capability Integration**: Processor capability advertisement enables system 
integration without core code modifications.

**Registration Mechanisms**: Dynamic processor discovery and registration through 
plugin management systems or configuration-based registration.

Custom Processor Development
-------------------------------------------------------------------------------

Clear development patterns support custom inventory processor creation:

**Development Guidelines**: Comprehensive documentation of interface requirements, 
performance expectations, and integration patterns.

**Testing Frameworks**: Standardized testing patterns and validation suites 
for processor development and verification.

**Reference Implementations**: Well-documented reference processors demonstrate 
implementation patterns and best practices.

Capability Evolution Support
-------------------------------------------------------------------------------

System design accommodates processor capability enhancement over time:

**Backward Compatibility**: Interface evolution strategies that maintain compatibility 
with existing processors while enabling enhanced functionality.

**Capability Versioning**: Version management for processor capabilities enabling 
gradual system enhancement and feature adoption.

**Feature Negotiation**: Dynamic feature negotiation between system components 
based on advertised processor capabilities.

Performance Optimization Strategies
-------------------------------------------------------------------------------

Extension points support continued performance optimization:

**Custom Caching**: Processor-specific caching strategies optimized for particular 
inventory formats and access patterns.

**Parallel Processing**: Opportunities for parallel inventory processing with 
appropriate synchronization and coordination mechanisms.

**Resource Management**: Adaptive resource allocation based on processor 
characteristics and operational requirements.

This inventory processor architecture provides a comprehensive foundation for 
format-agnostic inventory operations while maintaining clean separation between 
universal interfaces and format-specific implementations. The design supports 
extensibility, performance optimization, and consistent user experience across 
diverse documentation source formats.