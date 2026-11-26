## Context

`sources/librovore/server.py` builds the MCP server with the v1 idiom: `FastMCP('Librovore Documentation Server', port=port)`, then `await mcp.run_sse_async(mount_path=None)` or `await mcp.run_stdio_async()`. MCP SDK 2.x renames `FastMCP` to `MCPServer` (new module `mcp.server.mcpserver`, old path removed, not deprecated), moves transport parameters (`host`, `port`) off the constructor onto `run()`/app methods, and removes `mount_path`. Tool registration (`mcp.tool()`), JSON-schema-from-hints, and stdio semantics are unchanged. Three tests patch `mcp.server.fastmcp.FastMCP.run_*_async` and fail on import under 2.x. Stakeholders: downstream `python-libravore` (blocked on fresh envs), Template Owner (dependency-pin conventions).

## Goals / Non-Goals

**Goals:**
- Run unmodified server behavior (same tools, same stdio/SSE transports) on MCP SDK 2.x.
- Remove the `mcp<2` pin.

**Non-Goals:**
- Adopting streamable-HTTP transport (stays stdio/SSE as today).
- Adding a `host` CLI option (keep current `port`-only surface; bind host stays the SDK default).
- Changing tool schemas, names, or the `serve()` signature.

## Decisions

- **Direct v2 port, no compatibility shim.** Import `MCPServer` from `mcp.server.mcpserver` unconditionally and require MCP 2.x. Rationale: the v1 path is removed upstream (no deprecation window to straddle), and a try/except dual import would double the test matrix. Alternative (version-conditional import) rejected for that reason.
- **Keep awaiting `run_sse_async` / `run_stdio_async` in `serve()`.** Rationale: preserves the current async structure and test seams (mock-patch targets move mechanically to the v2 path). The v2 `run()` is sync and owns its own event loop, which would force restructuring `serve()`; the async entry points still exist in 2.x. Confirmed against MCP 2.3.0: `run_sse_async(*, host='127.0.0.1', port=8000, sse_path='/sse', message_path='/messages/', ...)` and argument-free `run_stdio_async`; the SSE call becomes `run_sse_async(port=port)` with no `mount_path`.
- **Drop `mount_path=None`, pass `port` at run time.** `mount_path` is removed in v2 (sub-path mounting goes through ASGI `root_path`, which we do not use); `port` moves from constructor to the SSE run call. stdio call is unchanged.
- **Pin floor `mcp>=2,<3`-style bound** (exact specifier per template dependency conventions at implementation time). Rationale: guard against a future v3 while tracking 2.x.

## Risks / Trade-offs

- [Risk] Transport tests only mock run entry points, and the protocol integration tests are commented out → Mitigation: harden the patches with `autospec` plus awaited-with assertions (non-default port for SSE), add an in-process `list_tools` check pinning registration and schemas, and add a small real-client smoke per promised transport (stdio and legacy SSE, including a non-default SSE port).
- [Risk] Fresh-env resolution picks an MCP 2.x newer than the one validated → Mitigation: upper-bound the pin below v3; CI builds a fresh env every run.
- [Risk] `mcp.server.mcpserver` internal layout shifts within 2.x → Mitigation: import from the documented public path only (`mcp.server.mcpserver.MCPServer`, with `from mcp.server import MCPServer` as the documented alternative if stable).

## Migration Plan

1. Land the port on a branch; validate on a fresh hatch env (new lock resolves MCP 2.x).
2. Merge to master; downstream `python-libravore`, which is waiting directly on a new `librovore` release, picks up MCP 2.x support at leisure.
3. Rollback: revert the branch (restores the `mcp<2` pin) — no data migration involved.

## Open Questions

- None: the `run_sse_async` signature was confirmed against MCP 2.3.0 during proposal review.
