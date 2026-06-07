#!/usr/bin/env node
/** Print the ENS subname for an entity alias. Usage: node scripts/register-entity.mjs bot */
import { toEnsSubname } from "./lib/constants.mjs";

const alias = process.argv[2];
const base = process.env.GRIDZ_ENS_BASE ?? "gridz.eth";

if (!alias) {
  console.error("Usage: node scripts/register-entity.mjs <alias>");
  console.error("Example: node scripts/register-entity.mjs bot  →  bot.gridz.eth");
  process.exit(1);
}

console.log(toEnsSubname(alias, base));
