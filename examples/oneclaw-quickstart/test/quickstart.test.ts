import { describe, it, expect } from "vitest";
import { LocalEip712Signer, type Hex } from "@gridz/core";
import { OneClawSigner } from "@gridz/oneclaw";
import { quickstart } from "../src/quickstart.js";

const CHAIN_ID = 11155111;
const RESOLVER = "0x000000000000000000000000000000000000c0de" as Hex;
const NOW = new Date("2026-01-01T00:00:00.000Z");
const KEY = `0x${"ab".repeat(32)}` as Hex;

// Stands in for the 1claw HSM: signs typed-data intents with a local key.
const hsm = LocalEip712Signer.fromPrivateKey(KEY, CHAIN_ID);

async function fakeOneClawFetch(_url: string | URL | Request, init?: RequestInit): Promise<Response> {
  const body = JSON.parse(String(init?.body ?? "{}"));
  const td = body.typed_data;
  // Handles both GridzCell and GridzRoot: revive each uint field as bigint.
  const fields = td.types[td.primaryType] as { name: string; type: string }[];
  const message: Record<string, unknown> = { ...td.message };
  for (const f of fields) {
    if (f.type.startsWith("uint")) message[f.name] = BigInt(message[f.name] as string);
  }
  const { signature } = await hsm.signTypedData({
    domain: td.domain,
    types: { [td.primaryType]: fields },
    primaryType: td.primaryType,
    message,
  });
  return { ok: true, status: 200, json: async () => ({ signature, from: hsm.address }) } as unknown as Response;
}

describe("oneclaw-quickstart", () => {
  it("HSM-signs an agent grid that verifies, reporting eip712-oneclaw", async () => {
    const signer = new OneClawSigner(
      { agentId: "a", apiKey: "ocv_x", address: hsm.address, chainId: CHAIN_ID },
      { fetch: fakeOneClawFetch },
    );
    const result = await quickstart(signer, { resolver: RESOLVER, chainId: CHAIN_ID, now: NOW });
    expect(result.format).toBe("eip712-oneclaw");
    expect(result.cells).toBe(2);
    expect(result.verified).toBe(true);
  });

  it("works with default now and in-memory db", async () => {
    const signer = new OneClawSigner(
      { agentId: "a", apiKey: "ocv_x", address: hsm.address, chainId: CHAIN_ID },
      { fetch: fakeOneClawFetch },
    );
    const result = await quickstart(signer, { resolver: RESOLVER, chainId: CHAIN_ID });
    expect(result.verified).toBe(true);
  });
});
