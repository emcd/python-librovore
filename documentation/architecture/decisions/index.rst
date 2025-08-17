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
Architectural Decision Records
*******************************************************************************

This section documents the significant architectural decisions made during the development of the project. Each ADR captures the context, reasoning, alternatives considered, and consequences of important design choices.

.. toctree::
   :maxdepth: 2

   001-extension-management-system
   002-search-architecture-separation
   003-dual-interface-architecture

Decision Summary
===============================================================================

**ADR-001: Extension Management System**
  Decision to implement a three-layer extension architecture (API, management, configuration) with clear separation of concerns and dependency isolation.

**ADR-002: Search Architecture Separation**  
  Decision to separate universal search logic from processor-specific data extraction, enabling consistent search behavior across all documentation formats.

**ADR-003: Dual Interface Architecture**
  Decision to provide both CLI and MCP server interfaces sharing common business logic, optimized for human users and AI agents respectively.

For ADR format and guidance, see the `architecture documentation guide
<https://emcd.github.io/python-project-common/stable/sphinx-html/common/architecture.html>`_.