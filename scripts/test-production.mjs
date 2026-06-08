#!/usr/bin/env node
/**
 * Production smoke tests for gridz.bio.
 *
 * Usage:
 *   node scripts/test-production.mjs
 *   GRIDZ_PRODUCTION_URL=https://preview.example.vercel.app node scripts/test-production.mjs
 */
const BASE_URL = (
  process.env.GRIDZ_PRODUCTION_URL ??
  process.env.NEXT_PUBLIC_SITE_URL ??
  "https://gridz.bio"
).replace(/\/$/, "");

const SITE_DOMAIN = process.env.NEXT_PUBLIC_SITE_DOMAIN ?? "gridz.bio";
const DEMO_SUBJECT =
  process.env.GRIDZ_DEMO_SUBJECT ??
  process.env.NEXT_PUBLIC_DEMO_PROFILE_SUBJECT ??
  "demo.gridz.eth";
const EMPTY_SUBJECT = process.env.GRIDZ_EMPTY_PROFILE_SUBJECT ?? "1claw.gridz.eth";
const UNKNOWN_SUBJECT = "nope-not-real.gridz.eth";

/** @type {string[]} */
const failures = [];

function fail(message) {
  failures.push(message);
  console.error(`✗ ${message}`);
}

function pass(message) {
  console.log(`✓ ${message}`);
}

/**
 * @param {string} path
 * @param {RequestInit} [init]
 */
async function fetchText(path, init) {
  const url = path.startsWith("http") ? path : `${BASE_URL}${path}`;
  const res = await fetch(url, init);
  const text = await res.text();
  return { url, res, text };
}

/**
 * @param {string} name
 * @param {Response} res
 * @param {string} text
 * @param {number} [expectedStatus]
 */
function assertHtmlPage(name, res, text, expectedStatus = 200) {
  if (res.status !== expectedStatus) {
    fail(`${name}: expected HTTP ${expectedStatus}, got ${res.status}`);
    return;
  }
  if (text.includes("Application error") || text.includes("server-side exception")) {
    fail(`${name}: Next.js server error page`);
    return;
  }
  pass(name);
}

async function testStaticPages() {
  const pages = [
    "/",
    "/docs",
    "/docs/getting-started",
    "/docs/api",
    "/docs/claim",
    "/docs/cli",
    "/docs/concepts",
    "/docs/spec",
    "/docs/spec/grid",
    "/docs/spec/keys",
    "/docs/spec/canonicalization",
    "/docs/spec/attestations",
    "/docs/spec/sinks",
    "/docs/spec/on-chain",
    "/docs/toolkit",
    "/docs/using-gridz",
    "/docs/verification",
    "/claim",
    "/find",
    "/for-ai",
  ];

  for (const path of pages) {
    const { res, text } = await fetchText(path);
    assertHtmlPage(`page ${path}`, res, text);
  }
}

async function testTextRoutes() {
  const routes = [
    { path: "/for-ai/llms.txt", needle: "# Gridz" },
    { path: "/for-ai/skill.md", needle: "name: gridz" },
    { path: "/llms.txt", needle: "# Gridz" },
    { path: "/skill.md", needle: "name: gridz" },
  ];

  for (const { path, needle } of routes) {
    const { res, text } = await fetchText(path);
    if (res.status !== 200) {
      fail(`${path}: expected HTTP 200, got ${res.status}`);
      continue;
    }
    if (!text.includes(needle)) {
      fail(`${path}: missing expected content (${needle})`);
      continue;
    }
    pass(`text route ${path}`);
  }
}

async function testProfilePages() {
  const subjects = [
    { subject: DEMO_SUBJECT, label: "demo profile" },
    { subject: EMPTY_SUBJECT, label: "empty profile" },
    { subject: UNKNOWN_SUBJECT, label: "unknown profile" },
  ];

  for (const { subject, label } of subjects) {
    const path = `/${encodeURIComponent(subject)}`;
    const { res, text } = await fetchText(path);
    assertHtmlPage(`${label} ${path}`, res, text);
  }
}

async function testSubdomainRewrites() {
  const hosts = [
    `https://demo.${SITE_DOMAIN}`,
    `https://${EMPTY_SUBJECT.split(".")[0]}.${SITE_DOMAIN}`,
  ];

  for (const url of hosts) {
    const { res, text } = await fetchText(url);
    assertHtmlPage(`subdomain ${url}`, res, text);
  }
}

