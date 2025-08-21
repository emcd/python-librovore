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
MkDocs Inventory Processor Design
*******************************************************************************

Overview
===============================================================================

The MkDocs inventory processor handles ``search_index.json`` files as inventory 
sources, enabling pure MkDocs sites without mkdocstrings to integrate with 
librovore's inventory-based architecture. This processor provides page-level 
object inventory extraction from MkDocs search indices.

Architecture Integration
===============================================================================

Processor Classification
-------------------------------------------------------------------------------

**Processor Type:** Inventory processor (``ProcessorGenera.Inventory``)
  - Extracts object inventories from MkDocs documentation sites
  - Operates in inventory detection pipeline alongside Sphinx inventory processor
  - Provides page-level granularity for documentation object enumeration

**Detection Priority:** Secondary to Sphinx inventory processor
  - Sphinx ``objects.inv`` files take precedence when both are detected
  - MkDocs search indices provide fallback inventory capability
  - Maintains consistent user experience through precedence-based selection

Component Architecture
-------------------------------------------------------------------------------

**Detection Component** (``inventories/mkdocs/detection.py``)
  - Implements ``MkDocsInventoryDetection`` class
  - Probes standard MkDocs search index locations
  - Validates JSON structure and content format
  - Returns confidence-scored detection results

**Main Processor** (``inventories/mkdocs/main.py``)
  - Implements ``MkDocsInventoryProcessor`` class
  - Inherits from base inventory processor interfaces
  - Parses and caches search index data structures
  - Provides standard inventory query operations

Data Source Specifications
===============================================================================

Search Index Structure
-------------------------------------------------------------------------------

The processor handles MkDocs search index files with standardized structure:

.. code-block:: json

    {
      "config": {
        "lang": ["en"],
        "separator": "[\\s\\-]+",
        "pipeline": ["stopWordFilter", "stemmer"]
      },
      "docs": [
        {
          "location": "api/",
          "title": "Developer Interface", 
          "text": "Full documentation content..."
        },
        {
          "location": "quickstart/",
          "title": "Quickstart",
          "text": "Getting started content..."
        }
      ]
    }

**Inventory Object Mapping:**
- **Object URI:** ``docs[].location`` field (relative page URLs)
- **Object Name:** ``docs[].title`` field (page titles)  
- **Content Source:** ``docs[].text`` field (embedded page content)

Detection Strategy
-------------------------------------------------------------------------------

**Probe Locations:** Sequential probing of standard search index paths:
1. ``/search/search_index.json`` (Material theme default)
2. ``/search_index.json`` (alternative root location)
3. ``/assets/search/search_index.json`` (theme-specific variants)

**Validation Requirements:**
- Valid JSON structure with ``docs`` array
- Each document entry must contain ``location`` and ``title`` fields
- Minimum threshold of document entries to qualify as valid inventory

**Confidence Scoring:**
- High confidence (0.9+) for well-structured indices with substantial content
- Medium confidence (0.7+) for minimal but valid indices
- Below threshold for malformed or empty indices

Interface Specifications  
===============================================================================

Detection Interface
-------------------------------------------------------------------------------

.. code-block:: python

    class MkDocsInventoryDetection( _processors.InventoryDetection ):
        ''' Detection results for MkDocs search index inventory. '''
        
        @property
        def processor_class( self ) -> type[ MkDocsInventoryProcessor ]
        
        @property  
        def capabilities( self ) -> __.immut.Dictionary[ str, __.typx.Any ]

Processor Interface
-------------------------------------------------------------------------------

.. code-block:: python

    class MkDocsInventoryProcessor( _processors.InventoryProcessor ):
        ''' Inventory processor for MkDocs search indices. '''
        
        def __init__(
            self,
            auxdata: _state.Globals,
            detection: MkDocsInventoryDetection
        )
        
        async def acquire_inventory(
            self
        ) -> __.immut.Dictionary[ str, InventoryObject ]
        
        async def query_inventory(
            self,
            term: str, *,
            search_behaviors: SearchBehaviors = SearchBehaviors( ),
            filters: __.cabc.Mapping[ str, __.typx.Any ] = __.immut.Dictionary( ),
            results_max: int = 10
        ) -> __.cabc.Sequence[ SearchResult ]

