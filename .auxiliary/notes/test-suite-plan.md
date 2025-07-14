# Test Suite Architecture Plan

## Overview

Design and implement a comprehensive test suite for the Sphinx MCP Server following project testing guidelines and leveraging the new `stdio-over-tcp` transport for integration testing.

## Testing Strategy

### Core Testing Principles

Following project guidelines:
1. **Dependency Injection Over Monkey-Patching**: Use injectable dependencies for testability
2. **Performance-Conscious**: Prefer in-memory filesystems (pyfakefs) over temp directories
3. **Avoid Monkey-Patching**: Never patch internal code; use dependency injection instead
4. **100% Coverage Goal**: Aim for complete line and branch coverage
5. **Test Behavior, Not Implementation**: Focus on observable behavior and contracts

### Test Categories by Numbering Convention

1. **Package Internals (000-099)**: Private utilities, base classes, foundational tests
2. **Public API by Layer (100+)**: Function/class-specific blocks in 100-increments
3. **Integration Tests (500+)**: Cross-module interactions and end-to-end workflows

## Test Architecture

### Core Test Infrastructure

```python
# tests/conftest.py - Shared fixtures and utilities
@pytest.fixture
def local_inventory():
    """Generate and return path to local test inventory."""
    
@pytest.fixture
def mock_inventory_data():
    """Provide mock inventory data for unit tests."""

@pytest.fixture
async def mcp_server_port():
    """Start MCP server and return dynamic port."""

class MCPTestClient:
    """Async context manager for MCP server testing."""
```

### Directory Structure (Following Project Standards)

```
tests/
├── README.md                   # Test numbering scheme and conventions
└── test_000_sphinxmcps/        # Package-specific test directory
    ├── __init__.py             # Test package init
    ├── fixtures.py             # Shared test fixtures and utilities
    ├── test_000_package.py     # Package infrastructure tests
    ├── test_010_internals.py   # Internal utilities and base classes
    ├── test_100_exceptions.py  # exceptions.py module (layer 0)
    ├── test_200_functions.py   # functions.py module (layer 1)
    ├── test_300_cli.py         # cli.py module (layer 2)
    ├── test_400_server.py      # server.py module (layer 3)
    └── test_500_integration.py # Cross-module integration tests
```

## Test Modules by Layer

### Package Infrastructure (test_000_package.py)

```python
# tests/test_000_sphinxmcps/test_000_package.py
def test_000_package_importable( ):
    ''' Package can be imported without errors. '''
    import sphinxmcps
    assert hasattr( sphinxmcps, '__version__' )

def test_010_main_entrypoint( ):
    ''' Package __main__ module provides CLI entrypoint. '''
    from sphinxmcps.__main__ import main
    assert callable( main )
```

### Internal Utilities (test_010_internals.py)

```python
# tests/test_000_sphinxmcps/test_010_internals.py
def test_000_common_imports_available( ):
    ''' Common imports module provides expected utilities. '''
    from sphinxmcps.__ import asyncio, json, sys
    assert asyncio.run is not None
    assert json.dumps is not None
    assert sys.stderr is not None

def test_010_globals_type_available( ):
    ''' Globals type is properly defined. '''
    from sphinxmcps.__ import Globals
    # Test Globals type structure if needed
```

### Exception Handling (test_100_exceptions.py)

```python
# tests/test_000_sphinxmcps/test_100_exceptions.py
def test_000_exception_hierarchy_inheritance( ):
    ''' Exception classes follow proper inheritance hierarchy. '''
    from sphinxmcps.exceptions import (
        InventoryNotFoundError, SphObjInvError, SphinxMCPError
    )
    
    exc = InventoryNotFoundError( "test.inv" )
    assert isinstance( exc, SphObjInvError )
    assert isinstance( exc, SphinxMCPError )

def test_010_validation_error_inheritance( ):
    ''' ValidationError follows proper hierarchy. '''
    from sphinxmcps.exceptions import InvalidURLError, ValidationError
    
    exc = InvalidURLError( "not-a-url" )
    assert isinstance( exc, ValidationError )

def test_100_inventory_not_found_message( ):
    ''' InventoryNotFoundError includes path in message. '''
    from sphinxmcps.exceptions import InventoryNotFoundError
    
    path = "/path/to/missing.inv"
    exc = InventoryNotFoundError( path )
    assert path in str( exc )

def test_110_invalid_domain_message( ):
    ''' InvalidDomainError includes domain and valid options. '''
    from sphinxmcps.exceptions import InvalidDomainError
    
    exc = InvalidDomainError( "invalid_domain", [ "py", "std" ] )
    assert "invalid_domain" in str( exc )
    assert "py" in str( exc )
```

