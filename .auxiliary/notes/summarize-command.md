# Inventory Summary Feature Proposal

## Problem Statement

When querying large inventories with `query-inventory`, users face discoverability challenges:

1. **Truncated results hide relevant items**: With default `results_max=5`, users might not see the objects they're looking for
2. **Domain ordering issues**: For example, querying `https://docs.python.org/3` for "print" returns C API functions (`c` domain) before Python builtins (`py` domain)
3. **No visibility into result distribution**: Users cannot see what categories (domains, roles) are available without manually inspecting truncated results
4. **Filter discovery difficulty**: Without knowing what domains/roles exist, users struggle to construct effective filter queries

### Example Problem Scenario

```bash
$ hatch run librovore query-inventory https://docs.python.org/3 print --results-max 5
```

Returns:
- `CO_FUTURE_PRINT_FUNCTION` (domain: c, role: macro)
- `PyErr_Print` (domain: c, role: function)
- `PyErr_PrintEx` (domain: c, role: function)
- `PyOS_snprintf` (domain: c, role: function)
- ... more C API items

Missing (truncated): `print()` function from `py` domain that user likely wants.

## Proposed Solution

Add inventory result summarization functionality to provide distribution statistics across grouping dimensions (domain, role, etc.).

### Core Capabilities

1. **Aggregate inventory query results** by filterable attributes (domain, role, priority)
2. **Display counts per group** to show result distribution
3. **Help users discover available filters** for narrowing results
4. **Work with existing query results** - no additional inventory fetching required

## Design Options

### Option A: Separate `summarize-inventory` Command

**CLI:**
```bash
librovore summarize-inventory <location> <term> [--group-by domain|role|priority]
```

**Pros:**
- Clean separation of concerns
- Dedicated command for summary-only use case
- Can optimize for summary without full object retrieval

**Cons:**
- Duplicates query logic and parameters
- Extra maintenance burden (as mentioned in user context)
- Users need two commands to browse then query

### Option B: Add `--summarize` Flag to `query-inventory`

**CLI:**
```bash
librovore query-inventory <location> <term> --summarize [--group-by domain]
```

**Behavior:**
- When `--summarize` is set, output summary statistics instead of object list
- Reuses all existing query parameters (filters, search behaviors, etc.)
- Can fetch all results internally for accurate statistics

**Pros:**
- Single command interface
- No duplication of query logic
- Natural workflow: explore with --summarize, then refine without it

**Cons:**
- Changes command semantics (returns different output type)
- Cannot show both summary and results in single call

### Option C: Hybrid Output (Summary + Results)

**CLI:**
```bash
librovore query-inventory <location> <term> --include-summary [--group-by domain]
```

**Output format (Markdown):**
```markdown
# Inventory Query Results

## Summary
- Total matches: 247
- Showing: 10 results

### By Domain
- `py`: 156 (63.2%)
- `c`: 78 (31.6%)
- `std`: 13 (5.3%)

### By Role (Top 5)
- `function`: 89 (36.0%)
- `class`: 67 (27.1%)
- `method`: 45 (18.2%)
- `attribute`: 28 (11.3%)
- `module`: 18 (7.3%)

## Objects
[... normal object listing ...]
```

**Pros:**
- Provides context without extra command
- Helps users understand why results are truncated
- Shows what filters to apply for refinement

**Cons:**
- More complex output
- Requires fetching full result set for accurate statistics

## Recommended Approach: **Hybrid of Options A + C**

### Rationale

1. **Best user experience**: Provides immediate context about result distribution
2. **Facilitates discovery**: Users see available domains/roles without separate query
3. **Natural workflow**: Users can immediately see which filter would help
4. **Minimal API surface**: Single `--summarize` flag rather than new command
5. **Backward compatible**: Flag is optional, existing behavior unchanged
6. **Simple implementation**: No new data structures - compute summary at render time from existing objects

### Implementation Strategy

#### 1. CLI Changes (`sources/librovore/cli.py`)

Add flag to `QueryInventoryCommand`:

