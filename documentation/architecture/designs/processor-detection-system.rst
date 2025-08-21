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
Processor Detection System Design
*******************************************************************************

Overview
===============================================================================

The processor detection system provides automated selection of appropriate 
inventory and structure processors for documentation sources. The design 
implements confidence-based scoring with TTL-based caching to balance 
performance with accuracy and data freshness.

Architecture
===============================================================================

Design Principles
-------------------------------------------------------------------------------

**Genus-Based Separation**
  Inventory processors and structure processors operate in separate detection 
  pipelines, allowing independent evolution and different selection criteria.
  Each genus maintains its own cache and processor registry.

**Confidence-Based Selection**
  Processors return numerical confidence scores (0.0-1.0). Only processors 
  exceeding ``CONFIDENCE_THRESHOLD_MINIMUM`` (0.5) are considered, with highest 
  confidence and registration order as stable tiebreaker.

**Immutable Data Structures**
  All detection results use immutable containers (``__.immut.Dictionary``, 
  ``tuple``) following project practices for thread safety and predictable 
  behavior.

**Wide Parameter, Narrow Return Pattern**
  Public functions accept abstract base classes for parameters and return 
  specific concrete types, following established project practices.

Component Structure
-------------------------------------------------------------------------------

**Detection Orchestration** (``detection.py``)
  Central coordination of processor selection across inventory and structure 
  genera. Provides both high-level convenience functions and low-level 
  extensible functions for custom processor mappings.

**Cache Management**
  TTL-based caching system with lazy expiration cleanup. Separate cache 
  instances per processor genus enable different configuration and evolution 
  patterns.

**Processor Integration**
  Abstract base classes in ``processors.py`` define detection contracts. 
  Format-specific implementations in ``inventories/`` and ``structures/`` 
  subpackages provide concrete detection logic.

Interface Specifications
===============================================================================

Primary Detection Functions
-------------------------------------------------------------------------------

.. code-block:: python

    async def detect(
        auxdata: _state.Globals,
        source: str, /,
        genus: _interfaces.ProcessorGenera, *,
        processor_name: __.Absential[ str ] = __.absent,
    ) -> _processors.Detection

    async def detect_inventory(
        auxdata: _state.Globals,
        source: str, /, *,
        processor_name: __.Absential[ str ] = __.absent,
    ) -> _processors.InventoryDetection

    async def detect_structure(
        auxdata: _state.Globals,  
        source: str, /, *,
        processor_name: __.Absential[ str ] = __.absent,
    ) -> _processors.StructureDetection

**Contract:**
- Returns highest-confidence processor detection above threshold
- Raises ``ProcessorInavailability`` if no suitable processor found
- Bypasses detection when specific ``processor_name`` provided
- Maintains detection results in genus-specific cache

Cache Access Functions
-------------------------------------------------------------------------------

.. code-block:: python

    async def access_detections(
        auxdata: _state.Globals,
        source: str, /, *,
        genus: _interfaces.ProcessorGenera
    ) -> tuple[
        _processors.DetectionsByProcessor,
        __.Absential[ _processors.Detection ]
    ]

    async def access_detections_ll(
        auxdata: _state.Globals,
        source: str, /, *,
        cache: DetectionsCache,
        processors: __.cabc.Mapping[ str, _processors.Processor ],
    ) -> tuple[
        _processors.DetectionsByProcessor,
        __.Absential[ _processors.Detection ]
    ]

**Contract:**
- Returns all processor detections plus optimal selection
- Executes fresh detection if cache miss or expiration
- Low-level variant accepts arbitrary processor mapping for extensibility
- Never raises exceptions; returns ``__.absent`` for missing optimal detection

Data Structures
===============================================================================

Detection Cache Design
-------------------------------------------------------------------------------

.. code-block:: python

    class DetectionsCacheEntry( __.immut.DataclassObject ):
        detections: __.cabc.Mapping[ str, _processors.Detection ]
        timestamp: float
        ttl: int
        
        @property
        def detection_optimal( self ) -> __.Absential[ _processors.Detection ]
        
        def invalid( self, current_time: float ) -> bool

    class DetectionsCache( __.immut.DataclassObject ):
        ttl: int = 3600
        _entries: dict[ str, DetectionsCacheEntry ] = __.dcls.field( 
            default_factory = dict[ str, DetectionsCacheEntry ] )
        
        def access_detections( 
            self, source: str 
        ) -> __.Absential[ _processors.DetectionsByProcessor ]
        
        def access_detection_optimal(
            self, source: str
        ) -> __.Absential[ _processors.Detection ]
        
        def add_entry(
            self, source: str, detections: _processors.DetectionsByProcessor
        ) -> __.typx.Self