### Business Logic (test_200_functions.py)

```python
# tests/test_000_sphinxmcps/test_200_functions.py
from pyfakefs.fake_filesystem_unittest import Patcher

def test_000_hello_default( ):
    ''' Hello function returns greeting with default name. '''
    from sphinxmcps.functions import hello
    result = hello( )
    assert result == "Hello, World!"

def test_010_hello_custom_name( ):
    ''' Hello function returns greeting with custom name. '''
    from sphinxmcps.functions import hello
    result = hello( "Claude" )
    assert result == "Hello, Claude!"

def test_100_extract_inventory_local_file( ):
    ''' Extract inventory processes local inventory files. '''
    from sphinxmcps.functions import extract_inventory
    with Patcher( ) as patcher:
        fs = patcher.fs
        # Create mock inventory file using dependency injection pattern
        inventory_path = '/fake/objects.inv'
        fs.create_file( inventory_path, contents = mock_inventory_bytes( ) )
        
        result = extract_inventory( inventory_path )
        assert 'project' in result
        assert 'objects' in result

def test_110_extract_inventory_with_domain_filter( ):
    ''' Extract inventory applies domain filtering correctly. '''
    from sphinxmcps.functions import extract_inventory
    with Patcher( ) as patcher:
        fs = patcher.fs
        inventory_path = '/fake/objects.inv'
        fs.create_file( inventory_path, contents = mock_inventory_bytes( ) )
        
        result = extract_inventory( inventory_path, domain = 'py' )
        assert result[ 'filters' ][ 'domain' ] == 'py'
        
def test_200_summarize_inventory_basic( ):
    ''' Summarize inventory provides human-readable summary. '''
    from sphinxmcps.functions import summarize_inventory
    with Patcher( ) as patcher:
        fs = patcher.fs
        inventory_path = '/fake/objects.inv'
        fs.create_file( inventory_path, contents = mock_inventory_bytes( ) )
        
        result = summarize_inventory( inventory_path )
        assert 'objects found' in result

def mock_inventory_bytes( ) -> bytes:
    ''' Create mock inventory bytes for testing. '''
    # Return minimal valid inventory data
    # This avoids external dependencies in unit tests
    pass
```

### CLI Module (test_300_cli.py)

```python
# tests/test_000_sphinxmcps/test_300_cli.py
import asyncio
from pyfakefs.fake_filesystem_unittest import Patcher

async def test_000_use_hello_default( ):
    ''' CLI use hello command with default name. '''
    result = await run_cli_command( [ 'use', 'hello' ] )
    assert "Hello, World!" in result.stdout

async def test_010_use_hello_custom_name( ):
    ''' CLI use hello command with custom name. '''
    result = await run_cli_command( [ 'use', 'hello', '--name', 'Test' ] )
    assert "Hello, Test!" in result.stdout

async def test_100_use_inventory_local( ):
    ''' CLI use inventory command processes local files. '''
    with Patcher( ) as patcher:
        fs = patcher.fs
        inventory_path = '/fake/objects.inv'
        fs.create_file( inventory_path, contents = mock_inventory_bytes( ) )
        
        result = await run_cli_command( [ 'use', 'inventory', '--source', inventory_path ] )
        assert "objects found" in result.stdout

async def test_110_use_inventory_with_filters( ):
    ''' CLI use inventory applies filtering correctly. '''
    with Patcher( ) as patcher:
        fs = patcher.fs
        inventory_path = '/fake/objects.inv'
        fs.create_file( inventory_path, contents = mock_inventory_bytes( ) )
        
        result = await run_cli_command( [
            'use', 'inventory', 
            '--source', inventory_path,
            '--domain', 'py',
            '--format', 'json'
        ] )
        data = json.loads( result.stdout )
        assert data[ 'filters' ][ 'domain' ] == 'py'

async def run_cli_command( args: list[ str ] ) -> subprocess.CompletedProcess:
    ''' Run CLI command and return result using dependency injection. '''
    # Use subprocess with proper isolation
    process = await asyncio.create_subprocess_exec(
        'hatch', 'run', 'sphinxmcps', *args,
        stdout = asyncio.subprocess.PIPE,
        stderr = asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate( )
    return MockCompletedProcess( 
        returncode = process.returncode,
        stdout = stdout.decode( ),
        stderr = stderr.decode( )
    )
```

