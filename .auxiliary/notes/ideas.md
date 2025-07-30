# Future Development Ideas - Documentation MCP Server

## Project Rebranding

### Proposed Name Change: `librovore`
**Current limitation**: `sphinx-mcp-server` name no longer fits the expanded vision with plugin/extension architecture supporting multiple documentation systems.

**Proposed name**: `librovore` (from Latin *librovorus* - "book devourer")
- **Perfect metaphor**: Captures how LLMs "devour" and process documentation
- **Morphologically correct**: Follows Latin o-stem pattern (library, librovore)
- **Memorable**: Evocative and immediately suggests the purpose
- **Available**: Not taken on PyPI (as of 2025-01-19)
- **Future-proof**: Not tied to any specific documentation tool

**Alternative considered**: `librocule` (little book), but `librovore` better captures the active processing nature.

### Migration Strategy
- Package rename: `sphinx-mcp-server` → `librovore`
- GitHub repository rename
- Update all documentation and branding
- PyPI package transfer/deprecation notice
- Maintain backward compatibility during transition period

## Builtin Processors Development Strategy

### Release Strategy: Graduated Rollout
**Phase 1 (Current)**: Ship with Sphinx processor to establish pattern and get community feedback
**Phase 2**: Add high-impact processors that demonstrate cross-tool capability
**Phase 3**: Expand to specialized/niche documentation systems

### Immediate Priority Processors (Phase 2)

#### 1. MkDocs Processor 🎯 **HIGH PRIORITY**
- **Rationale**: Extremely popular in Python ecosystem, fast-growing
- **Technical feasibility**: Supports `objects.inv` via `mkdocstrings` plugin
- **User impact**: Demonstrates cross-tool capability immediately
- **Implementation**: Similar to Sphinx but with MkDocs-specific parsing

#### 2. OpenAPI/Swagger Processor 🎯 **HIGH IMPACT**
- **Rationale**: REST API documentation is massive use case for LLMs
- **Technical feasibility**: Well-structured JSON/YAML input format
- **Differentiation**: Inventory-style search vs existing static MCP servers
- **Implementation**: Parse OpenAPI spec → generate inventory-like search interface
- **Note**: Research existing MCP servers to avoid duplication

#### 3. PyDoctor Processor 🤔 **INVESTIGATE**
- **Rationale**: Alternative Python documentation generator
- **Technical uncertainty**: Need to verify `objects.inv` format support
- **User base**: Smaller than Sphinx/MkDocs but still significant
- **Priority**: Lower due to smaller ecosystem impact

### Future Expansion Processors (Phase 3)

#### Documentation Systems
- **rustdoc**: Growing Rust ecosystem, JSON output available
- **JSDoc**: JavaScript/TypeScript ecosystem
- **Doxygen**: C/C++ documentation with XML output

#### API/Schema Systems
- **GraphQL Introspection** 🎯 **INNOVATIVE**: Schema exploration perfect for LLMs
- **AsyncAPI**: Async API specifications
- **JSON Schema**: Schema documentation and validation

#### Development Platform Integrations
- **GitHub API**: Extract documentation from repository structures
- **GitLab API**: Similar to GitHub but different ecosystem
- **Confluence**: Enterprise documentation systems

### Technical Implementation Notes

#### MCP Sweet Spot Analysis
**Ideal processors provide**:
- **Semantic search capabilities**: Not just static file serving
- **Contextual relationships**: Understanding connections between concepts
- **Structured exploration**: Inventory-style browsing and discovery
- **LLM-friendly output**: Clean, parseable, context-rich responses

**Avoid duplicating**:
- Simple file serving that existing MCP servers handle well
- Static content that doesn't benefit from structured exploration
- Tools where existing MCP integration is already excellent

## Plugin Architecture Concepts

### Core Plugin System
- **Abstract base classes**: `InventoryProvider`, `DocumentationExtractor`, `SearchProvider`
- **Plugin discovery**: Auto-discovery from entry points or explicit registration
- **Plugin lifecycle**: Initialize, configure, validate, execute, cleanup
- **Plugin dependencies**: Allow plugins to depend on other plugins or services
- **Plugin metadata**: Version compatibility, capabilities, configuration schema

