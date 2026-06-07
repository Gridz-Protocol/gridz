#!/usr/bin/env node
import { publish } from "./src/publish.js";

// Demo entry: reads gridz.yaml, GRIDZ_SIGNER_KEY, GRIDZ_RESOLVER from env.
const key = process.env.GRIDZ_SIGNER_KEY as `0x${string}` | undefined;
if (!key) {
  console.error("Set GRIDZ_SIGNER_KEY (a 0x private key) — see README. Gridz never stores it.");
  process.exit(1);
}
const result = await publish({
  configPath: process.argv[2] ?? "gridz.yaml",
  outHtml: process.argv[3] ?? "grid.html",
  signerKey: key,
  resolver: (process.env.GRIDZ_RESOLVER as `0x${string}`) ?? "0x000000000000000000000000000000000000c0de",
});
console.log(`✓ published ${result.cells} cells for ${result.did} → ${result.out} (verified: ${result.verified})`);
