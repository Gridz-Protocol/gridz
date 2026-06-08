#!/usr/bin/env node
/** Push Gridz env vars to the linked Vercel project for examples/next-app. */
import { spawnSync } from "node:child_process";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const require = createRequire(join(ROOT, "examples/next-app/package.json"));
const { privateKeyToAccount } = require("viem/accounts");

const VARS = [
  ["GRIDZ_RPC_URL", "production"],
  ["GRIDZ_RESOLVER", "production"],
  ["GRIDZ_CHAIN_ID", "production"],
  ["GRIDZ_ENS_BASE", "production"],
  ["NEXT_PUBLIC_GRIDZ_ENS_BASE", "production"],
  ["NEXT_PUBLIC_GRIDZ_RESOLVER", "production"],
  ["NEXT_PUBLIC_GRIDZ_CHAIN_ID", "production"],
  ["NEXT_PUBLIC_GRIDZ_RPC_URL", "production"],
  ["NEXT_PUBLIC_SITE_URL", "production"],
  ["NEXT_PUBLIC_SITE_DOMAIN", "production"],
  ["EAS_ADDRESS", "production"],
  ["CELL_SCHEMA", "production"],
  ["NEXT_PUBLIC_EAS_ADDRESS", "production"],
  ["NEXT_PUBLIC_CELL_SCHEMA", "production"],
  ["DEPLOYER_PRIVATE_KEY", "production"],
  ["NEXT_PUBLIC_DEMO_PROFILE_SUBJECT", "production"],
  ["GRIDZ_SIGNER_KEY", "production"],
  ["REGISTRAR_PRIVATE_KEY", "production"],
  ["NEXT_PUBLIC_REGISTRAR_ADDRESS", "production"],
  ["NEXT_PUBLIC_WALLETCONNECT_PROJECT_ID", "production"],
  ["PINATA_JWT", "production"],
  ["PINATA_API_KEY", "production"],
  ["PINATA_API_SECRET", "production"],
  ["PINATA_GATEWAY_URL", "production"],
  ["PINATA_GATEWAY", "production"],
];

function add(name, value, env) {
  if (!value) return;
  const res = spawnSync("vercel", ["env", "add", name, env, "--force"], {
    cwd: ROOT,
    input: value,
    encoding: "utf8",
  });
  if (res.status !== 0) {
    console.error(`vercel env add ${name} failed:`, res.stderr || res.stdout);
    process.exit(1);
  }
  console.log(`  ${name} (${env})`);
}

function registrarAddressFromEnv(env) {
  const key = env.REGISTRAR_PRIVATE_KEY ?? env.DEPLOYER_PRIVATE_KEY;
  if (!key?.startsWith("0x")) return env.NEXT_PUBLIC_REGISTRAR_ADDRESS ?? "";
  try {
    return privateKeyToAccount(key).address;
  } catch {
    return env.NEXT_PUBLIC_REGISTRAR_ADDRESS ?? "";
  }
}

const values = {
  ...process.env,
  REGISTRAR_PRIVATE_KEY: process.env.REGISTRAR_PRIVATE_KEY ?? process.env.DEPLOYER_PRIVATE_KEY ?? "",
  NEXT_PUBLIC_GRIDZ_ENS_BASE:
    process.env.NEXT_PUBLIC_GRIDZ_ENS_BASE ?? process.env.GRIDZ_ENS_BASE ?? "gridz.eth",
  NEXT_PUBLIC_GRIDZ_RESOLVER:
    process.env.NEXT_PUBLIC_GRIDZ_RESOLVER ?? process.env.GRIDZ_RESOLVER ?? "",
  NEXT_PUBLIC_GRIDZ_CHAIN_ID:
    process.env.NEXT_PUBLIC_GRIDZ_CHAIN_ID ?? process.env.GRIDZ_CHAIN_ID ?? "1",
  NEXT_PUBLIC_GRIDZ_RPC_URL:
    process.env.NEXT_PUBLIC_GRIDZ_RPC_URL ?? process.env.GRIDZ_RPC_URL ?? "",
  NEXT_PUBLIC_SITE_URL: process.env.NEXT_PUBLIC_SITE_URL ?? "https://gridz.bio",
  NEXT_PUBLIC_SITE_DOMAIN: process.env.NEXT_PUBLIC_SITE_DOMAIN ?? "gridz.bio",
  NEXT_PUBLIC_DEMO_PROFILE_SUBJECT: process.env.NEXT_PUBLIC_DEMO_PROFILE_SUBJECT ?? "demo.gridz.eth",
  NEXT_PUBLIC_EAS_ADDRESS: process.env.NEXT_PUBLIC_EAS_ADDRESS ?? process.env.EAS_ADDRESS ?? "",
  NEXT_PUBLIC_CELL_SCHEMA: process.env.NEXT_PUBLIC_CELL_SCHEMA ?? process.env.CELL_SCHEMA ?? "",
  NEXT_PUBLIC_REGISTRAR_ADDRESS:
    process.env.NEXT_PUBLIC_REGISTRAR_ADDRESS ?? registrarAddressFromEnv(process.env),
};

for (const [key, target] of VARS) {
  add(key, values[key], target);
}