### Built-in Plugins Implementation Priority
- **Sphinx plugin**: ✅ **Current reference implementation** (Phase 1)
- **MkDocs plugin**: 🎯 **Next priority** - Popular Python ecosystem tool (Phase 2)
- **OpenAPI plugin**: 🎯 **High impact** - API documentation for LLMs (Phase 2)
- **GraphQL plugin**: 🎯 **Innovative** - Schema introspection capabilities (Phase 3)
- **JSDoc plugin**: JavaScript/TypeScript ecosystem support (Phase 3)
- **rustdoc plugin**: Growing Rust ecosystem (Phase 3)
- **GitHub plugin**: Repository documentation extraction (Phase 3)
- **ReadTheDocs API plugin**: Enhanced API integration (Phase 3)

### Plugin Configuration System
- **Plugin-specific parameters**: Each plugin defines its own parameter schema
- **Configuration inheritance**: Global settings with plugin-specific overrides
- **Dynamic configuration**: Runtime configuration changes without restart
- **Configuration validation**: Schema-based validation with helpful error messages

## Advanced Caching Strategies

### Multi-Level Caching
- **Memory cache**: Hot data in memory with LRU eviction
- **Disk cache**: Persistent storage with TTL and size management
- **Distributed cache**: Redis/Memcached support for multi-instance deployments
- **Cache hierarchy**: Memory → Disk → Network with intelligent promotion

### Smart Cache Invalidation
- **ETag support**: Use HTTP ETags for efficient cache validation
- **Last-modified tracking**: Monitor documentation source changes
- **Dependency tracking**: Invalidate dependent content when sources change
- **Incremental updates**: Partial cache updates instead of full replacement

### Cache Analytics
- **Hit/miss ratios**: Monitor cache effectiveness
- **Performance metrics**: Track latency improvements from caching
- **Size monitoring**: Track cache growth and storage usage
- **Eviction reporting**: Understand what gets evicted and why

## Advanced Documentation Features

### Content Relationship Mapping
- **Inheritance hierarchies**: Track class inheritance trees
- **Cross-references**: Map all internal and external links
- **Usage examples**: Find and extract example code from documentation
- **See-also networks**: Build graphs of related objects

### Enhanced Content Extraction
- **Multi-theme support**: Adapt parsing for different Sphinx themes (Alabaster, RTD, Book, etc.)
- **Rich media handling**: Extract diagrams, charts, and embedded content
- **Code example extraction**: Parse and validate code examples from documentation
- **Version comparison**: Compare documentation across different versions

### Full-Text Search Engine
- **Search index building**: Build comprehensive search indices from documentation content
- **Relevance scoring**: Advanced scoring algorithms beyond simple text matching
- **Faceted search**: Filter by object type, module, topic, etc.
- **Search suggestions**: Auto-complete and query suggestions
- **Search analytics**: Track popular queries and improve results

## Immediate Enhancements

### Advanced Filtering and Search
- [ ] **Boolean search operators**: Support `domain=py AND role=class` expressions
- [ ] **Case-sensitive search**: Option for exact case matching
- [ ] **Content snippets**: Include relevant content excerpts in search results

### Enhanced Output Formats
- [ ] **Signature cleanup**: Remove Sphinx artifacts like `¶` from signatures
- [ ] **Code examples extraction**: Parse and format code blocks from documentation
- [ ] **Markdown tables**: For documentation embedding
- [ ] **Tree view**: Hierarchical display of domains/roles

### MCP Resources Integration
- **Inventory resources**: `@mcp.resource("inventory://{url}")` for cached access
- **Object resources**: `@mcp.resource("object://{url}/{domain}/{name}")` for individual objects
- **Search resources**: `@mcp.resource("search://{url}?q={query}")` for search results

### Content Quality Improvements
- [ ] **HTML artifact removal**: Clean up formatting remnants in extracted content
- [ ] **Link resolution**: Convert relative links to absolute URLs
- [ ] **Image handling**: Proper handling of images in documentation
- [ ] **Table formatting**: Better markdown conversion for HTML tables

## Technical Implementation Notes

### HTML Processing Architecture (Reference)
Current documentation extraction implementation:
- **Multi-format parsing**: Handles section elements (modules) and dt/dd pairs (functions/classes)
- **URL construction**: Supports $ placeholder replacement, file:// and http/https schemes
- **BeautifulSoup integration**: Custom minimal type stubs for clean type checking
- **Markdown conversion**: HTML to markdown with tag cleanup and formatting

### Documentation Structure Analysis (Reference)
Understanding of Sphinx search mechanisms:
- **searchindex.js structure**: Document mapping, object locations, URL construction
- **HTML patterns**: `<article role="main">`, `<dl class="py exception">`, `<dt class="sig">` elements
- **Theme compatibility**: Designed for Furo but extensible to other themes

## Advanced Features

