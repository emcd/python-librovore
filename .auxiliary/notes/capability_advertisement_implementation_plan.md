# Capability Advertisement Implementation Plan

## Overview

Implementation plan for processor capability advertisement and detection system improvements, incorporating feedback from o3 design review and architectural insights from capability advertisement proposal.

## Phase 1: Detection Foundation (Addresses o3 Review #1)

### 1.1 Migrate from Ad-hoc to Cached Detection ✅

**Status**: COMPLETED - Successfully migrated `functions._select_processor_for_source()` to use `detection.determine_processor_optimal()`

**Changes Made**:
- **Replaced** all calls to `_select_processor_for_source()` with cached detection logic
- **Removed** redundant ad-hoc detection function  
- **Added** detection import to functions.py
- **Refactored** processor selection into reusable `_determine_processor_optimal()` helper
- **Improved** code structure and compliance with project standards
- **Preserved** existing confidence scoring and processor selection logic
- **Ensured** detection results are cached with existing TTL configuration

**Key Considerations**:
- Maintain backward compatibility for existing API callers
- Handle detection cache misses gracefully (trigger fresh detection)
- Consider TTL appropriate for documentation sites (likely hours, not minutes)
- Test detection caching across multiple processor types

### 1.2 Switch from fuzzywuzzy to rapidfuzz

**Motivation**: Moving search logic to engine level provides excuse to upgrade from unmaintained `fuzzywuzzy` to actively maintained `rapidfuzz`.

**Implementation Details**:
- **Replace** `sphobjinv.suggest()` dependency on fuzzywuzzy with direct rapidfuzz usage
- **Update** fuzzy matching in inventory filtering (currently in `processors/sphinx/inventory.py`)
- **Maintain** existing fuzzy threshold semantics and scoring
- **Ensure** search term matching uses rapidfuzz consistently
- **Update** dependencies in pyproject.toml

**Key Considerations**:
- Verify scoring compatibility between fuzzywuzzy and rapidfuzz
- Test fuzzy matching behavior across different threshold values
- Consider performance implications (rapidfuzz should be faster)
- Update any documentation references to fuzzy matching algorithm

## Phase 2: Capability Advertisement Architecture

### 2.1 Add Capability Data Structures

**Implementation Details**:
- **Add** `FilterCapability` and `ProcessorCapabilities` dataclasses to `interfaces.py`
- **Extend** `Processor` interface with `capabilities` property
- **Implement** capabilities in `SphinxProcessor` (domain, role, priority filters)
- **Update** `ProcessorsRegistry` to expose processor capabilities

**Key Considerations**:
- Use proper nomenclature (`results_limit_max`, `response_time_typical`)
- Keep capability definitions processor-specific (no universal assumptions)
- Ensure immutable capability objects for thread safety
- Design capabilities to be easily serializable for MCP tools

### 2.2 Enhance Detection System with Capabilities

**Implementation Details**:
- **Add** `capabilities` property to `Detection` interface that delegates to processor
- **Create** `DetectionToolResponse` dataclass for new `detect` tool
- **Implement** conversion from `DetectionsByProcessor` to tool response format
- **Preserve** existing detection caching and confidence scoring logic

**Key Considerations**:
- Build on existing detection infrastructure, don't replace it
- Ensure capabilities are accessible through detection results
- Maintain compatibility with existing detection workflow
- Consider serialization for MCP tool responses

### 2.3 Implement New MCP Tools

**Implementation Details**:
- **Add** `detect` tool that exposes cached detection results with capabilities
- **Add** `processors_list` tool that enumerates available processors
- **Add** `processor_describe` tool for detailed capability inspection
- **Update** existing tools (`explore`, `query_documentation`, `summarize_inventory`) with optional `processor` parameter

**Key Considerations**:
- Default to auto-detection behavior (backward compatibility)
- Validate processor name when explicitly specified
- Provide meaningful error messages for unsupported processor/filter combinations
- Use consistent response formats across tools

### 2.4 Processor Parameter Validation

**Implementation Details**:
- **Add** filter validation logic that checks processor capabilities
- **Implement** meaningful error messages for unsupported filters
- **Update** business logic functions to validate filters against processor capabilities
- **Ensure** validation happens before expensive operations (inventory loading, HTTP requests)

