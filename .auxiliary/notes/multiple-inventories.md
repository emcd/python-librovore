# Multiple Inventory Sources Analysis

## Context

Currently, the librovore detection system uses a precedence-based approach where the highest-confidence processor is selected and other available inventory sources are discarded. This analysis explores strategies for utilizing multiple inventory sources simultaneously to maximize information coverage while managing complexity.

## Current State Analysis

### Precedence-Based Selection (Current Implementation)
Located in `detection.py:_select_detection_optimal()`:

- Selects processor with highest confidence above 0.5 threshold
- Uses registration order as tiebreaker for equal confidence
- **Benefits**: Predictable, consistent results with straightforward caching
- **Costs**: Potentially valuable information from other sources is discarded

### Real-World Scenarios
Documentation sites often have multiple inventory sources:
- **Sphinx + MkDocs hybrid sites**: Rich API documentation (Sphinx) + tutorial pages (MkDocs)
- **Multi-format documentation**: Different content types served by different processors
- **Supplementary sources**: Future `llms.txt` files alongside traditional inventories

### Current Schema Challenges
Different inventory sources provide incompatible data structures:
```python
# Sphinx inventory object
{
    'name': 'MyClass.method',
    'domain': 'py', 
    'role': 'meth',
    'uri': '/api/mymodule.html#MyClass.method',
    '_inventory_project': 'MyProject',
    '_inventory_version': '1.0.0'
}

# MkDocs search index object  
{
    'name': 'MyClass Reference',
    'domain': 'page',
    'role': 'doc', 
    'uri': '/api/myclass/',
    'content_preview': 'Class documentation...',
    '_inventory_source': 'mkdocs_search_index'
}
```

## Proposed Strategies

### 1. CONFIDENCE_PRECEDENCE (Current)
**Status**: Implemented  
**Behavior**: Use single highest-confidence source

**Pros**:
- Simple, predictable behavior
- No deduplication complexity
- Efficient caching and performance
- Clear error handling

**Cons**: 
- Information loss from other qualified sources
- Suboptimal for hybrid documentation sites

### 2. PRIMARY_SUPPLEMENTARY (Recommended Next Step)
**Status**: Proposed  
**Behavior**: Use highest-confidence source as primary, add non-duplicate objects from other qualified sources

**Implementation approach**:
```python
async def merge_primary_supplementary(
    detections: dict[str, Detection]
) -> list[InventoryObject]:
    # Select primary source (highest confidence)
    # Add supplementary objects from other qualified sources
    # Deduplicate and merge results
    pass
```

**Pros**:
- Increased information coverage
- Primary source maintains result quality
- Manageable complexity increase

**Cons**:
- Requires sophisticated deduplication logic
- Potential performance impact (2-3x latency)
- More complex error scenarios

### 3. SOURCE_UNION
**Status**: Future consideration  
**Behavior**: Merge all qualified sources with confidence weighting

**Pros**: 
- Maximum information preservation
- Democratic approach to source selection

**Cons**:
- High deduplication complexity
- Potential user confusion from mixed result types
- Difficult to maintain result quality

### 4. ADAPTIVE
**Status**: Future research  
**Behavior**: Choose strategy based on query characteristics

**Query Type Heuristics**:
- API/code searches → prefer Sphinx inventories
- Documentation page searches → prefer MkDocs indices  
- Broad exploratory searches → use union approach

**Pros**:
- Optimizes for specific use cases
- Maintains specialized processor strengths

**Cons**:
- Adds heuristic complexity
- Less predictable user experience
- Difficult to tune and debug

### 5. INVENTORY_STRUCTURE_HYBRID (Robustness Enhancement)
**Status**: Proposed for all strategies  
**Behavior**: Use inventory-guided extraction as primary approach with structure-based fallback

**Implementation approach**:
```python
async def extract_with_structure_fallback(
    inventory_objects: list[InventoryObject],
    structure_processor: StructureProcessor
) -> list[ContentDocument]:
    # Primary: Extract using inventory-guided approach
    inventory_results = await structure_processor.extract_contents_typed(inventory_objects)
    
    # Fallback: For failed extractions, try structure-based approach
    failed_objects = [obj for obj, result in zip(inventory_objects, inventory_results) if not result]
    if failed_objects:
        structure_results = await structure_processor.extract_content_structure_based(failed_objects)
        inventory_results.extend(structure_results)
    
    return inventory_results
```

