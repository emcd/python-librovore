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
003. Dual Interface Architecture
*******************************************************************************

Status
===============================================================================

Accepted

Context
===============================================================================

Librovore serves two distinct user constituencies with different interaction patterns and requirements:

**AI Agent Integration (Primary):**
- Programmatic access through structured protocols
- Integration with development workflows via Model Context Protocol (MCP)
- Long-running server processes with stateful caching
- JSON-based communication with schema validation
- Focus on reliability and consistent API contracts

**Human Developer Usage (Secondary):**
- Interactive command-line interface for testing and validation
- Standalone operation without additional infrastructure
- Human-readable output formats (Markdown, formatted JSON)
- Ad-hoc queries and exploration of documentation sites
- Support for debugging and development workflows

Key forces driving this decision:

- AI agents need protocol compliance and structured data exchange
- Human users need immediate accessibility without setup overhead
- Both interfaces should provide equivalent functionality
- Implementation should share core business logic to ensure consistency
- Testing and validation should be possible through human-accessible interface

Decision
===============================================================================

Implement a dual interface architecture with shared business logic layer:

**Interface Layer Separation:**
- **CLI Interface (cli.py)**: Human-accessible command-line tool using tyro framework
- **MCP Server (server.py)**: AI agent interface using FastMCP framework
- **Shared Functions Layer (functions.py)**: Common business logic and orchestration

**Functionality Parity:**
- Both interfaces support all core operations: detection, inventory queries, content search
- Identical parameter validation and error handling across interfaces
- Consistent result structure with interface-appropriate formatting
- Equivalent performance characteristics and caching behavior

**Output Format Adaptation:**
- CLI provides both JSON and Markdown output options for different use cases
- MCP server returns structured JSON conforming to protocol specifications
- Human-readable formatting includes syntax highlighting and structured presentation
- Machine-readable formats include comprehensive metadata and versioning

**Deployment Flexibility:**
- CLI can operate as standalone tool with no external dependencies
- MCP server supports long-running processes with stateful optimizations
- Single codebase supports both packaging as CLI tool and library integration

Alternatives
===============================================================================

**Alternative 1: CLI-Only with Optional MCP Bridge**
- Rejected because it would limit AI agent integration capabilities
- MCP protocol requires specific server behaviors that don't map well to CLI patterns
- Would result in sub-optimal performance for AI agent use cases

**Alternative 2: MCP-Only with CLI Wrapper**
- Rejected because it would create dependency overhead for human users
- CLI users shouldn't need to understand MCP concepts or server management
- Would make testing and development more cumbersome

**Alternative 3: Separate Applications**
- Rejected because it would require maintaining two independent codebases
- Would lead to feature drift between interfaces over time
- Duplicates business logic and testing requirements

**Alternative 4: Web Interface Addition**
- Considered but deemed out of scope for current requirements
- Would add significant complexity for deployment and security
- Current user base doesn't justify the development overhead

**Alternative 5: GraphQL API**
- Rejected as over-engineered for the interaction patterns
- MCP protocol provides better integration with AI development tools
- Would require additional tooling for client development

Consequences
===============================================================================

**Positive Consequences:**

- **User Experience**: Each interface optimized for its intended use case
- **Accessibility**: Human users can use the tool without protocol knowledge
- **Integration**: AI agents get purpose-built interface with proper protocol support
- **Development**: Shared business logic ensures consistent behavior
- **Testing**: CLI interface enables comprehensive testing without protocol complexity

**Negative Consequences:**

- **Maintenance overhead**: Two interfaces require ongoing compatibility testing
- **Documentation burden**: Must document both CLI usage and MCP integration patterns
- **Complexity**: Additional architectural layer increases cognitive load

**Implementation Impacts:**

- Functions layer must provide interface-agnostic business logic
- Error handling must work appropriately for both interactive and programmatic use
- Output formatting requires conditional logic based on interface type
- Parameter validation must accommodate both CLI argument parsing and JSON schemas

**User Benefits:**

- **Developers**: Can test and validate functionality through familiar CLI patterns
- **AI Systems**: Get reliable, schema-validated API with proper error handling
- **DevOps**: Can integrate into automation workflows through either interface
- **Testing**: Comprehensive validation possible through human-accessible interface

**Technical Benefits:**

- **Code reuse**: Core functionality implemented once and shared
- **Consistency**: Identical behavior across interfaces reduces confusion
- **Performance**: MCP server can maintain stateful optimizations
- **Deployment**: Flexible packaging options for different use cases

**Future Considerations:**

- Architecture supports adding additional interfaces (web, gRPC) without core changes
- Interface-specific optimizations can be added without affecting shared logic
- Protocol evolution (MCP updates) isolated to server interface implementation
- CLI can evolve independently for improved human user experience