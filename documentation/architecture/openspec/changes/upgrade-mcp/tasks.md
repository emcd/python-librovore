## 1. Dependencies

- [x] 1.1 Replace the `mcp<2` pin with an MCP 2.x bound in `pyproject.toml`.
- [x] 1.2 Refresh the hatch develop environment and confirm the resolved MCP version.

## 2. Server Port

- [x] 2.1 Switch `server.py` to `from mcp.server.mcpserver import MCPServer`, keeping the private-alias pattern with the new name.
- [x] 2.2 Construct the server with identity only; move `port` to the SSE run call and drop `mount_path`.
- [x] 2.3 Update type annotations, comments, docstrings, and the startup log string naming FastMCP.
- [x] 2.4 Call `run_sse_async(port=port)` (host stays the SDK default) and keep `run_stdio_async()` argument-free, per the confirmed 2.3.0 signature.

## 3. Tests

- [x] 3.1 Retarget the three `mcp.server.fastmcp.FastMCP.*` mock patches in `test_500_server.py` to the v2 path.
- [x] 3.2 Harden the patches with `autospec=True` and assert awaited-with arguments (non-default port for the SSE case, empty call for stdio).
- [x] 3.3 Add an in-process `list_tools` check pinning tool registration and schema generation under `MCPServer`.
- [x] 3.4 Add a small real-client smoke per promised transport (stdio and legacy SSE on a non-default port).
- [x] 3.5 Run the server test module plus the full suite green on the fresh env.

## 4. Validation

- [x] 4.1 Run `hatch --env develop run testers` green on the fresh environment.
- [x] 4.2 Run linters (`ruff`, `isort`, `pyright`) and confirm no direct MCP v1 references remain in `sources/` and `tests/` (`grep mcp.server.fastmcp`, `grep FastMCP`).
