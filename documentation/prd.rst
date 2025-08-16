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
Product Requirements Document
*******************************************************************************

Executive Summary
===============================================================================

Librovore is a dual-purpose tool that provides both an MCP (Model Context Protocol) server and CLI interface for searching and extracting content from static documentation sites. The name "librovore" (book-devourer) reflects its ability to consume and index documentation from multiple formats including Sphinx and MkDocs sites. It enables AI agents and human users to efficiently discover, search, and extract relevant information from documentation inventories and full-text content.

The product targets AI agents needing to access technical documentation during development workflows, as well as human developers seeking efficient documentation search capabilities outside of LLM environments.

For PRD format and guidance, see the `requirements documentation guide
<https://emcd.github.io/python-project-common/stable/sphinx-html/common/requirements.html>`_.

Problem Statement
===============================================================================

**Who experiences the problem:** AI agents, LLM developers, and human developers working with complex software ecosystems that rely on external documentation.

**When and where it occurs:** 
- During development when agents need specific API documentation or usage examples
- When searching across multiple documentation sites for related concepts
- When working offline or with limited documentation access
- When existing documentation search mechanisms are inadequate for programmatic access

**Impact and consequences:**
- AI agents cannot efficiently access up-to-date technical documentation
- Developers waste time manually searching through documentation sites
- Inconsistent access patterns across different documentation systems (Sphinx, MkDocs, etc.)
- Limited advanced search capabilities within documentation ecosystems

**Current limitations:**
- Static MCP servers only provide file serving without semantic search
- Documentation sites have varying search capabilities and interfaces
- No unified interface for accessing multiple documentation formats
- Limited programmatic access to documentation inventory and cross-references

Goals and Objectives
===============================================================================

**Primary Objectives (Critical):**
1. **Unified Documentation Access**: Provide consistent interface for both Sphinx and MkDocs documentation sites
2. **Advanced Search**: Enable fuzzy, exact, and regex-based search across documentation inventories and content
3. **MCP Integration**: Seamless integration with AI agents through Model Context Protocol
4. **Performance**: Fast response times with intelligent caching for frequently accessed documentation

**Secondary Objectives (High Priority):**
1. **Extensibility**: Plugin architecture supporting additional documentation formats
2. **CLI Usability**: Human-usable command-line interface for testing and standalone use
3. **Content Quality**: High-quality HTML-to-Markdown conversion preserving code blocks and formatting
4. **Developer Experience**: Clear error messages, helpful diagnostics, and robust error handling

**Success Metrics:**
- Sub-second response times for cached inventory queries
- Support for 90%+ of popular Sphinx and MkDocs sites
- Clean markdown output with preserved code formatting
- Successful integration with major MCP clients
- 90%+ test coverage with comprehensive edge case handling

Target Users
===============================================================================

**Primary Users - AI Agents/LLM Systems:**
- **Technical Context**: Programmatic access through MCP protocol
- **Needs**: Structured documentation access, search capabilities, content extraction
- **Usage Pattern**: Automated queries during development assistance
- **Environment**: Integration with Claude Code, other MCP-enabled systems

**Secondary Users - Developer Tool Creators:**
- **Technical Context**: Python developers building documentation tools
- **Needs**: Extensible plugin system, clean APIs, reliable performance
- **Usage Pattern**: Integration into larger development workflows
- **Environment**: CI/CD systems, development toolchains

**Tertiary Users - Human Developers:**
- **Technical Context**: Command-line proficient, working with multiple documentation sites
- **Needs**: Fast search across documentation, offline access capabilities
- **Usage Pattern**: Occasional direct CLI usage for testing or when LLM unavailable
- **Environment**: Local development environments, terminal-based workflows

Functional Requirements
===============================================================================

**REQ-001: MCP Server Implementation (Critical)**
- **Priority**: Critical
- **Description**: Implement complete MCP server with FastMCP framework
- **User Story**: As an AI agent, I want to connect to librovore via MCP so that I can programmatically access documentation
- **Acceptance Criteria**:
  - Server responds to MCP client connections
  - Implements query_inventory_with_context tool
  - Implements query_content_with_context tool
  - Implements summarize_inventory_with_context tool
  - Supports restart functionality for development
  - JSON schema generation for all tool parameters

**REQ-002: Sphinx Documentation Processing (Critical)**
- **Priority**: Critical
- **Description**: Full support for Sphinx documentation sites including inventory parsing and content extraction
- **User Story**: As a user, I want to search Sphinx documentation sites so that I can find API references and usage examples
- **Acceptance Criteria**:
  - Parse objects.inv files from Sphinx sites
  - Extract HTML content and convert to clean Markdown
  - Support major Sphinx themes (Furo, ReadTheDocs, pydoctheme)
  - Handle cross-references and object relationships
  - Preserve code block formatting and syntax highlighting hints

**REQ-003: MkDocs Documentation Processing (Critical)**
- **Priority**: Critical
- **Description**: Full support for MkDocs sites with mkdocstrings integration
- **User Story**: As a user, I want to search MkDocs documentation so that I can access API documentation generated by mkdocstrings
- **Acceptance Criteria**:
  - Parse objects.inv files from mkdocstrings-enabled MkDocs sites
  - Extract content from Material for MkDocs theme
  - Convert HTML to Markdown with language-aware code blocks
  - Handle mkdocstrings-specific content structure
  - Filter out navigation and UI elements during extraction