### Server Module (test_400_server.py)

```python
# tests/test_000_sphinxmcps/test_400_server.py
import asyncio

async def test_000_serve_stdio_over_tcp_dynamic_port( ):
    ''' Server supports stdio-over-tcp with dynamic port assignment. '''
    process = await start_server_process( [ '--transport', 'stdio-over-tcp', '--port', '0' ] )
    try:
        port = await extract_dynamic_port( process )
        await test_mcp_connection( port )
    finally:
        await cleanup_server_process( process )

async def test_010_serve_stdio_over_tcp_fixed_port( ):
    ''' Server supports stdio-over-tcp with fixed port. '''
    port = await find_free_port( )
    process = await start_server_process( [ '--transport', 'stdio-over-tcp', '--port', str( port ) ] )
    try:
        await test_mcp_connection( port )
    finally:
        await cleanup_server_process( process )

async def test_100_serve_sse_transport( ):
    ''' Server supports SSE transport. '''
    port = await find_free_port( )
    process = await start_server_process( [ '--transport', 'sse', '--port', str( port ) ] )
    try:
        await test_http_connection( port )
    finally:
        await cleanup_server_process( process )

async def start_server_process( args: list[ str ] ):
    ''' Start server subprocess with dependency injection. '''
    return await asyncio.create_subprocess_exec(
        'hatch', 'run', 'sphinxmcps', 'serve', *args,
        stdout = asyncio.subprocess.PIPE,
        stderr = asyncio.subprocess.PIPE,
        preexec_fn = os.setsid
    )
```

## Integration Tests (test_500_integration.py)

### MCP Protocol Tests

```python
# tests/test_000_sphinxmcps/test_500_integration.py
async def test_000_mcp_protocol_handshake( ):
    ''' MCP server completes proper initialization handshake. '''
    async with mcp_test_server( ) as port:
        async with MCPTestClient( port ) as client:
            response = await client.initialize( )
            assert response[ 'result' ][ 'serverInfo' ][ 'name' ] == 'Sphinx MCP Server'

async def test_010_mcp_tools_listing( ):
    ''' MCP server lists all available tools correctly. '''
    async with mcp_test_server( ) as port:
        async with MCPTestClient( port ) as client:
            await client.initialize( )
            tools = await client.list_tools( )
            tool_names = [ tool[ 'name' ] for tool in tools[ 'result' ][ 'tools' ] ]
            assert 'hello' in tool_names
            assert 'extract_inventory' in tool_names
            assert 'summarize_inventory' in tool_names

async def test_100_mcp_hello_tool( ):
    ''' MCP hello tool returns expected response format. '''
    async with mcp_test_server( ) as port:
        async with MCPTestClient( port ) as client:
            await client.initialize( )
            result = await client.call_tool( 'hello', { 'name': 'Integration Test' } )
            expected = 'Hello, Integration Test!'
            assert result[ 'result' ][ 'structuredContent' ][ 'result' ] == expected

async def test_110_mcp_extract_inventory_tool( ):
    ''' MCP extract_inventory tool processes inventory files. '''
    with Patcher( ) as patcher:
        fs = patcher.fs
        inventory_path = '/fake/objects.inv'
        fs.create_file( inventory_path, contents = mock_inventory_bytes( ) )
        
        async with mcp_test_server( ) as port:
            async with MCPTestClient( port ) as client:
                await client.initialize( )
                result = await client.call_tool( 'extract_inventory', { 'source': inventory_path } )
                data = result[ 'result' ][ 'structuredContent' ][ 'result' ]
                assert 'project' in data
                assert 'objects' in data
```

### Error Handling Integration

