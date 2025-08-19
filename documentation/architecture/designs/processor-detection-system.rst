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

Exception Hierarchy
-------------------------------------------------------------------------------

**Current Exceptions:**
- ``ProcessorInavailability``: No processor found above confidence threshold
- Individual processor failures are caught and logged, not propagated

**Recommended Future Enhancements:**

.. code-block:: python

    class DetectionFailure( Omnierror, RuntimeError ):
        ''' Processor detection operation failed. '''
        
        def __init__( 
            self, source: str, genus: str, processor_errors: __.cabc.Mapping[ str, Exception ] 
        )

    class ProcessorInavailability( Omnierror, RuntimeError ):  
        ''' No processor found to handle source. '''
        
        def __init__( 
            self, source: str, genus: str, attempted_processors: __.cabc.Sequence[ str ] 
        )

Error Recovery Strategies
-------------------------------------------------------------------------------

**Processor Failure Recovery:**
- Continue selection with remaining functional processors
- Log processor-specific errors for debugging
- Maintain detection attempts in cache for diagnostic purposes

**Cache Failure Recovery:**  
- Fresh detection execution on cache corruption or errors
- Graceful degradation to uncached operation
- Error logging with cache rebuild capability

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

Error Handling Evolution
===============================================================================

Current Error Handling State
-------------------------------------------------------------------------------

**Exception Design:**
The current system uses a single ``ProcessorInavailability`` exception raised 
when no processor exceeds the confidence threshold. The exception provides 
minimal context, containing only a generic class name identifier.

**Current Error Flow:**
1. Detection functions attempt processor selection
2. Failed detection raises ``ProcessorInavailability( genus_name )``
3. CLI and MCP interfaces format generic error messages
4. Users receive non-specific guidance regardless of failure cause

**Current Error Messages:**
- ``"No processor found to handle source: inventory"``
- ``"No processor found to handle source: structure"``
- ``"Cannot access documentation inventory: {source}"``

**Limitations:**
- No distinction between genus-specific failure modes
- No actionable guidance for common URL pattern issues
- Duplicate error formatting logic across interfaces
- No automatic recovery for common documentation site patterns

Desired Error Handling State
-------------------------------------------------------------------------------

**Enhanced Exception Design:**

.. code-block:: python

    class ProcessorInavailability( Omnierror, RuntimeError ):
        ''' No processor found to handle source with enhanced context. '''
        
        def __init__(
            self,
            source: str,
            genus: __.Absential[ str ] = __.absent,
            url_patterns_attempted: bool = False,
            final_error_type: __.Absential[ str ] = __.absent,
        )

**Enhanced Error Messages:**
- **Inventory Detection**: ``"No compatible inventory format detected at this documentation source"``
- **URL Pattern Intelligence**: ``"No inventory found - attempted common URL patterns"``
- **Enhanced Accessibility**: Context-aware guidance based on error type
- **Genus Clarity**: Clear distinction between inventory and structure failures

**Automatic URL Pattern Extension:**
Detection system automatically attempts common documentation URL patterns 
when base URL detection fails:

.. code-block:: python

    async def detect_with_url_patterns(
        auxdata: _state.Globals,
        source: str, /,
        genus: _interfaces.ProcessorGenera,
    ) -> _processors.Detection:
        # Try base URL first (current behavior)
        try: return await detect( auxdata, source, genus )
        except ProcessorInavailability:
            # Attempt common patterns for inventory detection
            if genus == _interfaces.ProcessorGenera.Inventory:
                patterns = [ '/en/latest/', '/latest/', '/main/' ]
                for pattern in patterns:
                    extended_url = urljoin( source, pattern )
                    try: return await detect( auxdata, extended_url, genus )
                    except ProcessorInavailability: continue
            # Re-raise with pattern attempt context
            raise ProcessorInavailability(
                source, genus = genus.name.lower( ), 
                url_patterns_attempted = True )

**Centralized Error Formatting:**
Functions layer provides consistent error formatting for both CLI and MCP:

.. code-block:: python

    def format_processor_inavailability(
        exc: ProcessorInavailability
    ) -> __.immut.Dictionary[ str, str ]:
        if exc.genus == 'inventory':
            return format_inventory_inavailability( exc )
        elif exc.genus == 'structure':  
            return format_structure_inavailability( exc )
        return format_generic_inavailability( exc )

**Cache Integration:**
When URL pattern extension discovers working URLs, detection cache entries 
are updated to use the successful URL for future requests, improving 
performance and user experience.

**Implementation Phases:**
1. **Enhanced Exception Context**: Add contextual fields to ``ProcessorInavailability``
2. **Automatic URL Patterns**: Implement intelligent URL extension for inventory detection  
3. **Centralized Error Formatting**: Create functions layer error message generation
4. **URL Pattern Detection**: Add utilities for documentation site pattern recognition

This detection system design provides robust, extensible automated processor 
selection while maintaining clean architectural boundaries and established 
project practices compliance.