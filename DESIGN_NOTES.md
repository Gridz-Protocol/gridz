# Gridz — Design Notes (spec PR #1)

This PR delivers only the six spec artifacts the brief's §19 asks for, plus this note. No package code, no templates, no example data. Stopping here for review.

Delivered:
- `specs/grid.schema.json`
- `specs/attestation.schema.json`
- `specs/standard-keys.md`
- `specs/eip712-types.ts`
- `specs/canonicalization.md`
- `DESIGN_NOTES.md` (this file)

I fetched and read the design-critical references first: ENSIP-5, ENSIP-18, ENSIP-25, ENSIP-26, and the 1claw `llms.txt` API index. The EAS docs page is client-rendered and returned no content via fetch; I relied on the EAS SDK's well-known offchain envelope rather than guessing, and deliberately did **not** hardcode EAS's own EIP-712 domain name/version (the SDK owns those).

---

## Where I applied judgment (brief left it open or inconsistent)

1. **Branding leftovers renamed.** The brief says the "Spritz Grids" name is retired and the namespace is `gridz.*`, yet two field names still carried the old brand:
   - `Theme.show_spritz_badge` → **`show_gridz_badge`**.
   - The EIP-712 fallback struct `SpritzCell` → **`GridzCell`**.
   If you actually want to keep a literal "spritz" token anywhere (e.g. attribution), tell me; otherwise the codebase stays `gridz.*` end to end.

2. **One EIP-712 struct, not one-per-key-family.** The brief says "one type per cell key family plus a generic fallback." I chose a **single** `GridzCell` struct with `key` as a signed string field instead. Rationale: distinct structs per family would require a struct registry kept byte-identical across TS/Python/Solidity and would break the moment someone uses a dynamic key (which the brief makes first-class). One struct that signs the key string covers every key uniformly and is far easier to keep cross-runtime-stable. The EAS `gridz.cell.v1` schema mirrors this. **Flag for your call** if you specifically want per-family structs.

3. **Sign a hash of the value, not the value.** `GridzCell.valueHashHex` commits to `keccak256(JCS(value))`. Keeps signed payloads bounded and matches the EAS schema shape. The cleartext value stays in the cell and is checked against the hash at verify time.

4. **Added `nonce` (cell) and `cellCount` (root) to the signed structs.** Not in the brief's EAS schema strings, but needed to prevent replay of stale cell values and silent cell-set truncation respectively. They live in the EIP-712 structs; the EAS schema strings stay as the brief specified (EAS carries the equivalent via envelope `refUID`/`time`). Easy to drop if you'd rather keep EIP-712 and EAS schemas field-identical.

5. **`name` → `alias`.** The brief's Tier-1 list includes `name`, but ENS has no bare `name` text key. I mapped it to ENSIP-18 `alias` (display name) and surfaced ENSIP-5 `display` as the canonical-capitalization key. Documented in `standard-keys.md`.

6. **Merkle leaves include hidden cells.** `is_visible:false` cells are still committed to the root — visibility is a render concern, not a membership concern. Sorted-pair (OpenZeppelin-compatible) hashing so proofs verify in `GridzResolver.sol`. Empty tree = 32 zero bytes; single leaf = itself.

7. **Authoring flags are in-schema but publish-forbidden.** `_needs_input` and `_unattested` live on the cell schema so templates/imports validate, but they MUST cause `gridz grid validate` to fail and MUST be absent on a published Grid. This bakes the brief's "templates ship shape, not content" and "staging before publish" rules into the data model.

8. **`agent.*` keys marked Gridz-defined, not ENS.** See correction (2) below.

---

## Corrections to the brief (verified against primary sources)

1. **ENSIP-26 scope.** ENSIP-26 defines **only** `agent-context` and `agent-endpoint[<protocol>]`. The brief (§2, §6) attributes `agent-registration[...]` to "ENSIP-25/26"; it is **ENSIP-25** only. `standard-keys.md` attributes each key correctly.

2. **`agent-registration` value + registry encoding.** Per ENSIP-25 the value is a non-empty string that SHOULD be `"1"` (presence is the attestation; the value is meaningless), and `<registry>` is the **ERC-7930 interoperable address** of the registry contract (hex with `0x`), not a bare chain id. Captured in `standard-keys.md`.

3. **1claw secrets endpoint path.** The brief's `oneclaw://` resolver text says it calls `GET /v1/secrets/{path}`. The actual 1claw API is **`GET /v1/vaults/{id}/secrets/{path}`** (vault-scoped). This affects the `oneclaw://` URI shape — see open question 1. The 1claw sign endpoint (`POST /v1/agents/{id}/sign`, `intent_type: typed_data|personal_sign`), key provisioning (`POST /v1/agents/{id}/signing-keys`), base URL (`https://api.1claw.xyz`), and `ocv_` agent-key prefix all match the brief.

4. **`agent.*` are not ENS standards.** The brief's §6 Tier-2 lists `agent.capabilities/model/version/operator` alongside ENSIP keys. These are Gridz-defined; they're namespaced under `agent.` (dot form) to avoid colliding with the bracketed ENSIP `agent-endpoint[...]` / `agent-registration[...]` keys.

---

## Open questions for you

1. **`oneclaw://` URI shape.** Given the real vault-scoped path, should the resolver URI be `oneclaw://vault/<vaultId>/<path>` (explicit vault) or `oneclaw://secret/<path>` with a default vault from config? The brief wrote `oneclaw://vault/<path>`, which omits the vault id the API requires. I'll default to `oneclaw://vault/<vaultId>/<path>` unless you say otherwise.

2. **Delegated / authorized signers.** Canonicalization step 6.3 references an "authorized-signer set" for the subject (so a relayer or an org's multisig member can attest on behalf of the subject). The brief's `org-multisig` template implies this. Do you want delegated-signer authority modeled in the spec now (e.g. a `signers[]` cell or an EAS schema), or deferred to the implementation phase? I deferred it for this PR.

3. **EAS schema field parity vs. replay protection (judgment call 4).** Keep `nonce`/`cellCount` only in the EIP-712 structs (current choice), or also extend the EAS `gridz.cell.v1` / `gridz.root.v1` schema strings to include them? The latter is cleaner but diverges from the exact schema strings you wrote in the brief.

4. **Hash-domain split.** I tied keccak256-vs-sha256 to the signing curve / attestation format. If you'd rather pin a single hash (e.g. always sha256 for portability, keccak only inside the EVM contract path), that's a one-line change here but affects every downstream package — better decided now.

5. **`did:ethr` chainId form.** I allow both `did:ethr:<chainId>:<addr>` and `did:pkh:eip155:<chainId>:<addr>`. `did:pkh` is the more interoperable choice (CAIP-10). OK to recommend `did:pkh` as canonical and treat `did:ethr` as accepted-but-discouraged?

6. **Test fixtures.** Per the no-mock-data rule, the spec-validation tests in the next PR will use **deterministic seed-derived** subjects (e.g. a fixed test mnemonic → addresses) under a clearly-labeled `__example__` namespace. Confirm that's the fixture strategy you want before I write step 1's tests, or point me at real data you'd prefer.

Awaiting review before touching any package, template, or example.
