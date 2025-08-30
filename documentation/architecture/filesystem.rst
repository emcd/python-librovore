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
Filesystem Organization
*******************************************************************************

This document describes the specific filesystem organization for the project,
showing how the standard organizational patterns are implemented for this
project's configuration. For the underlying principles and rationale behind
these patterns, see the `common architecture documentation
<https://raw.githubusercontent.com/emcd/python-project-common/refs/tags/docs-1/documentation/common/architecture.rst>`_.

Project Structure
===============================================================================

Root Directory Organization
-------------------------------------------------------------------------------

The project implements the standard filesystem organization:

.. code-block::

    python-librovore/
    ├── LICENSE.txt              # Project license
    ├── README.rst               # Project overview and quick start
    ├── pyproject.toml           # Python packaging and tool configuration
    ├── documentation/           # Sphinx documentation source
    ├── sources/                 # All source code
    ├── tests/                   # Test suites
    ├── data/                    # Redistributable data resources
    ├── pyinstaller.spec         # Executable packaging configuration
    └── .auxiliary/              # Development workspace

Source Code Organization
===============================================================================

Package Structure
-------------------------------------------------------------------------------

The main Python package follows the standard ``sources/`` directory pattern with a layered architecture:

.. code-block::

    sources/
    ├── librovore/                   # Main Python package
    │   ├── __/                      # Centralized import hub
    │   │   ├── __init__.py          # Re-exports core utilities
    │   │   ├── imports.py           # External library imports
    │   │   ├── doctab.py            # Documentation table utilities
    │   │   ├── inscription.py       # Logging and instrumentation utilities
    │   │   ├── interfaces.py        # Common interface definitions
    │   │   └── nomina.py            # Project-specific naming constants
    │   ├── __init__.py              # Package entry point
    │   ├── py.typed                 # Type checking marker
    │   ├── __main__.py              # CLI entry point for `python -m librovore`
    │   │
    │   │   # Interface Layer
    │   ├── cli.py                   # Command-line interface implementation
    │   ├── server.py                # MCP server implementation
    │   │
    │   │   # Business Logic Layer  
    │   ├── functions.py             # Core business logic shared between interfaces
    │   ├── results.py               # Result data structures and serialization
    │   ├── search.py                # Universal search engine with fuzzy/exact/regex
    │   ├── detection.py             # Processor detection and selection system
    │   │
    │   │   # Processor Layer
    │   ├── processors.py            # Abstract processor base classes and protocols
    │   ├── inventories/             # Inventory extraction processors
    │   │   ├── __.py                # Subpackage import hub
    │   │   ├── __init__.py
    │   │   ├── sphinx/              # Sphinx objects.inv processing
    │   │   │   ├── __.py            # Subpackage import hub
    │   │   │   ├── __init__.py
    │   │   │   ├── detection.py     # Sphinx inventory detection logic
    │   │   │   └── main.py          # Sphinx inventory processor implementation
    │   │   └── mkdocs/              # MkDocs search index processing
    │   │       ├── __.py            # Subpackage import hub
    │   │       ├── __init__.py
    │   │       ├── detection.py     # MkDocs inventory detection logic
    │   │       └── main.py          # MkDocs inventory processor implementation
    │   ├── structures/              # Content extraction processors  
    │   │   ├── __.py                # Subpackage import hub
    │   │   ├── __init__.py
    │   │   ├── sphinx/              # Sphinx HTML content processing
    │   │   │   ├── __.py            # Subpackage import hub
    │   │   │   ├── __init__.py
    │   │   │   ├── detection.py     # Sphinx structure detection
    │   │   │   ├── main.py          # Core Sphinx structure processor
    │   │   │   ├── conversion.py    # HTML to Markdown conversion
    │   │   │   ├── extraction.py    # Content extraction logic
    │   │   │   └── urls.py          # URL construction and resolution
    │   │   └── mkdocs/              # MkDocs content processing
    │   │       ├── __.py            # Subpackage import hub
    │   │       ├── __init__.py
    │   │       ├── detection.py     # MkDocs structure detection  
    │   │       ├── main.py          # Core MkDocs structure processor
    │   │       ├── conversion.py    # MkDocs-specific conversion logic
    │   │       └── extraction.py    # MkDocs content extraction
    │   │
    │   │   # Extension Management Layer
    │   ├── xtnsapi.py               # Extension developer API interface
    │   ├── xtnsmgr/                 # Extension manager subsystem
    │   │   ├── __.py                # Subpackage import hub
    │   │   ├── __init__.py          # Manager public interface
    │   │   ├── configuration.py     # Extension configuration management
    │   │   ├── installation.py      # Package installation via uv
    │   │   ├── importation.py       # Dynamic import management
    │   │   ├── cachemgr.py          # Extension package caching
    │   │   └── processors.py        # Processor lifecycle management
    │   │
    │   │   # Infrastructure Layer
    │   ├── interfaces.py            # Common enumerations and data structures
    │   ├── exceptions.py            # Package exception hierarchy
    │   ├── state.py                 # Global state and configuration management
    │   ├── cacheproxy.py            # HTTP caching and URL handling
    │   ├── urls.py                  # URL manipulation utilities
    │   ├── urlpatterns.py           # URL pattern matching and extension utilities
    │   │
    │   │   # Type Definitions
    │   └── _typedecls/              # External library type stubs

