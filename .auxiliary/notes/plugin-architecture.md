# Plugin Architecture Design - Sphinx MCP Server

## Overview

Design for a plugin system that allows the Sphinx MCP Server to support multiple documentation formats through a unified interface. The core innovation is **site format sniffing** - automatically detecting which plugin can handle a given documentation source.

## Architecture Components

### 1. Site Format Sniffer System

**Core Concept:** Each plugin provides a "sniffer" that examines a documentation source and returns a confidence score (0.0-1.0) indicating how well it can handle that source.

#### Sniffer Interface
```python
class DocumentationSniffer(ABC):
    @abstractmethod
    async def can_handle(self, source: str) -> float:
        """Return confidence score 0.0-1.0 that this plugin can handle the source."""

    @abstractmethod
    def get_name(self) -> str:
        """Return plugin name for identification."""
```

#### Sphinx Sniffer Logic
- **0.95 confidence**: `objects.inv` + `searchindex.js` present
- **0.7 confidence**: `objects.inv` present only
- **0.0 confidence**: Neither present

#### Plugin Selection Algorithm
1. Run all registered sniffers against the source
2. Sort by confidence score (descending)
3. Use registration order to break ties
4. Select highest confidence plugin

### 2. Sniff Result Caching

**Cache Structure:**
```python
{
    "https://docs.python.org/3/": {
        "timestamp": 1703123456,
        "ttl": 3600,
        "results": {
            "sphinx": {
                "confidence": 0.95,
                "metadata": {
                    "theme": "furo",
                    "has_searchindex": True,
                    "sphinx_version": "4.5.0"
                }
            }
        }
    }
}
```

**Cache Location Strategy:**
- **Production**: `~/.cache/sphinxmcps/detections/` (via `platformdirs`)
- **Development**: `.auxiliary/caches/sphinxmcps/detections/` (when `auxdata.distribution.editable` is True)

### 3. Plugin Registry

**Implementation:** `accretive.ValidatorDictionary` for plugin management

**Registry Operations:**
- Register built-in plugins during package import
- Load external plugins from configuration
- Maintain registration order for tie-breaking
- Validate plugin interfaces

### 4. External Plugin Loading

**Package Retrieval System:**
- Reuse logic from another unreleased package
- Async package downloading and installation
- Isolated cache management
- Support for PEP 508 URLs and PEP 440 version specs

**Plugin Loading Flow:**
```python
async def load_plugin_package(spec: str) -> ModuleType:
    cache_path = await fetch_package_to_cache(spec)
    return import_from_cache(cache_path)
```

### 5. Configuration System

**TOML Structure:**
```toml
[[extensions]]
name = "sphinx"
package = "sphinxmcps-sphinx"  # Built-in
enabled = true

[[extensions]]
name = "openapi"
package = "sphinxmcps-openapi>=1.0"  # PEP 440 version spec
enabled = true
[extensions.arguments]
timeout = 60
validate_schemas = true

[[extensions]]
name = "custom"
package = "git+https://github.com/user/plugin.git@main"  # PEP 508 URL
enabled = false
[extensions.arguments]
custom_param = "value"
```

**Configuration Features:**
- PEP 508 URL specifications (git, file, PyPI)
- PEP 440 version constraints
- Plugin-specific argument tables
- Enable/disable control per plugin

### 6. MCP Server Integration

**Unified Tool Interface:**
The MCP server exposes the same three tools regardless of plugins:

```python
@mcp.tool()
async def extract_inventory(source: str, **filters) -> dict:
    plugin = await _select_plugin_for_source(source)
    return await plugin.extract_inventory(source, **filters)

@mcp.tool()
async def extract_documentation(source: str, object_name: str) -> dict:
    plugin = await _select_plugin_for_source(source)
    return await plugin.extract_documentation(source, object_name)

@mcp.tool()
async def query_documentation(source: str, query: str, **filters) -> list:
    plugin = await _select_plugin_for_source(source)
    return await plugin.query_documentation(source, query, **filters)
```

**Plugin Selection Logic:**
1. Check sniff cache for source
2. If cache miss or expired, run sniffers
3. Cache results with TTL
4. Select highest confidence plugin
5. Delegate to plugin implementation

## Implementation Phases

### Phase 1: Core Sniffer System ✅ COMPLETED
- [x] Define `DocumentationSniffer` interface (now `Processor` protocol)
- [x] Implement sniff result caching with TTL
- [x] Create plugin selection algorithm
- [x] Build basic Sphinx sniffer as proof of concept

