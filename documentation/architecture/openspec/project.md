# Project Context

## Purpose
A Documentation Search Engine providing a CLI and MCP (Model Context Protocol) server for AI agents to search and extract documentation from Sphinx and MkDocs sites. It aims to make technical documentation easily consumable by AI agents.

## Tech Stack
- **Language**: Python 3.10+
- **Core Libraries**: `mcp`, `sphobjinv`, `beautifulsoup4`, `lxml`, `rapidfuzz`, `markdownify`, `rich`, `httpx`
- **CLI Framework**: `typer` (via `emcd-appcore`)
- **Build System**: `hatch`
- **Package Management**: `uv`
- **Testing**: `pytest`
- **Linting/Typing**: `ruff`, `isort`, `pyright`

## Project Conventions

### Filesystem Organization
The project follows a standard filesystem organization as detailed in [Filesystem Organization](../filesystem.rst).
- Source code is in `sources/`.
- Tests are in `tests/`.
- Documentation is in `documentation/`.
- The package uses a layered architecture (Interface, Business Logic, Processor, Infrastructure).

### Code Style
- **Line Length**: 79 characters.
- **Indentation**: 4 spaces.
- **Imports**: Sorted by `isort`, separated by type (stdlib, third-party, first-party).
- **Typing**: `pyright` is used for static type checking. `mypy` is explicitly avoided.
- **Linting**: `ruff` is used for linting with a specific set of rules (Flake8, Pylint, etc.).
- **Import Hubs**: Uses `__/imports.py` for centralized imports within packages.

### Architecture Patterns
- **Layered Architecture**: Defined in `filesystem.rst` (Interface, Business Logic, Processor, Extension Management, Infrastructure).
- **Extension System**: Uses a plugin architecture for supporting additional documentation formats.

### Testing Strategy
- **Framework**: `pytest`.
- **Naming**: Test files `test_*.py`, test functions `test_[0-9][0-9][0-9]_*`.
- **Coverage**: tracked via `coverage`, artifacts in `.auxiliary/artifacts/coverage-pytest`.
- **Doctests**: Executed via Sphinx.

### Git Workflow
- **Changelog**: Uses `towncrier` for managing changelog fragments in `documentation/changelog.rst`. Fragments go in `.auxiliary/data/towncrier`.

## Domain Context
- **Sphinx**: Understands `objects.inv` inventory files.
- **MkDocs**: Understands `search_index.json`.
- **MCP**: Implements Model Context Protocol for AI integration.
- **HTML to Markdown**: Converts documentation HTML to clean Markdown for AI consumption.

## Important Constraints
- **Python Version**: Minimum 3.10.
- **License**: Apache-2.0.

## External Dependencies
- **Target Documentation Sites**: Requires internet access to fetch documentation from remote URLs.
