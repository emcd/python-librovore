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
System Overview
*******************************************************************************

The project is a documentation processing and search system that provides both CLI and MCP server interfaces for accessing structured documentation. The system follows a layered plugin architecture with clear separation of concerns between universal search logic, processor-specific data extraction, and extension management.

High-Level Architecture
===============================================================================

Component Relationships
-------------------------------------------------------------------------------

The system is organized into four primary layers:

.. code-block:: text

    ┌─────────────────────────────────────────────────────────────┐
    │                    INTERFACE LAYER                          │
    │  ┌─────────────┐                   ┌─────────────┐          │
    │  │    CLI      │                   │ MCP Server  │          │
    │  │  (cli.py)   │                   │ (server.py) │          │
    │  └─────────────┘                   └─────────────┘          │
    └─────────────────────────────────────────────────────────────┘
                              │
                              ▼
    ┌─────────────────────────────────────────────────────────────┐
    │                 BUSINESS LOGIC LAYER                        │
    │  - Universal search algorithms (search.py)                 │
    │  - Query orchestration (functions.py)                      │
    │  - Result formatting and metadata                          │
    │  - Cross-processor operations                               │
    └─────────────────────────────────────────────────────────────┘
                              │
                              ▼
    ┌─────────────────────────────────────────────────────────────┐
    │                  PROCESSOR LAYER                            │
    │  - Detection system (detection.py)                         │
    │  - Processor abstractions (processors.py)                  │
    │  - Format-specific implementations                          │
    │  - Content extraction and filtering                         │
    └─────────────────────────────────────────────────────────────┘
                              │
                              ▼
    ┌─────────────────────────────────────────────────────────────┐
    │                EXTENSION MANAGEMENT LAYER                   │
    │  - Extension API (xtnsapi.py)                              │
    │  - Extension manager (xtnsmgr/)                            │
    │  - Configuration and lifecycle management                   │
    │  - Package installation and isolation                       │
    └─────────────────────────────────────────────────────────────┘

Data Flow Architecture
-------------------------------------------------------------------------------

The system processes documentation queries through a well-defined flow:

.. code-block:: text

    User Request (CLI/MCP)
           │
           ▼
    ┌─────────────────┐
    │ Query Handling  │ ◄─── Functions Layer
    │ (functions.py)  │      - Validates parameters
    └─────────────────┘      - Orchestrates operations
           │
           ▼
    ┌─────────────────┐
    │ Detection       │ ◄─── Detection System
    │ (detection.py)  │      - Processor selection
    └─────────────────┘      - Confidence scoring
           │
           ▼
    ┌─────────────────┐
    │ Data Extraction │ ◄─── Processor Layer
    │ (processors)    │      - Format-specific logic
    └─────────────────┘      - Inventory filtering
           │
           ▼
    ┌─────────────────┐
    │ Search Engine   │ ◄─── Universal Search
    │ (search.py)     │      - Fuzzy/regex/exact matching
    └─────────────────┘      - Score ranking
           │
           ▼
    ┌─────────────────┐
    │ Content Fetch   │ ◄─── Structure Processors
    │ (structures/)   │      - HTML extraction
    └─────────────────┘      - Markdown conversion
           │
           ▼
    ┌─────────────────┐
    │ Result Format   │ ◄─── Functions Layer
    │ & Return        │      - JSON/Markdown output
    └─────────────────┘      - Metadata aggregation

Major Components
===============================================================================

Interface Layer
-------------------------------------------------------------------------------

**Command Line Interface (cli.py)**
  - Provides human-accessible interface for testing and standalone use
  - Supports all core operations: detection, inventory queries, content search
  - Handles argument parsing with tyro framework
  - Formats output in JSON or Markdown for different use cases

**MCP Server (server.py)**
  - Implements Model Context Protocol for AI agent integration
  - Uses FastMCP framework for JSON schema generation
  - Provides tools: query_inventory, query_content, summarize_inventory
  - Supports server restart functionality for development workflows

Business Logic Layer
-------------------------------------------------------------------------------

**Core Functions (functions.py)**
  - Contains shared business logic between CLI and MCP interfaces
  - Orchestrates complex multi-step operations
  - Handles error aggregation and result formatting
  - Provides consistent API surface for different interfaces

