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
├── __/                     # Common imports ✅
├── __init__.py            # Package init ✅
├── __main__.py            # Entry point ✅
├── cli.py                 # CLI implementation ✅
├── exceptions.py          # Custom exceptions with Omnierror hierarchy ✅
├── functions.py           # Shared business logic ✅
├── server.py              # MCP server implementation ✅
├── interfaces.py          # CLI interfaces ✅
└── _typedecls/            # Type stubs for external libraries ✅
    └── sphobjinv/         # sphobjinv type declarations ✅
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

### Phase 1: Hello World Foundation ✅ COMPLETED
- [x] Research MCP protocol and FastMCP
- [x] Design architecture following emcdproj patterns
- [x] Add MCP dependency to pyproject.toml
- [x] Create interfaces.py (local implementation, not import from emcdproj)
- [x] Implement functions.py with hello business logic
- [x] Update cli.py with proper Command classes
- [x] Create server.py with dynamic FastMCP construction
- [x] Implement programmatic tool registration
- [x] Add port configuration for SSE transport
- [x] Test hello functionality via CLI and MCP
- [x] Establish socat bridge testing infrastructure

### Phase 2: Transport Options ✅ COMPLETED
- [x] Add SSE transport support with dynamic port configuration
- [x] Establish socat bridge for stdio testing (preferred for development)
- [x] Test different transport methods (stdio via socat, SSE via HTTP)
- [ ] Add Unix socket support for development (optional future enhancement)

### Phase 3: Sphinx Integration ✅ COMPLETED
- [x] Implement sphobjinv-based inventory extraction
- [x] Add extract_inventory tool with comprehensive filtering
- [x] Add auto-append objects.inv functionality
- [x] Add URL validation and robust exception handling
- [x] Support both local files and remote URLs
- [x] Add summarize_inventory tool for human-readable output

### Phase 4: Advanced Features ✅ COMPLETED  
- [x] Advanced filtering (domain, role, search parameters)
- [x] Enhanced error reporting with structured exceptions
- [x] Performance optimizations (filter during iteration)
- [x] Function consolidation and architecture cleanup
- [x] Comprehensive MCP tool documentation

### Phase 5: Testing and Polish (IN PROGRESS)
- [ ] Comprehensive test suite with pytest
- [ ] Integration tests using subprocess + TCP bridge
- [ ] CLI restructuring (`use` command for operations)
- [ ] Enhanced serve command for TCP bridging

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
- MCP server tests using socat bridge and netcat
- Rapid iteration testing without Claude Code restarts

## Development Workflow ✅ ESTABLISHED

1. Start socat bridge: `socat TCP-LISTEN:8002,fork,reuseaddr EXEC:"hatch run sphinxmcps serve"`
2. Test via MCP protocol over TCP using netcat with proper JSON-RPC handshake
3. Iterate without restarting Claude Code session
4. See `testing-protocol.md` for detailed testing procedures

## Key Achievements

### Foundation ✅
- ✅ Dynamic FastMCP server construction with port configuration
- ✅ Programmatic tool registration (vs decorator-based at module level)
- ✅ Working socat bridge testing infrastructure  
- ✅ Full MCP protocol handshake and tool execution validation
- ✅ Hello world functionality proven via both CLI and MCP

### Sphinx Integration ✅
- ✅ Complete sphobjinv integration for inventory extraction
- ✅ Auto-append objects.inv to URLs and file paths
- ✅ Support for both local files and remote URLs
- ✅ Robust exception handling with custom hierarchy
- ✅ Type safety with custom sphobjinv type stubs

### Advanced Filtering ✅
- ✅ Domain filtering (`domain=py`)
- ✅ Role filtering (`role=function`) 
- ✅ Object name search (`search=datetime`)
- ✅ Filter during iteration for performance
- ✅ Comprehensive filter parameter documentation

### Architecture Cleanup ✅
- ✅ Consolidated duplicate functions (extract_inventory + filter_inventory)
- ✅ Eliminated duplicate formatting code (CLI + functions)
- ✅ Centralized URL detection logic with `_is_url` helper
- ✅ Single well-documented MCP tool with optional filters
- ✅ Enhanced summarize_inventory with filter display support

### Current Status
- **MCP Tools**: `hello`, `extract_inventory` (with filtering), `summarize_inventory`
- **CLI Commands**: `hello`, `inventory` (with all filter options), `serve`
- **Transports**: stdio (primary), SSE (secondary)
- **Testing**: Socat bridge with full MCP protocol validation
- **Ready for**: Production use, testing infrastructure, CLI enhancements

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