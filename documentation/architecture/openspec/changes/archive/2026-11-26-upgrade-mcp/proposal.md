## Why

The project pins `mcp<2` because MCP SDK 2.x removed `mcp.server.fastmcp.FastMCP` (renamed to `mcp.server.mcpserver.MCPServer`), which breaks our server import on any fresh environment resolving MCP 2.x. The pin is already biting downstream consumers. Migrating to the supported v2 API removes the pin and restores forward compatibility.

## What Changes

- Replace `from mcp.server.fastmcp import FastMCP` with the v2 `mcp.server.mcpserver.MCPServer` import in `sources/librovore/server.py`.
- Construct the server without transport parameters and pass `port` at run time for SSE (the SDK-default host is kept), per the v2 transport-configuration move (`MCPServer(..., port=...)` is now a `TypeError`; `mount_path` is removed).
- Update the three `mcp.server.fastmcp.FastMCP.*` mock-patch targets in `tests/test_000_librovore/test_500_server.py` to the v2 path.
- Replace the `mcp<2` pin with an MCP 2.x floor in `pyproject.toml`.
- No tool, transport, or CLI surface changes: stdio and SSE transports keep working exactly as before. **BREAKING** (dependency floor only): environments must resolve MCP SDK 2.x after this change.

## Capabilities

### New Capabilities

- None: no new user-facing behavior is introduced.

### Modified Capabilities

- `mcp-server`: the server implementation requirement names the FastMCP framework and v1 import/construction idioms; update it to the v2 `MCPServer` import, identity-only construction, and run-time transport configuration.

## Impact

- `sources/librovore/server.py` (import, construction, SSE/stdio run calls, type annotations, comments).
- `tests/test_000_librovore/test_500_server.py` (mock-patch targets).
- `pyproject.toml` (dependency pin).
- Downstream `python-libravore` (and any fresh environment resolving MCP 2.x) can run against a new release without a workaround pin.
- Requires a hatch environment refresh resolving MCP 2.x to validate; the exact v2 `run_sse_async` signature was confirmed against MCP 2.3.0 during proposal review.
