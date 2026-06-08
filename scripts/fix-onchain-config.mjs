#!/usr/bin/env node
/**
 * Upgrade GridzResolver and fix EAS + CELL_SCHEMA config on mainnet.
 * Requires DEPLOYER_PRIVATE_KEY (admin) and GRIDZ_RESOLVER in .env.
 */
import { readFileSync, existsSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { createRequire } from "node:module";
import { parseEnvBlock } from "./lib/constants.mjs";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const ENV_PATH = join(ROOT, ".env");
const require = createRequire(join(ROOT, "examples/next-app/package.json"));
const { createWalletClient, createPublicClient, http, getAddress, keccak256, encodePacked } = require("viem");
const { privateKeyToAccount } = require("viem/accounts");
const { mainnet } = require("viem/chains");

const EAS_MAINNET = getAddress("0xA1207F3BBa224E2c9c3c6D5aF63D0eb1582Ce587");
const CELL_SCHEMA_STRING =
  "bytes32 gridId, string key, string valueHashHex, uint64 expiresAt, bytes32 widgetTypeHash";

const RESOLVER_ABI = [
  {
    name: "setEas",
    type: "function",
    stateMutability: "nonpayable",
    inputs: [{ name: "_eas", type: "address" }],
    outputs: [],
  },
  {
    name: "setCellSchema",
    type: "function",
    stateMutability: "nonpayable",
    inputs: [{ name: "_cellSchema", type: "bytes32" }],
    outputs: [],
  },
  {
    name: "upgradeToAndCall",
    type: "function",
    stateMutability: "payable",
    inputs: [
      { name: "newImplementation", type: "address" },
      { name: "data", type: "bytes" },
    ],
    outputs: [],
  },
];

function cellSchemaUid() {
  const zero = getAddress("0x0000000000000000000000000000000000000000");
  return keccak256(encodePacked(["string", "address", "bool"], [CELL_SCHEMA_STRING, zero, true]));
}

function upsertEnv(key, value) {
  const text = readFileSync(ENV_PATH, "utf8");
  const line = `${key}=${value}`;
  const next = new RegExp(`^${key}=`, "m").test(text)
    ? text.replace(new RegExp(`^${key}=.*$`, "m"), line)
    : `${text.trimEnd()}\n${line}\n`;
  require("node:fs").writeFileSync(ENV_PATH, next, "utf8");
}

async function main() {
  if (!existsSync(ENV_PATH)) throw new Error("Missing .env");
  const env = parseEnvBlock(readFileSync(ENV_PATH, "utf8"));
  const key = env.DEPLOYER_PRIVATE_KEY;
  const proxy = env.GRIDZ_RESOLVER;
  const rpc = env.GRIDZ_RPC_URL ?? "https://ethereum.publicnode.com";
  if (!key?.startsWith("0x")) throw new Error("DEPLOYER_PRIVATE_KEY required");
  if (!proxy?.startsWith("0x")) throw new Error("GRIDZ_RESOLVER required");

  const schemaUid = cellSchemaUid();
  upsertEnv("EAS_ADDRESS", EAS_MAINNET);
  upsertEnv("CELL_SCHEMA", schemaUid);
  console.log(`CELL_SCHEMA=${schemaUid}`);
  console.log(`EAS_ADDRESS=${EAS_MAINNET}`);

  console.log("Upgrading GridzResolver implementation…");
  const up = spawnSync(
    "forge",
    ["script", "script/Upgrade.s.sol:Upgrade", "--rpc-url", rpc, "--broadcast", "--private-key", key],
    {
      cwd: join(ROOT, "contracts"),
      env: { ...process.env, PROXY_ADDRESS: proxy },
      stdio: "inherit",
    },
  );
  if (up.status !== 0) throw new Error("forge upgrade failed");

  const account = privateKeyToAccount(key);
  const transport = http(rpc);
  const walletClient = createWalletClient({ account, chain: mainnet, transport });
  const publicClient = createPublicClient({ chain: mainnet, transport });
  const resolver = getAddress(proxy);

  for (const [fn, args] of [
    ["setEas", [EAS_MAINNET]],
    ["setCellSchema", [schemaUid]],
  ]) {
    console.log(`Calling ${fn}…`);
    const hash = await walletClient.writeContract({
      account,
      chain: mainnet,
      address: resolver,
      abi: RESOLVER_ABI,
      functionName: fn,
      args,
    });
    await publicClient.waitForTransactionReceipt({ hash });
    console.log(`  tx ${hash}`);
  }

  console.log("On-chain config fixed.");
}

main().catch((e) => {
  console.error(e.message ?? e);
  process.exit(1);
});
