# oneclaw-quickstart

End-to-end agent flow signed by a **1claw HSM** — the private key never leaves the
HSM, yet the resulting grid verifies like any other.

```bash
# 1. Create a 1claw agent and provision an Ethereum signing key (dashboard.1claw.xyz).
# 2. Import it and add the Gridz EIP-712 domain to the agent's allowlist:
gridz identity import --from oneclaw --agent <agentId>
# 3. Run the quickstart:
export ONECLAW_AGENT_ID=... ONECLAW_AGENT_KEY=ocv_... ONECLAW_ADDRESS=0x... ONECLAW_CHAIN_ID=11155111
node bin.ts
```

It signs two cells (`agent-context`, `agent-endpoint[mcp]`) inside the HSM,
publishes to a sink, and verifies. The attestations report `format:
"eip712-oneclaw"` — provenance only; verification is byte-identical to a local
signer.

The test (`test/quickstart.test.ts`) runs this offline with a local HSM stand-in,
so CI exercises the whole path without a 1claw account. Live runs against the real
sandbox are gated on `GRIDZ_ONECLAW_API_KEY`.