```python
summarize: __.typx.Annotated[
    bool,
    __.tyro.conf.arg(
        help="Show distribution summary instead of full object list."
    ),
] = False

group_by: __.typx.Annotated[
    __.cabc.Sequence[str],
    __.tyro.conf.arg(
        help="Grouping dimensions for summary. Uses processor's supported filters if not specified."
    ),
] = ()
```

Pass these to the render method instead of changing query logic.

#### 2. MCP Server Changes (`sources/librovore/server.py`)

Add parameters to `query_inventory` function:

```python
summarize: __.typx.Annotated[
    bool,
    _Field(description="Show distribution summary instead of full object list"),
] = False

group_by: __.typx.Annotated[
    __.cabc.Sequence[str],
    _Field(description="Grouping dimensions for summary. Uses processor's supported filters if not specified."),
] = ()
```

Pass these to the render method: `result.render_as_json(reveal_internals=..., summarize=summarize, group_by=group_by)`

#### 3. Results Rendering (`sources/librovore/results.py`)

**No new data structures needed!** Simply enhance render methods to accept summarization parameters.

Update `InventoryQueryResult` render methods:

```python
class InventoryQueryResult(ResultBase):
    ...

    def render_as_json(
        self, /, *,
        reveal_internals: bool = False,
        summarize: bool = False,
        group_by: __.cabc.Sequence[str] = (),
    ) -> __.immut.Dictionary[str, __.typx.Any]:
        """Renders inventory query result as JSON."""
        if summarize:
            return self._render_summary_json(group_by, reveal_internals)
        else:
            # Existing rendering logic
            ...

    def render_as_markdown(
        self, /, *,
        reveal_internals: bool = False,
        summarize: bool = False,
        group_by: __.cabc.Sequence[str] = (),
    ) -> tuple[str, ...]:
        """Renders inventory query result as Markdown."""
        if summarize:
            return self._render_summary_markdown(group_by, reveal_internals)
        else:
            # Existing rendering logic
            ...

    def _render_summary_json(
        self, group_by: __.cabc.Sequence[str], reveal_internals: bool
    ) -> __.immut.Dictionary[str, __.typx.Any]:
        """Computes and renders summary statistics."""
        distributions = self._compute_distributions(group_by)
        return __.immut.Dictionary(
            location=self.location,
            term=self.term,
            matches_total=len(self.objects),
            group_by=list(group_by),
            distributions=distributions,
            search_metadata=dict(self.search_metadata.render_as_json()),
        )

    def _render_summary_markdown(
        self, group_by: __.cabc.Sequence[str], reveal_internals: bool
    ) -> tuple[str, ...]:
        """Computes and renders summary statistics as Markdown."""
        distributions = self._compute_distributions(group_by)
        lines = ["# Inventory Query Summary"]
        lines.append(f"- **Term:** {self.term}")
        lines.append(f"- **Total matches:** {len(self.objects)}")
        lines.append(f"- **Grouped by:** {', '.join(group_by)}")

        for dimension in group_by:
            if dimension in distributions:
                lines.append("")
                lines.append(f"### By {dimension.title()}")
                dist = distributions[dimension]
                total = sum(dist.values())
                for value, count in sorted(
                    dist.items(), key=lambda x: x[1], reverse=True
                ):
                    pct = (count / total * 100) if total > 0 else 0
                    lines.append(f"- `{value}`: {count} ({pct:.1f}%)")

        return tuple(lines)

    def _compute_distributions(
        self, group_by: __.cabc.Sequence[str]
    ) -> dict[str, dict[str, int]]:
        """Computes distribution statistics from objects."""
        distributions: dict[str, dict[str, int]] = {}

        for dimension in group_by:
            dist: dict[str, int] = {}
            for obj in self.objects:
                value = obj.specifics.get(dimension)
                if value is not None:
                    value_str = str(value)
                    dist[value_str] = dist.get(value_str, 0) + 1
            distributions[dimension] = dist

        return distributions
```

**Key insight**: Since we already have all matched objects in `self.objects`, we can compute summary statistics on-demand during rendering. No need to store summary as a separate field.

#### 4. Query Function Changes (`sources/librovore/functions.py`)