**Design Features:**
- TTL-based expiration with configurable timeouts per cache instance
- Lazy cleanup on access operations to minimize overhead  
- Pre-computed optimal selection stored in cache entries
- Method chaining support through ``__.typx.Self`` returns

Type Aliases
-------------------------------------------------------------------------------

.. code-block:: python

    DetectionsByProcessor: __.typx.TypeAlias = __.cabc.Mapping[ 
        str, _processors.Detection ]

**Purpose:** Provides semantic clarity for function signatures and return types 
while maintaining wide parameter acceptance patterns.

Behavioral Contracts
===============================================================================

Processor Selection Contract
-------------------------------------------------------------------------------

**Selection Algorithm:**
1. Execute all processors in genus-specific registry on source
2. Filter results to confidence >= ``CONFIDENCE_THRESHOLD_MINIMUM`` (0.5)
3. Select highest confidence; use registration order for ties
4. Return ``__.absent`` if no processors meet confidence threshold

**Error Handling:**
- Individual processor detection failures are logged but not propagated
- Failed processors are excluded from selection consideration
- Selection continues with remaining successful processors

Cache Management Contract
-------------------------------------------------------------------------------

**Cache Population:**
- Fresh detection triggered on cache miss or TTL expiration
- All genus processors executed in parallel (future enhancement)
- Results cached regardless of optimal selection success

**Cache Access:**
- Thread-safe read operations using immutable data structures
- Expired entries removed lazily on access
- Missing or expired entries trigger fresh processor execution

**TTL Management:**
- Configurable per-cache instance (default: 3600 seconds)
- Based on cache entry creation timestamp
- Independent expiration per source URL

Extension Points
===============================================================================

Processor Genus Extension
-------------------------------------------------------------------------------

**Adding New Processor Types:**
1. Extend ``ProcessorGenera`` enumeration in ``interfaces.py``
2. Add genus-specific cache instance in ``detection.py``
3. Update genus dispatch in ``access_detections`` function
4. Register processors in genus-specific registry

**Processor Implementation Requirements:**
- Implement ``detect`` method returning confidence-scored ``Detection``
- Handle detection failures gracefully (should not raise exceptions)
- Return confidence score in range 0.0-1.0
- Provide processor capabilities metadata

Cache Strategy Extension
-------------------------------------------------------------------------------

**Custom Cache Implementations:**
- ``DetectionsCache`` interface supports alternative implementations
- Size-based eviction strategies can be added via subclassing  
- Different TTL strategies per processor type or source pattern
- External cache stores (Redis, etc.) through interface compliance

**Performance Optimization:**
- Parallel processor execution via async fanout (marked TODO)
- Processor-specific timeout configuration
- Cache warming strategies for frequently accessed sources

Error Handling Design
===============================================================================

Structured Error Response System
-------------------------------------------------------------------------------

The system implements a structured error response pattern where the functions layer
handles all processor detection exceptions and returns user-friendly structured
responses. This design eliminates error interpretation at interface layers while
providing consistent, actionable error messaging.

**Response Structure:**

.. code-block:: python

    ErrorResponse: __.typx.TypeAlias = __.immut.Dictionary[ str, __.typx.Any ]
    
    def _produce_inventory_error_response( 
        source: str, 
        attempted_patterns: __.Absential[ __.cabc.Sequence[ str ] ] = __.absent 
    ) -> ErrorResponse
    
    def _produce_structure_error_response( source: str ) -> ErrorResponse
    
    def _produce_generic_error_response( 
        source: str, genus: str 
    ) -> ErrorResponse

**Error Response Content:**
- Structured responses include error type, user-friendly title, detailed message
- Actionable suggestions provided based on specific failure scenarios
- Clear distinction between inventory and structure detection failures
- Pre-formatted messages eliminate interface layer error interpretation

Automatic URL Pattern Extension
-------------------------------------------------------------------------------

The detection system implements universal URL pattern extension that applies to
all processor types. When detection fails at the original URL, the system
automatically probes common documentation site patterns before reporting failure.

**Universal Pattern Extension:**
- Applies to both inventory and structure processors uniformly
- Documentation content location affects both inventory files and content uniformly
- Common patterns include ``/en/latest/``, ``/latest/``, ``/main/``, etc.
- Working URLs are cached in global redirects mapping for future operations

**Redirects Cache Integration:**

.. code-block:: python

    _url_redirects_cache: dict[ str, str ]  # original_url → working_url
    
    def normalize_location( location: str ) -> str

**Transparent URL Resolution:**
- All operations automatically use working URLs from redirects cache
- Users receive actual working URLs as canonical source in responses
- Cache updates ensure consistent URL usage across all subsequent operations

Exception Hierarchy
-------------------------------------------------------------------------------

**Core Exceptions:**

