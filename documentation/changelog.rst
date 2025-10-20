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

librovore 1.0a7 (2025-10-20)
============================

Enhancements
------------

- Add ``--summarize`` and ``--group-by`` options to query-inventory command to display distribution statistics across inventory dimensions instead of full object lists.
- Add comprehensive filter validation with user-facing warnings to prevent silent filter failures.


librovore 1.0a6 (2025-09-28)
============================

Enhancements
------------

- CLI: Add new options from appcore.cli framework migration including --inscription.level, --inscription.presentation, --configfile, and --environment for enhanced logging and configuration support.
- Implement graceful degradation for robots.txt access failures - queries now succeed with warnings instead of failing completely when robots.txt is inaccessible.
- Improve content extraction quality with universal patterns that work across different documentation themes and provide better theme-specific precedence.


Notices
-------

- MCP Server: Change configuration parameters from --logfile to --inscription.target-file and --inscription.level for consistency with new CLI framework.


Repairs
-------

- CLI: Fix broken 'filters' option that was not working correctly.
- Fix Sphinx content extraction returning sidebar content instead of main documentation for Python modules.
- Fix confusing error messages when robots.txt access fails, now shows clear "Robots.txt Access Failure" instead of misleading "No Compatible Processor Found" messages.


librovore 1.0a5 (2025-09-05)
============================

Enhancements
------------

- CLI: Consolidate display options into unified dataclass with mutual exclusion validation for better user experience.
- Implement unified partial_ratio search strategy to dramatically improve substring discovery in documentation inventories.
- Improve UX formatting by cleaning up metadata display order and removing dead architecture.


Repairs
-------

- Fix Rich markdown rendering by converting metadata patterns to bullet lists for improved readability.


librovore 1.0a4 (2025-09-03)
============================

Enhancements
------------

- CLI: Add Rich markdown terminal display with syntax highlighting and improved formatting, plus new ``--color``/``--no-color`` and ``--ansi-sgr``/``--no-ansi-sgr`` flags for output control.
- CLI: Add ``--content-id`` parameter enabling browse-then-extract workflows where users can preview content with limited lines then extract full content by ID.
- MCP: Improve workflow descriptions and rename server from "Sphinx MCP Server" to "Librovore Documentation Server" to better reflect multi-processor capabilities.


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
