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
001. Extension Management System
*******************************************************************************

Status
===============================================================================

Accepted

Context
===============================================================================

The project needs to support multiple documentation formats (Sphinx, MkDocs, future formats like OpenAPI) through a plugin architecture. The system must handle:

- **Built-in processors** for core formats that ship with the application
- **External extensions** that can be installed dynamically from PyPI or other sources
- **Configuration-driven loading** to enable/disable processors based on user preferences
- **Isolation** to prevent conflicts between extensions and core functionality
- **Lifecycle management** including installation, loading, and cleanup of extensions

Key requirements driving this decision:

- Extensions should not interfere with core system stability
- Users should be able to extend functionality without modifying core code
- The system should gracefully handle missing or incompatible extensions
- Extension management should be transparent to end users
- Configuration should control which processors are active

Decision
===============================================================================

Implement a layered extension management system with clear separation between API, management, and configuration concerns:

**Three-Layer Architecture:**

1. **Extension API Layer (xtnsapi.py)**: Clean interface for extension developers
2. **Extension Manager Layer (xtnsmgr/)**: Handles processor lifecycle and package management  
3. **Configuration Layer**: User-controlled processor selection and settings

**Dependency Flow:**
- ``xtnsmgr`` uses ``xtnsapi`` (management layer uses API layer)
- ``xtnsapi`` does NOT import ``xtnsmgr`` (API layer independent of management)
- Extensions interact only with ``xtnsapi`` (clean separation)
- Server uses ``xtnsapi`` for processor access (service layer uses API)

**Package Installation Strategy:**
- Use ``uv`` for external package installation with isolated environments
- Cache installed packages with proper versioning and dependency management
- Support import path manipulation for runtime loading
- Provide cleanup mechanisms for removing unused extensions

Alternatives
===============================================================================

**Alternative 1: Single Monolithic Extension Module**
- Rejected because it would mix API concerns with management concerns
- Would make testing more difficult due to tight coupling
- Would limit future extensibility for different management strategies

**Alternative 2: Plugin Discovery via Entry Points**
- Considered but rejected for initial implementation
- Requires packages to be installed in the same environment as the main application
- Less flexible for dynamic installation and configuration management
- Could be added later as an additional discovery mechanism

**Alternative 3: External Extension Server**
- Rejected as over-engineered for current requirements
- Would add network dependencies and deployment complexity
- Not justified by current scale of extension ecosystem

**Alternative 4: No Extension System**
- Rejected because supporting only built-in processors limits adaptability
- Would require core code changes for each new documentation format
- Conflicts with design goal of extensibility for future formats

Consequences
===============================================================================

**Positive Consequences:**

- **Clean separation of concerns**: API development separate from lifecycle management
- **Testability**: Each layer can be tested independently with clear interfaces
- **Extensibility**: New management strategies can be implemented without changing APIs
- **Stability**: Extension failures isolated from core system functionality
- **User control**: Configuration-driven processor selection provides flexibility

**Negative Consequences:**

- **Complexity**: Three-layer architecture adds cognitive overhead for developers
- **Performance**: Dynamic loading may introduce latency for first-time extension use
- **Maintenance**: Multiple extension management strategies require ongoing maintenance

**Implementation Impacts:**

- Extension developers must learn the xtnsapi interface patterns
- Core system must handle cases where configured extensions fail to load
- Package management requires careful handling of version conflicts
- Configuration validation needed to prevent invalid extension specifications

**Future Flexibility:**

- Architecture supports future addition of entry-point based discovery
- Can evolve to support remote extension repositories
- Enables fine-grained security controls for extension permissions
- Allows for extension dependency management and compatibility checking