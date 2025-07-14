# Sphinx MCP Server - Testing Protocol

## Overview

This document describes the testing infrastructure established for rapid development and testing of the Sphinx MCP Server without requiring Claude Code restarts.

## Testing Infrastructure

### Native TCP Bridge (stdio-over-tcp transport)

The primary testing method uses the built-in `stdio-over-tcp` transport:

```bash
# Start TCP bridge with dynamic port assignment
hatch run sphinxmcps serve --transport stdio-over-tcp --port 0

# Or use fixed port
hatch run sphinxmcps serve --transport stdio-over-tcp --port 8005
```

This approach provides:
- ✅ **No external dependencies** (eliminates socat requirement)
- ✅ **Dynamic port assignment** (eliminates port conflicts)
- ✅ **Direct JSON-RPC communication** over TCP
- ✅ **Multiple concurrent connections** via asyncio
- ✅ **Clean subprocess management** with proper cleanup

### MCP Protocol Handshake

All MCP communication requires proper initialization sequence:

1. **Initialize connection** with client info and capabilities
2. **Send initialized notification** to complete handshake  
3. **Send actual commands** (tools/list, tools/call, etc.)

### Standard Test Template

```bash
timeout 5 bash -c 'printf "%s\n%s\n%s\n" \
  "INITIALIZE_JSON" \
  "NOTIFY_INITIALIZED_JSON" \
  "COMMAND_JSON" | nc localhost PORT'
```

## Common Test Commands

### 1. Initialize Connection

```json
{
  "jsonrpc": "2.0",
  "method": "initialize", 
  "params": {
    "protocolVersion": "2024-11-05",
    "capabilities": {
      "roots": {"listChanged": true},
      "sampling": {}
    },
    "clientInfo": {
      "name": "test-client", 
      "version": "1.0.0"
    }
  },
  "id": 1
}
```

### 2. Initialized Notification

```json
{
  "jsonrpc": "2.0",
  "method": "notifications/initialized"
}
```

### 3. List Available Tools

```json
{
  "jsonrpc": "2.0",
  "method": "tools/list",
  "id": 2
}
```

### 4. Call a Tool

```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "hello",
    "arguments": {
      "name": "Claude"
    }
  },
  "id": 3
}
```

## Working Examples

### Test Tools List

```bash
timeout 5 bash -c 'printf "%s\n%s\n%s\n" \
  "{\"jsonrpc\":\"2.0\",\"method\":\"initialize\",\"params\":{\"protocolVersion\":\"2024-11-05\",\"capabilities\":{\"roots\":{\"listChanged\":true},\"sampling\":{}},\"clientInfo\":{\"name\":\"test-client\",\"version\":\"1.0.0\"}},\"id\":1}" \
  "{\"jsonrpc\":\"2.0\",\"method\":\"notifications/initialized\"}" \
  "{\"jsonrpc\":\"2.0\",\"method\":\"tools/list\",\"id\":2}" | nc localhost PORT'
```

**Expected Response:**
```json
{"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"2024-11-05","capabilities":{"experimental":{},"prompts":{"listChanged":false},"resources":{"subscribe":false,"listChanged":false},"tools":{"listChanged":false}},"serverInfo":{"name":"Sphinx MCP Server","version":"1.11.0"}}}
{"jsonrpc":"2.0","id":2,"result":{"tools":[{"name":"hello","description":" Says hello with the given name. ","inputSchema":{"properties":{"name":{"default":"World","title":"Name","type":"string"}},"title":"helloArguments","type":"object"},"outputSchema":{"properties":{"result":{"title":"Result","type":"string"}},"required":["result"],"title":"helloOutput","type":"object"}}]}}
```

### Test Tool Execution

```bash
timeout 5 bash -c 'printf "%s\n%s\n%s\n" \
  "{\"jsonrpc\":\"2.0\",\"method\":\"initialize\",\"params\":{\"protocolVersion\":\"2024-11-05\",\"capabilities\":{\"roots\":{\"listChanged\":true},\"sampling\":{}},\"clientInfo\":{\"name\":\"test-client\",\"version\":\"1.0.0\"}},\"id\":1}" \
  "{\"jsonrpc\":\"2.0\",\"method\":\"notifications/initialized\"}" \
  "{\"jsonrpc\":\"2.0\",\"method\":\"tools/call\",\"params\":{\"name\":\"hello\",\"arguments\":{\"name\":\"Claude\"}},\"id\":3}" | nc localhost PORT'
```

**Expected Response:**
```json
{"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"2024-11-05","capabilities":{"experimental":{},"prompts":{"listChanged":false},"resources":{"subscribe":false,"listChanged":false},"tools":{"listChanged":false}},"serverInfo":{"name":"Sphinx MCP Server","version":"1.11.0"}}}
{"jsonrpc":"2.0","id":3,"result":{"content":[{"type":"text","text":"Hello, Claude!"}],"structuredContent":{"result":"Hello, Claude!"},"isError":false}}
```

## Server Monitoring

The server logs show processing activity:
```text
mcp.server.lowlevel.server: Processing request of type ListToolsRequest
mcp.server.lowlevel.server: Processing request of type CallToolRequest
```

## Alternative Testing Approaches

### HTTP/SSE Transport (More Complex)

The HTTP/SSE transport requires session management:
1. Connect to `/sse` endpoint to get session ID
2. Use session ID for `/messages/` POST requests  
3. Listen to SSE stream for responses

This approach is more complex due to session persistence requirements.

### Python asyncio Testing (Recommended for Integration Tests)

For programmatic testing, use Python asyncio clients:
```python
async def test_mcp_server():
    reader, writer = await asyncio.open_connection('localhost', port)
    # Send MCP requests and receive responses
    # See .auxiliary/scribbles/test_stdio_over_tcp.py for examples
```

## Testing Guidelines

### ⚠️ Important: Avoid Large Inventory Dumps

**DO NOT** dump entire inventories from large sites like `python.org` during testing:
- ❌ **Avoid**: `extract_inventory` or `filter_inventory` with minimal filtering on large sites
- ❌ **Avoid**: JSON output of complete inventories from major documentation sites
- ✅ **Prefer**: Local inventories generated by `hatch --env develop run docsgen`
- ✅ **Prefer**: Highly filtered results (`domain` + `role` + `search` filters)
- ✅ **Prefer**: Summary output format for large inventories

### Recommended Test Sources

1. **Local inventory** (preferred for development):
   ```bash
   # Generate local docs first
   hatch --env develop run docsgen
   # Use local inventory
   ".auxiliary/artifacts/sphinx-html/objects.inv"
   ```

2. **Small external inventories**:
   - `https://sphobjinv.readthedocs.io/en/latest` (220 objects)
   - Other smaller documentation sites

3. **Filtered large inventories** (when testing filters):
   - `domain=py&role=class&search=Exception` (small result set)
   - Use summary format, not JSON for large sites

## Development Workflow Benefits

This testing infrastructure enables:
- ✅ **Rapid iteration** on tool development
- ✅ **Immediate feedback** on schema changes
- ✅ **No Claude Code restarts** required
- ✅ **Full MCP protocol validation**
- ✅ **Easy debugging** of tool behavior

## Integration with Claude Code

For full integration testing, the server can be registered with Claude Code using:
```bash
uv run mcp install server.py --name "Sphinx MCP Server"
```

However, the socat bridge testing is preferred for development iteration.