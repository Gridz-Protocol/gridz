# Gridz Canonicalization & Hashing

Verification only works if every runtime hashes the exact same bytes. This document is normative: TS, Python, the contracts, and any third-party verifier MUST follow it byte-for-byte. The cross-runtime fixture tests (`tests/cross-runtime/`) exist to enforce it.

## 1. Canonical form: RFC 8785 (JCS)

All hashing is over the **JSON Canonicalization Scheme** (RFC 8785) serialization of the value, hereafter `JCS(x)`.

JCS guarantees:
- object keys sorted by UTF-16 code unit,
- no insignificant whitespace,
- shortest round-tripping number form (ECMAScript `Number` semantics),
- UTF-8 output with minimal escaping.

Libraries: `canonicalize` (TS), `rfc8785` / a vetted JCS impl (Python). We do **not** hand-roll JCS.

> **Constraint:** values MUST be JSON-serializable and MUST NOT rely on number precision beyond IEEE-754 double. Big integers (token ids, wei) are encoded as **strings**, never JSON numbers. This is validated by the cell value schemas.

## 2. Hash functions

| Domain | Hash | Used for |
|---|---|---|
| EVM (did:ethr, did:pkh:eip155, EAS, contracts) | `keccak256` | `value_hash`, `gridId`, merkle nodes |
| non-EVM (did:pkh:solana, did:key, did:web with ed25519) | `sha256` | `value_hash`, `gridId`, merkle nodes |

A Grid's hash domain is fixed by the subject DID's signing curve. It is recorded implicitly by the attestation `format` (`eip712-*` ⇒ keccak256; `jws-ed25519`/`cose-webauthn` ⇒ sha256) and MUST be consistent across all cells in a Grid.

All hash outputs are 32 bytes, rendered lowercase hex with a `0x` prefix where stored as strings.

## 3. Derived values

### 3.1 `value_hash`
```
value_hash = H( JCS(cell.value) )           // H = keccak256 (EVM) | sha256 (non-EVM)
```
This is the `valueHashHex` field of `GridzCell` (as 0x-hex string) and `attestation.value_hash`.

### 3.2 `gridId`
A stable 32-byte id for the Grid, independent of cell contents so a Grid keeps its id across edits:
```
gridId = H( JCS({ "did": subject.did, "schema_version": grid.schema_version }) )
```

### 3.3 `widgetTypeHash`
```
widgetTypeHash = H( utf8( cell.widget_type ?? "" ) )    // hash of the empty string when unset
```
Note: a plain UTF-8 hash of the string, **not** JCS (the input is already a primitive string).

## 4. Cell-level merkle tree

The Grid root signs a merkle root over cell **attestation UIDs**, so the root commits to the set of cells while leaving each cell independently verifiable (verifying one leaf never requires the others).

### Leaves
- Leaf set = the `attestation.uid` of every cell in the Grid, **including** cells with `is_visible: false` (visibility is a render concern, not a membership concern).
- Each `uid` is normalized to 32 bytes:
  - if `uid` is `0x`-prefixed 32-byte hex (EAS uid), use those bytes directly;
  - otherwise `leaf = H( utf8(uid) )`.
- Sort leaves ascending by their 32-byte big-endian value. Sorting makes the root order-independent and lets us use sorted-pair hashing (no position bits to track).

### Internal nodes (sorted-pair, OpenZeppelin-compatible on EVM)
```
parent(a, b) = H( min(a,b) ‖ max(a,b) )      // concatenate the two 32-byte values, lower first
```
- Build bottom-up. If a level has an odd number of nodes, the unpaired node is **promoted unchanged** to the next level (no duplication).
- Empty tree (0 cells): `merkleRoot = 0x00…00` (32 zero bytes). A Grid with no cells is valid but renders empty.
- Single leaf: `merkleRoot = that leaf`.

`cellCount` in `GridzRoot` records the leaf count so a verifier can detect a root that silently dropped cells.

> On EVM, this matches OpenZeppelin `MerkleProof` (sorted pairs) so proofs can be checked in `GridzResolver.sol`. The non-EVM variant is identical with `sha256` substituted for `keccak256`.

## 5. What gets signed

| Attestation | Signed struct | Commits to |
|---|---|---|
| Cell | `GridzCell` (EIP-712) or EAS `gridz.cell.v1` | `gridId`, `key`, `value_hash`, `widgetTypeHash`, `expiresAt`, `nonce` |
| Root | `GridzRoot` (EIP-712) or EAS `gridz.root.v1` | `gridId`, `merkleRoot`, `schemaVersion`, `cellCount`, `issuedAt` |

For `jws-ed25519` / `cose-webauthn`, the signed payload is `JCS` of the same logical field set (the JWS/COSE claim set carries the fields by name); the recovered/verified key MUST map to `attestation.attester`.

## 6. Verification order (normative)

A verifier given a cell + envelope MUST, in order:
1. Recompute `value_hash` from `JCS(cell.value)` and check it equals `attestation.value_hash` **and** the signed `valueHashHex`.
2. Recover/verify the signature over the canonical struct and resolve the signer to a DID; check it equals `attestation.attester`.
3. Check the attester is authorized for `subject.did` (self-issued: attester == subject; or delegated: attester is in the subject's authorized-signer set — out of scope for this spec PR, see DESIGN_NOTES.md).
4. Check time bounds: `nbf`/`iat` ≤ now ≤ `exp`/`expires_at` when present.
5. Check revocation (`revocation` pointer / EAS revocable status) when present.

A cell passing 1–5 is **verified**. Failing 2/3 ⇒ ✗ failed (red). Failing 4 ⇒ ⚠ expired (amber). No network sink is consulted in steps 1–2; that is the point.
