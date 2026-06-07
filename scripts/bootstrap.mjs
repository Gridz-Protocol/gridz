#!/usr/bin/env node
/**
 * Gridz bootstrap — reads root .env, optionally deploys contracts, configures ENS,
 * and syncs examples/next-app/.env.local.
 *
 * Usage:
 *   cp .env.example .env   # first time: fill in values
 *   pnpm bootstrap
 *   pnpm bootstrap -- --deploy --ens --vercel --yes
 */
import { createInterface } from "node:readline/promises";
import { stdin as input, stdout as output } from "node:process";
import { readFileSync, writeFileSync, existsSync, copyFileSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { NETWORKS, parseEnvBlock, buildEnvFiles, toEnsSubname } from "./lib/constants.mjs";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const ENV_PATH = join(ROOT, ".env");
const ENV_EXAMPLE = join(ROOT, ".env.example");

function usage() {
  console.log(`Gridz bootstrap

  cp .env.example .env   # first time — edit .env with your secrets
  pnpm bootstrap [options]

Options:
  --network <name>   mainnet (default) or sepolia — fills RPC/EAS defaults only when unset in .env
  --deploy           Deploy GridzResolver via Foundry
  --ens              Set gridz.eth resolver to GridzResolver
  --vercel           Deploy examples/next-app to Vercel
  --yes              Skip confirmation prompts
  -h, --help         Show help
`);
}

function parseArgs(argv) {
  const opts = { network: "mainnet", deploy: false, ens: false, vercel: false, yes: false };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "-h" || a === "--help") {
      usage();
      process.exit(0);
    }
    if (a === "--network") opts.network = argv[++i] ?? "mainnet";
    else if (a === "--deploy") opts.deploy = true;
    else if (a === "--ens") opts.ens = true;
    else if (a === "--vercel") opts.vercel = true;
    else if (a === "--yes") opts.yes = true;
    else {
      console.error(`Unknown option: ${a}`);
      usage();
      process.exit(1);
    }
  }
  if (!NETWORKS[opts.network]) {
    console.error(`Unknown network: ${opts.network}`);
    process.exit(1);
  }
  return opts;
}

function loadEnv() {
  if (!existsSync(ENV_PATH)) {
    if (existsSync(ENV_EXAMPLE)) {
      copyFileSync(ENV_EXAMPLE, ENV_PATH);
      console.error("Created .env from .env.example — fill in your values, then run pnpm bootstrap again.");
    } else {
      console.error("Missing .env — create one at the repo root (see .env.example).");
    }
    process.exit(1);
  }
  return parseEnvBlock(readFileSync(ENV_PATH, "utf8"));
}

function run(cmd, args, { cwd = ROOT, env = {} } = {}) {
  const res = spawnSync(cmd, args, {
    cwd,
    stdio: "inherit",
    env: { ...process.env, ...env },
  });
  if (res.status !== 0) process.exit(res.status ?? 1);
}

function readDeployedResolver(chainId) {
  const broadcast = join(ROOT, "contracts/broadcast/Deploy.s.sol", String(chainId), "run-latest.json");
  if (!existsSync(broadcast)) {
    console.error(`No broadcast artifact at ${broadcast}`);
    process.exit(1);
  }
  const run = JSON.parse(readFileSync(broadcast, "utf8"));
  const txs = run.transactions ?? [];
  const proxy = txs.find((t) => t.contractName === "ERC1967Proxy" && t.contractAddress);
  if (proxy?.contractAddress) return proxy.contractAddress;
  const direct = txs.find((t) => t.contractName === "GridzResolver" && t.contractAddress);
  if (direct?.contractAddress) return direct.contractAddress;
  console.error("ERC1967Proxy / GridzResolver address not found in broadcast output");
  process.exit(1);
}

async function confirm(message, yes) {
  if (yes) return true;
  const rl = createInterface({ input, output });
  const go = await rl.question(`${message} [y/N] `);
  rl.close();
  return /^y(es)?$/i.test(go.trim());
}

function writeEnvFiles(env) {
  const { root, nextApp } = buildEnvFiles(env);
  writeFileSync(ENV_PATH, root, "utf8");
  writeFileSync(join(ROOT, "examples/next-app/.env.local"), nextApp, "utf8");
  console.log("Updated .env and examples/next-app/.env.local");
}