**Key Considerations**:
- Fail fast with clear error messages
- Distinguish between unsupported filters and invalid filter values
- Provide suggestions for correct filter usage
- Consider validation at MCP tool level vs business logic level

## Phase 3: Search Architecture Refinement

### 3.1 Separate Processor Filtering from Search Matching

**Current Architecture Issue**: Search responsibilities are mixed between processors and engine.

**Implementation Details**:
- **Clarify** that processors handle domain-specific filtering (domain, role, priority)
- **Ensure** engine handles universal search matching (query terms, fuzzy matching, scoring)
- **Remove** any search-related logic from processor capability advertisements
- **Consolidate** search scoring logic in business functions (functions.py)

**Key Considerations**:
- Processors focus on inventory filtering, not search term matching
- Engine provides consistent search behavior across all processors
- Avoid duplicating search logic in each processor
- Maintain clear separation of concerns

### 3.2 Improve Search Performance with rapidfuzz

**Implementation Details**:
- **Optimize** search term matching using rapidfuzz performance features
- **Consider** batch fuzzy matching for multiple candidates
- **Evaluate** different rapidfuzz algorithms (ratio, partial_ratio, token_sort_ratio)
- **Benchmark** performance improvements over fuzzywuzzy

**Key Considerations**:
- Maintain scoring consistency with existing behavior
- Consider memory usage for large inventories
- Test performance across different query patterns
- Document search algorithm choice for future maintainers

## Phase 4: Integration and Testing

### 4.1 Update CLI Integration

**Implementation Details**:
- **Add** CLI commands for new tools (`detect`, `processors-list`, `processor-describe`)
- **Update** existing CLI commands to support `--processor` parameter
- **Ensure** CLI provides good error messages for capability violations
- **Test** CLI workflow with explicit processor selection

**Key Considerations**:
- Maintain existing CLI behavior as default
- Provide helpful processor discovery through CLI
- Consider CLI help text that shows available processors
- Test CLI with both valid and invalid processor/filter combinations

### 4.2 Comprehensive Testing Strategy

**Implementation Details**:
- **Test** detection caching behavior (cache hits, misses, TTL expiration)
- **Test** capability advertisement accuracy across processors
- **Test** filter validation for supported and unsupported combinations
- **Test** backward compatibility with existing API usage
- **Test** MCP tool integration with capability-aware clients

**Key Considerations**:
- Create test fixtures that exercise capability edge cases
- Test with multiple processor types (prepare for MkDocs processor)
- Verify performance improvements from detection caching
- Test error handling and user experience with invalid inputs

### 4.3 Documentation Updates

**Implementation Details**:
- **Update** API documentation to reflect capability advertisement
- **Document** processor-specific filter capabilities
- **Provide** examples of capability-aware tool usage
- **Update** architecture documentation with new detection flow

**Key Considerations**:
- Include migration guide for existing integrations
- Document capability discovery workflow for new users
- Provide processor development guide for future extensions
- Include performance and caching behavior documentation

## Implementation Sequence

### Sprint 1: Detection Foundation
1. Migrate to cached detection system
2. Switch to rapidfuzz
3. Validate detection caching performance

### Sprint 2: Core Capability Architecture  
1. Add capability data structures
2. Implement processor capabilities
3. Create new MCP tools

### Sprint 3: Validation and Integration
1. Add processor parameter validation
2. Update CLI integration
3. Implement comprehensive testing

### Sprint 4: Search Refinement and Documentation
1. Optimize search architecture with rapidfuzz
2. Complete documentation updates
3. Performance benchmarking and tuning

## Success Criteria

- **Detection Performance**: Elimination of duplicate detection calls through caching ✅
- **Capability Accuracy**: Processors accurately advertise their filtering capabilities
- **User Experience**: Clear error messages for unsupported processor/filter combinations
- **API Consistency**: Clean, consistent API design without legacy constraints
- **Extensibility**: Clean foundation for adding MkDocs processor
- **Performance**: Measurable improvement in fuzzy search performance with rapidfuzz

## Risk Mitigation

- **Detection Migration**: Extensive testing to ensure cached detection maintains existing behavior
- **Fuzzy Algorithm Change**: Careful validation of scoring consistency between fuzzywuzzy and rapidfuzz
- **API Design**: Focus on clean, intuitive API without legacy constraints
- **Complexity**: Incremental implementation with testing at each phase