### Phase 2: Plugin Registry ✅ COMPLETED
- [x] Add `accretive` dependency
- [x] Implement plugin registry with `ValidatorDictionary`
- [x] Create plugin registration system
- [x] Register built-in Sphinx plugin

### Phase 3: External Plugin Loading ⏸️ DEFERRED
- [ ] Adapt package loading logic from another unreleased package
- [ ] Implement isolated cache management
- [ ] Add support for PEP 508/440 specifications
- [ ] Create plugin loading and validation system

### Phase 4: Configuration Integration ⏸️ DEFERRED
- [ ] Implement TOML `[[extensions]]` parsing
- [ ] Add plugin-specific argument handling
- [ ] Create enable/disable controls
- [ ] Validate configuration schema

### Phase 5: Plugin Interface Design ✅ COMPLETED
- [x] Define minimal plugin interface based on learnings
- [x] Retrofit existing Sphinx functionality as plugin
- [x] Implement plugin lifecycle management
- [x] Add error handling and fallback mechanisms

### Phase 6: Sphinx Code Refactoring ✅ COMPLETED
- [x] Move Sphinx-specific code from `functions.py` to `processors/sphinx.py`
- [x] Extract helper functions from processor methods to standalone functions
- [x] Fix coding practices (try blocks, spacing, comments, blank lines)
- [x] Maintain backward compatibility
- [ ] Update public API functions to delegate to processors
- [ ] Update tests and documentation

**Refactoring Improvements:**
- Extracted all Sphinx-specific processing logic from class methods to standalone functions
- Fixed overly-broad try blocks by narrowing to specific failing operations
- Added proper spacing inside delimiters throughout codebase
- Removed unnecessary blank lines within function bodies
- Cleaned up obvious comments, keeping only meaningful ones
- Processor methods now delegate to functions rather than implementing logic directly
- All 118 tests continue to pass, ensuring backward compatibility

## Design Principles

### User Experience
- **Automatic detection**: Users provide URLs, system selects appropriate plugin
- **Unified interface**: Same MCP tools work with all plugins
- **Transparent operation**: Plugin selection happens behind the scenes
- **Fallback graceful**: Clear error messages when no plugin can handle source

### Plugin Developer Experience
- **Minimal interface**: Simple sniffer + core operations
- **Standard configuration**: TOML-based plugin-specific settings
- **Metadata flexibility**: Plugins can store custom sniff metadata
- **Registration simplicity**: Built-in plugins auto-register, external plugins load via config

### Security & Performance
- **Isolated loading**: External plugins loaded in isolated caches
- **Cached sniffing**: Avoid repeated network requests for detection
- **Configurable TTL**: Balance freshness vs performance
- **Validation**: Plugin interface validation before registration

## Technical Considerations

### Caching Strategy
- **Development mode detection**: Use local cache when `auxdata.distribution.editable` is True
- **TTL management**: Configurable cache expiration per plugin type
- **Cache invalidation**: Manual cache clearing capabilities
- **Metadata storage**: Plugin-specific metadata alongside confidence scores

### Error Handling
- **Plugin failures**: Graceful fallback to next highest confidence plugin
- **Network errors**: Cached results used when sniffing fails
- **Configuration errors**: Clear validation messages for malformed plugin configs
- **Import errors**: Helpful messages when external plugins fail to load

### Performance Optimization
- **Lazy loading**: Plugins loaded only when needed
- **Async operations**: All network operations are async
- **Connection pooling**: Reuse HTTP connections across plugin operations
- **Batch operations**: Support for processing multiple sources efficiently

## Future Extensions

### Advanced Plugin Features
- **Plugin dependencies**: Plugins that depend on other plugins
- **Plugin composition**: Combining multiple plugins for complex sources
- **Plugin priorities**: Manual priority overrides for specific use cases
- **Plugin versioning**: Compatibility checks and version constraints

### Enhanced Detection
- **Content-based sniffing**: Examine HTML content for theme/format detection
- **Multi-stage sniffing**: Progressive refinement of confidence scores
- **Machine learning**: Learn from usage patterns to improve detection
- **User feedback**: Allow users to correct plugin selection

This architecture provides a solid foundation for extensible documentation processing while maintaining simplicity and performance.