async function main() {
  // pnpm/npm may forward a bare `--` separator; ignore it.
  const opts = parseArgs(process.argv.slice(2).filter((a) => a !== "--"));
  const net = NETWORKS[opts.network];
  const fromFile = loadEnv();

  let env = {
    GRIDZ_CHAIN_ID: String(net.chainId),
    GRIDZ_RPC_URL: net.rpc,
    GRIDZ_ENS_RPC_URL: net.rpc,
    GRIDZ_ENS_BASE: "gridz.eth",
    GRIDZ_ENS_NAME: "gridz.eth",
    EAS_ADDRESS: net.eas,
    ONECLAW_CHAIN_ID: String(net.chainId),
    ...fromFile,
  };

  console.log(`Loaded .env (${Object.keys(fromFile).length} keys)`);

  if (opts.deploy) {
    if (!env.DEPLOYER_PRIVATE_KEY?.startsWith("0x")) {
      console.error("--deploy requires DEPLOYER_PRIVATE_KEY in .env");
      process.exit(1);
    }
    if (!env.CELL_SCHEMA?.startsWith("0x")) {
      console.log("CELL_SCHEMA missing — registering gridz.cell.v1 on EAS…");
      run("node", ["scripts/register-cell-schema.mjs"]);
      env = { ...env, ...parseEnvBlock(readFileSync(ENV_PATH, "utf8")) };
      if (!env.CELL_SCHEMA?.startsWith("0x")) {
        console.error("--deploy requires CELL_SCHEMA in .env");
        process.exit(1);
      }
    }
    if (await confirm(`Deploy GridzResolver to ${opts.network}?`, opts.yes)) {
      console.log("\n→ Deploying GridzResolver…");
      run(
        "forge",
        [
          "script",
          "script/Deploy.s.sol",
          "--rpc-url",
          env.GRIDZ_RPC_URL,
          "--broadcast",
          "--private-key",
          env.DEPLOYER_PRIVATE_KEY,
        ],
        {
          cwd: join(ROOT, "contracts"),
          env: {
            EAS_ADDRESS: env.EAS_ADDRESS,
            CELL_SCHEMA: env.CELL_SCHEMA,
            ...(env.ADMIN_ADDRESS ? { ADMIN_ADDRESS: env.ADMIN_ADDRESS } : {}),
          },
        },
      );
      env.GRIDZ_RESOLVER = readDeployedResolver(net.chainId);
      console.log(`GridzResolver proxy deployed (UUPS): ${env.GRIDZ_RESOLVER}`);
      console.log("Point ENS at this proxy address — it stays stable across upgrades.");
    }
  }

  writeEnvFiles(env);

  if (opts.ens) {
    if (!env.GRIDZ_RESOLVER?.startsWith("0x") || env.GRIDZ_RESOLVER.length < 42) {
      console.error("--ens requires GRIDZ_RESOLVER in .env (run --deploy first or set it manually)");
      process.exit(1);
    }
    const controllerKey = env.ENS_CONTROLLER_PRIVATE_KEY || env.DEPLOYER_PRIVATE_KEY;
    if (!controllerKey?.startsWith("0x")) {
      console.error("--ens requires ENS_CONTROLLER_PRIVATE_KEY or DEPLOYER_PRIVATE_KEY in .env");
      process.exit(1);
    }
    if (await confirm(`Point ${env.GRIDZ_ENS_NAME} resolver at ${env.GRIDZ_RESOLVER}?`, opts.yes)) {
      console.log("\n→ Configuring ENS…");
      run("pnpm", ["install"]);
      run("node", ["scripts/ens-setup.mjs"], {
        env: {
          GRIDZ_RPC_URL: env.GRIDZ_RPC_URL,
          GRIDZ_ENS_NAME: env.GRIDZ_ENS_NAME,
          GRIDZ_RESOLVER: env.GRIDZ_RESOLVER,
          ENS_CONTROLLER_PRIVATE_KEY: controllerKey,
          GRIDZ_CHAIN_ID: env.GRIDZ_CHAIN_ID,
        },
      });
    }
  }

  if (opts.vercel) {
    if (await confirm("Deploy examples/next-app to Vercel?", opts.yes)) {
      console.log("\n→ Installing workspace deps…");
      run("pnpm", ["install"]);
      console.log("\n→ Pushing env to Vercel…");
      run("node", ["scripts/push-vercel-env.mjs"], { env });
      console.log("\n→ Building next-app…");
      run("pnpm", ["--filter", "gridz-next-app...", "run", "build"]);
      console.log("\n→ Deploying to Vercel from repo root (project Root Directory: examples/next-app)…");
      run("vercel", ["--prod", "--yes"], { cwd: ROOT });
    }
  }

  const base = env.GRIDZ_ENS_BASE ?? "gridz.eth";
  const agentKey = env.ONECLAW_AGENT_KEY ?? env.GRIDZ_ONECLAW_API_KEY;
  console.log(`
Done.

ENS subname convention:
  entity "bot"   →  ${toEnsSubname("bot", base)}
  entity "alice" →  ${toEnsSubname("alice", base)}
  CLI helper:     node scripts/register-entity.mjs <alias>
`);

  if (agentKey) {
    console.log(`1Claw MCP (Cursor): add to .cursor/mcp.json —
{
  "mcpServers": {
    "1claw": {
      "command": "npx",
      "args": ["-y", "@1claw/mcp@0.32.2"],
      "env": { "ONECLAW_AGENT_API_KEY": "${agentKey.slice(0, 12)}…" }
    }
  }
}
See https://1claw.xyz/for-ai
`);
  }

  console.log(`Next steps:
  1. 1claw dashboard → agent → EIP-712 allowlist: add Gridz domain (gridz identity import --from oneclaw).
  2. Publish a profile to ${toEnsSubname("bot", base)} via EnsSink / minimal-cli.
  3. Public site: /${toEnsSubname("bot", base)}
  4. Tests: pnpm test
`);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
