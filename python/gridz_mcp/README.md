# gridz-mcp (Python)

Gridz MCP server (jlowin/fastmcp). Same tool surface as `@gridz/mcp`. Never signs
server-side: `cell_prepare_write` returns an unsigned EIP-712 payload and
`cell_attach_signature` stitches in a client-produced signature.

```bash
uv sync --extra dev && uv run pytest
uv run gridz-mcp           # stdio
```

End-to-end validation uses the MCP Inspector (see ../../packages/mcp-ts/test/README.md).
