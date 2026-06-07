# Cross-runtime fixtures

The brief's step-3 gate: **a Grid signed in TypeScript must verify in Python, and
vice versa.** This directory holds the committed fixtures that prove it, so each
language lane can run independently in CI without invoking the other.

| Fixture | Signed by | Format | Verified by |
|---|---|---|---|
| `ts-eip712-grid.json` | `@gridz/core` (TS) | `eip712-raw` | Python (`test_crossruntime.py`) |
| `ts-ed25519-grid.json` | `@gridz/core` (TS) | `jws-ed25519` | Python |
| `py-eip712-grid.json` | `gridz` (Python) | `eip712-raw` | TS (`cross-runtime.test.ts`) |
| `py-ed25519-grid.json` | `gridz` (Python) | `jws-ed25519` | TS |

All fixtures are deterministic: seed-derived keys
(`keccak256("gridz/__example__/signer/1")`, `sha256("gridz/__example__/ed/1")`) and a
frozen `now = 2026-01-01T00:00:00Z`. Regenerating produces byte-identical output.

Beyond mutual verification, `test_python_eip712_signature_matches_ts_bit_for_bit`
asserts the two runtimes produce **identical** EIP-712 signatures (deterministic
ECDSA over an identical typed-data digest) — proving JCS, hashing, and EIP-712
encoding agree exactly, not merely that each can check the other.

## Regenerate

```bash
# TS fixtures
pnpm --filter @gridz/core build && node tests/cross-runtime/gen.ts
# Python fixtures
cd python/gridz && uv run python tests/_gen_fixtures.py
```
