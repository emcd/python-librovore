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

### **Phase 1: Enhanced ProcessorInavailability Exception**

**1.1 Exception Enhancement**
- **File**: `sources/librovore/exceptions.py`
- **Change**: Enhance existing `ProcessorInavailability` class with additional context fields
- **New Fields**: 
  - `genus: Optional[str]` - 'inventory' or 'structure' 
  - `url_patterns_attempted: bool` - Whether automatic URL pattern fallback was tried
  - `final_error_type: Optional[str]` - Category of final error (e.g., 'http_404', 'network_error')
- **Backward Compatibility**: Maintain existing constructor signature

### **Phase 2: Automatic URL Pattern Extension**

**2.1 Inventory Detection Enhancement**
- **Files**: `sources/librovore/inventories/sphinx/detection.py` or new common inventory utilities
- **Enhancement**: Automatic URL pattern fallback when base URL fails
- **Pattern Logic**:
  - Try base URL first (current behavior)
  - If 404 or connection fails, automatically try `/en/latest/` appended to base URL
  - Consider additional common documentation URL patterns as appropriate
- **Cache Integration**: When extended URL succeeds, ensure detection cache reflects the working URL

**2.2 HTTP Redirect Handling**
- **Integration**: Work with `httpx` redirect following to identify final working URLs
- **Cache Update**: Update detection cache entries to use redirected/working URLs for future requests

### **Phase 3: Centralized Error Message Generation**

**3.1 Functions Layer Error Formatting**
- **File**: `sources/librovore/functions.py`
- **New Functions**:
  - `_format_processor_inavailability(exc: ProcessorInavailability) -> Dict[str, str]`
  - `_format_inventory_inavailability(exc: ProcessorInavailability) -> Dict[str, str]`
  - `_format_structure_inavailability(exc: ProcessorInavailability) -> Dict[str, str]`
- **Return Format**: Dictionary with keys like `{'title': '...', 'message': '...', 'suggestion': '...'}`
- **Integration**: Called by both CLI and MCP server layers

**3.2 CLI Error Formatter Updates**
- **File**: `sources/librovore/cli.py`
- **Function**: `_format_cli_exception()`
- **Change**: Call functions layer error formatting and format for CLI display
- **Simplification**: Remove duplicate error handling logic

**3.3 MCP Server Error Updates**  
- **File**: `sources/librovore/server.py`
- **Function**: Error mapping function for MCP responses
- **Change**: Call functions layer error formatting and format for MCP structured responses
- **Consistency**: Use same error categorization as CLI

### **Phase 4: URL Pattern Detection Utilities**

**4.1 URL Analysis Functions**
- **Purpose**: Identify documentation site patterns for intelligent URL extension
- **Functions**:
  - `_is_readthedocs_domain(url: str) -> bool` - Detect ReadTheDocs sites
  - `_generate_url_variants(base_url: str) -> List[str]` - Generate common URL patterns
  - `_extract_base_url(url: str) -> str` - Normalize URLs for pattern generation

**4.2 Detection Result Context**
- **Purpose**: Provide error context without exposing internal details to users
- **Integration**: Work with existing detection cache system
- **Data**: Success/failure indicators, error categories, working URL discoveries

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