### Multi-Inventory Operations
- **Cross-reference tool**: Find objects across multiple inventories
- **Inventory comparison**: Compare versions or different projects
- **Unified search**: Search across multiple documentation sites

### Caching and Performance
- [ ] **Inventory caching**: Cache downloaded inventories with TTL

### Discovery and Automation
- **Sitemap parsing**: Extract inventory URLs from sitemaps

## Developer Experience

### Enhanced CLI
- **Interactive mode**: Browse inventories interactively
- **Shell completion**: Bash/zsh completion for commands
- **Configuration files**: Store frequently used inventory URLs
- **Alias support**: Short names for common inventories

## Protocol Extensions

### Enhanced MCP Features
- **Completion support**: Auto-complete object names in prompts
- **Progress reporting**: For long-running inventory operations
- **Subscription updates**: Notify when inventories change
- **Batch operations**: Process multiple inventories efficiently

### Custom Data Sources
- [ ] **Multiple Sphinx themes**: Support themes beyond Furo (alabaster, rtd, etc.)
- [ ] **GitHub API integration**: Extract from repository documentation
- [ ] **ReadTheDocs API**: Direct API access beyond objects.inv
- [ ] **Custom inventory formats**: Support non-Sphinx documentation
- [ ] **API specification parsing**: OpenAPI, AsyncAPI inventory extraction

## Next Phase Enhancements

### Sphinx Search Box Emulation
- [x] **HTML content extraction**: Use BeautifulSoup to extract object documentation ✅
- [ ] **JavaScript search analysis**: Reverse-engineer Sphinx search.js functionality
- [ ] **Site mapping**: Build complete site maps from Sphinx documentation
- [x] **Full-text search**: Index and search complete documentation content beyond just objects.inv
- [ ] **Search suggestion**: Provide auto-complete and search suggestions

### Object Detail and Relationships
- [x] **Object detail retrieval**: Get full documentation for specific objects by name/path ✅
- [ ] **Relationship mapping**: Show inheritance hierarchies and cross-references between objects
- [ ] **Cross-reference validation**: Verify that object links are valid and accessible

### Batch Operations and Advanced Search
- [x] **Search result ranking**: Score and rank search results by relevance

### CLI and UX Improvements
- [ ] **Interactive inventory browser**: Navigate inventories with arrow keys/search
- [ ] **Configuration files**: Store frequently used inventory sources and filters
- [ ] **Shell completion**: Bash/zsh auto-completion for commands and parameters

## Technical Improvements

### Error Handling and Robustness
- **Better error messages**: More descriptive failure information
- **Fallback strategies**: Alternative inventory sources
- **Validation**: Comprehensive inventory format validation

### Performance Optimization
- **Streaming processing**: Handle large inventories efficiently
- **Memory optimization**: Reduce memory footprint
- **Lazy loading**: Load inventory data on demand
- **Index building**: Pre-computed search indices

### Security and Privacy
- **Authentication support**: Handle protected documentation
- **Rate limiting**: Respect server rate limits
- **Privacy controls**: Option to disable external requests
- **Security scanning**: Check for malicious inventory content

## Testing Infrastructure Ideas

### Filesystem-Independent Path Objects
- **StringIO-backed PurePath subclass**: Path objects backed by in-memory content instead of filesystem
- **Preloaded content caching**: Load real filesystem data into memory for fast test execution
- **Directory simulation**: Support `.iterdir()` on fake directories with cached file contents
- **No global patching**: Unlike pyfakefs, avoid global `open()` patching that interferes with aiofiles
- **Test isolation**: Each test gets its own isolated filesystem view
- **Performance benefits**: Eliminate I/O bottlenecks in test suites

**Potential Implementation:**
```python
# String-backed paths
fake_path = FakePath("/test/file.py", content="print('hello')")

# Real file-backed (loads into StringIO cache)
fake_path = FakePath("/real/file.py", source_path=Path("real_file.py"))

# Directory-backed (loads all files in directory)
fake_dir = FakePath("/test/dir", source_path=Path("real_dir/"))
for child in fake_dir.iterdir():  # Returns FakePath objects
    content = child.read_text()   # From StringIO, not filesystem
```

**Benefits over existing solutions:**
- No interference with aiofiles or other async file operations
- Faster test execution through memory-only operations
- Easy preloading of real test data without filesystem dependency
- Clear separation between test data and test logic
- Potential for broader ecosystem adoption as standalone project

## Community and Ecosystem

### Integration Ecosystem
- **Template system**: Customizable output formats

### Documentation and Examples
- **Recipe collection**: Common use case examples
- **Best practices guide**: Optimal usage patterns
