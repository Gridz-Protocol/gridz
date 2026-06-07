import { buildGrid, verifyGrid, type Hex, type Signer } from "@gridz/core";
import { sqliteSink } from "@gridz/sinks";
import { DEFAULT_THEME } from "@gridz/cli";

export interface QuickstartOptions {
  resolver: Hex;
  chainId: number;
  dbPath?: string;
  now?: Date;
}

/**
 * End-to-end agent flow signed by an HSM. Pass a OneClawSigner (HSM-backed) — the
 * agent's two cells (agent-context, agent-endpoint[mcp]) are signed inside the
 * HSM, published to a sink, and verified. The grid's attestations report format
 * eip712-oneclaw, yet verify identically to any local signer.
 */
export async function quickstart(
  signer: Signer,
  opts: QuickstartOptions,
): Promise<{ did: string; format: string; cells: number; verified: boolean }> {
  const did = await signer.did();
  const grid = await buildGrid(signer, {
    subject: { type: "agent", did },
    theme: DEFAULT_THEME,
    chainId: opts.chainId,
    verifyingContract: opts.resolver,
    now: opts.now,
    cells: [
      { id: "a1", key: "agent-context", value: "An example Gridz agent.", position: { x: 0, y: 0, w: 2, h: 2 }, size: "2x2" },
      { id: "a2", key: "agent-endpoint[mcp]", value: "https://gridz.dev/mcp", position: { x: 2, y: 0, w: 1, h: 1 }, size: "1x1" },
    ],
  });

  await sqliteSink(opts.dbPath).write(grid.cells, { subject: grid.subject });
  const result = await verifyGrid(grid, opts.now ? { now: opts.now } : {});
  return { did, format: grid.cells[0]!.attestation.format, cells: grid.cells.length, verified: result.ok };
}
