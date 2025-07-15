# Hot-Reload Debugging Session - Findings and Analysis

## Issue Summary
The `--develop` flag for hot-reloading was implemented successfully, but MCP tool parameter validation fails after hot-reload with error `-32602: Invalid request parameters`.

## Root Cause Discovered
**MCP Session ID Persistence Issue**: The problem is NOT a race condition, but rather that Claude Code maintains session state and tries to reuse a session ID from before the hot-reload, while the new child process has no knowledge of that session.

### Debug Evidence
From `.auxiliary/inscriptions/server-child.txt`:
```
root: Failed to validate request: Received request before initialization was complete
root: Message that failed validation: method='tools/call' params={'name': 'extract_inventory', 'arguments': {'source': '.auxiliary/artifacts/sphinx-html', 'domain': 'py', 'role': 'function', 'term': 'extract'}} jsonrpc='2.0' id=5
```

The MCP protocol requires this initialization handshake:
1. Client sends "initialize" request
2. Server responds with capabilities  
3. Client sends "initialized" notification
4. Only then can tool calls be made

After hot-reload, the child process restarts fresh, but Claude Code skips re-initialization assuming the session is still valid.

## Debugging Infrastructure Added
1. **Separate child process logging**: Modified `_build_child_args()` to pass `--logfile .auxiliary/inscriptions/server-child.txt` to child processes
2. **Debug logging in tool functions**: Added `_scribe.debug()` calls to track tool invocations
3. **Fixed argument order**: MCP CLI requires `--logfile` before `serve` subcommand

## Hot-Reload Architecture Analysis
Current implementation:
- Parent process uses `watchfiles` to monitor source changes
- When changes detected, parent terminates child and starts new one
- Parent bridges stdio between Claude Code and child process
- Child process runs actual MCP server with tools

## Alternative Approaches Brainstormed

### 1. In-Process Module Reloading (Most Promising)
```python
import importlib
import sys

# Watch for changes and reload modules
for module_name in list(sys.modules.keys()):
    if module_name.startswith('sphinxmcps'):
        module = sys.modules[module_name]
        importlib.reload(module)
```

**Pros:** 
- Maintains MCP session
- Simpler implementation  
- No stdio bridging complexity

**Cons:**
- Module reloading tricky with complex dependencies
- Some changes might not take effect (class definitions, decorators)
- Event loop and file watcher would still reference original modules

### 2. Exec-Based Restart
```python
import os
import sys
os.execv(sys.executable, [sys.executable] + sys.argv)
```

**Pros:**
- Complete process restart
- Maintains stdio file descriptors
- Should preserve MCP session from Claude Code's perspective

**Cons:**
- Platform-specific behavior
- Might not work reliably across all systems

### 3. Signal-Based Internal Reload
Send signal (SIGUSR1) to trigger module reloading without process restart.

### 4. Session State Management
- Handle session state at parent level
- Parent process manages MCP session and proxies/translates requests to child processes
- Complex due to need to inspect/patch MCP traffic

### 5. Convenience Scripts for stdio-over-tcp
Since hot-reload complexity may not be worth it, consider improving the existing `stdio-over-tcp` transport with convenience scripts for development workflow.

## MCP Python SDK Investigation
Searched official MCP Python SDK documentation - no mechanism found to initialize new MCP server with specific session ID. Session initialization appears handled automatically by MCP protocol implementation.

## Current Status
- **Issue reproduced and root cause identified**: MCP session ID persistence in Claude Code
- **Debugging infrastructure working**: Child process logging successfully captures tool invocations
- **Hot-reload mechanism working**: File changes trigger restarts correctly
- **Problem isolated**: Not a race condition but session state management issue

## Next Steps
1. **Evaluate if hot-reload complexity is worthwhile** vs improving stdio-over-tcp development workflow
2. **Consider in-process module reloading** as potentially simpler approach
3. **Investigate exec-based restart** for maintaining stdio file descriptors
4. **Create convenience scripts** for stdio-over-tcp development if hot-reload proves too complex

## Files Modified
- `sources/sphinxmcps/server.py`: Added debug logging, fixed child process logging
- `.auxiliary/configuration/mcp-servers.json`: Added logging configuration  
- `.auxiliary/inscriptions/server.txt`: Parent process logs
- `.auxiliary/inscriptions/server-child.txt`: Child process logs (new)

## Key Insight
The fundamental challenge is that MCP protocol sessions are stateful, but our hot-reload approach creates new processes that break session continuity. Any solution must either:
1. Maintain session continuity across reloads (in-process reloading)
2. Preserve process identity while reloading code (exec-based restart)
3. Manage session state at a higher level (parent process proxying)
4. Accept the limitation and improve alternative development workflows

The stdio-over-tcp transport may be the most pragmatic approach for development iteration.