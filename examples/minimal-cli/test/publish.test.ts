import { describe, it, expect } from "vitest";
import { mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { stringify } from "yaml";
import { LocalEip712Signer, type Hex } from "@gridz/core";
import { DEFAULT_THEME } from "@gridz/cli";
import { publish } from "../src/publish.js";

const KEY = `0x${"99".repeat(32)}` as Hex;
const RESOLVER = "0x000000000000000000000000000000000000c0de" as Hex;
const NOW = new Date("2026-01-01T00:00:00.000Z");

describe("minimal-cli publish flow", () => {
  it("signs, publishes to sqlite, verifies, and renders HTML", async () => {
    const dir = mkdtempSync(join(tmpdir(), "gridz-min-"));
    const configPath = join(dir, "gridz.yaml");
    const outHtml = join(dir, "grid.html");
    const did = await LocalEip712Signer.fromPrivateKey(KEY, 11155111).did();

    // A config filled with deterministic, clearly-example values (no real-person data).
    writeFileSync(
      configPath,
      stringify({
        schema_version: "gridz/1.0.0",
        subject: { type: "human", did },
        theme: DEFAULT_THEME,
        cells: [
          { key: "alias", value: "gridz-example", size: "1x1" },
          { key: "url", value: "https://gridz.dev", size: "1x1" },
        ],
      }),
    );

    const result = await publish({ configPath, outHtml, signerKey: KEY, resolver: RESOLVER, dbPath: join(dir, "g.db"), now: NOW });
    expect(result).toMatchObject({ did, cells: 2, published: 2, verified: true });

    const html = readFileSync(outHtml, "utf8");
    expect(html).toContain("gridz-example");
    expect(html).toContain('data-status="verified"');
  });

  it("works with an ENS subname and default chainId (no now/db overrides)", async () => {
    const dir = mkdtempSync(join(tmpdir(), "gridz-min-"));
    const configPath = join(dir, "gridz.yaml");
    const did = await LocalEip712Signer.fromPrivateKey(KEY, 11155111).did();
    writeFileSync(
      configPath,
      stringify({
        schema_version: "gridz/1.0.0",
        // gridz.eth subname — the operator's own name, resolved via the wildcard resolver.
        subject: { type: "human", did, ens: "kevin.gridz.eth" },
        theme: DEFAULT_THEME,
        cells: [{ key: "alias", value: "gridz-example", size: "1x1" }],
      }),
    );
    const result = await publish({ configPath, outHtml: join(dir, "grid.html"), signerKey: KEY, resolver: RESOLVER });
    expect(result.verified).toBe(true);
  });

  it("refuses an unfilled (invalid) config", async () => {
    const dir = mkdtempSync(join(tmpdir(), "gridz-min-"));
    const configPath = join(dir, "gridz.yaml");
    writeFileSync(
      configPath,
      stringify({
        schema_version: "gridz/1.0.0",
        subject: { type: "human", did: null },
        theme: DEFAULT_THEME,
        cells: [{ key: "alias", value: null, _needs_input: true }],
      }),
    );
    await expect(
      publish({ configPath, outHtml: join(dir, "o.html"), signerKey: KEY, resolver: RESOLVER, now: NOW }),
    ).rejects.toThrow(/not ready/);
  });
});