```python
# tests/integration/test_mcp_errors.py
class TestMCPErrorHandling:
    async def test_tool_not_found(self, mcp_server_port):
        async with MCPTestClient(mcp_server_port) as client:
            await client.initialize()
            response = await client.call_tool('nonexistent_tool', {})
            assert 'error' in response
            
    async def test_invalid_inventory_source(self, mcp_server_port):
        async with MCPTestClient(mcp_server_port) as client:
            await client.initialize()
            result = await client.call_tool('extract_inventory', {'source': '/nonexistent/file.inv'})
            # Should return error structure in MCP format
            assert result['result']['isError'] == True
```

## Performance Tests

### Benchmarking

```python
# tests/performance/test_inventory_speed.py
class TestInventoryPerformance:
    def test_local_inventory_extraction_speed(self, local_inventory, benchmark):
        result = benchmark(extract_inventory, local_inventory)
        assert 'objects' in result
        
    def test_filtering_performance(self, large_inventory_data, benchmark):
        result = benchmark(
            extract_inventory, 
            large_inventory_data, 
            domain='py', 
            role='function'
        )
        assert len(result['objects']['py']) > 0

class TestMCPPerformance:
    async def test_tool_call_latency(self, mcp_server_port, benchmark):
        async def call_hello():
            async with MCPTestClient(mcp_server_port) as client:
                await client.initialize()
                return await client.call_tool('hello', {'name': 'Benchmark'})
        
        result = await benchmark(call_hello)
        assert 'Hello, Benchmark!' in str(result)
```

## Test Infrastructure

### MCPTestClient Implementation

```python
# tests/conftest.py
class MCPTestClient:
    """Async context manager for MCP testing."""
    
    def __init__(self, port: int):
        self.port = port
        self.reader = None
        self.writer = None
        self.request_id = 0
        
    async def __aenter__(self):
        self.reader, self.writer = await asyncio.open_connection('localhost', self.port)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()
            
    async def send_request(self, request: dict) -> dict:
        self.request_id += 1
        if 'id' not in request:
            request['id'] = self.request_id
            
        request_line = json.dumps(request) + '\n'
        self.writer.write(request_line.encode())
        await self.writer.drain()
        
        response_line = await self.reader.readline()
        return json.loads(response_line.decode().strip())
        
    async def initialize(self) -> dict:
        request = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"roots": {"listChanged": True}, "sampling": {}},
                "clientInfo": {"name": "test-client", "version": "1.0.0"}
            }
        }
        result = await self.send_request(request)
        
        # Send initialized notification
        await self.send_request({
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        })
        
        return result
        
    async def list_tools(self) -> dict:
        return await self.send_request({
            "jsonrpc": "2.0",
            "method": "tools/list"
        })
        
    async def call_tool(self, name: str, arguments: dict) -> dict:
        return await self.send_request({
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {"name": name, "arguments": arguments}
        })
```

### Server Management

```python
# tests/conftest.py
@pytest.fixture
async def mcp_server_port():
    """Start MCP server and return dynamic port."""
    process = await asyncio.create_subprocess_exec(
        'hatch', 'run', 'sphinxmcps', 'serve', 
        '--transport', 'stdio-over-tcp', '--port', '0',
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        preexec_fn=os.setsid
    )
    
    # Extract dynamic port from stderr
    await asyncio.sleep(1)
    stderr_data = await process.stderr.read(1024)
    port_match = re.search(r'127\.0\.0\.1:(\d+)', stderr_data.decode())
    
    if not port_match:
        await cleanup_process(process)
        pytest.fail("Could not extract dynamic port from server output")
        
    port = int(port_match.group(1))
    
    try:
        yield port
    finally:
        await cleanup_process(process)

async def cleanup_process(process):
    """Clean up server process and children."""
    try:
        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
        await asyncio.wait_for(process.wait(), timeout=3.0)
    except (ProcessLookupError, asyncio.TimeoutError):
        try:
            os.killpg(os.getpgid(process.pid), signal.SIGKILL)
            await process.wait()
        except ProcessLookupError:
            pass
```

## Pytest Configuration

### pytest.ini

```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --strict-markers
    --strict-config
    -ra
markers =
    slow: marks tests as slow (integration tests)
    integration: marks tests as integration tests  
    cli: marks tests as CLI tests
    unit: marks tests as unit tests
    performance: marks tests as performance benchmarks
asyncio_mode = auto
```

