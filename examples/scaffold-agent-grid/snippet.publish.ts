// Snippet: an agent publishing its own Gridz profile, then reading a peer's over MCP.
// Drop into a scaffold-agent project (after `pnpm add @gridz/* `).
import { buildGrid, verifyGrid, type Signer } from "@gridz/core";
import { sqliteSink } from "@gridz/sinks";

const THEME = {
  background_type: "solid" as const,
  background_value: "#0b0b0f",
  accent_color: "#7c5cff",
  text_color: "#f4f4f5",
  card_style: "rounded" as const,
  card_background: "#16161c",
  font_family: "mono",
};

/** Publish this agent's own grid. `signer` is the agent's signer (key/passkey/1claw). */
export async function publishAgentGrid(signer: Signer, mcpEndpoint: string) {
  const did = await signer.did();
  const grid = await buildGrid(signer, {
    subject: { type: "agent", did },
    theme: THEME,
    chainId: 11155111,
    verifyingContract: "0x000000000000000000000000000000000000c0de",
    cells: [
      { id: "ctx", key: "agent-context", value: "Describe what this agent does.", position: { x: 0, y: 0, w: 2, h: 2 }, size: "2x2" },
      { id: "mcp", key: "agent-endpoint[mcp]", value: mcpEndpoint, position: { x: 2, y: 0, w: 1, h: 1 }, size: "1x1" },
    ],
  });
  await sqliteSink("./agent.db").write(grid.cells, { subject: grid.subject });
  const result = await verifyGrid(grid);
  return { did, verified: result.ok };
}

/** Read a peer agent's grid over MCP and verify before trusting it. */
export async function readPeerGrid(mcpClient: { callTool: (n: string, a: unknown) => Promise<unknown> }, subject: string) {
  const grid = await mcpClient.callTool("grid.read", { subject });
  const verification = await mcpClient.callTool("grid.verify", { grid });
  return { grid, verification };
}
