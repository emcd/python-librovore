# Better Error Messages Implementation Plan

## Architecture-Aligned Understanding

### **Current Processor Architecture**
- **Inventory Processors** (`ProcessorGenera.Inventory`) - Detect and parse object inventories (currently: Sphinx, future: others)
- **Structure Processors** (`ProcessorGenera.Structure`) - Extract content from documentation HTML (currently: Sphinx, MkDocs)
- **Separate detection pipelines** - inventory detection must not be mixed with structure detection

### **Current Error Flow**
1. **Functions layer** calls detection for both inventory and structure processors
2. **Detection layer** (`sources/librovore/detection.py`) raises `ProcessorInavailability(class_name)` where `class_name` is 'inventory' or 'structure'
3. **CLI/MCP formatting** provides generic messages

## Error Scenario Mapping

### **Scenario 1: No Compatible Inventory Format Detected**
- **Current**: "No processor found to handle source: inventory"
- **Should be**: "No compatible inventory format detected at this documentation source"
- **Detection**: All inventory detectors fail (currently only Sphinx, future: multiple formats)

### **Scenario 2: URL Pattern Intelligence for Inventory Detection**
- **Current**: "No processor found to handle source: inventory"
- **Should be**: "No inventory found - attempted common URL patterns"
- **Detection**: Base URL inventory detection fails, automatically try `/en/latest/` and other common patterns
- **Cache Update**: When extended URLs work, update cached detections to reflect the working URL

### **Scenario 3: Enhanced Inaccessibility Information**
- **Current**: "Cannot access documentation inventory: {source}"
- **Should be**: Enhanced with actionable guidance based on error type
- **Detection**: HTTP errors during inventory access with contextual suggestions

### **Scenario 4: Structure vs Inventory Clarity**
- **Current**: Both say "No processor found"
- **Should be**: Clear distinction between inventory and structure detection failures
- **Detection**: Error messages specify which processor genus failed

## Implementation Plan

### **Phase 1: Functions Layer Error Response Design** ✅ **COMPLETED**

**Status**: ✅ **IMPLEMENTED AND VALIDATED** (Both CLI and MCP interfaces)

**1.1 Structured Error Response Requirements** ✅ **COMPLETE**
- ✅ Functions layer provides pre-formatted error information to interface layers
- ✅ All public functions in functions layer return structured responses for processor detection failures
- ✅ Consistent response structure with error type, user-friendly title, detailed message, and actionable suggestions
- ✅ Interface layers consume structured error information without interpreting raw exceptions

**1.2 Error Context Enhancement** ✅ **COMPLETE**
- ✅ Error responses distinguish between inventory and structure detection failures
- ✅ Contextual guidance provided based on specific failure scenarios
- ✅ Consistent error types and messages across different processor genera
- ✅ Clear user-friendly titles and actionable suggestions

**1.3 Interface Layer Responsibility Reduction** ✅ **COMPLETE**
- ✅ Eliminated error interpretation logic from CLI and MCP interface layers
- ✅ Interface layers extract pre-formatted error information and apply appropriate display formatting
- ✅ Removed duplicate error handling and formatting code across interfaces
- ✅ Single source of truth for error message generation achieved

**Implementation Summary**:
- **Files Modified**: `sources/librovore/functions.py` (added 66 lines of error handling code)
- **Functions Enhanced**: `query_content()`, `query_inventory()`, `summarize_inventory()`, `detect()`
- **Helper Functions Added**: `_produce_inventory_error_response()`, `_produce_structure_error_response()`, `_produce_generic_error_response()`, `_produce_processor_error_response()`
- **Response Format**: Consistent `{"success": boolean, "data"|"error": object}` structure
- **Quality Assurance**: ✅ All linters pass, ✅ All tests pass (188), ✅ No type errors
- **Testing**: ✅ Validated with problematic sites (docs.pydantic.dev, requests.readthedocs.io, starlette.readthedocs.io)
- **Testing**: ✅ Validated with working sites (docs.python.org, flask.palletsprojects.com)
- **Validation**: ✅ Both CLI and MCP server interfaces return identical structured responses

### **Phase 2: Universal URL Pattern Extension and Redirects Cache** ✅ **COMPLETED**

**Status**: ✅ **IMPLEMENTED AND VALIDATED** 

**2.1 Universal Pattern Extension Requirements** ✅ **COMPLETE**
- ✅ **Objective**: Automatically attempt common documentation URL patterns when base URL detection fails
- ✅ **Scope**: **ALL processor types** - both inventory and structure processors benefit from URL correction
- ✅ **Rationale**: If documentation content is at `/en/latest/` instead of `/`, then both objects.inv AND HTML pages will be at that path
- ✅ **Behavior**: System tries common documentation site patterns (e.g., `/en/latest/`, `/latest/`, `/main/`) before reporting failure
- ✅ **Redirects Cache**: Implemented universal URL redirection mapping original_url → working_url for all future operations

