#!/usr/bin/env node
import { OneClawSigner, loadOneClawConfig } from "@gridz/oneclaw";
import { quickstart } from "./src/quickstart.js";

// Real 1claw: set ONECLAW_AGENT_ID, ONECLAW_AGENT_KEY (ocv_…), ONECLAW_ADDRESS,
// ONECLAW_CHAIN_ID. The CLI must already have added the Gridz EIP-712 domain to
// the agent's allowlist (gridz identity import --from oneclaw).
const config = loadOneClawConfig();
if (!config) {
  console.error("Set ONECLAW_AGENT_ID / ONECLAW_AGENT_KEY / ONECLAW_ADDRESS — see README.");
  process.exit(1);
}
const signer = new OneClawSigner(config);
const result = await quickstart(signer, {
  resolver: (process.env.GRIDZ_RESOLVER as `0x${string}`) ?? "0x000000000000000000000000000000000000c0de",
  chainId: config.chainId,
});
console.log(`✓ HSM-signed agent grid for ${result.did} — format ${result.format}, verified: ${result.verified}`);
