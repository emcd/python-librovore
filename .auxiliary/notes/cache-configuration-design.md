# HTTP Cache Configuration Design Proposal

## Problem Analysis

### Current State
Librovore implements HTTP content caching to improve performance and reduce server load when accessing documentation sites. The current implementation uses hardcoded TTL values that cannot be configured by users, leading to several issues:

1. **Development Friction**: During development and testing, cached responses mask code improvements and bug fixes
2. **Inflexible Deployment**: Production deployments cannot tune cache behavior for their specific access patterns
3. **One-Size-Fits-All**: Different content types (robots.txt, inventory files, documentation pages) have different optimal cache lifetimes
4. **No Emergency Override**: No mechanism to bypass cache for debugging or testing scenarios

### Cache Architecture Overview
The system currently implements three distinct cache types:
- **ContentCache**: Caches GET request responses for documentation content
- **ProbeCache**: Caches HEAD request results for resource existence checks  
- **RobotsCache**: Caches robots.txt files with request delay management

Each cache type uses TTL-based expiration with memory management and LRU eviction policies.

## Proposed Solution: Hybrid Configuration Approach

### Primary Solution: TOML Configuration
Add cache configuration section to the general configuration file allowing granular control over cache behavior for different content types.

**Configuration Structure:**
```
[cache.content]
success-ttl = 3600      # Documentation pages (1 hour)
error-ttl = 30          # Failed requests (30 seconds)
memory-limit = 33554432 # 32MB memory limit

[cache.probe] 
success-ttl = 1800      # Resource existence checks (30 minutes)
error-ttl = 30          # Failed probes (30 seconds)
entries-max = 1000      # Maximum cached entries

[cache.robots]
ttl = 86400             # Robots.txt files (24 hours)
entries-max = 500       # Maximum cached entries
request-timeout = 5.0   # Request timeout in seconds
user-agent = "librovore/1.0"
```

**Key Design Principles:**
- Use TOML format consistent with existing configuration
- Avoid underscores in key names per project standards
- TTL values in seconds for precise control
- TTL of 0 disables caching for that content type
- Sensible defaults maintain current behavior when config absent

### Secondary Solution: CLI Override
Provide immediate cache bypass capability through command-line flags for debugging and testing scenarios.

**CLI Integration:**
- Add `--no-cache` flag to bypass all caching
- Add `--cache-ttl=N` flag to override TTL temporarily
- Flags apply only to current command execution
- Override configuration file settings when present

## Implementation Benefits

### Development Workflow
- Set `content-ttl = 0` in development configuration
- Eliminates cache-related debugging confusion
- Immediate feedback on code changes
- No need to remember command flags

### Production Deployment
- Tune cache lifetimes based on documentation update frequency
- Reduce server load with appropriate caching
- Different TTLs for different content stability levels
- Memory usage control for resource-constrained environments

### Operational Flexibility
- Emergency cache bypass for troubleshooting
- Per-deployment cache optimization
- A/B testing different cache strategies
- Gradual cache behavior migration

## Migration Strategy

### Backward Compatibility
- Maintain existing hardcoded defaults when configuration absent
- Graceful degradation if configuration file malformed
- No breaking changes to existing CLI interface

### Configuration Discovery
- Configuration loaded during cache initialization
- Runtime configuration updates not supported (restart required)
- Clear error messages for invalid TTL values
- Validation ensures non-negative TTL values

### CLI Integration Points
- Query-content and query-inventory commands gain cache flags
- MCP server operations respect configuration file settings
- Consistent cache behavior across all access patterns

## Implementation Architecture

### No Global State
- **Principle**: Avoid global variables and state that require linter suppressions
- **Approach**: Pass cache instances through the application via dependency injection
- **Benefit**: Improved testability, thread safety, and architectural clarity

### Custom Globals Subclass
- **Design**: Subclass `appcore.Globals` to create `LibrovoreGlobals` 
- **Content**: Include configured cache instances as attributes
- **Initialization**: Configure caches during application preparation phase
- **Threading**: Cache instances initialized once per application context

### Function Threading Strategy
- **CLI Functions**: Pass `auxdata` parameter through all function signatures
- **MCP Server**: Use closures to capture `auxdata` for tool functions
- **Processor Interface**: Modify processor methods to accept cache parameters
- **Backward Compatibility**: Maintain existing processor interfaces where possible

### Configuration Structure
- **Separate Tables**: Each cache type gets its own TOML table (`[cache.content]`, `[cache.probe]`, `[cache.robots]`)
- **Granular Control**: Individual TTL, memory, and behavioral settings per cache type
- **Validation**: Configuration validation with clear error messages for invalid values

## Technical Considerations

### Cache Granularity
The solution provides content-type granularity rather than per-site or per-URL granularity. This balances configurability with complexity, addressing the most common use cases without over-engineering.

### Memory Management
Existing memory management and LRU eviction remain unchanged. The memory limit becomes configurable to support different deployment scenarios.

### Performance Impact
Configuration parsing occurs once during initialization. Runtime performance remains unchanged, with potential improvements from optimized TTL values.

## Success Criteria

### Functional Requirements
- Development environments can disable caching entirely
- Production environments can optimize cache lifetimes
- Emergency cache bypass available for troubleshooting
- Backward compatibility maintained

### Operational Requirements
- Configuration changes take effect on restart
- Invalid configurations provide clear error messages
- CLI overrides work consistently across commands
- Documentation reflects new configuration options

This design addresses the root cause of cache-related development friction while providing production-ready cache management capabilities.