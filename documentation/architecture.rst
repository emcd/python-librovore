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