**REQ-004: Search Functionality (Critical)**
- **Priority**: Critical
- **Description**: Multiple search modes with configurable behavior
- **User Story**: As a user, I want to search documentation using different matching strategies so that I can find relevant content efficiently
- **Acceptance Criteria**:
  - Fuzzy search with configurable threshold (default 50)
  - Exact string matching
  - Regular expression search
  - Search across inventory objects and full content
  - Filtering by domain, role, and custom processor filters
  - Configurable result limits and detail levels

**REQ-005: Caching System (High)**
- **Priority**: High
- **Description**: Intelligent caching to improve performance and reduce network requests
- **User Story**: As a user, I want fast response times for repeated queries so that my workflow is not interrupted
- **Acceptance Criteria**:
  - Cache downloaded inventories with TTL
  - Cache extracted content with appropriate invalidation
  - Memory-efficient caching strategy
  - Cache hit/miss metrics for optimization
  - Configurable cache settings

**REQ-006: CLI Interface (High)**
- **Priority**: High
- **Description**: Human-usable command-line interface for testing and standalone use
- **User Story**: As a developer, I want to test librovore functionality from the command line so that I can validate behavior and debug issues
- **Acceptance Criteria**:
  - Commands for inventory querying, content search, and summarization
  - JSON and Markdown output formats
  - Comprehensive help text and error messages
  - Support for all MCP server capabilities
  - Configuration file support for frequent use cases

**REQ-007: Processor Detection (High)**
- **Priority**: High
- **Description**: Automatic detection of appropriate processor for given documentation site
- **User Story**: As a user, I want librovore to automatically determine the correct processor so that I don't need to specify the documentation type
- **Acceptance Criteria**:
  - Detect Sphinx sites by robots.txt and objects.inv presence
  - Detect MkDocs sites with mkdocstrings by objects.inv and site structure
  - Graceful fallback when detection is ambiguous
  - Clear error messages when no suitable processor is found
  - Confidence scoring for processor selection

**REQ-008: Content Quality (Medium)**
- **Priority**: Medium
- **Description**: High-quality content extraction and formatting
- **User Story**: As a user, I want extracted content to be clean and well-formatted so that it's easily readable and usable
- **Acceptance Criteria**:
  - Remove HTML artifacts and navigation elements
  - Preserve code block structure and language hints
  - Maintain proper whitespace and formatting
  - Convert HTML tables to Markdown tables
  - Handle images and media references appropriately

**REQ-009: Error Handling (Medium)**
- **Priority**: Medium
- **Description**: Robust error handling and user feedback
- **User Story**: As a user, I want clear error messages when something goes wrong so that I can understand and resolve issues
- **Acceptance Criteria**:
  - Graceful handling of network failures
  - Validation of input parameters with helpful messages
  - Fallback strategies for partially available documentation
  - Detailed logging for debugging purposes
  - Recovery from temporary service unavailability

**REQ-010: Plugin Architecture Foundation (Low)**
- **Priority**: Low
- **Description**: Extensible architecture for additional documentation processors
- **User Story**: As a tool developer, I want to extend librovore with custom processors so that I can support additional documentation formats
- **Acceptance Criteria**:
  - Abstract base classes for processors
  - Plugin discovery mechanism
  - Documentation for plugin development
  - Example plugin implementation
  - Backward compatibility guarantees

Non-Functional Requirements
===============================================================================

**Scalability Requirements:**
- Handle inventories with 10,000+ objects
- Support documentation sites with 1,000+ pages
- Efficient memory usage for large content extraction
- Configurable resource limits to prevent abuse

**Reliability Requirements:**
- Graceful degradation when documentation sites are unavailable
- Automatic retry with exponential backoff for network failures
- Recovery from corrupted cache data
- Consistent behavior across different operating systems

**Security Requirements:**
- No execution of untrusted code from documentation sites
- Safe handling of potentially malicious HTML content
- Input validation for all user-provided parameters
- Protection against resource exhaustion attacks

**Usability Requirements:**
- Clear, actionable error messages
- Comprehensive CLI help text
- JSON output compatible with standard tools (jq, etc.)
- Markdown output suitable for human reading
- Minimal configuration required for basic operation

**Compatibility Requirements:**
- Python 3.10+ support
- MCP protocol compliance
- Support for major documentation hosting platforms (GitHub Pages, ReadTheDocs, etc.)
- Cross-platform operation (Linux, macOS, Windows)

Constraints and Assumptions
===============================================================================

**Technical Constraints:**
- Must use Python for implementation (existing codebase)
- Must comply with MCP protocol specifications
- Cannot modify remote documentation sites or require site-specific changes
- Limited to documentation formats that provide machine-readable inventories

**Regulatory Constraints:**
- Must respect robots.txt directives
- Must not overwhelm documentation sites with excessive requests
- Must handle rate limiting appropriately

**Assumptions:**
- Target documentation sites will continue supporting objects.inv format
- Network connectivity available for accessing remote documentation
- Documentation sites follow standard patterns for content organization
- Users have appropriate permissions to access target documentation sites

Out of Scope
===============================================================================

**Excluded Features:**
- Real-time synchronization with documentation source repositories
- Modification or annotation of documentation content
- Full-text indexing of documentation sites without inventories
- Support for documentation formats without machine-readable inventories
- Authentication mechanisms for private documentation sites
- Multi-user collaboration features
- Web-based user interface
- Integration with version control systems
- Automated documentation generation
- Support for multimedia content (videos, audio)
- Advanced analytics or usage tracking
- Integration with specific IDE plugins (beyond MCP)

**Future Considerations:**
- OpenAPI/Swagger processor support
- GraphQL schema introspection
- Enhanced relationship mapping between documentation objects
- Interactive CLI browser mode
- Multi-site search aggregation