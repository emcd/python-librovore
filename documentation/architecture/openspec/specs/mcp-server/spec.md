# MCP Server

## Purpose
The MCP (Model Context Protocol) Server interface enables AI agents to programmatically discover, search, and extract technical documentation. It acts as the primary bridge between AI systems and the documentation engine.

## Requirements

### Requirement: MCP Server Implementation
The system SHALL implement a complete MCP server with FastMCP framework.

Priority: Critical

#### Scenario: AI Agent Connection
- **WHEN** an AI agent connects to the MCP server
- **THEN** the server accepts the connection
- **AND** exposes available tools (query_inventory, query_content, summarize_inventory)

### Requirement: JSON Schema Generation
The server SHALL generate JSON schemas for all tool parameters.

Priority: Critical

#### Scenario: Tool Discovery
- **WHEN** an AI agent requests the list of available tools
- **THEN** the server returns the tool list
- **AND** includes valid JSON schemas for all parameters

### Requirement: Query Inventory Tool
The server SHALL implement a `query_inventory` tool for searching documentation objects.

Priority: Critical

#### Scenario: Searching Inventory
- **WHEN** the agent calls `query_inventory` with a search term
- **THEN** the server searches the loaded inventories
- **AND** returns a list of matching objects

### Requirement: Query Content Tool
The server SHALL implement a `query_content` tool for retrieving full text.

Priority: Critical

#### Scenario: Fetching Content
- **WHEN** the agent calls `query_content` with a URL or object ID
- **THEN** the server retrieves the content
- **AND** returns it in clean Markdown format

### Requirement: Summarize Inventory Tool
The server SHALL implement a `summarize_inventory` tool for high-level overview.

Priority: Critical

#### Scenario: Inventory Summary
- **WHEN** the agent calls `summarize_inventory` for a site
- **THEN** the server provides statistics and top-level structure of the documentation