.. code-block:: python

    class ProcessorInavailability( Omnierror, RuntimeError ):
        ''' No processor found to handle source. '''
        
        def __init__( 
            self, source: str, genus: str, 
            attempted_processors: __.cabc.Sequence[ str ] 
        )

    class DetectionFailure( Omnierror, RuntimeError ):
        ''' Processor detection operation failed. '''
        
        def __init__( 
            self, source: str, genus: str, 
            processor_errors: __.cabc.Mapping[ str, Exception ] 
        )

**Error Propagation:**
- Individual processor failures are caught and logged, not propagated upward
- Functions layer catches all detection exceptions and produces structured responses
- Interface layers receive pre-formatted error information, never raw exceptions

Error Recovery Strategies
-------------------------------------------------------------------------------

**Processor Failure Recovery:**
- Continue selection with remaining functional processors after individual failures
- Log processor-specific errors for debugging without disrupting detection flow
- Maintain detection attempts in cache for diagnostic and performance purposes

**URL Pattern Recovery:**
- Automatic pattern extension discovers working URLs for failed base URLs
- Successful redirects are cached globally for performance optimization
- Pattern extension applies universally to all processor types

**Cache Failure Recovery:**  
- Fresh detection execution triggered on cache corruption or access errors
- Graceful degradation to uncached operation maintains system availability
- Error logging with cache rebuild capability supports system maintenance

Design Trade-offs
===============================================================================

Performance vs. Accuracy
-------------------------------------------------------------------------------

**Caching Trade-offs:**
- **Advantage:** Significant performance improvement for repeated source access
- **Advantage:** Reduces external service load (HTTP requests, file system)  
- **Disadvantage:** Cached results may become stale for dynamic documentation
- **Mitigation:** Configurable TTL values balance freshness vs. performance

**Confidence Threshold Trade-offs:**
- **Advantage:** Prevents selection of unreliable processors
- **Advantage:** Consistent, objective selection criteria
- **Disadvantage:** Fixed threshold may not suit all processor types
- **Future Enhancement:** Processor-specific or adaptive thresholds

Memory vs. Functionality  
-------------------------------------------------------------------------------

**Cache Memory Trade-offs:**
- **Advantage:** Fast access to detection results without re-execution
- **Disadvantage:** Memory usage grows with unique source URLs
- **Mitigation:** TTL-based expiration provides bounded memory usage
- **Future Enhancement:** Size-based LRU eviction strategies

**Immutability Trade-offs:**
- **Advantage:** Thread-safe cache access without locking
- **Advantage:** Predictable behavior and easier debugging
- **Disadvantage:** Higher memory usage than mutable alternatives
- **Assessment:** Acceptable trade-off for architectural benefits

Multiple Inventory Handling Strategy
===============================================================================

Processor Precedence Design
-------------------------------------------------------------------------------

When multiple inventory processors successfully detect inventory sources for the 
same documentation site, the system applies a precedence-based selection strategy 
to maintain consistency and user predictability.

**Detection Precedence Order:**
1. **Sphinx Inventory Processor** (``objects.inv`` files)
2. **MkDocs Inventory Processor** (``search_index.json`` files)
3. **Future processors** in registration order

**Precedence Selection Algorithm:**

.. code-block:: python

    def select_optimal_detection(
        detections: __.cabc.Mapping[ str, _processors.Detection ]
    ) -> __.Absential[ _processors.Detection ]:
        ''' Selects optimal detection using precedence and confidence. '''
        # 1. Filter detections meeting confidence threshold
        # 2. Apply processor precedence order for qualified detections
        # 3. Use highest confidence as tiebreaker within same precedence level
        # 4. Return __.absent if no detections meet threshold

**Design Rationale:**
- **Consistency**: Predictable processor selection across documentation sites
- **Granularity**: Sphinx inventories provide API-level symbol granularity
- **Completeness**: MkDocs search indices provide page-level content coverage
- **Extensibility**: Registration order precedence supports future processor types

Inventory Content Coordination
-------------------------------------------------------------------------------

For sites with multiple detected inventories, the system coordinates content 
operations to leverage the selected inventory processor while maintaining 
architectural separation between inventory and structure processing.

**Content Operation Coordination:**
- Selected inventory processor determines object enumeration and filtering
- Structure processors operate independently on content extraction
- Content queries use inventory-selected URIs to guide structure processor operations
- No cross-processor inventory merging to maintain architectural boundaries

**Cache Strategy:**
- Detection cache stores all successful detections per processor type
- Optimal detection selection cached separately from individual processor results
- Cache entries track processor precedence decisions for consistency
- TTL expiration applies uniformly to all cached detection results

This detection system design provides robust, extensible automated processor 
selection while maintaining clean architectural boundaries and established 
project practices compliance.