# Dual Registry Implementation Plan

## Overview
Implement separate registries for inventory and structure processors to improve architecture, eliminate cross-imports, and enable flexible processor delegation.

## Architecture Goals
- **Clean Separation**: Inventory vs structure concerns completely separated
- **Dual Detection Systems**: Separate detection for inventory files vs structure files
- **Function Dispatch**: Functions module routes queries to appropriate processor type
- **Configuration Clarity**: Extension types explicit in configuration files
- **No Cross-Imports**: Each processor type stays in its domain
- **Registry-Based DI**: Replace direct imports with dependency injection

## Current Issues
- Structure processors directly import inventory processors (spaghetti imports)
- Single extension configuration conflates inventory and structure types
- Cross-module detection imports like `from ..sphinx.urls import derive_inventory_url`
- Tight coupling between structure and inventory detection logic
- Inventory concerns (`check_objects_inv`, `extract_inventory`) mixed into structure processors
- Structure processors defining inventory capabilities instead of inventory processors
- Single detection system conflates inventory detection (objects.inv) with structure detection (searchindex.js)
- Functions module bypasses detection system with helper functions instead of proper dispatch
- Legacy `processors` registry still exists alongside dual registries
- Backward compatibility aliases that should be removed
- Need separate `detect_inventory` and `detect_structure` functions
- Detection module needs updating for dual processor registries

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

### Phase 3: Implement Dual Detection Systems
**Status**: Pending
**Files**:
- `sources/librovore/inventories/sphinx.py` (inventory detection)
- `sources/librovore/structures/sphinx/detection.py` (structure detection)
- `sources/librovore/structures/mkdocs/detection.py` (structure detection)

**Tasks**:
- Create separate inventory detection system (objects.inv, etc.)
- Create separate structure detection system (searchindex.js, themes, etc.)
- Move `check_objects_inv` from structure to inventory processors
- Move `extract_inventory` from structure to inventory processors
- Structure detections become pure structural analysis (themes, navigation, content)

### Phase 4: Registry-Based Dependency Injection
**Status**: Pending
**Files**: All structure processors

**Tasks**:
- Replace direct inventory imports with registry lookups
- Use `__.inventory_processors['sphinx']` instead of direct imports
- Structure processors delegate inventory operations via registry
- Update error handling for missing inventory processors

### Phase 5: Function Dispatch System
**Status**: Pending
**Files**: 
- `sources/librovore/functions.py`

**Tasks**:
- Update `query_inventory` to use inventory processor detection and registry
- Update `query_content` to use structure processor detection and registry
- Ensure proper routing based on query type
- Remove mixed detection logic from functions module

### Phase 6: Clean Architecture Implementation
**Status**: Completed

**Tasks**:
- ✅ Add `ProcessorGenera` enum with `Inventory` and `Structure` variants to interfaces.py
- ✅ Preserve original detection functions (`access_detections`, `determine_processor_optimal`, etc.)
- ✅ Augment original functions with `genus: ProcessorGenera` parameter via caller selection of cache/processors
- ✅ Implement cache selection based on genus (separate caches for inventory vs structure)
- ✅ Create `detect_inventory` and `detect_structure` convenience wrapper functions
- ✅ Use dependency injection pattern with cache parameter instead of genus parameter
- ✅ Extension system properly routes inventory-extensions to `register_<name>_inventory` functions
- ✅ Proper dispatch through detection system with genus-based registry selection in calling code

### Phase 7: Final Validation
**Status**: Pending

**Tasks**:
- ⏳ Restore dependency injection for `cache` parameter on `access_detections()` method
- ⏳ Modify test setup to register processors under test (inventory and structure)
- ⏳ Update calling code to select appropriate cache based on processor genus
- ⏳ Validate all processors register and lookup correctly through detection system
- ⏳ Test dual detection and registry systems
- ⏳ Ensure no legacy registry dependencies remain
- ⏳ Verify proper separation of inventory vs structure concerns

### Implementation Notes
- Core dual registry architecture is complete and functional
- Extension system properly routes `[[inventory-extensions]]` to `register_<name>_inventory()` functions  
- Detection functions use proper dependency injection with cache/processors parameters
- Test failures are due to missing processor registration in test setup, not architecture issues

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

### Detection Separation Strategy
Separate detection systems for different concerns:

**Inventory Detection** (handled by inventory processors):
- `objects.inv` files (Sphinx inventory)
- API documentation indices
- Symbol/reference databases
- Cross-reference systems

**Structure Detection** (handled by structure processors):
- `searchindex.js` files (Sphinx search)
- `mkdocs.yml` configuration files
- Theme detection and metadata
- Navigation structure
- Content organization and hierarchy

**Function Dispatch** (via proper detection system):
- `query_inventory()` → calls `detect_inventory()` → routes to inventory processors
- `query_content()` → calls `detect_structure()` → routes to structure processors

**ProcessorGenera Enum**:
- `ProcessorGenera.Inventory` - for inventory processor operations
- `ProcessorGenera.Structure` - for structure processor operations
- Replaces string literals and improves type safety
- **Required parameter**: All detection functions require explicit `genus: ProcessorGenera` parameter
- **Registry Selection**: `genus` parameter determines which registry (`inventory_processors` vs `structure_processors`) to use
- **Cache Selection**: Separate caches for each genus to avoid cross-contamination

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