**Robustness Benefits**:
- **Inventory metadata errors**: When inventory URIs are wrong or object metadata is inaccurate
- **Theme evolution**: When documentation sites change themes/structure without updating inventories  
- **Mixed content types**: When inventory objects span multiple content patterns
- **Incomplete inventories**: When inventory misses content that exists in HTML

**Integration with Other Strategies**:
- **PRIMARY_SUPPLEMENTARY + HYBRID**: Use structure fallback for each inventory source independently
- **SOURCE_UNION + HYBRID**: Apply structure fallback to merged inventory results
- **ADAPTIVE + HYBRID**: Choose inventory vs structure approach based on query characteristics

**Implementation Details**:
- Structure-based extraction uses HTML semantic analysis (skip `aside`, `nav`, `header`)
- LLM-assisted pattern discovery for unknown documentation structures
- Content quality scoring to prefer inventory-guided results when both succeed
- Graceful degradation: inventory → structure → generic text extraction

**Performance Impact**: 
- Minimal when inventory extraction succeeds (common case)
- 2-3x latency increase only for failed inventory extractions
- Caching of structure-based patterns reduces repeated analysis costs

## Technical Challenges

### Deduplication Logic
The core challenge is identifying when objects from different sources represent the same logical entity:

```python
def deduplicate_objects(objects: list[InventoryObject]) -> list[InventoryObject]:
    """
    Deduplication strategies:
    1. Exact URI matches (after normalization)
    2. Fuzzy name matching above confidence threshold
    3. Content similarity analysis for pages
    4. Domain-specific heuristics
    """
    # Implementation details to be determined by designer/coder
    pass

def merge_duplicate_objects(duplicates: list[InventoryObject]) -> InventoryObject:
    """Merge strategy: prefer higher confidence source for primary fields,
    combine metadata from all sources."""
    # Implementation details to be determined by designer/coder
    pass
```

### Structure Processor Coordination
Multiple inventory sources complicate content extraction:
- Different URI patterns require different structure processors
- Mixed content types need appropriate handling strategies
- Fallback logic when primary structure processor fails

### Performance Implications
Multi-source processing impacts:
- **Network requests**: Multiple inventory sources = multiple HTTP requests
- **CPU processing**: Deduplication algorithms add computational overhead  
- **Memory usage**: Holding multiple source results in memory
- **Cache complexity**: More sophisticated cache key management

**Estimated Impact**:
- Current single-source: ~100-500ms
- PRIMARY_SUPPLEMENTARY: ~200-1000ms (2-3x increase)
- SOURCE_UNION: ~500-2000ms (5-10x increase)

## Implementation Recommendations

### Prerequisites
**CRITICAL**: Multiple inventory support requires structured objects as foundation. The current `dict[str, Any]` returns cannot handle the complexity of multi-source attribution and metadata merging.

### Phase 1: Foundation
1. **Complete structured objects migration** from structured-objects-discussion.md
2. **Implement source attribution** in all inventory processors
3. **Create deduplication utilities** with comprehensive test coverage
4. **Add configuration system** for strategy selection

### Phase 2: PRIMARY_SUPPLEMENTARY Implementation
1. **Extend detection system** to return all qualified detections
2. **Implement merge logic** with PRIMARY_SUPPLEMENTARY strategy
3. **Add performance monitoring** and configurable timeouts
4. **Create feature flag** for experimental multi-source behavior

### Phase 3: Validation and Optimization
1. **Gather user feedback** on result quality and performance
2. **Optimize deduplication algorithms** based on real-world patterns
3. **Implement caching strategies** for merged results
4. **Document best practices** for different site types

### Phase 4: Advanced Strategies
1. **Implement ADAPTIVE strategy** based on validation results
2. **Add user preference configuration** for strategy selection
3. **Support custom deduplication rules** per site or domain

## Configuration Design

