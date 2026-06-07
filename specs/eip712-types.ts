/**
 * specs/eip712-types.ts
 *
 * Canonical EIP-712 typed-data definitions for Gridz attestations.
 *
 * These are the single source of truth for what gets signed. `@gridz/core` and
 * the Python `gridz` package both encode against these exact type tuples; a Grid
 * signed in one runtime MUST verify in the other (enforced by tests/cross-runtime/).
 *
 * Design rules:
 *  - We sign a *hash of the value*, never the raw value. The cleartext value lives
 *    in the cell; `valueHashHex` binds it. This keeps payloads bounded and matches
 *    the EAS schema shapes (gridz.cell.v1 / gridz.root.v1).
 *  - There is ONE generic cell type, `GridzCell`. We do NOT mint a distinct EIP-712
 *    struct per key family — the `key` string is a signed field, so one struct
 *    covers every key (standard, agent, widget, or dynamic) without a registry of
 *    structs to keep in sync across runtimes. See DESIGN_NOTES.md ("one struct vs
 *    many").
 *  - For EVM-native attestations, prefer EAS offchain over raw EIP-712: you inherit
 *    a schema registry, revocation, and indexers. The EAS offchain envelope wraps
 *    these same logical fields; its own EIP-712 domain (name/version) comes from the
 *    EAS SDK and is NOT redefined here.
 *
 * This file is `.ts` because the brief names it so; it is pure data with types and
 * is consumed verbatim by the codegen that produces the Python mirror.
 */

/** EIP-712 field descriptor. */
export interface TypedDataField {
  name: string;
  type: string;
}

/** EIP-712 domain. `verifyingContract` is the deployed GridzResolver for the chain. */
export interface GridzDomain {
  name: "Gridz";
  version: "1";
  chainId: number;
  verifyingContract: `0x${string}`;
}

/**
 * Build the domain for a given chain + resolver. The resolver address is what an
 * operator adds to a 1claw `eip712_domain_allowlist` (see §2.5 / DESIGN_NOTES.md).
 */
export function gridzDomain(chainId: number, verifyingContract: `0x${string}`): GridzDomain {
  return { name: "Gridz", version: "1", chainId, verifyingContract };
}

/**
 * Primary type for a single cell attestation.
 *
 *  gridId         keccak256(JCS(grid identity tuple)) — stable per Grid (see canonicalization.md)
 *  key            the cell key string, verbatim (e.g. "com.github", "gridz.poll")
 *  valueHashHex   keccak256(JCS(cell.value)) as 0x-hex (== attestation.value_hash on EVM)
 *  widgetTypeHash keccak256(utf8(widget_type ?? "")) — empty string hash when unset
 *  expiresAt      unix seconds; 0 == never
 *  nonce          monotonic per (gridId, key); prevents replay of stale values
 */
export const GridzCell: TypedDataField[] = [
  { name: "gridId", type: "bytes32" },
  { name: "key", type: "string" },
  { name: "valueHashHex", type: "string" },
  { name: "widgetTypeHash", type: "bytes32" },
  { name: "expiresAt", type: "uint64" },
  { name: "nonce", type: "uint64" },
];

/**
 * Primary type for the Grid root attestation.
 *
 *  gridId        same gridId as the cells it covers
 *  merkleRoot    sorted merkle root over each cell attestation `uid` (see canonicalization.md)
 *  schemaVersion the Grid schema_version string, e.g. "gridz/1.0.0"
 *  cellCount     number of leaves in the tree (guards against silent truncation)
 *  issuedAt      unix seconds
 */
export const GridzRoot: TypedDataField[] = [
  { name: "gridId", type: "bytes32" },
  { name: "merkleRoot", type: "bytes32" },
  { name: "schemaVersion", type: "string" },
  { name: "cellCount", type: "uint64" },
  { name: "issuedAt", type: "uint64" },
];

/**
 * The complete `types` maps passed to an EIP-712 signer. EIP712Domain is included
 * for completeness; most libraries (ethers, viem, the EAS SDK) inject it implicitly.
 */
export const EIP712_DOMAIN_TYPE: TypedDataField[] = [
  { name: "name", type: "string" },
  { name: "version", type: "string" },
  { name: "chainId", type: "uint256" },
  { name: "verifyingContract", type: "address" },
];

export const GridzCellTypes = {
  EIP712Domain: EIP712_DOMAIN_TYPE,
  GridzCell,
} as const;

export const GridzRootTypes = {
  EIP712Domain: EIP712_DOMAIN_TYPE,
  GridzRoot,
} as const;

/** Primary type names, kept as constants so callers don't stringly-type them. */
export const PRIMARY_TYPE_CELL = "GridzCell" as const;
export const PRIMARY_TYPE_ROOT = "GridzRoot" as const;

/**
 * EAS schema registrations — the on/off-chain mirror of the structs above.
 * `gridz cell sign` registers these once per chain via `gridz schema register`.
 *
 *   gridz.cell.v1: bytes32 gridId, string key, string valueHashHex, uint64 expiresAt, bytes32 widgetTypeHash
 *   gridz.root.v1: bytes32 gridId, bytes32 merkleRoot, string schemaVersion
 *
 * (EAS schema strings intentionally omit `nonce`/`cellCount`/`issuedAt`, which EAS
 * carries in its own envelope as `refUID`/`time`; see DESIGN_NOTES.md.)
 */
export const EAS_SCHEMAS = {
  cell: {
    name: "gridz.cell.v1",
    schema:
      "bytes32 gridId, string key, string valueHashHex, uint64 expiresAt, bytes32 widgetTypeHash",
    revocable: true,
  },
  root: {
    name: "gridz.root.v1",
    schema: "bytes32 gridId, bytes32 merkleRoot, string schemaVersion",
    revocable: true,
  },
} as const;
