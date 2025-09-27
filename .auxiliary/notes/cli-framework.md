# CLI Framework Migration Plan

## Overview

Migrate librovore CLI from manual appcore setup to the new `appcore.cli` framework while preserving domain-specific functionality. This migration will eliminate ~40-80 lines of boilerplate while maintaining compatibility with existing interfaces.

## Current State Analysis

### Boilerplate to Eliminate
- Custom `DisplayOptions` class (lines 47-85) - stream/file handling logic
- Manual `_prepare()` function (lines 526-565) - duplicates appcore preparation
- Custom `_CliCommand` protocol (lines 216-230) - replaced by framework equivalent

### Functionality to Preserve
- `intercept_errors` decorator - domain-specific `Omnierror` handling
- Format-specific rendering (JSON/Markdown) - core to librovore interface
- Existing command structure and argument patterns

### Current Logging Setup
- **MCP Server**: Logs to `.auxiliary/inscriptions/server.txt` via `--logfile` parameter
- **CLI Configuration**: Manual `logfile` parameter creates `appcore.inscription.Control`
- **External Configuration**: `mcp-servers.json` specifies server log destination

## Migration Strategy

### Phase 1: DisplayOptions Extension

**Replace** custom `DisplayOptions` class with framework extension:

```python
from appcore.cli import DisplayOptions as _BaseDisplayOptions

class DisplayOptions(_BaseDisplayOptions):
    ''' Consolidated display configuration for CLI output. '''

    format: _interfaces.DisplayFormat = _interfaces.DisplayFormat.Markdown

    def decide_rich_markdown(self, stream: __.typx.TextIO) -> bool:
        ''' Determines whether to use Rich markdown rendering. '''
        return self.determine_colorization(stream)
```

**Benefits:**
- Inherit stream/file handling, tyro configuration, colorization logic
- Keep librovore-specific format handling
- Direct replacement for existing `decide_rich_markdown()` calls

**Changes Required:**
- Update imports
- Replace `decide_rich_markdown()` calls with `determine_colorization()`
- Remove custom stream/file handling logic

### Phase 2: Application Base Class Migration

**Replace** custom `Cli` class with framework application:

```python
class Cli(appcore.cli.Application):
    ''' MCP server CLI. '''

    display: DisplayOptions = __.dcls.field(default_factory=DisplayOptions)
    command: __.typx.Union[
        # existing command union - unchanged
    ]

    async def execute(self, auxdata: _state.Globals) -> None:
        from . import xtnsmgr
        await xtnsmgr.register_processors(auxdata)
        await self.command(auxdata=auxdata, display=self.display)
```

**Benefits:**
- Eliminate `_prepare()` function entirely
- Automatic appcore preparation via framework
- Simplified application lifecycle
- Retain extension registration logic

**Changes Required:**
- Remove `prepare_invocation_args()` method
- Remove `__call__()` method (handled by framework)
- Update command invocation pattern

### Phase 3: Command Protocol Standardization

**Update** command classes to use framework protocol:

```python
class DetectCommand(appcore.cli.Command):
    ''' Detect which processors can handle a documentation source. '''

    location: LocationArgument
    genus: # existing fields unchanged

    @intercept_errors()  # Keep existing decorator
    async def execute(self, auxdata: _state.Globals) -> None:
        # existing logic unchanged
```

**Benefits:**
- Standardized command interface
- Framework-provided `__call__()` and `prepare()` methods
- Consistent with appcore ecosystem

**Changes Required:**
- Update base class inheritance
- Remove custom `__call__()` implementations
- Keep `@intercept_errors()` decorators

### Phase 4: Inscription Unification (Optional)

**Unify** logging configuration using framework `InscriptionControl`:

```python
class Cli(appcore.cli.Application):
    ''' MCP server CLI. '''

    # Replace manual logfile parameter with framework inscription control
    inscription: appcore.cli.InscriptionControl = __.dcls.field(
        default_factory=lambda: appcore.cli.InscriptionControl(
            level='debug',
            target_file=__.Path('.auxiliary/inscriptions/server.txt')
        )
    )
```