```python
@dataclass
class MultiInventoryConfig:
    """Configuration for multiple inventory source handling."""
    
    strategy: InventoryMergingStrategy = InventoryMergingStrategy.CONFIDENCE_PRECEDENCE
    confidence_threshold: float = 0.5
    supplementary_threshold: float = 0.3  # Lower threshold for supplementary sources
    deduplication_similarity_threshold: float = 0.85
    supplementary_sources_max: int = 3
    timeout_per_source_ms: int = 5000
    enable_content_similarity: bool = False  # Expensive feature
    
    # Strategy-specific settings
    adaptive_heuristics: dict[str, Any] = field(default_factory=dict)
    source_priorities: dict[str, int] = field(default_factory=dict)  # Manual precedence overrides
```

## Success Metrics

### Quality Metrics
- **Coverage increase**: % more relevant objects found vs single-source
- **Precision maintenance**: % of results remain high-quality
- **Deduplication accuracy**: % of true duplicates correctly identified

### Performance Metrics  
- **Latency impact**: Query time increase (target: <100% increase)
- **Error rate**: % of queries that fail due to multi-source complexity
- **Cache hit rate**: Effectiveness of merged result caching

### User Experience Metrics
- **Result relevance**: User satisfaction with merged results
- **Predictability**: Consistency of results across similar queries
- **Transparency**: User understanding of result sources

## Decision Framework

**Immediate Decision**: **APPROVED** for PRIMARY_SUPPLEMENTARY implementation after structured objects completion.

**Rationale**:
- Provides clear benefit for hybrid documentation sites
- Manageable complexity increase 
- Maintains backward compatibility
- Allows validation of multi-source approach before considering more complex strategies

**Future Decisions**: Evaluate advanced strategies (SOURCE_UNION, ADAPTIVE) after 6 months of PRIMARY_SUPPLEMENTARY usage and user feedback collection.

## Dependencies

1. **Structured Objects Implementation**: Absolute prerequisite - cannot proceed without source attribution and type safety
2. **Performance Monitoring Infrastructure**: Need detailed metrics to validate multi-source benefits
3. **Configuration System Enhancement**: Support for strategy selection and tuning
4. **Documentation Updates**: Clear guidance on when and how multi-source processing helps users

## Risk Mitigation

### Technical Risks
- **Performance degradation**: Implement timeouts, circuit breakers, and fallback to single-source
- **False deduplication**: Comprehensive test coverage with real-world documentation sites
- **Memory pressure**: Streaming processing and result limiting

### User Experience Risks  
- **Result inconsistency**: Clear documentation of merge behavior and source attribution
- **Complexity confusion**: Simple default configuration with expert-level customization options
- **Breaking changes**: Feature flags and gradual rollout strategy

This multi-inventory approach represents a significant architectural enhancement that can substantially improve librovore's value proposition for complex documentation sites while maintaining the simplicity and reliability of the current single-source approach.

## Multi-Source Object Model Design

### Universal Object Enhancement for Multi-Source Support

Future multi-source operations will be enabled through the structured object design:

**Source Identification**: Complete source attribution in `InventoryObject` enables tracking and coordination across multiple inventory sources for comprehensive documentation coverage.

**Conflict Resolution**: Universal object interface provides foundation for conflict resolution strategies when multiple sources contain overlapping or contradictory information.

**Aggregation Strategies**: Structured objects enable various aggregation approaches including merging, ranking, and source-specific organization of results.

### Multi-Source Result Objects

```python
class MultiSourceInventoryResult( __.immut.DataclassObject ):
    ''' Aggregated results from multiple inventory sources. '''
    
    primary_location: str  # Primary location URL used for aggregation
    query: str             # Search term applied across all sources  
    objects: tuple[ InventoryObject, ... ]  # Aggregated and ranked objects
    search_metadata: SearchMetadata         # Combined search metadata
    location_breakdown: __.immut.Dictionary[ str, InventorySourceInfo ]  # Breakdown by location
    aggregation_metadata: __.immut.Dictionary[ str, __.typx.Any ]        # Aggregation process metadata
```

This design accommodates the PRIMARY_SUPPLEMENTARY strategy by enabling:
- Primary source selection based on confidence
- Supplementary object integration with full attribution  
- Deduplication tracking through aggregation metadata
- Performance monitoring through enhanced search metadata