async function testProfileApi() {
  const cases = [
    { subject: DEMO_SUBJECT, status: 200, ok: true },
    { subject: UNKNOWN_SUBJECT, status: 404, ok: false },
    { subject: "not-a-name", status: 400, ok: false },
  ];

  for (const { subject, status, ok } of cases) {
    const path = `/api/profile/${encodeURIComponent(subject)}`;
    const { res, text } = await fetchText(path);
    if (res.status !== status) {
      fail(`api ${path}: expected HTTP ${status}, got ${res.status}`);
      continue;
    }

    let data;
    try {
      data = JSON.parse(text);
    } catch {
      fail(`api ${path}: response is not JSON`);
      continue;
    }

    if (data.ok !== ok) {
      fail(`api ${path}: expected ok=${ok}, got ${JSON.stringify(data)}`);
      continue;
    }

    pass(`api ${path} → ${status}`);
  }

  const options = await fetch(`${BASE_URL}/api/profile/${encodeURIComponent(DEMO_SUBJECT)}`, {
    method: "OPTIONS",
  });
  if (options.status !== 204) {
    fail(`api OPTIONS profile: expected 204, got ${options.status}`);
  } else {
    pass("api OPTIONS profile → 204");
  }
}

async function testPublishApi() {
  const { res, text } = await fetchText("/api/publish", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: "{}",
  });

  if (res.status !== 400) {
    fail(`/api/publish: expected HTTP 400 for empty body, got ${res.status}`);
    return;
  }

  let data;
  try {
    data = JSON.parse(text);
  } catch {
    fail("/api/publish: response is not JSON");
    return;
  }

  if (data.ok !== false || !data.error) {
    fail(`/api/publish: expected validation error, got ${text.slice(0, 120)}`);
    return;
  }

  pass("/api/publish rejects empty body with 400");
}

async function testVerifyApi() {
  const path = `/api/verify/${encodeURIComponent(DEMO_SUBJECT)}`;
  const { res, text } = await fetchText(path);
  if (res.status !== 200) {
    fail(`verify api: expected 200, got ${res.status}`);
    return;
  }

  let data;
  try {
    data = JSON.parse(text);
  } catch {
    fail("verify api: response is not JSON");
    return;
  }

  if (!data.report?.cells?.length) {
    fail(`verify api: missing verification report (${path})`);
    return;
  }

  const verified = data.report.cells.filter((c) => c.result?.ok).length;
  if (verified < 5) {
    fail(`verify api: expected verified cells, got ${verified} (${path})`);
    return;
  }

  pass(`verify api — ${verified}/${data.report.cells.length} cells verified at ${DEMO_SUBJECT}`);
}

async function testDemoProfile() {
  const path = `/api/profile/${encodeURIComponent(DEMO_SUBJECT)}`;
  const { res, text } = await fetchText(path);
  if (res.status !== 200) {
    fail(`demo profile api: expected 200, got ${res.status}`);
    return;
  }

  let data;
  try {
    data = JSON.parse(text);
  } catch {
    fail("demo profile api: response is not JSON");
    return;
  }

  if (!data.ok || !data.grid?.cells?.length) {
    fail(`demo profile api: missing grid cells (${path})`);
    return;
  }

  const keys = data.grid.cells.map((c) => c.key);
  const required = ["alias", "description", "url", "gridz.stats", "gridz.poll", "gridz.keys"];
  const missing = required.filter((k) => !keys.includes(k));
  if (missing.length) {
    fail(`demo profile api: missing cells ${missing.join(", ")}`);
    return;
  }

  const easCells = data.grid.cells.filter((c) => c.attestation?.format === "eas-onchain").length;
  if (easCells < required.length) {
    fail(`demo profile api: expected eas-onchain attestations, found ${easCells}`);
    return;
  }

  pass(`demo profile api — ${data.grid.cells.length} cells at ${DEMO_SUBJECT}`);
}

async function main() {
  console.log(`Running production smoke tests against ${BASE_URL}\n`);

  await testStaticPages();
  await testTextRoutes();
  await testProfilePages();
  await testSubdomainRewrites();
  await testProfileApi();
  await testPublishApi();
  await testVerifyApi();
  await testDemoProfile();

  console.log("");
  if (failures.length) {
    console.error(`Failed ${failures.length} check(s).`);
    process.exit(1);
  }

  console.log("All production smoke tests passed.");
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