**Minimal changes needed!** The query function doesn't need to know about summarization.

**Current behavior to preserve:**
- Already fetches all matching inventory objects (as noted in user feedback)
- Applies `results_max` truncation

**Recommended enhancement:**
```python
async def query_inventory(
    auxdata: Globals,
    location: str,
    term: str, /, *,
    ...,
    results_max: int = 5,
) -> _results.InventoryQueryResult:
    ...

    # Fetch all matching objects (already done for filtering)
    all_objects = await _search_inventory(...)

    # When rendering, truncation can happen based on summarize flag:
    # - If summarize=True, render uses all objects for statistics
    # - If summarize=False, render honors results_max

    return _results.InventoryQueryResult(
        ...,
        objects=all_objects,  # Keep all objects, truncate at render time
        search_metadata=_results.SearchMetadata(
            results_count=len(all_objects),
            results_max=results_max,
            matches_total=len(all_objects),
        ),
    )
```

**Alternative**: Keep current truncation in query logic, document that summary statistics are computed from truncated set. This is acceptable since users can increase `results_max` to get more accurate statistics.

## Output Format Examples

### Markdown (summarize mode)

```markdown
# Inventory Query Summary
- **Term:** print
- **Total matches:** 247
- **Grouped by:** domain, role

### By Domain
- `py`: 156 (63.2%)
- `c`: 78 (31.6%)
- `std`: 13 (5.3%)

### By Role
- `function`: 89 (36.0%)
- `class`: 67 (27.1%)
- `method`: 45 (18.2%)
- `attribute`: 28 (11.3%)
- `module`: 18 (7.3%)

**Tip:** Use filters to narrow results: `--filters domain=py role=function`
```

### Markdown (normal mode - unchanged)

```markdown
# Inventory Query Results
- **Term:** print
- **Results:** 10 of 247

## Objects

📦 ── Object 1 ─────────────────────── 📦
...
```

### JSON (summarize mode)

```json
{
  "location": "https://docs.python.org/3",
  "term": "print",
  "matches_total": 247,
  "group_by": ["domain", "role"],
  "distributions": {
    "domain": {
      "py": 156,
      "c": 78,
      "std": 13
    },
    "role": {
      "function": 89,
      "class": 67,
      "method": 45,
      "attribute": 28,
      "module": 18
    }
  },
  "search_metadata": {
    "results_count": 247,
    "results_max": 10,
    "matches_total": 247
  }
}
```

### JSON (normal mode - unchanged)

```json
{
  "location": "https://docs.python.org/3",
  "term": "print",
  "objects": [...],
  "search_metadata": {
    "results_count": 10,
    "results_max": 10,
    "matches_total": 247
  }
}
```

## Usage Workflows

### Discovery Workflow

```bash
# Step 1: Get overview of available objects
$ librovore query-inventory https://docs.python.org/3 print --summarize --group-by domain role

# Output shows: py domain has 156 items, c domain has 78 items

# Step 2: Filter to Python domain
$ librovore query-inventory https://docs.python.org/3 print \
    --filters domain=py --results-max 10

# Now see relevant Python functions instead of C API
```

### MCP Client Workflow

```python
# AI assistant uses summarize to understand inventory
result = await query_inventory(
    location="https://docs.python.org/3",
    term="print",
    summarize=True,
    group_by=["domain", "role"]
)

# Sees: "Most results (63%) are in 'py' domain, 31% in 'c' domain"
# Automatically applies filter for more relevant results
result = await query_inventory(
    location="https://docs.python.org/3",
    term="print",
    filters={"domain": "py"},
    results_max=5
)
```

## Implementation Considerations

### Performance

**Good news:** As confirmed by user feedback, we already fetch all inventory objects for filtering! The current implementation loads the entire `objects.inv` file and filters in memory.

**Impact of summarization:**
- **Minimal**: Computing distribution statistics is O(n) where n = number of matched objects
- **Computation happens at render time**: Only when `--summarize` flag is used
- **No additional network requests**: Works with existing fetched data

**Potential optimizations (if needed later):**
1. Cache computed distributions for repeated renders
2. Limit statistics computation to top N values per dimension
3. For extremely large inventories (>100k objects), consider sampling

