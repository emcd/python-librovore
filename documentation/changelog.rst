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
Release Notes
*******************************************************************************

.. towncrier release notes start

Librovore 1.0a3 (2025-09-01)
============================

Enhancements
------------

- Remove unreliable signature detection system to provide cleaner, more focused output with better performance.


Repairs
-------

- CLI: Fix exception rendering to respect --display-format setting for consistent JSON output.
- MCP: Fix content length issues that caused tool failures by implementing proper response size control through user-specified limits.


Librovore 1.0a2 (2025-08-28)
============================

Enhancements
------------

- Add MkDocs inventory processor to support pure MkDocs sites using ``search_index.json`` files.
- Implement parallel URL pattern probing for improved performance and network efficiency.
- Transform JSON output format from dictionary-based to structured dataclass objects with enhanced error handling.


Removals
--------

- CLI: Remove ``summarize-inventory`` subcommand and MCP server tool.


Librovore 1.0a1 (2025-08-20)
============================

Enhancements
------------

- Add automatic URL pattern extension for documentation sites. The system now automatically discovers working documentation URLs when the base URL fails, significantly improving compatibility with ReadTheDocs, GitHub Pages, and other hosting platforms that use versioned paths like ``/en/latest/`` or ``/latest/``. Previously failing sites like ``requests.readthedocs.io`` and ``docs.pydantic.dev`` now work seamlessly with transparent URL resolution.
- Improve error messages with structured, user-friendly responses. Replace generic "No processor found" errors with clear, actionable messages that distinguish between inventory and structure detection failures. Error responses now include specific titles, detailed explanations, and practical suggestions for resolving issues with unsupported documentation sites.


Repairs
-------

- Fix JSON serialization error for frigid.Dictionary objects in CLI and MCP server responses. Previously, commands like ``summarize-inventory`` with ``--group-by`` parameter would fail with "Unable to serialize unknown type" errors. Enhanced serialization now properly handles all internal data structures for consistent JSON output.


Librovore 1.0a0 (2025-08-17)
============================

No significant changes.
