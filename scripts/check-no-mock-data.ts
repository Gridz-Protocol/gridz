#!/usr/bin/env node
/**
 * Fails the build if invented demo data leaks into non-test source (BRIEF §15).
 * Fixtures and tests are exempt — that is where deterministic, clearly-labelled
 * example data is allowed to live.
 */
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join, relative } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = fileURLToPath(new URL("..", import.meta.url));

const SCAN_DIRS = [
  "packages",
  "python",
  "examples",
  "specs",
];

const SOURCE_EXT = /\.(ts|tsx|js|jsx|py|svelte|sol|md|yaml|yml|json)$/;
const EXEMPT = /(\/test\/|\/tests\/|__fixtures__|\/dist\/|\/node_modules\/|\/\.venv\/|check-no-mock-data)/;

// Patterns that indicate fabricated demo data. Deliberately specific to avoid
// false positives on ordinary words.
const PATTERNS: { re: RegExp; label: string }[] = [
  { re: /elon\s*musk/i, label: "Elon Musk" },
  { re: /@elonmusk/i, label: "@elonmusk" },
  { re: /acme\s*corp/i, label: "Acme Corp" },
  { re: /lorem\s+ipsum/i, label: "Lorem ipsum" },
  { re: /john\.doe/i, label: "john.doe" },
  { re: /\bexample\.com\b/i, label: "example.com" },
  { re: /\bacme\.com\b/i, label: "acme.com" },
];

function walk(dir: string, out: string[]): void {
  let entries: string[];
  try {
    entries = readdirSync(dir);
  } catch {
    return;
  }
  for (const name of entries) {
    const full = join(dir, name);
    if (EXEMPT.test(full)) continue;
    const st = statSync(full);
    if (st.isDirectory()) walk(full, out);
    else if (SOURCE_EXT.test(full)) out.push(full);
  }
}

const files: string[] = [];
for (const d of SCAN_DIRS) walk(join(ROOT, d), files);

const violations: string[] = [];
for (const file of files) {
  const text = readFileSync(file, "utf8");
  for (const { re, label } of PATTERNS) {
    if (re.test(text)) violations.push(`${relative(ROOT, file)}: "${label}"`);
  }
}

if (violations.length > 0) {
  console.error("✗ no-mock-data check FAILED — invented demo data in non-test source:");
  for (const v of violations) console.error(`  - ${v}`);
  process.exit(1);
}
console.log(`✓ no-mock-data check passed (${files.length} source files scanned)`);
