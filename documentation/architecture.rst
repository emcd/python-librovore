Architecture
============

Extension Management System
----------------------------

The extension management system follows a layered architecture with clear separation of concerns:

.. code-block:: text

    ┌─────────────┐     ┌──────────────┐     ┌─────────────┐
    │    CLI      │────▶│   xtnsmgr    │────▶│  xtnsapi    │
    │             │     │              │     │             │
    │ - Loads     │     │ - Manages    │     │ - Provides  │
    │   processors│     │   processors │     │   API for   │
    │ - Invokes   │     │ - Installs   │     │   extensions│
    │   server    │     │   packages   │     │             │
    └─────────────┘     └──────────────┘     └─────────────┘
            │                                        ▲
            │           ┌──────────────┐             │
            └──────────▶│   server     │─────────────┘
                        │              │
                        │ - Serves MCP │
                        │ - Uses APIs  │
                        └──────────────┘

Components
~~~~~~~~~~

**CLI Layer**
  - Entry point for application
  - Loads and registers processors based on configuration
  - Invokes server with prepared environment

**Extension Manager (xtnsmgr)**
  - Manages processor lifecycle
  - Handles external package installation via ``uv``
  - Provides import isolation and cache management
  - Configuration-driven processor loading

**Extension API (xtnsapi)**
  - Clean interface for extension developers
  - Processor registry and validation
  - Type definitions and interfaces

**Server Layer**
  - MCP server implementation
  - Uses registered processors via xtnsapi
  - Focuses solely on serving, not processor management

Dependency Flow
~~~~~~~~~~~~~~~

The system maintains proper dependency direction:

- ``xtnsmgr`` uses ``xtnsapi`` (management layer uses API layer)
- ``xtnsapi`` does NOT import ``xtnsmgr`` (API layer independent of management)
- Extensions interact only with ``xtnsapi`` (clean separation)
- Server uses ``xtnsapi`` for processor access (service layer uses API)

Key Principles
~~~~~~~~~~~~~~

**Configuration-Driven**
  All processor loading respects configuration files and enablement/disablement settings.
  No hardcoded fallbacks that bypass user configuration.

**Separation of Concerns**
  Each layer has a single, well-defined responsibility.
  Management concerns are separated from API concerns.

**Extension Isolation**
  External extensions are installed in isolated environments with proper import path management.

Search Architecture
-------------------

The search architecture has been refactored to eliminate duplicate search logic and follows a clean separation of concerns between universal search logic and processor-specific data extraction:

**Current Clean Architecture**:

.. code-block:: text

    ┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
    │   functions.py  │───▶│ inventory.py     │───▶│   search.py     │
    │                 │    │                  │    │                 │
    │ Query handling  │    │ Structural       │    │ Term matching   │
    │                 │    │ filtering only   │    │ (exact/regex/   │
    │                 │    │ (domain/role/    │    │  fuzzy)         │
    │                 │    │  priority)       │    │                 │
    └─────────────────┘    └──────────────────┘    └─────────────────┘

The search architecture follows a clear separation of concerns between universal search logic and processor-specific data extraction:

.. code-block:: text

    ┌─────────────────────────────────────────────────────────────┐
    │                    FUNCTIONS LAYER                          │
    │  - Universal search matching (fuzzy, regex, exact)         │
    │  - Search scoring and ranking (via search.py)              │
    │  - Result formatting and metadata                          │
    │  - API orchestration and business logic                    │
    └─────────────────────────────────────────────────────────────┘
                              │
                              ▼
    ┌─────────────────────────────────────────────────────────────┐
    │                 PROCESSOR LAYER                             │
    │  - Data extraction (extract_filtered_inventory)            │
    │  - Processor-specific filtering (domain, role, priority)   │
    │  - Documentation fetching (extract_documentation_for_objects)│
    │  - Source-specific logic (Sphinx vs MkDocs vs ...)        │
    └─────────────────────────────────────────────────────────────┘

Search Flow
~~~~~~~~~~~

1. **Functions Layer** receives user query with search behaviors and processor filters
2. **Processor Layer** extracts and filters objects using processor-specific logic
3. **Functions Layer** applies universal search matching via ``search.filter_by_name()``
4. **Processor Layer** fetches documentation content for top candidates (if needed)
5. **Functions Layer** formats and returns results with consistent structure

**Benefits**:
  - Consistent search behavior across all processors
  - Centralized search algorithms (rapidfuzz-based)
  - Processors focus purely on data extraction/filtering
  - Easy to add new processors without reimplementing search logic