## Shared Test Infrastructure (fixtures.py)

```python
# tests/test_000_sphinxmcps/fixtures.py
import asyncio
import json
import os
import signal
from pathlib import Path
from contextlib import asynccontextmanager
from pyfakefs.fake_filesystem_unittest import Patcher

class MCPTestClient:
    ''' Async context manager for MCP server testing with dependency injection. '''
    
    def __init__( self, port: int ):
        self.port = port
        self.reader = None
        self.writer = None
        self.request_id = 0
        
    async def __aenter__( self ):
        self.reader, self.writer = await asyncio.open_connection( 'localhost', self.port )
        return self
        
    async def __aexit__( self, exc_type, exc_val, exc_tb ):
        if self.writer:
            self.writer.close( )
            await self.writer.wait_closed( )
            
    async def send_request( self, request: dict ) -> dict:
        self.request_id += 1
        if 'id' not in request:
            request[ 'id' ] = self.request_id
            
        request_line = json.dumps( request ) + '\n'
        self.writer.write( request_line.encode( ) )
        await self.writer.drain( )
        
        response_line = await self.reader.readline( )
        return json.loads( response_line.decode( ).strip( ) )
        
    async def initialize( self ) -> dict:
        ''' Complete MCP initialization handshake. '''
        request = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": { "roots": { "listChanged": True }, "sampling": { } },
                "clientInfo": { "name": "test-client", "version": "1.0.0" }
            }
        }
        result = await self.send_request( request )
        
        # Send initialized notification
        await self.send_request( {
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        } )
        
        return result
        
    async def list_tools( self ) -> dict:
        return await self.send_request( {
            "jsonrpc": "2.0",
            "method": "tools/list"
        } )
        
    async def call_tool( self, name: str, arguments: dict ) -> dict:
        return await self.send_request( {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": { "name": name, "arguments": arguments }
        } )

@asynccontextmanager
async def mcp_test_server( ):
    ''' Context manager for MCP server with dependency injection. '''
    process = await asyncio.create_subprocess_exec(
        'hatch', 'run', 'sphinxmcps', 'serve', 
        '--transport', 'stdio-over-tcp', '--port', '0',
        stdout = asyncio.subprocess.PIPE,
        stderr = asyncio.subprocess.PIPE,
        preexec_fn = os.setsid
    )
    
    try:
        # Extract dynamic port from stderr
        await asyncio.sleep( 1 )
        stderr_data = await process.stderr.read( 1024 )
        port_match = re.search( r'127\.0\.0\.1:(\d+)', stderr_data.decode( ) )
        
        if not port_match:
            raise RuntimeError( "Could not extract dynamic port from server output" )
            
        port = int( port_match.group( 1 ) )
        yield port
        
    finally:
        await cleanup_server_process( process )

async def cleanup_server_process( process ):
    ''' Clean up server process using dependency injection pattern. '''
    try:
        os.killpg( os.getpgid( process.pid ), signal.SIGTERM )
        await asyncio.wait_for( process.wait( ), timeout = 3.0 )
    except ( ProcessLookupError, asyncio.TimeoutError ):
        try:
            os.killpg( os.getpgid( process.pid ), signal.SIGKILL )
            await process.wait( )
        except ProcessLookupError:
            pass

def mock_inventory_bytes( ) -> bytes:
    ''' Create minimal valid inventory data for testing. '''
    # Return minimal sphobjinv-compatible inventory data
    # This avoids external dependencies in unit tests
    # Implementation would create valid inventory format
    pass
```

### Test Commands (Following Project Standards)

```bash
# Run all tests with coverage
hatch --env develop run testers

# Run linting checks
hatch --env develop run linters

# Run specific test modules
hatch --env develop run pytest tests/test_000_sphinxmcps/test_100_functions.py

# Run tests by numbering ranges
hatch --env develop run pytest tests/test_000_sphinxmcps/test_0*.py  # Infrastructure
hatch --env develop run pytest tests/test_000_sphinxmcps/test_[1-4]*.py  # API layers
hatch --env develop run pytest tests/test_000_sphinxmcps/test_5*.py  # Integration

# Generate coverage reports
hatch --env develop run coverage report --show-missing
hatch --env develop run coverage html
```

## Tests README.md

