#!/usr/bin/env node
/** Smoke-test the on-chain demo profile after publish-demo. */
const SITE = process.env.NEXT_PUBLIC_SITE_DOMAIN ?? "gridz.bio";
const SUBJECT = process.env.GRIDZ_DEMO_SUBJECT ?? process.env.NEXT_PUBLIC_DEMO_PROFILE_SUBJECT ?? "demo.gridz.eth";
const url = `https://${SITE}/api/profile/${encodeURIComponent(SUBJECT)}`;

const res = await fetch(url);
const data = await res.json();

if (!data.ok || !data.grid?.cells?.length) {
  console.error(`✗ Demo profile not found at ${url}`);
  console.error(JSON.stringify(data, null, 2));
  process.exit(1);
}

const keys = data.grid.cells.map((c) => c.key);
const required = ["alias", "description", "url", "gridz.stats", "gridz.poll", "gridz.keys"];
const missing = required.filter((k) => !keys.includes(k));

if (missing.length) {
  console.error(`✗ Demo profile missing cells: ${missing.join(", ")}`);
  console.error(`  Found: ${keys.join(", ")}`);
  process.exit(1);
}

console.log(`✓ Demo profile live — ${data.grid.cells.length} cells at ${SUBJECT}`);
console.log(`  https://${SITE}/${encodeURIComponent(SUBJECT)}`);
