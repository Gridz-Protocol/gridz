# Gridz

An open, multi-modal framework for **cryptographically-attested social graphs** that work for humans, AI agents, and organizations.

A **Grid** is a profile built from typed, signed fields ("cells"), each carrying a verifiable attestation chain. A consumer with only `(grid_id, public_key, attestation)` can prove who said what, when, and under which key — no sink, server, or vault required.

## Status

Early development. Spec-first, tests-first.

| Area | State |
|---|---|
| Specs (`specs/`) | ✅ Grid model, attestation envelope, key registry, EIP-712 types, canonicalization |
| `@gridz/core` | ✅ types, JCS canonicalization, EIP-712, merkle, signers, universal verifier — 49 tests, 98% coverage |
| Python `gridz` | ✅ byte-compatible mirror — 31 tests, 95% coverage; cross-runtime verified both directions |
| `@gridz/sinks` | ✅ Sink interface + MemorySink + ENS sink (swappable backend) + round-trip harness; live ENS test gated on testnet creds |
| `@gridz/server` | ✅ Fastify + OpenAPI 3.1, attestation-validated writes, no key custody; `specs/openapi.yaml` generated from routes (18 tests) |
| SDK, CLI, MCP, renderer, more sinks, 1claw, contracts | ⏳ per `BRIEF.md` §16 build order |

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
