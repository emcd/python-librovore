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

### **Phase 2: Automatic URL Pattern Extension and Detection Utilities**

**2.1 Inventory Detection Enhancement Requirements**
- **Objective**: Automatically attempt common documentation URL patterns when base URL detection fails
- **Scope**: Inventory detection processes that encounter HTTP 404 or connection failures
- **Behavior**: System must try common documentation site patterns (e.g., `/en/latest/`, `/latest/`, `/main/`) before reporting failure
- **Cache Integration**: Successful URL discoveries must update detection cache to use working URLs for future requests

**2.2 HTTP Redirect Handling Requirements**
- **Objective**: Follow HTTP redirects to identify final working URLs for documentation sources
- **Integration**: Must work with existing HTTP client redirect following capabilities
- **Cache Update**: Detection cache must reflect redirected URLs to avoid unnecessary redirects on subsequent requests

**2.3 URL Analysis Capabilities**
- **Requirement**: System must identify documentation site patterns to enable intelligent URL extension
- **Capability**: Detect common documentation hosting patterns (ReadTheDocs, GitHub Pages, etc.)
- **Capability**: Generate appropriate URL variants based on detected site patterns
- **Capability**: Normalize URLs for consistent pattern generation and caching

**2.4 Detection Context Enhancement**
- **Objective**: Provide error context about URL pattern attempts without exposing internal implementation details
- **Integration**: Must work with existing detection cache system
- **Context Data**: Track success/failure indicators, error categories, and working URL discoveries for error reporting

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
- Automatic URL pattern fallback for common documentation site patterns
- Cache optimization through discovered working URLs
- Centralized error handling reduces code duplication
- Enhanced diagnostic context for future debugging needs

This implementation plan provides structural guidance while maintaining clean separation of concerns and following established codebase patterns.
