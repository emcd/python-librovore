# MCP Server

## Purpose
The MCP (Model Context Protocol) Server interface enables AI agents to programmatically discover, search, and extract technical documentation. It acts as the primary bridge between AI systems and the documentation engine.

## MODIFIED Requirements

### Requirement: MCP Server Implementation
The system SHALL implement a complete MCP server with the MCP SDK v2 `MCPServer` framework.

Priority: Critical

#### Scenario: AI Agent Connection
- **WHEN** an AI agent connects to the MCP server
- **THEN** the server accepts the connection
- **AND** exposes available tools (`query_inventory`, `query_content`, plus opt-in extras)

#### Scenario: Transport Configuration At Run Time
- **WHEN** the server starts with the SSE transport and a configured port
- **THEN** the port is passed to the run call, not the server constructor
- **AND** stdio transport starts with no transport arguments

#### Scenario: Stdio And Legacy-SSE Compatibility
- **WHEN** a real MCP client connects over stdio, and over legacy SSE on a non-default port
- **THEN** both connections succeed
- **AND** the exposed tool list is served on each transport
