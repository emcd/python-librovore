# Search

## Purpose
The Search capability provides flexible and powerful mechanisms to query the ingested documentation, supporting various matching strategies to help users find relevant information quickly.

## Requirements

### Requirement: Search Modes
The system SHALL support multiple search modes (Fuzzy, Exact, Regex).

Priority: Critical

#### Scenario: Fuzzy Search
- **WHEN** a user searches with a potentially misspelled term
- **THEN** the system uses fuzzy matching
- **AND** returns relevant results based on similarity

#### Scenario: Regex Search
- **WHEN** a user searches with a regular expression
- **THEN** the system matches patterns against the inventory
- **AND** returns matching objects

### Requirement: Filtering
The system SHALL support filtering by domain, role, and custom properties.

Priority: Critical

#### Scenario: Filter by Domain
- **WHEN** a user searches with a domain filter (e.g., `py:class`)
- **THEN** only objects matching that domain are returned

### Requirement: Scope
The system SHALL search across inventory objects and full content.

Priority: Critical

#### Scenario: Full Content Search
- **WHEN** a user requests a full content search
- **THEN** the system searches the text body of the documentation
- **AND** returns pages containing the term
