# Summarize Inventory JSON Return Design

## Current State

`summarize_inventory()` function currently returns a formatted string (human-readable text) directly from the functions layer.

## Proposed Change

Modify `summarize_inventory()` to return structured JSON data like other functions in the module.

## Rationale

1. **Separation of Concerns**: Business logic should return structured data; presentation formatting belongs in the CLI layer

2. **Consistency**: All other functions in the module return JSON/structured data, making `summarize_inventory` an outlier

3. **MCP Compatibility**: LLMs and programmatic consumers can easily process JSON without needing to parse formatted text

4. **CLI Flexibility**: Enables the CLI to choose between JSON output (for scripting) and Markdown formatting (for human readability)

5. **API Design**: Functions module becomes a pure data processing layer, with formatting handled at appropriate presentation boundaries

## Implementation Impact

- Functions layer: `summarize_inventory()` returns `dict[str, Any]` instead of `str`
- CLI layer: Handles Markdown formatting when `--output-format markdown` (default)
- MCP layer: Receives structured JSON data suitable for LLM consumption
- Backward compatibility: CLI default behavior can remain human-readable via Markdown formatting