**Benefits:**
- **Unified logging configuration**: Same pattern for CLI and MCP server
- **Standardized inscription control**: Leverage framework capabilities
- **Simplified external configuration**: Remove custom `--logfile` handling

**Migration Path:**
1. **Update** `mcp-servers.json` to use framework inscription arguments:
   ```json
   "args": [
     "hatch", "run", "librovore",
     "--inscription.target-file", ".auxiliary/inscriptions/server.txt",
     "--inscription.level", "debug",
     "serve"
   ]
   ```

2. **Remove** manual `logfile` parameter and related preparation logic
3. **Test** that server logging behavior remains identical

**Considerations:**
- **Backward compatibility**: External MCP configurations would need updates
- **Default behavior**: Framework provides sensible defaults for inscription
- **Configuration flexibility**: Users can override inscription settings per command

## Framework Limitations and Enhancement Opportunities

### NO_COLOR Environment Variable Support

**Issue**: The `appcore.cli.DisplayOptions.determine_colorization()` method does not check the `NO_COLOR` environment variable, which is a widely adopted standard for disabling colored output.

**Current Behavior**: Framework only checks `self.colorize`, `self.assume_rich_terminal`, and `stream.isatty()`.

**Expected Behavior**: Should also respect `NO_COLOR` environment variable when present.

**Upstream Enhancement**: Consider adding `NO_COLOR` support to `appcore.cli.DisplayOptions.determine_colorization()`:

```python
def determine_colorization( self, stream: __.typx.TextIO ) -> bool:
    ''' Determines whether to use colorized output. '''
    if self.assume_rich_terminal:
        return self.colorize and not __.os.environ.get( 'NO_COLOR' )
    return (
            self.colorize
        and hasattr( stream, 'isatty' )
        and stream.isatty( )
        and not __.os.environ.get( 'NO_COLOR' ) )
```

**Workaround**: Previously implemented `decide_rich_markdown()` compatibility method, but removed per code review to use framework directly. Current librovore behavior will not respect `NO_COLOR` until upstream support is added.

## Preserved Patterns

### Error Handling
- **Keep** `intercept_errors` decorator unchanged
- **Reason**: Domain-specific `Omnierror` handling and format-specific error rendering

### Format Logic
- **Keep** existing JSON/Markdown format distinction
- **Keep** `_render_and_print_result()` function
- **Reason**: Core to librovore's interface, not provided by framework

### Command Structure
- **Keep** existing tyro configuration and argument patterns
- **Keep** command-specific fields and validation
- **Reason**: Well-tested interface, no framework equivalent

## Implementation Order

1. **Phase 1 First**: Lowest risk, direct replacement with inheritance
2. **Phase 2 Second**: Medium risk, eliminates major boilerplate
3. **Phase 3 Third**: Lowest value-add, can be done incrementally per command
4. **Phase 4 Optional**: Inscription unification for consistency (breaking change)

## Validation Approach

1. **Reference Implementation**: Use `appcore.introspection.Application` as template
2. **Incremental Testing**: Validate each phase before proceeding
3. **Interface Preservation**: Ensure CLI behavior remains identical

## Expected Outcomes

- **40-80 lines eliminated**: Stream handling, preparation logic, custom protocols
- **Improved maintainability**: Standardized patterns, framework integration
- **Enhanced functionality**: Better terminal detection, configuration handling
- **Preserved specialization**: Domain-specific error handling and formatting
- **Zero breaking changes**: CLI interface remains identical (Phases 1-3)
- **Optional unification**: Standardized inscription configuration (Phase 4)

## Risk Assessment

- **Low risk**: Direct API compatibility confirmed via source code analysis
- **Proven patterns**: Introspection module provides working reference
- **Incremental approach**: Each phase can be validated independently
- **Fallback available**: Changes are reversible if issues arise