**2.2 HTTP Redirect Handling Requirements** ✅ **COMPLETE**
- ✅ **Objective**: Follow HTTP redirects to identify final working URLs for documentation sources
- ✅ **Integration**: Works with existing HTTP client redirect following capabilities via aiohttp
- ✅ **Cache Update**: Detection cache reflects redirected URLs, avoiding unnecessary redirects on subsequent requests

**2.3 URL Analysis Capabilities** ✅ **COMPLETE**
- ✅ **Requirement**: System identifies documentation site patterns to enable intelligent URL extension
- ✅ **Capability**: Detects common documentation hosting patterns (ReadTheDocs, GitHub Pages, etc.)
- ✅ **Capability**: Generates appropriate URL variants based on detected site patterns
- ✅ **Capability**: Normalizes URLs for consistent pattern generation and caching

**2.4 Transparent URL Resolution** ✅ **COMPLETE**
- ✅ **Objective**: Return working URLs as canonical source in all responses
- ✅ **Integration**: All operations automatically use working URLs from redirects cache
- ✅ **User Benefits**: Users see actual working URLs, subsequent operations work consistently
- ✅ **Architecture**: Simple redirects cache provides clean abstraction layer

### **Phase 3: Enhanced ProcessorInavailability Exception**

**3.1 Exception Context Enhancement Requirements**
- **Objective**: Provide additional context in `ProcessorInavailability` exceptions to enable better error messaging
- **Scope**: Existing `ProcessorInavailability` class in exceptions module
- **Context Requirements**: Exception must indicate processor genus (inventory vs structure)
- **Context Requirements**: Exception must categorize the type of final error encountered
- **Context Requirements**: Exception must indicate whether URL pattern extension was attempted
- **Backward Compatibility**: Changes must not break existing exception handling code

## Implementation Guidelines

### **Error Message Principles**
- **Concise**: Focus on what the user needs to know, not internal process details
- **Actionable**: Provide clear guidance on potential solutions
- **Non-Technical**: Avoid exposing internal URL attempts or format lists
- **Consistent**: Use centralized formatting to ensure consistency across interfaces

### **Code Standards Adherence**
- Follow existing codebase patterns for error handling and exception hierarchy
- Maintain separation between inventory and structure detection logic
- Use established caching patterns and data structures
- Apply consistent naming conventions (e.g., "inavailability" not "unavailability")

### **Detection Cache Integration**
- Ensure URL pattern discoveries update existing cache entries appropriately
- Consider cache key strategies for base URL vs discovered working URLs
- Maintain cache TTL and invalidation logic for updated URLs

## Success Metrics

### **User Experience Improvements**
- Clear distinction between inventory and structure detection failures
- Actionable guidance without overwhelming technical detail
- Consistent error experience across CLI and MCP interfaces
- Automatic handling of common URL pattern issues

### **System Behavior Improvements**
- Universal URL pattern fallback for all processor types
- Transparent URL redirection ensures consistency across all operations
- Centralized error handling reduces code duplication
- Users receive working URLs for reliable subsequent operations

## Phase 2 Architectural Design Decisions

### **Universal Pattern Extension Architecture**

**Core Principle**: URL pattern extension must apply to ALL processor types because documentation content location affects both inventory files and structure content uniformly.

**Redirects Cache Design**:
```python
# Simple global cache mapping original URLs to working URLs
_url_redirects_cache: dict[str, str] = {}  # original_url → working_url
```

**Modified Detection Flow**:
1. **URL Resolution**: Check redirects cache first - if redirect exists, use working URL immediately
2. **Original Attempt**: Try original URL with all processors of requested genus  
3. **Pattern Extension**: If original fails, try pattern extension to find working URL
4. **Cache Update**: Store successful redirect mapping for future operations
5. **Transparent Results**: Return working URL as canonical source in all responses

**Benefits**:
- **Architectural Consistency**: All processor types benefit equally from URL correction
- **User Transparency**: Results show actual working URLs, enabling reliable subsequent operations  
- **Operational Consistency**: All future operations automatically use correct URLs
- **Performance**: Redirects cache eliminates repeated pattern probing

**Integration Points**:
- `_execute_processors_with_patterns()`: Remove genus restrictions, apply universally
- `normalize_location()`: Check redirects cache before processing
- Response formatting: Use working URLs as canonical source
- Cache management: Simple key-value mapping with appropriate TTL

This implementation plan provides structural guidance while maintaining clean separation of concerns and following established codebase patterns.
