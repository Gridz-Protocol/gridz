/**
 * Generates canonical cross-runtime fixtures from @gridz/core. Run with:
 *   node tests/cross-runtime/gen.ts
 * (Node 24 strips TS types natively.) Output JSON is committed so the Python
 * lane can be tested without first running the TS lane. Determinism comes from
 * seed-derived keys + a frozen `NOW`; re-running produces byte-identical output.
 */
import { writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import {
  LocalEip712Signer,
  Ed25519Signer,
  buildGrid,
  hashUtf8,
  type Hex,
  type Theme,
} from "../../packages/core-ts/dist/index.js";

const CHAIN_ID = 11155111;
const RESOLVER = "0x000000000000000000000000000000000000c0de";
const NOW = new Date("2026-01-01T00:00:00.000Z");

const hexToBytes = (h: Hex) =>
  Uint8Array.from((h.slice(2).match(/.{2}/g) ?? []).map((b) => parseInt(b, 16)));

const eip712 = LocalEip712Signer.fromPrivateKey(
  hashUtf8("keccak256", "gridz/__example__/signer/1"),
  CHAIN_ID,
);
const ed25519 = new Ed25519Signer(hexToBytes(hashUtf8("sha256", "gridz/__example__/ed/1")));

const theme: Theme = {
  background_type: "solid",
  background_value: "#0b0b0f",
  accent_color: "#7c5cff",
  text_color: "#f4f4f5",
  card_style: "rounded",
  card_background: "#16161c",
  font_family: "sans",
  show_gridz_badge: true,
};

const pos = { x: 0, y: 0, w: 1, h: 1 };
const cells = [
  { id: "c1", key: "alias", value: "gridz-example", position: pos, size: "1x1" },
  {
    id: "c2",
    key: "description",
    value: "a seed-derived example grid",
    position: { ...pos, x: 1 },
    size: "2x1",
  },
  {
    id: "c3",
    key: "gridz.poll",
    value: { q: "ship it?", options: ["yes", "also yes"] },
    widget_type: "gridz.poll",
    position: { ...pos, y: 1 },
    size: "2x2",
  },
];

const out = (name: string) => fileURLToPath(new URL(`./fixtures/${name}`, import.meta.url));

const eipGrid = await buildGrid(eip712, {
  subject: { type: "human", did: await eip712.did() },
  theme,
  chainId: CHAIN_ID,
  verifyingContract: RESOLVER,
  now: NOW,
  cells,
});
writeFileSync(out("ts-eip712-grid.json"), JSON.stringify(eipGrid, null, 2) + "\n");

const edGrid = await buildGrid(ed25519, {
  subject: { type: "agent", did: await ed25519.did() },
  theme,
  now: NOW,
  cells: [
    { id: "a1", key: "agent-context", value: "example agent context", position: pos, size: "1x1" },
    { id: "a2", key: "agent-endpoint[mcp]", value: "https://gridz.dev/mcp", position: pos, size: "1x1" },
  ],
});
writeFileSync(out("ts-ed25519-grid.json"), JSON.stringify(edGrid, null, 2) + "\n");

console.log("wrote ts-eip712-grid.json, ts-ed25519-grid.json");
