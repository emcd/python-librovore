# Rich Markdown Terminal Display Implementation

## Overview
Adding rich terminal formatting to CLI markdown output using the `rich` library that's already available via Tyro dependency.

## Technical Analysis

### Current State
- CLI commands generate results with `render_as_markdown()` methods
- Output is plain text joined with `\n` and printed directly
- Clean separation between result generation and display logic

### Implementation Approach
- Keep single `DisplayFormat.Markdown` enum value
- Add automatic rich/plain selection based on terminal capabilities
- Use `rich.markdown.Markdown` with `rich.console.Console` for rendering

### Terminal Detection Logic
```python
def should_use_rich_markdown(stream, no_color_flag: bool) -> bool:
    return (
        stream.isatty() 
        and not no_color_flag 
        and not os.getenv('NO_COLOR')
    )
```

## Flag Design Decision

### The Naming Dilemma
**Technical accuracy**: We're disabling ANSI SGR (Select Graphic Rendition) sequences including color, bold, underline, italic, etc.

**User expectations**: "Color" is understood as "all terminal formatting"

**Industry precedent**: Most tools use `--no-color` even for non-color formatting:
- `git --no-color` disables bold/underline too
- `grep --color=never`
- `cargo --color=never`

### Resolution
- **Primary flags**: `--color`/`--no-color` (user-friendly, follows convention)
- **Alias flags**: `--ansi-sgr`/`--no-ansi-sgr` (technically accurate)
- **Help text**: "Disable colored output and terminal formatting"

## Standards Compliance

### NO_COLOR Environment Variable
Support the [NO_COLOR](https://no-color.org/) standard:
- Environment variable `NO_COLOR` (any non-empty value) disables color
- Widely adopted by terminal applications
- Rich library already respects this automatically

## Benefits
- Dramatically improved readability for documentation output
- Syntax-highlighted code snippets via Pygments integration
- Natural rendering of headers, emphasis, lists
- Professional appearance
- Graceful degradation for non-capable terminals

## Implementation Notes
- Modify command `__call__` methods to use Rich rendering for markdown format
- Ensure piped output automatically uses plain format
- Maintain existing plain markdown generation as fallback
- Terminal capability detection handles edge cases automatically

## Testing Considerations
- Keep existing plain markdown tests
- Add separate tests for rich rendering behavior
- Verify graceful degradation in various terminal environments