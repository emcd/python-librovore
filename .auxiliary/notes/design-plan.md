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

tests/
├── README.md              # Test documentation ✅
└── test_000_sphinxmcps/   # Test suite ✅
    ├── fixtures.py        # Test fixtures and utilities ✅
    ├── test_000_package.py    # Package infrastructure (6 tests) ✅
    ├── test_010_internals.py  # Internal utilities (7 tests) ✅
    ├── test_100_exceptions.py # Exception hierarchy (13 tests) ✅
    ├── test_200_functions.py  # Business logic (17 tests) ✅
    ├── test_300_cli.py        # CLI commands (17 tests) ✅
    └── test_500_integration.py # MCP integration (18 tests) ✅
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

### Phase 5: Testing and Polish ✅ COMPLETED
- [x] CLI restructuring (`use` command for operations) ✅ COMPLETED
- [x] Enhanced serve command for TCP bridging ✅ COMPLETED
- [x] Implement stdio-over-tcp transport with dynamic port assignment ✅ COMPLETED
- [x] Fix Pyright compliance and clean up overloaded behaviors ✅ COMPLETED
- [ ] Comprehensive test suite with pytest (NEXT)
- [ ] Integration tests using subprocess + TCP bridge (NEXT)

## Dependencies to Add

```toml
dependencies = [
    'mcp',  # Model Context Protocol Python SDK
    # ... existing dependencies
]
```

## Testing Strategy ✅ COMPLETED

### Comprehensive Test Infrastructure (78 tests)
- ✅ **Package infrastructure tests** (6 tests) - Import validation, version checks
- ✅ **Internal utilities tests** (7 tests) - Common imports and globals validation  
- ✅ **Exception hierarchy tests** (13 tests) - Complete exception validation with inheritance checks
- ✅ **Business logic tests** (17 tests) - Core functions with pyfakefs filesystem mocking
- ✅ **CLI integration tests** (17 tests) - Subprocess testing with real command execution
- ✅ **MCP protocol tests** (18 tests) - Full protocol testing with stdio-over-tcp transport

### Test Infrastructure Features
- ✅ **Dependency injection patterns** - No monkey-patching used
- ✅ **Subprocess testing** - Real CLI and server testing via subprocess execution
- ✅ **stdio-over-tcp transport** - Eliminates external dependencies (no socat required)
- ✅ **Slow test optimization** - Fast tests (~1s) vs complete tests (~64s)
- ✅ **Clean execution** - No warnings, proper subprocess cleanup
- ✅ **Automated test scripts** - `testers` (fast) and `testers-all` (complete)

### Coverage Analysis
- **Overall coverage**: 56% despite comprehensive testing
- **Excellent coverage**: exceptions.py (100%), internals (100%)  
- **Good coverage**: functions.py (77%)
- **Coverage gaps**: server.py (12%), cli.py (42%), interfaces.py (48%)
- **Root cause**: Integration-heavy testing misses unit-level code paths

## Development Workflow ✅ ENHANCED

1. Start TCP bridge: `hatch run sphinxmcps serve --transport stdio-over-tcp --port 0`
2. Test via MCP protocol over TCP using asyncio connections
3. Iterate without restarting Claude Code session  
4. Dynamic port assignment eliminates port conflicts
5. See `testing-protocol.md` for updated testing procedures

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
- **MCP Tools**: `extract_inventory` (with filtering), `summarize_inventory`
- **CLI Commands**: `use extract-inventory`, `use summarize-inventory` (with all filter options), `serve`
- **Transports**: stdio (primary), sse, stdio-over-tcp (with dynamic ports)
- **Testing**: stdio-over-tcp bridge replaces socat dependency
- **Architecture**: Clean transport semantics, Pyright compliant
- **Ready for**: Comprehensive test suite development

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