# --develop Flag Implementation Plan

## Overview
This document outlines the implementation plan for adding a `--develop` flag to the `serve` subcommand, enabling hot reloading during development.

## Simple Implementation Approach
We're starting with a simple implementation that:
- **Does not queue requests** during restart
- **Allows temporary request/response interruption** during file change restarts
- **Focuses on basic functionality** first
- **Can be enhanced later** with buffering/queuing if needed

## Architecture

### Process Structure
```
Claude Code ↔ Parent Process (--develop mode) ↔ Child Process (normal MCP server)
```

### Parent Process Responsibilities
- Monitor `sources/sphinxmcps/` directory for `.py` file changes using `watchfiles`
- Manage child process lifecycle (start, restart, terminate)
- Proxy stdio streams between Claude Code and child process
- Handle graceful shutdown

### Child Process Responsibilities
- Run normal MCP server in `stdio` mode
- No knowledge of development mode
- Gets restarted when files change

## Implementation Details

### 1. CLI Changes (`sources/sphinxmcps/cli.py`)
- Add `develop: bool = False` parameter to `ServeCommand`
- Pass develop flag to `server.serve()`

### 2. Server Changes (`sources/sphinxmcps/server.py`)
- Add `develop: bool = False` parameter to `serve()` function
- Route to `_serve_develop()` when develop=True
- Keep existing functionality unchanged for normal mode

### 3. Development Server (`_serve_develop()`)
- Use `watchfiles.awatch()` to monitor file changes
- Create child subprocess with filtered arguments (no --develop)
- Implement stdio bridging with `asyncio.gather()`
- Handle graceful restart on file changes

### 4. Argument Filtering
Child process receives filtered arguments:
- `--develop` flag is removed (handled by parent only)
- `--transport` forced to `stdio` (parent handles other transports)
- `--port` passed through if specified

### 5. File Monitoring
- Watch `sources/sphinxmcps/` directory
- Monitor `.py` files only
- Ignore `__pycache__` and other non-source files

## Error Handling Strategy

### Simple Approach (Initial Implementation)
- **During restart**: Temporarily interrupt stdio streams
- **Connection loss**: Allow natural MCP protocol error handling
- **Subprocess failure**: Log error, attempt restart
- **File watch failure**: Log error, continue with current process

### Future Enhancements (Deferred)
- Request buffering during restart
- Response queuing
- Graceful request-response pairing
- Connection state preservation

## Edge Cases (Simple Handling)

### 1. Stdin Write During Restart
- **Simple approach**: Allow write to fail/block temporarily
- **Impact**: Client may timeout and retry
- **Mitigation**: Fast restart times minimize window

### 2. Stdout Read During Restart
- **Simple approach**: Allow read to return empty/EOF temporarily
- **Impact**: Client may see disconnection
- **Mitigation**: MCP protocol should handle reconnection

### 3. Rapid File Changes
- **Simple approach**: Ignore changes during restart
- **Impact**: Some changes may be missed
- **Mitigation**: Developers can manually restart if needed

## Testing Strategy
- Unit tests for argument filtering
- Integration tests for basic restart functionality
- Manual testing with actual file changes
- Performance testing for restart times

## Success Criteria
- ✅ `sphinxmcps serve --develop` starts successfully
- ✅ File changes trigger server restart
- ✅ Basic MCP functionality works after restart
- ✅ No crashes or hangs during normal operation
- ✅ Graceful shutdown works correctly

## Implementation Status: COMPLETED

### What We've Accomplished
1. **CLI Integration**: Added `--develop` flag to `ServeCommand` with proper help text
2. **Server Routing**: Modified `serve()` function to route to development mode when flag is set
3. **File Watching**: Implemented `_serve_develop()` using `watchfiles.awatch()` to monitor source files
4. **Subprocess Management**: Created child process management with graceful termination
5. **Stdio Bridging**: Implemented transparent stdio stream bridging between parent and child processes
6. **Argument Filtering**: Child processes receive filtered arguments (no --develop flag)
7. **Error Handling**: Added proper exception handling and cleanup
8. **Code Quality**: All linters pass, follows project style guidelines
9. **Existing Tests**: All existing tests continue to pass

### Architecture Summary
```
Claude Code ↔ Parent Process (--develop mode) ↔ Child Process (normal MCP server)
                      ↓
               watchfiles monitors
             sources/sphinxmcps/*.py
```

### Key Implementation Details
- **Parent Process**: Handles file watching, subprocess lifecycle, stdio bridging
- **Child Process**: Runs normal MCP server in stdio mode (no knowledge of development)
- **File Monitoring**: Watches `.py` files, ignores `__pycache__`
- **Restart Logic**: Graceful termination → new process → resume stdio bridging
- **Simple Approach**: No request queuing (can be added later if needed)

## Future Enhancements
Once basic functionality is working, consider:
- Request buffering during restart
- Response queuing
- Connection state preservation
- Configurable file watch patterns
- Restart debouncing for rapid changes
- Better error recovery

## Implementation Order
1. Add CLI parameter and basic routing
2. Implement simple subprocess management
3. Add file watching with basic restart
4. Implement stdio bridging
5. Add error handling and cleanup
6. Testing and refinement