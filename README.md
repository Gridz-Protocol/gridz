# Gridz

An open, multi-modal framework for **cryptographically-attested social graphs** that work for humans, AI agents, and organizations.

A **Grid** is a profile built from typed, signed fields ("cells"), each carrying a verifiable attestation chain. A consumer with only `(grid_id, public_key, attestation)` can prove who said what, when, and under which key — no sink, server, or vault required.

## Status

All 15 BRIEF §16 steps complete. ~270 tests across TypeScript, Python, and
Foundry — all green. Spec-first, tests-first, no mock data.

| Area | State |
|---|---|
| Specs (`specs/`) | ✅ Grid model, attestation envelope, key registry, EIP-712 types, canonicalization, OpenAPI 3.1 |
| `@gridz/core` + Python `gridz` | ✅ JCS, EIP-712, merkle, signers, verifier — cross-runtime byte-identical signatures |
| `@gridz/sinks` + Python `gridz_sinks` | ✅ Sink interface, Memory + ENS + SQLite (real) + Postgres/MySQL/Mongo/Redis/Neo4j/S3 (docker-gated); SNS preview |
| `@gridz/server` | ✅ Fastify + OpenAPI 3.1, attestation-validated writes, no key custody |
| `@gridz/sdk` + Python client | ✅ typed clients; cross-language integration (Python-signed grid round-trips the TS server) |
| `@gridz/cli` | ✅ init/validate/build/verify/publish + bootstrap templates (shape only) |
| `@gridz/mcp` + Python `gridz_mcp` | ✅ FastMCP servers; no server-side signing |
| `@gridz/react` / `vue` / `svelte` / `element` | ✅ renderers with verification badges |
| `@gridz/oneclaw` + Python `gridz_oneclaw` | ✅ optional 1claw HSM adapter |
| `contracts/` | ✅ `GridzResolver.sol` — ENSIP-10 wildcard over EAS, 100% coverage |
| `examples/`, `docs/` | ✅ minimal-cli, oneclaw-quickstart, next-app, scaffold-agent-grid; Vocs docs |

## Layout

```
specs/        canonical JSON Schemas + EIP-712 types + canonicalization (source of truth)
packages/     TypeScript monorepo (@gridz/*)
  core-ts/    @gridz/core — the crypto core everything else builds on
DESIGN_NOTES.md   judgment calls, brief corrections, open questions
```

## Develop

```bash
pnpm install
pnpm -w run check     # turbo: lint + typecheck + test + build
```

## Principles

- **Spec first** — the schemas in `specs/` are the product; SDKs are written against them.
- **No bespoke crypto** — EIP-712 / EAS, JWS, COSE, audited libraries only.
- **No custodied keys** — bring your own signer (local wallet, passkey, or 1claw HSM).
- **Sinks are projections, not sources of truth** — the signed attestation is authoritative.
- **No mock data** — fixtures are deterministic and seed-derived; see `DESIGN_NOTES.md`.

Licensed under [MIT](./LICENSE).