```markdown
# Test Organization for Sphinx MCP Server

## Numbering Scheme

This test suite follows the project standard numbering conventions:

### Module Organization
- `test_000_package.py` - Package infrastructure and imports
- `test_010_internals.py` - Internal utilities and common imports
- `test_100_exceptions.py` - Exception hierarchy and error handling (layer 0)
- `test_200_functions.py` - Core business logic functions (layer 1)  
- `test_300_cli.py` - Command-line interface (layer 2)
- `test_400_server.py` - MCP server functionality (layer 3)
- `test_500_integration.py` - Cross-module integration tests

### Function Numbering within Modules
- `000-099`: Foundational functionality
- `100-199`: Primary feature blocks  
- `200-299`: Secondary feature blocks
- Increment by 10-20 for related test groups

## Testing Principles Applied

### Dependency Injection
All tests use dependency injection rather than monkey-patching:
- Subprocess testing for CLI and server components
- In-memory filesystem (pyfakefs) for file operations
- Mock external services but not internal code

### Performance Considerations
- Use `pyfakefs.Patcher()` for filesystem operations
- Minimize temp directory usage
- Isolate external dependencies

### Coverage Strategy
- Target 100% line and branch coverage
- Use `# pragma: no cover` only as last resort
- Focus on behavioral testing over implementation details

## MCP Testing Infrastructure

### stdio-over-tcp Transport
Tests leverage the built-in `stdio-over-tcp` transport for integration testing:
- Dynamic port assignment eliminates conflicts
- No external dependencies (socat not required)
- Clean subprocess management with proper cleanup

### Test Fixtures
- `MCPTestClient`: Async context manager for MCP protocol testing
- `mcp_test_server()`: Context manager for server subprocess management
- `mock_inventory_bytes()`: Creates minimal test inventory data

## Special Considerations

### Async Testing
All integration tests are async and use proper asyncio patterns:
- Server subprocess management
- TCP connection handling
- Graceful cleanup on test completion

### Exception Testing
Exception tests verify both inheritance hierarchy and message content without monkey-patching internal code.
```

## Implementation Priority

### Phase 1: Foundation 
1. Create `tests/README.md` with numbering scheme and conventions
2. Set up `tests/test_000_sphinxmcps/` directory structure  
3. Implement `fixtures.py` with MCPTestClient and utilities
4. Package infrastructure tests (`test_000_package.py`, `test_010_internals.py`)

### Phase 2: Core Functionality
1. Exception hierarchy tests (`test_100_exceptions.py`) 
2. Business logic tests (`test_200_functions.py`) with pyfakefs
3. CLI command tests (`test_300_cli.py`) using subprocess injection
4. Target 100% coverage for core modules

### Phase 3: Server and Integration
1. Server transport tests (`test_400_server.py`) with stdio-over-tcp
2. Full MCP protocol integration tests (`test_500_integration.py`)
3. End-to-end workflow testing
4. Verify all anti-patterns are avoided

### Phase 4: Validation and Polish
1. Run full validation: `hatch --env develop run testers && hatch --env develop run linters`
2. Verify coverage improvements without regressions
3. Document any pragma directives with rationale
4. Ensure dependency injection patterns throughout

## Success Criteria (Project Standards)

### Coverage and Quality
- [ ] **100% Coverage Goal**: Target complete line and branch coverage
- [ ] **No Monkey-Patching**: All tests use dependency injection
- [ ] **Performance-Conscious**: pyfakefs for filesystem, minimal temp directories
- [ ] **Behavioral Testing**: Focus on contracts, not implementation details

### Test Organization  
- [ ] **Systematic Numbering**: Follow project numbering conventions exactly
- [ ] **Layer-Based Structure**: Tests organized by module layer (exceptions→functions→cli→server→integration)
- [ ] **Proper Documentation**: README.md explains numbering scheme and principles

### Validation
- [ ] **All Tests Pass**: `hatch --env develop run testers` succeeds
- [ ] **Clean Linting**: `hatch --env develop run linters` passes
- [ ] **No Coverage Regression**: New tests improve overall coverage
- [ ] **Architecture Compliance**: No violations of project testing principles

---

*This test suite architecture ensures comprehensive coverage while leveraging the new stdio-over-tcp transport for reliable, dependency-free integration testing.*