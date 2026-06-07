"""Build self-contained, offline-verifiable attestations.

Mirrors packages/core-ts/src/attest.ts — produces byte-compatible bundles.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .canonicalize import hash_bytes
from .eip712 import GRIDZ_CELL, GRIDZ_ROOT, gridz_domain
from .hashing import (
    SCHEMA_VERSION,
    algo_for_format,
    grid_id,
    value_hash,
    widget_type_hash,
)
from .signer import Ed25519Signer
from .util import encode_bundle, iso_z


def _now(now: datetime | None) -> datetime:
    return now or datetime.now(timezone.utc)


def _uid_eip712(signature: str) -> str:
    return hash_bytes("keccak256", bytes.fromhex(signature[2:]))


def _uid_jws(jws: str) -> str:
    return hash_bytes("sha256", jws.encode("utf-8"))


def build_cell_attestation(
    signer: Any,
    *,
    subject_did: str,
    key: str,
    value: Any,
    widget_type: str | None = None,
    expires_at: datetime | None = None,
    nonce: int = 0,
    chain_id: int | None = None,
    verifying_contract: str | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    fmt = signer.format()
    algo = algo_for_format(fmt)
    ts = _now(now)

    gid = grid_id(algo, subject_did)
    vhash = value_hash(algo, value)
    whash = widget_type_hash(algo, widget_type)
    expires_sec = int(expires_at.timestamp()) if expires_at else 0
    attester = signer.did()

    base: dict[str, Any] = {"attester": attester, "iat": iso_z(ts), "value_hash": vhash}
    if expires_at:
        base["exp"] = iso_z(expires_at)

    if fmt in ("eip712-raw", "eip712-oneclaw"):
        if chain_id is None or verifying_contract is None:
            raise ValueError("EIP-712 cell attestation requires chain_id + verifying_contract")
        domain = gridz_domain(chain_id, verifying_contract)
        typed = {
            "gridId": bytes.fromhex(gid[2:]),
            "key": key,
            "valueHashHex": vhash,
            "widgetTypeHash": bytes.fromhex(whash[2:]),
            "expiresAt": expires_sec,
            "nonce": int(nonce),
        }
        sig, _ = signer.sign_typed_data(domain, {"GridzCell": GRIDZ_CELL}, "GridzCell", typed)
        serialized = {
            "gridId": gid,
            "key": key,
            "valueHashHex": vhash,
            "widgetTypeHash": whash,
            "expiresAt": str(expires_sec),
            "nonce": str(int(nonce)),
        }
        payload = encode_bundle(
            {
                "kind": "eip712",
                "domain": domain,
                "types": {"GridzCell": GRIDZ_CELL},
                "primaryType": "GridzCell",
                "message": serialized,
                "signature": sig,
            }
        )
        uid = _uid_eip712(sig)
        return {**base, "format": fmt, "uid": uid, "uri": f"data://inline/{uid}", "payload": payload}

    if fmt == "jws-ed25519":
        if not isinstance(signer, Ed25519Signer):
            raise ValueError("jws-ed25519 requires an Ed25519Signer")
        claims = {
            "iss": attester,
            "gridId": gid,
            "key": key,
            "valueHashHex": vhash,
            "widgetTypeHash": whash,
            "expiresAt": expires_sec,
            "nonce": str(int(nonce)),
            "iat": int(ts.timestamp()),
        }
        jws = signer.sign_jws(claims)
        uid = _uid_jws(jws)
        payload = encode_bundle({"kind": "jws", "jws": jws})
        return {**base, "format": fmt, "uid": uid, "uri": f"data://inline/{uid}", "payload": payload}

    raise ValueError(f"core cannot author format {fmt}")


def build_root_attestation(
    signer: Any,
    *,
    subject_did: str,
    merkle_root: str,
    cell_count: int,
    chain_id: int | None = None,
    verifying_contract: str | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    fmt = signer.format()
    algo = algo_for_format(fmt)
    ts = _now(now)
    gid = grid_id(algo, subject_did)
    attester = signer.did()
    base: dict[str, Any] = {"attester": attester, "iat": iso_z(ts), "value_hash": merkle_root}

    if fmt in ("eip712-raw", "eip712-oneclaw"):
        if chain_id is None or verifying_contract is None:
            raise ValueError("EIP-712 root attestation requires chain_id + verifying_contract")
        domain = gridz_domain(chain_id, verifying_contract)
        typed = {
            "gridId": bytes.fromhex(gid[2:]),
            "merkleRoot": bytes.fromhex(merkle_root[2:]),
            "schemaVersion": SCHEMA_VERSION,
            "cellCount": int(cell_count),
            "issuedAt": int(ts.timestamp()),
        }
        sig, _ = signer.sign_typed_data(domain, {"GridzRoot": GRIDZ_ROOT}, "GridzRoot", typed)
        serialized = {
            "gridId": gid,
            "merkleRoot": merkle_root,
            "schemaVersion": SCHEMA_VERSION,
            "cellCount": str(int(cell_count)),
            "issuedAt": str(int(ts.timestamp())),
        }
        payload = encode_bundle(
            {
                "kind": "eip712",
                "domain": domain,
                "types": {"GridzRoot": GRIDZ_ROOT},
                "primaryType": "GridzRoot",
                "message": serialized,
                "signature": sig,
            }
        )
        uid = _uid_eip712(sig)
        return {**base, "format": fmt, "uid": uid, "uri": f"data://inline/{uid}", "payload": payload}

    if fmt == "jws-ed25519":
        if not isinstance(signer, Ed25519Signer):
            raise ValueError("jws-ed25519 requires an Ed25519Signer")
        claims = {
            "iss": attester,
            "gridId": gid,
            "merkleRoot": merkle_root,
            "schemaVersion": SCHEMA_VERSION,
            "cellCount": cell_count,
            "iat": int(ts.timestamp()),
        }
        jws = signer.sign_jws(claims)
        uid = _uid_jws(jws)
        payload = encode_bundle({"kind": "jws", "jws": jws})
        return {**base, "format": fmt, "uid": uid, "uri": f"data://inline/{uid}", "payload": payload}

    raise ValueError(f"core cannot author format {fmt}")
