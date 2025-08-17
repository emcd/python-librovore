# Extension Manager Testing Plan

## Overview

Create comprehensive tests for the xtnsmgr module covering installation, caching, import management, and integration scenarios. Use fake extension packages with PEP 508/440 file:// URLs for realistic but controlled testing.

## 1. Test Package Infrastructure

### Fake Extension Package Structure
```
tests/fixtures/fake-extension/
├── pyproject.toml              # Minimal package metadata
├── fake_extension/
│   ├── __init__.py
│   ├── processor.py            # Main processor implementation
│   └── data.pth               # Test .pth file processing
└── README.md                  # Package documentation
```

**Package Requirements:**
- Implements expected `register(arguments)` interface
- Returns mock processor with basic functionality
- Includes .pth files for import path testing
- Supports different argument configurations
- Minimal dependencies to avoid conflicts

### Test Package Variants
- **Basic Package**: Simple processor, no .pth files
- **Complex Package**: Multiple modules, .pth files, dependencies
- **Broken Package**: Invalid structure for error testing
- **Version Package**: Multiple versions for upgrade/conflict testing

## 2. Test Organization Strategy

### Test File Structure
```
tests/test_000_librovore/
├── test_610_configuration.py   # Extension config validation
├── test_620_installation.py    # Package installation testing
├── test_630_importation.py     # Import path and .pth processing
├── test_640_cachemgr.py        # Cache behavior and TTL
├── test_650_processors.py      # Processor loading and registration
├── test_660_integration.py     # End-to-end scenarios
└── test_670_error_handling.py  # Failure modes and recovery
```

### Test Infrastructure
- **Isolated Test Environment**: Separate cache directory per test
- **Mock Network Conditions**: Simulate failures, timeouts, retries
- **Platform Testing**: Test platform ID calculation and isolation
- **Cleanup Automation**: Ensure no test pollution between runs

## 3. Core Test Scenarios

### Installation Testing (`test_620_installation.py`)
- **PEP 508 file:// URL Installation**: Local package installation via file URLs
- **Parallel Installation**: Multiple packages installing concurrently
- **Retry Logic**: Network failure simulation with exponential backoff
- **Cache Hit/Miss**: Verify cache usage vs fresh installation
- **Platform Isolation**: Ensure platform-specific cache separation
- **TTL Behavior**: Cache expiration and refresh logic

### Cache Management (`test_640_cachemgr.py`)
- **Cache Path Calculation**: SHA256-based deterministic paths
- **Platform ID Generation**: Correct platform identification
- **Metadata Persistence**: Cache info saving and loading
- **TTL Expiration**: Time-based cache invalidation
- **Cache Cleanup**: Expired cache removal
- **Cache Corruption**: Invalid metadata handling and recovery

### Import Management (`test_630_importation.py`)
- **sys.path Manipulation**: Correct path addition and removal
- **.pth File Processing**: Various .pth file scenarios:
  - Simple path additions
  - Import statement execution
  - Hidden file detection (platform-specific)
  - Encoding variations (UTF-8-BOM, locale)
  - Error handling for malformed .pth files
- **Module Import**: Successful processor module loading
- **Import Cleanup**: Proper sys.path restoration

### Configuration Testing (`test_610_configuration.py`)
- **Valid Configurations**: Proper extension config parsing
- **Invalid Configurations**: Error handling for malformed configs
- **Built-in vs External**: Correct classification and handling
- **Argument Extraction**: Extension-specific argument passing
- **Enable/Disable Logic**: Respect enabled/disabled status

### Processor Management (`test_650_processors.py`)
- **Registration Process**: End-to-end processor registration
- **Built-in Processors**: Loading existing Sphinx processor
- **External Processors**: Loading from installed packages
- **Mixed Scenarios**: Built-in and external processors together
- **Registration Failures**: Graceful handling of processor failures

## 4. Integration Testing (`test_660_integration.py`)

### End-to-End Scenarios
- **Complete Loading Pipeline**: Configuration → Installation → Import → Registration
- **Mixed Extension Types**: Built-in and external extensions together
- **Real Configuration**: Using actual TOML extension configurations
- **Performance Testing**: Parallel installation performance verification
- **Memory Usage**: Ensure no memory leaks or excessive usage

### CLI Integration
- **Extension Loading in CLI**: Verify extensions load during CLI startup
- **MCP Server Integration**: Extensions available in server context
- **Error Propagation**: Proper error reporting to users

## 5. Error Handling Testing (`test_670_error_handling.py`)

### Installation Failures
- **Network Simulation**: Connection failures, timeouts
- **Invalid Packages**: Malformed package structures
- **Version Conflicts**: Incompatible dependency scenarios
- **Permission Issues**: Write permission failures
- **Disk Space**: Insufficient space simulation

### Import Failures
- **Module Import Errors**: Missing dependencies, syntax errors
- **Registration Failures**: Invalid processor interfaces
- **sys.path Conflicts**: Multiple packages with same names

### Recovery Scenarios
- **Cache Corruption Recovery**: Automatic cache invalidation and retry
- **Partial Installation**: Handling some successes, some failures
- **Graceful Degradation**: Continue with available processors

## 6. Test Implementation Strategy

