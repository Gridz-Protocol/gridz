"""EIP-712 typed-data definitions (mirror of specs/eip712-types.ts)."""

from __future__ import annotations

from typing import Any

GRIDZ_CELL = [
    {"name": "gridId", "type": "bytes32"},
    {"name": "key", "type": "string"},
    {"name": "valueHashHex", "type": "string"},
    {"name": "widgetTypeHash", "type": "bytes32"},
    {"name": "expiresAt", "type": "uint64"},
    {"name": "nonce", "type": "uint64"},
]

GRIDZ_ROOT = [
    {"name": "gridId", "type": "bytes32"},
    {"name": "merkleRoot", "type": "bytes32"},
    {"name": "schemaVersion", "type": "string"},
    {"name": "cellCount", "type": "uint64"},
    {"name": "issuedAt", "type": "uint64"},
]

EIP712_DOMAIN_TYPE = [
    {"name": "name", "type": "string"},
    {"name": "version", "type": "string"},
    {"name": "chainId", "type": "uint256"},
    {"name": "verifyingContract", "type": "address"},
]

PRIMARY_TYPE_CELL = "GridzCell"
PRIMARY_TYPE_ROOT = "GridzRoot"

EAS_SCHEMAS = {
    "cell": {
        "name": "gridz.cell.v1",
        "schema": "bytes32 gridId, string key, string valueHashHex, uint64 expiresAt, bytes32 widgetTypeHash",
        "revocable": True,
    },
    "root": {
        "name": "gridz.root.v1",
        "schema": "bytes32 gridId, bytes32 merkleRoot, string schemaVersion",
        "revocable": True,
    },
}

UINT64_FIELDS = {"GridzCell": ["expiresAt", "nonce"], "GridzRoot": ["cellCount", "issuedAt"]}


def gridz_domain(chain_id: int, verifying_contract: str) -> dict[str, Any]:
    return {"name": "Gridz", "version": "1", "chainId": chain_id, "verifyingContract": verifying_contract}


def coerce_message(fields: list[dict[str, str]], message: dict[str, str]) -> dict[str, Any]:
    """Turn the all-strings bundle message into the native types eth-account needs."""
    out: dict[str, Any] = {}
    for f in fields:
        name, t = f["name"], f["type"]
        v = message[name]
        if t.startswith(("uint", "int")):
            out[name] = int(v)
        elif t.startswith("bytes") and t != "bytes":
            out[name] = bytes.fromhex(v[2:])
        else:
            out[name] = v
    return out
