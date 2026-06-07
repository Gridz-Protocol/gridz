#!/usr/bin/env node
/**
 * Set the ENS resolver for gridz.eth (or GRIDZ_ENS_NAME) to the deployed GridzResolver.
 * Requires the name owner's private key in ENS_CONTROLLER_PRIVATE_KEY.
 */
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const require = createRequire(join(ROOT, "examples/next-app/package.json"));

const { createWalletClient, createPublicClient, http } = require("viem");
const { privateKeyToAccount } = require("viem/accounts");
const { mainnet, sepolia } = require("viem/chains");
const { namehash, normalize } = require("viem/ens");

const ENS_REGISTRY = "0x00000000000C2E074eC69A0dFb2997BA6C7d2e1e";

const registryAbi = [
  {
    name: "setResolver",
    type: "function",
    inputs: [
      { name: "node", type: "bytes32" },
      { name: "resolver", type: "address" },
    ],
    outputs: [],
    stateMutability: "nonpayable",
  },
  {
    name: "owner",
    type: "function",
    inputs: [{ name: "node", type: "bytes32" }],
    outputs: [{ type: "address" }],
    stateMutability: "view",
  },
  {
    name: "resolver",
    type: "function",
    inputs: [{ name: "node", type: "bytes32" }],
    outputs: [{ type: "address" }],
    stateMutability: "view",
  },
];

async function main() {
  const rpc = process.env.GRIDZ_RPC_URL ?? "https://ethereum.publicnode.com";
  const ensName = process.env.GRIDZ_ENS_NAME ?? "gridz.eth";
  const resolver = process.env.GRIDZ_RESOLVER;
  const key = process.env.ENS_CONTROLLER_PRIVATE_KEY;
  const chainId = Number(process.env.GRIDZ_CHAIN_ID ?? "1");

  if (!resolver?.startsWith("0x")) throw new Error("GRIDZ_RESOLVER required");
  if (!key?.startsWith("0x")) throw new Error("ENS_CONTROLLER_PRIVATE_KEY required");

  const chain = chainId === 11155111 ? sepolia : mainnet;
  const account = privateKeyToAccount(key);
  const transport = http(rpc);
  const publicClient = createPublicClient({ chain, transport });
  const walletClient = createWalletClient({ chain, transport, account });

  const node = namehash(normalize(ensName));
  const owner = await publicClient.readContract({
    address: ENS_REGISTRY,
    abi: registryAbi,
    functionName: "owner",
    args: [node],
  });
  if (owner.toLowerCase() !== account.address.toLowerCase()) {
    throw new Error(`Signer ${account.address} is not owner of ${ensName} (owner: ${owner})`);
  }

  const current = await publicClient.readContract({
    address: ENS_REGISTRY,
    abi: registryAbi,
    functionName: "resolver",
    args: [node],
  });
  if (current.toLowerCase() === resolver.toLowerCase()) {
    console.log(`${ensName} already points to ${resolver}`);
    return;
  }

  const hash = await walletClient.writeContract({
    address: ENS_REGISTRY,
    abi: registryAbi,
    functionName: "setResolver",
    args: [node, resolver],
  });
  console.log(`setResolver tx: ${hash}`);
  await publicClient.waitForTransactionReceipt({ hash });
  console.log(`${ensName} resolver → ${resolver}`);
  console.log(`Subnames like bot.${ensName} resolve via this wildcard resolver.`);
}

main().catch((e) => {
  console.error(e.message ?? e);
  process.exit(1);
});
