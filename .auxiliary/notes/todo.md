# Release 1.0 TODO - Sphinx MCP Server

## Core Architecture (High Priority)

**🎉 Extension Manager (xtnsmgr) - COMPLETED**: Full implementation with cache-driven package management, .pth file processing, and simplified processor orchestration. See `xtnsmgr.md` for complete documentation.

### 🔌 Plugin/Extensions Architecture - COMPLETED
- [x] **Design plugin interface**: Define abstract base classes for inventory and documentation providers
- [x] **Retrofit Sphinx support**: Convert current Sphinx inventory/documentation extraction to plugin
- [x] **Plugin discovery system**: Mechanism to register and load plugins
- [x] **Plugin API stability**: Ensure backwards compatibility for plugins
- [x] **Refactor Sphinx code**: Move Sphinx-specific functions from `functions.py` to `processors/sphinx.py`
- [x] **Code organization**: Organize all processor functions in lexicographical order
- [x] **Test decoupling**: Remove tests that couple to private implementation details
- [x] **Plugin configuration**: Extension configuration system with validation and argument extraction
- [x] **External plugin installation**: Complete xtnsmgr implementation with cache-driven package management
- [x] **SphinxDetection refactoring**: Replace metadata dict with typed dataclass attributes

### 🏗️ Sphinx Processor Improvements (Current Priority)
- [ ] **Refactor into subpackage**: Break large processors/sphinx.py into organized subpackage
- [ ] **Comprehensive testing**: Add tests for processors/sphinx module (currently 51% coverage)
- [ ] **xtnsmgr.processors testing**: Add tests for processor extraction and registration (currently 45% coverage)

### 💾 Caching System
- [ ] **Inventory caching**: Cache downloaded `objects.inv` files with TTL
- [ ] **Documentation caching**: Cache fetched HTML content to reduce network requests
- [ ] **Cache management**: Configurable TTL, cache invalidation, size limits
- [ ] **Cache storage**: `.auxiliary/caches/{inventories,documentation}/` with metadata
- [ ] **Cache CLI commands**: Ability to inspect, clear, and manage cache

## Code Quality & Maintenance (Medium Priority)

### 🔧 Technical Debt
- [ ] **Type alias consolidation**: Move duplicated type aliases from `cli.py` and `functions.py` to `interfaces.py`
- [x] **Code style cleanup**: Remove obvious comments, fix delimiter placement, lexicographical sorting
- [x] **Function refactoring**: Ensure functions stay under 30 lines, modules under 600 lines

### 🧪 Testing Strategy Improvements
- [x] **Reduce test overlap**: Target specific uncovered lines instead of comprehensive functionality tests
- [ ] **Mock heavy operations**: Replace inventory parsing with mocks for unit tests
- [ ] **Separate test types**: Split fast unit tests from slower integration tests
- [ ] **Easy coverage wins**: Target `interfaces.py` file output streams and CLI error handling
- [ ] **Focus on hard gaps**: Mock HTTP/network failures for error path testing

## API Stability (High Priority)

### 📋 Interface Finalization
- [ ] **CLI command stability**: Finalize argument names and behavior
- [ ] **MCP tool parameters**: Lock down parameter names and types
- [ ] **Error message consistency**: Standardize error reporting across all tools
- [ ] **Output format stability**: Ensure consistent JSON structure for MCP responses

### 📖 Documentation
- [ ] **API documentation**: Complete documentation for all public interfaces
- [ ] **Plugin development guide**: Documentation for creating custom plugins
- [ ] **Usage examples**: Real-world examples for common use cases
- [ ] **Migration guide**: If any breaking changes are needed before 1.0

## Performance & Production Readiness (Medium Priority)

### ⚡ Performance
- [ ] **Async optimization**: Ensure all network operations are properly async
- [ ] **Connection pooling**: Reuse HTTP connections for multiple requests
- [ ] **Parallel operations**: Allow concurrent inventory/documentation fetching
- [ ] **Memory efficiency**: Profile and optimize memory usage for large inventories

### 🛡️ Production Features
- [ ] **Error handling robustness**: Comprehensive error handling for all failure modes
- [ ] **Rate limiting**: Respect server rate limits and provide user controls
- [ ] **Timeout configuration**: Configurable timeouts for all network operations
- [ ] **Logging and monitoring**: Structured logging for production debugging

## Release Preparation (Low Priority)

### 📦 Package Management
- [ ] **Version pinning**: Lock dependency versions for stability
- [ ] **Package metadata**: Complete pyproject.toml with proper classifiers
- [ ] **Distribution testing**: Test installation from PyPI test server
- [ ] **Documentation publishing**: Ensure docs build and publish correctly

### 🔍 Quality Assurance
- [ ] **Integration testing**: End-to-end testing with real documentation sites
- [ ] **Cross-platform testing**: Ensure compatibility across OS platforms
- [ ] **Performance benchmarking**: Establish baseline performance metrics
- [ ] **Security review**: Review for potential security issues

## Post-1.0 Considerations

### 🌟 Extension Ideas (Not for 1.0)
- Support for non-Sphinx documentation formats
- Full-text search across documentation content
- Interactive CLI browser mode
- Multi-site search capabilities
- Advanced relationship mapping between objects

## Test Analysis Integration

### Coverage Gap Strategy
Based on coverage analysis showing 75% overall coverage with significant test path overlap:

**Immediate Focus:**
- Target easy wins in `interfaces.py` (file output streams)
- Mock network failures for `functions.py` HTTP error paths
- CLI error handling in `cli.py` validation paths

**Testing Efficiency:**
- Stop adding comprehensive tests for stable functionality
- Use targeted mocking for uncovered error paths
- Separate unit tests (fast, mocked) from integration tests (slow, real data)
- Focus on testing plugin architecture thoroughly once implemented

## Success Criteria for 1.0

- [ ] **Plugin architecture** allows easy addition of new documentation sources
- [ ] **Caching system** reduces redundant network requests significantly
- [ ] **API stability** with semantic versioning commitment
- [ ] **90%+ test coverage** through targeted testing strategy
- [ ] **Production ready** with proper error handling and performance
- [ ] **Documentation complete** for users and plugin developers