# CLI Interface

## Purpose
The CLI (Command Line Interface) provides human developers with direct access to documentation search and extraction capabilities. It serves as a testing ground for the engine and a standalone tool for offline documentation access.

## Requirements

### Requirement: CLI Implementation
The system SHALL implement a human-usable command-line interface.

Priority: High

#### Scenario: Basic Usage
- **WHEN** a user runs the `librovore` command
- **THEN** help text is displayed showing available commands

### Requirement: Inventory Query Command
The CLI SHALL provide a command for searching documentation inventories.

Priority: High

#### Scenario: Searching from CLI
- **WHEN** a user runs `librovore search <term>`
- **THEN** the system searches configured inventories
- **AND** displays matching results in a human-readable table

### Requirement: Content Extraction Command
The CLI SHALL provide a command for extracting full content.

Priority: High

#### Scenario: Extracting Content
- **WHEN** a user runs `librovore extract <url>`
- **THEN** the system downloads and processes the page
- **AND** outputs the clean Markdown to stdout or a file

### Requirement: Output Formats
The CLI SHALL support multiple output formats (JSON, Markdown).

Priority: High

#### Scenario: JSON Output
- **WHEN** a user runs a command with `--format json`
- **THEN** the output is strictly valid JSON
- **AND** suitable for piping to tools like `jq`

### Requirement: Configuration Support
The CLI SHALL support configuration files.

Priority: High

#### Scenario: Loading Config
- **WHEN** the CLI starts
- **THEN** it looks for a configuration file
- **AND** applies settings for inventories, cache, etc.
