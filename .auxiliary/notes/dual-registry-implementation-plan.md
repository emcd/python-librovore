# Dual Registry Implementation Plan

## Overview
Implement separate registries for inventory and structure processors to improve architecture, eliminate cross-imports, and enable flexible processor delegation.

## Architecture Goals
- **Clean Separation**: Inventory vs structure concerns completely separated
- **Flexible Delegation**: Structure processors can use any available inventory processor via registry lookup
- **Configuration Clarity**: Extension types explicit in configuration files
- **No Cross-Imports**: Each processor type stays in its domain
- **Registry-Based DI**: Replace direct imports with dependency injection

## Current Issues
- Structure processors directly import inventory processors (spaghetti imports)
- Single extension configuration conflates inventory and structure types
- Cross-module detection imports like `from ..sphinx.urls import derive_inventory_url`
- Tight coupling between structure and inventory detection logic

## Implementation Phases

### Phase 1: Configuration Schema Update
**Status**: Pending
**Files**: 
- `data/configuration/general.toml`
- `sources/librovore/xtnsmgr/configuration.py`

**Tasks**:
- Split `[[extensions]]` into `[[inventory-extensions]]` and `[[structure-extensions]]`
- Update configuration parsing to handle dual extension types
- Maintain backward compatibility during transition

### Phase 2: Extensions Manager Registry Routing  
**Status**: Pending
**File**: `sources/librovore/xtnsmgr/processors.py`

**Tasks**:
- Route inventory extensions to `inventory_processors` registry
- Route structure extensions to `structure_processors` registry  
- Use extension type from configuration to determine routing
- Update registration error handling for dual registries

### Phase 3: Decouple Detection Systems
**Status**: Pending
**Files**:
- `sources/librovore/structures/mkdocs/detection.py:75`
- `sources/librovore/structures/sphinx/inventory.py:34`

**Tasks**:
- Remove `from ..sphinx.urls import derive_inventory_url` cross-imports
- Move inventory detection logic to inventory processors
- Structure detections become pure structural analysis
- Eliminate detection spaghetti between modules

### Phase 4: Registry-Based Dependency Injection
**Status**: Pending
**Files**: All structure processors

**Tasks**:
- Replace direct inventory imports with registry lookups
- Use `__.inventory_processors['sphinx']` instead of direct imports
- Structure processors delegate inventory operations via registry
- Update error handling for missing inventory processors

### Phase 5: Update Capabilities & Validation
**Status**: Pending

**Tasks**:
- Update MkDocs filter capabilities to reflect actual vs delegated functionality
- Validate all processors register and lookup correctly
- Ensure extension loading works with both processor types
- Test registry-based delegation

## Key Design Decisions

### Configuration Strategy
Use separate TOML table arrays:
```toml
[[inventory-extensions]]
name = "sphinx"
enabled = true

[[structure-extensions]]  
name = "mkdocs"
enabled = true
```

### MkDocs Inventory Strategy
For release 1.0: MkDocs uses Sphinx inventory processor via registry lookup
Post-1.0: Consider native MkDocs inventory processor if needed

### Detection Decoupling
Move inventory detection concerns to inventory processors:
- Structure processors: analyze document structure only
- Inventory processors: handle inventory detection and extraction
- Registry: provides loose coupling between the two

## Benefits
1. **Modularity**: Each processor type has single responsibility
2. **Flexibility**: Structure processors can use any inventory processor
3. **Maintainability**: No cross-module imports or tight coupling
4. **Testability**: Each processor type can be tested independently
5. **Extensibility**: Easy to add new processor types without architectural changes

## Risks & Mitigations
- **Configuration Complexity**: Mitigate with clear documentation and validation
- **Registry Lookup Failures**: Implement graceful fallbacks and error messages
- **Performance**: Registry lookups are minimal overhead vs import complexity