### Processor Compatibility and Dynamic Group-By Dimensions

**Key principle:** Don't hardcode dimensions - discover them from processor capabilities!

**Implementation approach:**

1. **Default behavior (empty `group_by`)**: Use all supported filter dimensions from processor
   ```python
   # In CLI/MCP, when group_by is empty:
   processor_capabilities = await get_processor_capabilities(location)
   default_dimensions = [
       f.name for f in processor_capabilities.supported_filters
   ]
   ```

2. **Explicit group-by**: User can specify subset of processor's supported dimensions
   ```bash
   # Only group by domain
   $ librovore query-inventory https://docs.python.org/3 print --summarize --group-by domain
   ```

3. **Validation**: Reject unsupported dimensions with helpful message
   ```
   Error: Dimension 'custom_field' not supported by processor 'sphinx'.
   Supported dimensions: domain, role, priority
   ```

**Per-processor capabilities:**

**Sphinx inventories:**
- Advertised filters: `domain`, `role`, `priority`
- All available in `specifics` dict
- Well-structured and consistent

**MkDocs inventories:**
- Advertised filters: Depends on mkdocstrings configuration
- Typically includes: `role`, potentially `category` or `module`
- May have fewer dimensions than Sphinx

### Alternative Grouping Dimensions

Beyond domain/role/priority, future extensions could support:

1. **URL patterns**: Group by documentation sections (e.g., `/library/`, `/reference/`)
2. **Custom attributes**: Processor-specific metadata
3. **Hierarchical grouping**: Nested summaries (domain → role → priority)

## Migration Path

Since this is a new feature (not reviving old command):

1. **Phase 1**: Implement `--summarize` flag for `query-inventory` CLI and MCP tool
2. **Phase 2**: Consider expanding to `query-content` if useful
3. **Future**: Could add hybrid mode (show both summary and objects) if user demand exists

## Open Questions

1. **How to handle empty `group_by` parameter?**
   - ✅ **Resolved**: Use all supported filter dimensions from processor capabilities
   - No hardcoded defaults

2. **How to display summary when no groupable attributes exist?**
   - ✅ **Resolved**: Show total object count only
   - Simple fallback when processor has no supported filter dimensions

3. **Should we limit number of values shown per dimension?**
   - ✅ **Resolved**: Show top 20 with "...and N more" indicator if needed
   - Most dimensions won't have that many items
   - `--summary-limit` flag is good future consideration but overkill for initial implementation

4. **Should summary be computed from filtered or unfiltered results?**
   - ✅ **Resolved**: From filtered results (shows what's available after filters applied)
   - Makes sense: if user filters to `domain=py`, summary shows py subdistribution

5. **Should results_max affect summary computation?**
   - Option A: Always compute summary from all matched objects (requires fetching all)
   - Option B: Compute summary from truncated set, document limitation
   - ✅ **Resolved**: Since we already fetch all objects, compute from all matched objects

## Related Future Enhancements

1. **Interactive mode**: Show summary, prompt for filter selection
2. **Filter suggestions**: Automatically suggest filters based on summary
3. **Drill-down**: Click/select dimension value to apply filter
4. **Cross-inventory summaries**: Compare distributions across multiple inventories

## Summary

Recommended implementation (incorporating user feedback):
- **Add `--summarize` flag** to `query-inventory` command and MCP tool
- **Dynamic grouping dimensions**: Discovered from processor's advertised filter capabilities (no hardcoding)
- **Summary-only output**: When flag is set, show distribution statistics instead of object list
- **Render-time computation**: Calculate statistics from existing objects during rendering (no new data structures)
- **Performance**: Negligible impact - we already fetch all inventory objects for filtering
- **Backward compatible**: Optional flag, existing behavior unchanged

**Key simplifications from user feedback:**
1. No new result data structures - compute at render time
2. No hardcoded dimensions - use processor capabilities
3. No query logic changes - all handled in rendering layer
4. Minimal performance impact - already have all data

This provides immediate value for discovery while maintaining simplicity and avoiding the maintenance burden of a separate command.
