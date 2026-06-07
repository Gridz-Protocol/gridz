#!/usr/bin/env node
/** Push Gridz env vars to the linked Vercel project for examples/next-app. */
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");

const VARS = [
  ["GRIDZ_RPC_URL", "production"],
  ["GRIDZ_RESOLVER", "production"],
  ["GRIDZ_CHAIN_ID", "production"],
  ["GRIDZ_ENS_BASE", "production"],
  ["NEXT_PUBLIC_GRIDZ_ENS_BASE", "production"],
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

const values = {
  ...process.env,
  NEXT_PUBLIC_GRIDZ_ENS_BASE:
    process.env.NEXT_PUBLIC_GRIDZ_ENS_BASE ?? process.env.GRIDZ_ENS_BASE ?? "gridz.eth",
};

for (const [key, target] of VARS) {
  add(key, values[key], target);
}