**Universal Search Engine (search.py)**
  - Centralized search algorithms using rapidfuzz for fuzzy matching
  - Supports exact string matching and regex pattern matching
  - Provides consistent scoring and ranking across all processors
  - Returns structured SearchResult objects with match metadata

**Detection System (detection.py)**
  - Automatic processor selection based on documentation site characteristics
  - Confidence-based scoring with configurable thresholds
  - Caching of detection results with TTL management
  - Support for both inventory and structure processor detection

Processor Layer
-------------------------------------------------------------------------------

**Processor Abstractions (processors.py)**
  - Abstract base classes: Processor, Detection, InventoryDetection, StructureDetection
  - Protocol-based interfaces for type safety and extensibility
  - Capability advertisement system for dynamic feature discovery
  - Clear separation between inventory extraction and structure processing

**Format-Specific Processors**
  - **Sphinx Inventory (inventories/sphinx/)**: Objects.inv parsing, domain/role filtering
  - **Sphinx Structure (structures/sphinx/)**: HTML extraction, Markdown conversion, theme support
  - **MkDocs Structure (structures/mkdocs/)**: Material theme support, mkdocstrings integration

Extension Management Layer
-------------------------------------------------------------------------------

**Extension API (xtnsapi.py)**
  - Clean interface for extension developers
  - Re-exports core types and utilities
  - Provides stable API surface independent of internal changes
  - Supports processor registration and capability queries

**Extension Manager (xtnsmgr/)**
  - Package installation via uv with isolation
  - Dynamic import path management
  - Configuration-driven processor loading
  - Cache management for installed packages

Key Architectural Patterns
===============================================================================

Plugin Architecture
-------------------------------------------------------------------------------

The system uses a plugin-based architecture where processors are discovered and loaded dynamically:

- **Abstract base classes** define contracts for processors
- **Detection protocols** allow processors to advertise their capabilities  
- **Registry pattern** manages processor instances and metadata
- **Factory pattern** creates processor instances based on detection results

Layered Separation of Concerns
-------------------------------------------------------------------------------

Clear functional boundaries prevent cross-cutting concerns:

- **Interface layer** handles user interaction and protocol compliance
- **Business logic layer** implements domain logic and orchestration
- **Processor layer** handles format-specific data extraction
- **Extension layer** manages processor lifecycle and configuration

Search Strategy Pattern
-------------------------------------------------------------------------------

The search system implements strategy pattern for different matching modes:

- **Exact matching** for precise string searches
- **Regex matching** for pattern-based queries  
- **Fuzzy matching** with configurable thresholds using rapidfuzz
- **Pluggable scoring** allows custom relevance algorithms

Caching Strategy
-------------------------------------------------------------------------------

Multi-level caching improves performance and reduces external requests:

- **Detection caching** with TTL for processor selection results
- **URL caching** via aiohttp for HTTP requests
- **Package caching** for extension installations
- **Configurable TTL** values for different cache types

Deployment Architecture
===============================================================================

The system supports multiple deployment patterns:

**Standalone CLI Tool**
  - Single executable with all dependencies bundled
  - No external services required beyond network access
  - Configuration via command-line arguments or config files

**MCP Server**
  - Long-running server process for AI agent integration
  - Stateful caching for improved performance
  - Supports multiple concurrent client connections

**Library Integration**
  - Python package for embedding in larger applications
  - Clean API boundaries for custom integration patterns
  - Extension points for custom processors and data sources

Quality Attributes
===============================================================================

**Performance**
  - Sub-second response times for cached operations
  - Parallel processing for independent operations
  - Efficient memory usage through lazy loading patterns

**Reliability**
  - Graceful degradation when external services unavailable
  - Automatic retry with exponential backoff for network failures
  - Comprehensive error handling with meaningful messages

**Extensibility**
  - Plugin architecture supports new documentation formats
  - Protocol-based interfaces enable custom implementations
  - Configuration-driven processor selection and management

**Maintainability**
  - Clear separation of concerns across architectural layers
  - Comprehensive type annotations for static analysis
  - Consistent naming conventions and code organization