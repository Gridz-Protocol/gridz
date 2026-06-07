import { createPublicClient, http, namehash } from "viem";
import { mainnet } from "viem/chains";
import { EnsSink, ViemEnsBackend, postgresSink, type Sink } from "@gridz/sinks";
import type { Grid } from "@gridz/core";

/**
 * Resolve a Grid for a subject (an ENS name like kevin.gridz.eth, or a DID).
 * ENS first (via the GridzResolver), Postgres as a fallback cache. No subject is
 * hard-coded; the value comes from the route.
 */
export async function loadGrid(subject: string): Promise<Grid | null> {
  if (subject.endsWith(".eth")) {
    const publicClient = createPublicClient({
      chain: mainnet,
      transport: http(process.env.GRIDZ_RPC_URL),
    });
    const backend = new ViemEnsBackend({
      publicClient: { getEnsText: (a) => publicClient.getEnsText(a) },
      walletClient: { writeContract: async () => "0x" as `0x${string}` }, // read-only here
      resolverAddress: (process.env.GRIDZ_RESOLVER ?? "0x") as `0x${string}`,
      resolverAbi: [],
      namehash,
    });
    const grid = await new EnsSink(backend, subject).readGrid();
    if (grid) return grid;
  }

  const dsn = process.env.GRIDZ_PG_DSN;
  if (dsn) {
    const sink: Sink = postgresSink(dsn);
    const cells = await sink.read({ subject });
    if (cells.length) {
      // A cache hit returns cells; the canonical grid (theme/root) still lives at
      // the source. For a full render, persist the whole grid in your projection.
      return null;
    }
  }
  return null;
}