### Test Environment Isolation
- **Temporary Directories**: Isolated cache and installation paths
- **Environment Variables**: Override cache locations for testing
- **Mock External Dependencies**: Control uv behavior and responses
- **Cleanup Automation**: Ensure pristine state between tests

### Mock Strategy
- **Network Calls**: Mock HTTP requests for failure simulation
- **File System Operations**: Mock disk space, permissions
- **Process Execution**: Mock uv subprocess calls
- **Time-based Operations**: Mock time for TTL testing

### Performance Considerations
- **Fast Tests**: Most tests should run quickly with mocks
- **Integration Tests**: Slower tests with real package installation
- **Parallel Execution**: Tests should be parallelizable
- **Resource Cleanup**: Prevent test resource accumulation

## 7. Specific Test Cases

### File URL Testing
```python
# Test PEP 508 file:// URL installation
fake_extension_path = "file://" + str(Path("tests/fixtures/fake-extension").absolute())
await cachemgr.ensure_package(fake_extension_path)
```

### .pth File Scenarios
- **Simple Path**: `relative/path/to/module`
- **Absolute Path**: `/absolute/path/to/module`
- **Import Statement**: `import sys; sys.path.append('dynamic_path')`
- **Hidden Files**: `.hidden.pth` (should be ignored)
- **Encoding Test**: UTF-8 BOM, non-ASCII characters
- **Malformed Files**: Invalid syntax, broken imports

### Cache Behavior Testing
- **TTL Expiration**: Mock time advancement to test expiration
- **Platform ID**: Test on different simulated platforms
- **Cache Corruption**: Malformed JSON metadata files
- **Concurrent Access**: Multiple processes accessing same cache

### Error Recovery Testing
- **Network Failures**: Timeout, connection refused, DNS errors
- **Partial Downloads**: Interrupted package installation
- **Invalid Packages**: Missing setup.py, import errors
- **Permission Denied**: Read-only cache directories

## 8. Mock Implementation Details

### uv Process Mocking
```python
# Mock successful uv installation
@patch('asyncio.create_subprocess_exec')
async def test_successful_installation(mock_subprocess):
    mock_process = Mock()
    mock_process.communicate.return_value = (b'', b'')
    mock_process.returncode = 0
    mock_subprocess.return_value = mock_process
```

### File System Mocking
```python
# Mock disk space errors
@patch('pathlib.Path.mkdir')
def test_disk_space_error(mock_mkdir):
    mock_mkdir.side_effect = OSError("No space left on device")
```

### Time Mocking for TTL
```python
# Mock time for TTL testing
@patch('datetime.datetime')
def test_cache_expiration(mock_datetime):
    mock_datetime.now.return_value = datetime(2024, 1, 1)  # Initial time
    # ... perform caching operation ...
    mock_datetime.now.return_value = datetime(2024, 1, 2)  # 24+ hours later
    # ... verify cache expiration ...
```

## 9. Documentation and Maintenance

### Test Documentation
- **Test Purpose**: Clear description of what each test verifies
- **Setup Requirements**: Any special configuration needed
- **Failure Debugging**: Guide for investigating test failures
- **Mock Explanations**: Document mock behaviors and rationales

### Maintenance Strategy
- **Test Package Updates**: How to update fake extension packages
- **Platform Testing**: Ensuring cross-platform compatibility
- **Performance Monitoring**: Track test execution time
- **Coverage Analysis**: Ensure comprehensive xtnsmgr coverage

## 10. Success Criteria

### Functional Coverage
- All xtnsmgr public interfaces tested
- All error paths verified
- Platform-specific behaviors validated
- Integration with existing systems confirmed

### Quality Metrics
- 95%+ test coverage for xtnsmgr modules
- All tests pass on major platforms
- Performance tests verify parallel installation benefits
- Error simulation tests confirm graceful failure handling

## 11. Implementation Phases

### Phase 1: Infrastructure Setup ✓ COMPLETED
- ✓ Create fake extension packages in `tests/fixtures/`
  - Created `tests/fixtures/fake-extension/` with working package structure
  - Created `tests/fixtures/broken-extension/` for error testing
- ✓ Set up test directories and isolation utilities
  - Added `tests/test_000_librovore/test_utils.py` with helper functions
  - Added numbered test files: `test_610_configuration.py`, `test_620_installation.py`
- ✓ Implement basic test utilities and mock frameworks
  - Added URL helpers for fake packages
  - Added mock utilities for subprocess and time

### Phase 2: Unit Testing
- Test individual xtnsmgr modules in isolation
- Verify core functionality: installation, caching, importing
- Focus on fast, mock-heavy tests

### Phase 3: Integration Testing
- End-to-end extension loading scenarios
- CLI and MCP server integration testing
- Performance and reliability validation

### Phase 4: Error Testing
- Comprehensive failure mode testing
- Recovery scenario validation
- Edge case and boundary testing

## 12. Test Execution Strategy

### Local Development
- Fast unit tests run during development
- Integration tests run before commits
- Error tests run in CI/CD pipeline

### CI/CD Integration
- All test phases run on multiple platforms
- Performance regression detection
- Coverage reporting and trends

### Test Data Management
- Fake packages checked into repository
- Test cache directories in `.auxiliary/test-caches/`
- Automatic cleanup of test artifacts

This comprehensive testing plan ensures the xtnsmgr module is thoroughly validated across all scenarios before moving to the project rename phase.
