# Changelog

This file is driven by [Changesets](https://github.com/changesets/changesets).
Per-package changelogs live in each package directory. Below is the repo-level
history of milestones.

## Unreleased

### Added — initial framework (BRIEF §16 steps 1–15)

- **Specs** — canonical Grid model, attestation envelope, standard-key registry,
  EIP-712 types, canonicalization (`specs/`). Source of truth.
- **`@gridz/core`** + Python **`gridz`** — JCS canonicalization, EIP-712, sorted
  merkle root, signers (local, ed25519, and detached-signature assembly), and the
  universal verifier. Cross-runtime: TS- and Python-signed grids verify in the
  other, with byte-identical EIP-712 signatures.
- **`@gridz/sinks`** + Python **`gridz_sinks`** — Sink interface, MemorySink, ENS
  sink (swappable backend), SQLite (real), and Postgres/MySQL/Mongo/Redis/Neo4j/S3
  cell stores (docker-gated). SNS sink: preview.
- **`@gridz/server`** — Fastify + OpenAPI 3.1; write endpoints validate signed
  attestations; no key custody.
- **`@gridz/sdk`** + Python client — typed clients over the API, integration-tested
  cross-language.
- **`@gridz/cli`** — `init`/`validate`/`build`/`verify`/`publish` + bootstrap
  templates (shape only).
- **`@gridz/mcp`** + Python **`gridz_mcp`** — FastMCP servers; no server-side
  signing (prepare → sign → attach flow).
- **Renderers** — `@gridz/react`, `@gridz/vue`, `@gridz/svelte`, `@gridz/element`
  with verification badges.
- **`@gridz/oneclaw`** + Python **`gridz_oneclaw`** — optional 1claw HSM adapter.
- **Contracts** — `GridzResolver.sol`, an ENSIP-10 wildcard resolver over EAS
  (100% coverage).
- **Examples** — minimal-cli, oneclaw-quickstart, next-app, scaffold-agent-grid.
