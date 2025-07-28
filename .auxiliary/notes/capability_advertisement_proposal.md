# Capability Advertisement Proposal

## Overview

Extend the MCP server architecture to support processor-specific capabilities, enabling better multi-processor support (Sphinx, MkDocs, etc.) and improved user experience through capability-aware tools.

## Current Limitations

1. **Universal Filter Assumption**: All filters (domain, role, priority) are treated as universally applicable, but many are Sphinx-specific
2. **No Processor Discovery**: Users can't discover what processors are available or which applies to their site
3. **Poor Error Messages**: Failures don't indicate processor-specific limitations
4. **Rigid Interface**: Hard to extend with processor-specific features

## Proposed Workflow (context7 Pattern)

### Phase 1: Detection
```bash
# Detect what processor(s) can handle a site
sphinxmcps use detect --source https://docs.python.org
```

### Phase 2: Processor-Specific Operations  
```bash
# Use specific processor (explicit)
sphinxmcps use query-documentation --source https://docs.python.org --processor sphinx --query "async"

# Use best detection (implicit - current behavior)
sphinxmcps use query-documentation --source https://docs.python.org --query "async"
```

## Architecture Components

### 1. Processor Capabilities

```python
@dataclass
class FilterCapability:
    """Describes a filter supported by a processor."""
    name: str                    # e.g., "domain", "role"
    description: str             # Human-readable description
    type: str                    # "string", "enum", "boolean"
    values: list[str] | None     # For enums, list valid values
    required: bool = False       # Whether filter is required

@dataclass
class ProcessorCapabilities:
    """Complete capability description for a processor."""
    processor_name: str
    version: str
    supported_filters: list[FilterCapability]
    results_limit_max: int | None = None
    response_time_typical: str | None = None  # "fast", "moderate", "slow"
    notes: str | None = None
```

**Note**: Search capabilities (fuzzy matching, scoring) are handled generically by the engine. Processors only advertise their filtering capabilities.

### 2. Enhanced Detection System

Build on existing detection infrastructure by adding capability advertisement:

```python
# Extend existing Detection interface to include capabilities
@property  
def capabilities(self) -> ProcessorCapabilities:
    """Get capabilities for this detection's processor."""
    return self.processor.capabilities

# New tool response that wraps existing DetectionsCacheEntry
@dataclass
class DetectionToolResponse:
    """Response from detect tool."""
    source: str
    detections: list[Detection]           # From existing DetectionsByProcessor
    detection_best: Detection | None     # From existing select_best_detection()
    time_detection_ms: int
```

This approach:
- **Reuses** existing detection caching and confidence logic
- **Extends** processors to advertise capabilities  
- **Adds** new `detect` tool that exposes cached detections
- **Maintains** backward compatibility

### 3. Enhanced Tool Interface

All existing tools gain optional `processor` parameter:

```python
async def query_documentation(
    source: str,
    query: str,
    processor: str | None = None,  # NEW: explicit processor selection
    filters: FiltersMutable = FiltersMutable(),
    results_max: int = 10,
    include_snippets: bool = True,
) -> dict[str, Any]:
    """
    If processor is None, auto-detect and use best match.
    If processor is specified, validate it can handle the source.
    """
```

### 4. New Tools

```python
async def detect(
    source: str,
    all_detections: bool = False,  # If False, return only best detection
) -> DetectionToolResponse:
    """Detect which processor(s) can handle a documentation source."""

async def processors_list() -> dict[str, ProcessorCapabilities]:
    """List all available processors and their capabilities."""

async def processor_describe(
    processor_name: str
) -> ProcessorCapabilities:
    """Get detailed capabilities for a specific processor."""
```

## Capability Examples

### Sphinx Processor Capabilities
```python
sphinx_capabilities = ProcessorCapabilities(
    processor_name="sphinx",
    version="1.0.0",
    supported_filters=[
        FilterCapability(
            name="domain",
            description="Sphinx domain (py, std, js, etc.)",
            type="string", 
            values=None,  # Open-ended
        ),
        FilterCapability(
            name="role", 
            description="Object role (class, function, method, etc.)",
            type="string",
            values=None,  # Open-ended
        ),
        FilterCapability(
            name="priority",
            description="Documentation priority level",
            type="string",
            values=["0", "1", "-1"],
        ),
        # Note: match_mode and fuzzy_threshold are handled generically by engine
    ],
    results_limit_max=100,
    response_time_typical="fast",
    notes="Works with Sphinx-generated documentation sites"
)
```

### Future MkDocs Processor Capabilities
```python
mkdocs_capabilities = ProcessorCapabilities(
    processor_name="mkdocs",
    version="1.0.0", 
    supported_filters=[
        FilterCapability(
            name="section",
            description="Documentation section/category",
            type="string",
            values=None
        ),
        FilterCapability(
            name="tag",
            description="Page tags",
            type="string", 
            values=None
        ),
        # Note: match_mode and fuzzy_threshold handled generically
        # MkDocs processor might not support regex matching in its inventory filtering
    ],
    results_limit_max=50,  # Different limit than Sphinx
    response_time_typical="moderate",
    notes="Works with MkDocs-generated documentation sites"
)
```

## Implementation Strategy

### Phase 1: Core Infrastructure
1. Add capability data structures to `interfaces.py`
2. Extend existing processors to advertise capabilities
3. Add `detect` tool with current auto-detection logic
4. Update existing tools to accept optional `processor` parameter

### Phase 2: Enhanced Detection  
1. Improve detection algorithms to return confidence scores
2. Support multiple processor detections per source
3. Add processor validation in tools

### Phase 3: MkDocs Processor
1. Implement MkDocs processor with different capabilities
2. Validate architecture with real multi-processor scenarios
3. Refine capability system based on learnings

## Benefits

### For Users
- **Discoverability**: `detect` tool shows what's possible with their site
- **Clarity**: Clear feedback about which filters are relevant
- **Reliability**: Better error messages when features aren't supported
- **Flexibility**: Can override auto-detection when needed

### For Developers
- **Extensibility**: Clean framework for adding new processors
- **Separation**: Clear boundaries between universal and processor-specific features  
- **Testing**: Capability-driven testing strategies
- **Documentation**: Self-documenting API through capability advertisement

## Example User Workflows

### Discovery Workflow
```bash
# User discovers what's possible with their site
$ sphinxmcps use detect --source https://docs.myproject.org
Best Detection: mkdocs (confidence: 0.95)
Supported filters: section, tag
Results limit: 50

# User explores available processors
$ sphinxmcps use processors-list
Available processors: sphinx, mkdocs
```

### Explicit Processor Workflow  
```bash
# User wants to ensure they're using Sphinx processor
$ sphinxmcps use query-documentation \
    --source https://docs.python.org \
    --processor sphinx \
    --query "async" \
    --domain py \
    --role function
```

### Error Handling Workflow
```bash
# User tries unsupported feature
$ sphinxmcps use query-documentation \
    --source https://mkdocs-site.org \
    --processor mkdocs \
    --domain py  # Not supported by MkDocs

Error: Filter 'domain' not supported by mkdocs processor.
Supported filters: section, tag
Use 'sphinxmcps use processor-describe mkdocs' for details.
```

## Migration Strategy

- **Backward Compatibility**: Existing tools work unchanged (auto-detection)
- **Gradual Adoption**: Users can start using `processor` parameter incrementally
- **Capability Evolution**: Processors can extend capabilities over time
- **Documentation**: Update docs to show processor-specific examples

This proposal provides a foundation for clean multi-processor architecture while maintaining the current user experience as the default path.