Architectural Layer Mapping
-------------------------------------------------------------------------------

The filesystem organization directly maps to the architectural layers:

**Interface Layer (Entry Points)**
  - ``cli.py``: Human-accessible command-line interface
  - ``server.py``: AI agent MCP server interface
  - ``__main__.py``: Python module execution entry point

**Business Logic Layer (Core Operations)**
  - ``functions.py``: Shared business logic and orchestration
  - ``results.py``: Result data structures and serialization
  - ``search.py``: Universal search algorithms and ranking
  - ``detection.py``: Processor selection and confidence scoring

**Processor Layer (Format-Specific Logic)**
  - ``processors.py``: Abstract base classes and protocols
  - ``inventories/``: Documentation inventory extraction (Sphinx objects.inv and MkDocs search indexes)
  - ``structures/``: Documentation content extraction and conversion

**Extension Management Layer (Plugin System)**
  - ``xtnsapi.py``: Clean API for extension developers
  - ``xtnsmgr/``: Extension lifecycle, installation, and configuration

**Infrastructure Layer (Supporting Utilities)**
  - ``interfaces.py``: Common data structures and enumerations
  - ``exceptions.py``: Error handling hierarchy
  - ``state.py``: Application state and globals management
  - ``cacheproxy.py``: HTTP caching and network operations
  - ``urls.py``: URL manipulation and validation
  - ``urlpatterns.py``: URL pattern matching and extension utilities

All package modules use the standard ``__`` import pattern as documented
in the common architecture guide. Subpackages (``inventories/``, ``structures/``, ``xtnsmgr/``) 
implement the cascading import hierarchy where each level inherits parent imports 
and adds specialized functionality.

Component Integration
===============================================================================

CLI Implementation
-------------------------------------------------------------------------------

The command-line interface is organized for maintainability:

.. code-block::

    librovore/
    ├── __main__.py      # Entry point: `python -m librovore`
    └── cli.py           # CLI implementation and argument parsing

This separation allows the CLI logic to be imported and tested independently
while following Python's standard module execution pattern.

Exception Organization
-------------------------------------------------------------------------------

Package-wide exceptions are centralized in ``sources/librovore/exceptions.py``
following the standard hierarchy patterns documented in the `common practices guide
<https://raw.githubusercontent.com/emcd/python-project-common/refs/tags/docs-1/documentation/common/practices.rst>`_.

Architecture Evolution
===============================================================================

This filesystem organization provides a foundation that architect agents can
evolve as the project grows. For questions about organizational principles,
subpackage patterns, or testing strategies, refer to the comprehensive common
documentation:

* `Architecture Patterns <https://raw.githubusercontent.com/emcd/python-project-common/refs/tags/docs-1/documentation/common/architecture.rst>`_
* `Development Practices <https://raw.githubusercontent.com/emcd/python-project-common/refs/tags/docs-1/documentation/common/practices.rst>`_
* `Test Development Guidelines <https://raw.githubusercontent.com/emcd/python-project-common/refs/tags/docs-1/documentation/common/tests.rst>`_
