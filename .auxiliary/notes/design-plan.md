# Sphinx MCP Server - Design and Development Plan

## Project Overview

Building an MCP (Model Context Protocol) server to extract object inventories (`objects.inv`) from Sphinx documentation websites. The server will be dual-purpose: usable as both a CLI tool and an MCP server.

## Architecture Design

### Core Principles
- **Shared business logic**: CLI commands and MCP tools call the same core functions
- **Immutable data structures**: Following emcdproj patterns with `__.immut.DataclassObject`
- **Transport flexibility**: Start with stdio, add SSE/HTTP and Unix socket support
- **Development-friendly**: Unix socket for iterative testing without restarts
- **Tyro-based CLI**: Using same patterns as emcdproj with `CliCommand` and `ConsoleDisplay`

### Module Structure

```
sources/sphinxmcps/
├── __/                     # Common imports (existing)
├── __init__.py            # Package init (existing)
├── __main__.py            # Entry point (existing)
├── cli.py                 # CLI implementation (existing, to be expanded)
├── exceptions.py          # Custom exceptions (existing)
├── core.py                # Shared business logic (new)
├── mcp_server.py          # MCP server implementation (new)
└── interfaces.py          # CLI interfaces (new)
```

### CLI Structure (Following emcdproj patterns)

```python
# interfaces.py - Import CLI interfaces from emcdproj
from emcdproj.interfaces import CliCommand, ConsoleDisplay

# cli.py structure
class HelloCommand(CliCommand):
    ''' Says hello with the given name. '''
    name: str = "World"
    
    async def __call__(
        self, auxdata: __.Globals, display: ConsoleDisplay
    ) -> None:
        from .core import hello_func
        result = hello_func(self.name)
        display.print(result)

class ServeCommand(CliCommand):
    ''' Start MCP server. '''
    transport: str = "stdio"  # stdio, sse, unix-socket
    port: int = 3000
    socket_path: str = "/tmp/sphinxmcps.sock"
    
    async def __call__(
        self, auxdata: __.Globals, display: ConsoleDisplay
    ) -> None:
        from .mcp_server import start_server
        await start_server(self.transport, self.port, self.socket_path)

class Cli(__.immut.DataclassObject):
    ''' Sphinx MCP server CLI. '''
    application: __.appcore.ApplicationInformation
    display: ConsoleDisplay
    command: __.typx.Union[
        __.typx.Annotated[HelloCommand, __.tyro.conf.subcommand('hello')],
        __.typx.Annotated[ServeCommand, __.tyro.conf.subcommand('serve')],
    ]
```

### MCP Server Structure

```python
# mcp_server.py
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Sphinx MCP Server")

@mcp.tool()
def hello(name: str = "World") -> str:
    ''' Hello world tool. '''
    from .core import hello_func
    return hello_func(name)

# Future Sphinx-specific tools
@mcp.tool()
def extract_inventory(url: str) -> dict:
    ''' Extract objects.inv from Sphinx documentation site. '''
    from .core import extract_sphinx_inventory
    return extract_sphinx_inventory(url)

@mcp.resource("inventory://{url}")
def get_inventory(url: str) -> str:
    ''' Get Sphinx inventory as a resource. '''
    from .core import get_inventory_content
    return get_inventory_content(url)
```

### Shared Business Logic

```python
# core.py - Pure business logic functions
def hello_func(name: str) -> str:
    ''' Core hello logic used by both CLI and MCP. '''
    return f"Hello, {name}!"

# Future Sphinx functionality
def extract_sphinx_inventory(url: str) -> dict:
    ''' Extract and parse objects.inv from a Sphinx site. '''
    # Will use sphobjinv library
    pass

def get_inventory_content(url: str) -> str:
    ''' Get formatted inventory content. '''
    pass
```

## Development Phases

### Phase 1: Hello World Foundation
- [x] Research MCP protocol and FastMCP
- [x] Design architecture following emcdproj patterns
- [ ] Add MCP dependency to pyproject.toml
- [ ] Create interfaces.py (import from emcdproj)
- [ ] Implement core.py with hello_func
- [ ] Update cli.py with proper Command classes
- [ ] Create mcp_server.py with FastMCP
- [ ] Test hello functionality via CLI and MCP

### Phase 2: Transport Options
- [ ] Add SSE transport support
- [ ] Add Unix socket support for development
- [ ] Test different transport methods

### Phase 3: Sphinx Integration
- [ ] Implement sphobjinv-based inventory extraction
- [ ] Add extract_inventory tool
- [ ] Add inventory resource
- [ ] Add URL validation and error handling

### Phase 4: Advanced Features
- [ ] Caching for inventory data
- [ ] Multiple site support
- [ ] Enhanced error reporting
- [ ] Performance optimizations

## Dependencies to Add

```toml
dependencies = [
    'mcp',  # Model Context Protocol Python SDK
    # ... existing dependencies
]
```

## Testing Strategy

- Unit tests for core functions
- Integration tests for CLI commands
- MCP server tests using test client
- Unix socket tests for development workflow

## Development Workflow

1. Use `--serve` with Unix socket for live testing
2. Connect via `Bash` tool to test MCP server responses
3. Iterate without restarting Claude Code session

## Coding Standards Adherence

- Python 3.10+ with modern idioms (`match`/`case`, `|` unions)
- Type hints for all functions and attributes
- Immutable data structures with `__.immut.DataclassObject`
- Module-level functions over class methods where appropriate
- Functions ≤ 30 lines, modules ≤ 600 lines
- Dependency injection patterns
- Triple-single-quote docstrings with space padding
- No `__all__` exports (use private `_` naming)
- Import common modules from `__` subpackage