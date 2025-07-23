# Test Organization for Sphinx MCP Server

## Numbering Scheme

This test suite follows the project standard numbering conventions:

### Module Organization
- `test_000_package.py` - Package infrastructure and imports
- `test_010_internals.py` - Internal utilities and common imports (renamed from test_010_base.py)
- `test_100_exceptions.py` - Exception hierarchy and error handling (layer 0)
- `test_200_detection.py` - Detection system and processor selection (layer 1)
- `test_210_functions.py` - Core business logic functions (layer 1)  
- `test_300_cli.py` - Command-line interface (layer 2)
- `test_400_server.py` - MCP server functionality (layer 3)
- `test_500_integration.py` - Cross-module integration tests

### Extension Manager Subpackage Tests (600s)
- `test_610_xtnsmgr_configuration.py` - Configuration validation and extraction
- `test_620_xtnsmgr_importation.py` - Package importing and .pth file processing  
- `test_630_xtnsmgr_installation.py` - Package installation via uv
- `test_640_xtnsmgr_cachemgr.py` - Cache management and coordination
- `test_650_xtnsmgr_processors.py` - Processor extraction and registration

### Processor-Specific Tests (700s)
- `test_710_sphinx.py` - Sphinx processor implementation (future)

### Function Numbering within Modules
- `000-099`: Foundational functionality
- `100-199`: Primary feature blocks  
- `200-299`: Secondary feature blocks
- `300-399`: Tertiary feature blocks
- Increment by 10-20 for related test groups

#### Special: Detection Module Function Organization
`test_200_detection.py` uses specialized numbering:
- `100-199`: DetectionsCacheEntry tests
- `200-299`: DetectionsCache tests  
- `300-399`: determine_processor_optimal tests
- `700-799`: Sphinx processor integration tests (future)

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

## Commands

```bash
# Run all tests with coverage (excludes slow tests by default)
hatch --env develop run testers

# Run linting checks
hatch --env develop run linters

# Run specific test modules
hatch --env develop run pytest tests/test_000_sphinxmcps/test_100_exceptions.py

# Run slow tests (subprocess-based CLI and server tests)
hatch --env develop run pytest -m "slow"

# Run all tests including slow tests
hatch --env develop run pytest -m ""

# Run tests by numbering ranges
hatch --env develop run pytest tests/test_000_sphinxmcps/test_0*.py  # Infrastructure
hatch --env develop run pytest tests/test_000_sphinxmcps/test_[1-4]*.py  # API layers
hatch --env develop run pytest tests/test_000_sphinxmcps/test_5*.py  # Integration

# Generate coverage reports
hatch --env develop run coverage report --show-missing
hatch --env develop run coverage html
```