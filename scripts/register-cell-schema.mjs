#!/usr/bin/env node
/**
 * Register gridz.cell.v1 on EAS (or reuse existing UID) and write CELL_SCHEMA to .env.
 */
import { readFileSync, writeFileSync, existsSync } from "node:fs";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { parseEnvBlock } from "./lib/constants.mjs";
import { gridzChainForId } from "./lib/gridzChain.mjs";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const ENV_PATH = join(ROOT, ".env");
const require = createRequire(join(ROOT, "examples/next-app/package.json"));

const {
  createWalletClient,
  createPublicClient,
  http,
  getAddress,
  keccak256,
  encodePacked,
  toBytes,
} = require("viem");
const { privateKeyToAccount } = require("viem/accounts");
/** @see https://github.com/ethereum-attestation-service/eas-contracts deployments */
const SCHEMA_REGISTRY = {
  1: getAddress("0xA7b39296258348C78294F95B872b282326A97BDF"),
  11155111: getAddress("0x0a7E2Ff54e576B096E04665717A6C3B2a33b9e4a"),
  8453: getAddress("0x4200000000000000000000000000000000000020"),
};

const CELL_SCHEMA_STRING =
  "bytes32 gridId, string key, string valueHashHex, uint64 expiresAt, bytes32 widgetTypeHash";

const registryAbi = [
  {
    name: "register",
    type: "function",
    inputs: [
      { name: "schema", type: "string" },
      { name: "resolver", type: "address" },
      { name: "revocable", type: "bool" },
    ],
    outputs: [{ type: "bytes32" }],
    stateMutability: "nonpayable",
  },
  {
    name: "getSchema",
    type: "function",
    inputs: [{ name: "uid", type: "bytes32" }],
    outputs: [
      {
        type: "tuple",
        components: [
          { name: "uid", type: "bytes32" },
          { name: "resolver", type: "address" },
          { name: "revocable", type: "bool" },
          { name: "schema", type: "string" },
        ],
      },
    ],
    stateMutability: "view",
  },
];

function schemaUid(schema, resolver, revocable) {
  return keccak256(encodePacked(["string", "address", "bool"], [schema, resolver, revocable]));
}

function upsertEnv(key, value) {
  const text = readFileSync(ENV_PATH, "utf8");
  const line = `${key}=${value}`;
  if (new RegExp(`^${key}=`, "m").test(text)) {
    writeFileSync(ENV_PATH, text.replace(new RegExp(`^${key}=.*$`, "m"), line), "utf8");
  } else {
    writeFileSync(ENV_PATH, `${text.trimEnd()}\n${line}\n`, "utf8");
  }
}

async function main() {
  if (!existsSync(ENV_PATH)) throw new Error("Missing .env");
  const env = parseEnvBlock(readFileSync(ENV_PATH, "utf8"));
  const key = env.DEPLOYER_PRIVATE_KEY;
  const rpc = env.GRIDZ_RPC_URL ?? "https://ethereum.publicnode.com";
  const chainId = Number(env.GRIDZ_CHAIN_ID ?? "1");
  if (!key?.startsWith("0x")) throw new Error("DEPLOYER_PRIVATE_KEY required in .env");

  const registry = SCHEMA_REGISTRY[chainId];
  if (!registry) throw new Error(`No EAS SchemaRegistry for chain ${chainId}`);

  const chain = gridzChainForId(chainId);
  const account = privateKeyToAccount(key);
  const transport = http(rpc);
  const publicClient = createPublicClient({ chain, transport });
  const walletClient = createWalletClient({ chain, transport, account });

  const zeroResolver = getAddress("0x0000000000000000000000000000000000000000");
  const uid = schemaUid(CELL_SCHEMA_STRING, zeroResolver, true);

  const existing = await publicClient.readContract({
    address: registry,
    abi: registryAbi,
    functionName: "getSchema",
    args: [uid],
  });

  if (!existing?.schema) {
    console.log("Registering gridz.cell.v1 on EAS…");
    const hash = await walletClient.writeContract({
      address: registry,
      abi: registryAbi,
      functionName: "register",
      args: [CELL_SCHEMA_STRING, zeroResolver, true],
    });
    await publicClient.waitForTransactionReceipt({ hash });
    console.log(`Registered. tx: ${hash}`);
  } else {
    console.log("gridz.cell.v1 schema already registered — reusing UID");
  }

  upsertEnv("CELL_SCHEMA", uid);
  console.log("CELL_SCHEMA written to .env");
}

main().catch((e) => {
  console.error(e.message ?? e);
  process.exit(1);
});
