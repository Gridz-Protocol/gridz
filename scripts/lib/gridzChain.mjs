import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const require = createRequire(join(dirname(fileURLToPath(import.meta.url)), "../../examples/next-app/package.json"));
const { base, mainnet, sepolia } = require("viem/chains");

/** @param {number} chainId */
export function gridzChainForId(chainId) {
  if (chainId === 11155111) return sepolia;
  if (chainId === 8453) return base;
  return mainnet;
}

/** @param {number} chainId */
export function gridzChainLabel(chainId) {
  if (chainId === 1) return "Ethereum";
  if (chainId === 11155111) return "Sepolia";
  if (chainId === 8453) return "Base";
  return `Chain ${chainId}`;
}

/** @param {number} chainId */
export function easExplorerBase(chainId) {
  if (chainId === 8453) return "https://base.easscan.org";
  if (chainId === 11155111) return "https://sepolia.easscan.org";
  return "https://easscan.org";
}
