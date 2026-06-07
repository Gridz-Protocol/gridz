import { writeFileSync } from "node:fs";
import { LocalEip712Signer, buildGrid, verifyGrid, type Hex } from "@gridz/core";
import { renderGrid } from "@gridz/element";
import { sqliteSink } from "@gridz/sinks";
import { loadConfig, validateConfig, configToDrafts } from "@gridz/cli";

export interface PublishOptions {
  configPath: string;
  outHtml: string;
  signerKey: Hex;
  resolver: Hex;
  dbPath?: string;
  chainId?: number;
  now?: Date;
}

/**
 * The whole flow in one function: load a gridz.yaml, sign every cell with a local
 * key, publish to a sink, verify, and render to static HTML. Swap sqliteSink for
 * an ENS sink to publish to mygrid.eth (needs an RPC + wallet — see README).
 */
export async function publish(opts: PublishOptions): Promise<{
  did: string;
  cells: number;
  published: number;
  verified: boolean;
  out: string;
}> {
  const config = loadConfig(opts.configPath);
  const validation = validateConfig(config);
  if (!validation.ok) {
    throw new Error(`config is not ready: ${JSON.stringify(validation.errors)}`);
  }

  const chainId = opts.chainId ?? 11155111;
  const signer = LocalEip712Signer.fromPrivateKey(opts.signerKey, chainId);
  // validateConfig guarantees subject.did is present.
  const did = config.subject.did as string;

  const grid = await buildGrid(signer, {
    subject: { type: config.subject.type, did, ...(config.subject.ens ? { ens: config.subject.ens } : {}) },
    theme: config.theme,
    cells: configToDrafts(config.cells),
    chainId,
    verifyingContract: opts.resolver,
    now: opts.now,
  });

  const published = await sqliteSink(opts.dbPath).write(grid.cells, { subject: grid.subject });

  const result = await verifyGrid(grid, opts.now ? { now: opts.now } : {});
  const statuses = Object.fromEntries(result.cells.map((c) => [c.id, c.result.status]));
  writeFileSync(
    opts.outHtml,
    `<!doctype html><html><head><meta charset="utf-8"><title>Gridz</title></head><body>${renderGrid(grid, statuses)}</body></html>`,
  );

  return { did, cells: grid.cells.length, published: published.length, verified: result.ok, out: opts.outHtml };
}