**Contract Specifications:**
- ``acquire_inventory`` returns mapping of object URI to inventory object
- ``query_inventory`` provides fuzzy/exact/regex search over page titles and locations  
- Search results include page-level objects with titles as display names
- Filtering support for location patterns and content characteristics

Inventory Object Structure
-------------------------------------------------------------------------------

.. code-block:: python

    class MkDocsInventoryObject( __.immut.DataclassObject ):
        ''' Inventory object from MkDocs search index. '''
        
        uri: str                    # Page location (relative URL)
        name: str                   # Page title  
        content_preview: str        # Truncated text content
        source_url: str            # Full URL to documentation page
        
        @property
        def display_name( self ) -> str
        
        @property 
        def object_type( self ) -> str  # Always 'page'

Search Integration
===============================================================================

Query Processing
-------------------------------------------------------------------------------

**Search Target Fields:**
- Primary matching against ``title`` fields for semantic relevance
- Secondary matching against ``location`` fields for URI-based queries  
- Tertiary matching against ``text`` content for comprehensive coverage

**Search Algorithm Integration:**
- Leverages universal search engine (``search.py``) for consistent scoring
- Fuzzy matching applied to page titles using rapidfuzz
- Regex pattern matching supported for location-based filtering
- Exact string matching for precise title or location queries

**Result Ranking Strategy:**
1. Title matches receive highest priority weighting
2. Location matches weighted for navigational relevance  
3. Content matches provide supplementary scoring
4. Result diversity maintains coverage across documentation sections

Content Operations Coordination
-------------------------------------------------------------------------------

**Structure Processor Integration:**
- MkDocs inventory provides page URIs for content extraction
- Existing MkDocs structure processor handles HTML content retrieval
- Inventory text field provides embedded content alternative
- Hybrid strategy: prefer embedded content, fallback to page fetching

**Content Strategy Specification:**

.. code-block:: python

    class ContentStrategy( __.typx.Enum ):
        ''' Content retrieval strategy for MkDocs inventory objects. '''
        
        EmbeddedPreferred = 'embedded_preferred'    # Use text field, fallback to page
        EmbeddedOnly = 'embedded_only'              # Use only text field content  
        PageFetchOnly = 'page_fetch_only'           # Always fetch from actual pages
        
    # Default configuration
    _CONTENT_STRATEGY_DEFAULT = ContentStrategy.EmbeddedPreferred

Performance Characteristics
===============================================================================

Caching Strategy
-------------------------------------------------------------------------------

**Search Index Caching:**
- Parsed search indices cached in inventory processor instances
- Cache invalidation aligned with detection cache TTL management  
- Memory usage proportional to documentation site size
- Lazy loading of content fields for large indices

**Detection Results Caching:**
- Detection results cached in standard processor detection cache
- Cache keys include search index file URL and modification metadata
- TTL expiration triggers fresh search index retrieval and parsing

Scalability Considerations
-------------------------------------------------------------------------------

**Large Index Handling:**
- Streaming JSON parsing for large search indices
- Pagination support for query results over configurable thresholds
- Memory-efficient object creation using dataclass patterns
- Content field truncation to manage memory usage per object

**Query Performance:**
- Search operations utilize indexed data structures for title/location queries
- Content searching applied selectively based on query patterns
- Result limiting prevents excessive memory allocation
- Fuzzy matching optimized through rapidfuzz performance characteristics

Extension Points
===============================================================================

Theme Variant Support
-------------------------------------------------------------------------------

**Detection Path Extension:**
- Additional probe paths configurable for theme-specific locations
- Detection logic extensible for alternative search index formats
- Version-specific handling for MkDocs format evolution

**Content Format Handling:**
- Pluggable parsing for search index format variations
- Content extraction strategies configurable per theme type
- Backward compatibility maintenance for format changes

Integration Testing
===============================================================================

**Validation Sites:**
- HTTPX documentation (pure MkDocs without mkdocstrings)
- Material theme documentation sites
- Standard MkDocs theme implementations
- Mixed inventory sites (both Sphinx and MkDocs indices)

**Test Coverage Requirements:**
- Detection accuracy across theme variants
- Query performance with large indices  
- Content retrieval strategy validation
- Multiple inventory precedence verification
- Cache behavior under various TTL configurations

This MkDocs inventory processor design extends librovore's inventory-based 
architecture to support pure MkDocs documentation sites while maintaining 
consistent user experience and architectural integrity.