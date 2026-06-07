"""The universal verifier. Mirrors packages/core-ts/src/verify.ts.

Verification is fully local given the embedded payload; no sink/server/vault is
consulted. Never raises on untrusted input — returns a status dict instead.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from eth_account import Account
from eth_account.messages import encode_typed_data

from .eip712 import EIP712_DOMAIN_TYPE, coerce_message
from .hashing import algo_for_format, value_hash
from .merkle import merkle_root
from .signer import public_key_from_did_key, verify_ed25519
from .util import b64u_decode, decode_bundle, parse_iso


def _result(ok: bool, status: str, reason: str | None = None, attester: str | None = None) -> dict[str, Any]:
    out: dict[str, Any] = {"ok": ok, "status": status}
    if reason is not None:
        out["reason"] = reason
    if attester is not None:
        out["attester"] = attester
    return out


def _fail(reason: str, attester: str | None = None) -> dict[str, Any]:
    return _result(False, "failed", reason, attester)


def _now(ctx: dict[str, Any]) -> datetime:
    return ctx.get("now") or datetime.now(timezone.utc)


def _decode_jws(jws: str) -> tuple[dict[str, Any], bytes, bytes]:
    import json

    parts = jws.split(".")
    if len(parts) != 3:
        raise ValueError("malformed compact JWS")
    claims = json.loads(b64u_decode(parts[1]).decode("utf-8"))
    return claims, f"{parts[0]}.{parts[1]}".encode("utf-8"), b64u_decode(parts[2])


def _bound_hash(bundle: dict[str, Any]) -> str | None:
    if bundle["kind"] == "eip712":
        msg = bundle["message"]
        return msg.get("valueHashHex") or msg.get("merkleRoot")
    claims, _, _ = _decode_jws(bundle["jws"])
    return claims.get("valueHashHex") or claims.get("merkleRoot")


def _authenticate(bundle: dict[str, Any], attester_did: str) -> tuple[bool, str]:
    if bundle["kind"] == "eip712":
        types = bundle["types"]
        primary = bundle["primaryType"]
        msg = coerce_message(types[primary], bundle["message"])
        full = {
            "types": {**types, "EIP712Domain": EIP712_DOMAIN_TYPE},
            "domain": bundle["domain"],
            "primaryType": primary,
            "message": msg,
        }
        signable = encode_typed_data(full_message=full)
        recovered = Account.recover_message(signable, signature=bundle["signature"])
        return True, f"did:pkh:eip155:{bundle['domain']['chainId']}:{recovered.lower()}"

    claims, signing_input, sig = _decode_jws(bundle["jws"])
    pub = public_key_from_did_key(attester_did)
    if not verify_ed25519(pub, signing_input, sig):
        return False, "bad-signature"
    return True, attester_did


def _time_check(att: dict[str, Any], now: datetime) -> dict[str, Any] | None:
    if att.get("nbf") and parse_iso(att["nbf"]) > now:
        return _fail("not-yet-valid", att.get("attester"))
    if att.get("exp") and parse_iso(att["exp"]) < now:
        return _result(False, "expired", "expired", att.get("attester"))
    return None


def verify_attestation(att: dict[str, Any], value: Any, ctx: dict[str, Any] | None = None) -> dict[str, Any]:
    ctx = ctx or {}
    algo = algo_for_format(att["format"])
    if value_hash(algo, value) != att["value_hash"]:
        return _fail("value-hash-mismatch", att.get("attester"))

    if not att.get("payload"):
        return _result(False, "unsupported", f"no inline payload for {att['format']}", att.get("attester"))

    try:
        bundle = decode_bundle(att["payload"])
        if _bound_hash(bundle) != att["value_hash"]:
            return _fail("bound-hash-mismatch", att.get("attester"))
        ok, recovered = _authenticate(bundle, att["attester"])
        if not ok:
            return _fail(recovered, att.get("attester"))
        if recovered != att["attester"]:
            return _fail("attester-mismatch", att.get("attester"))
    except Exception:
        return _fail("malformed-payload", att.get("attester"))

    subject = ctx.get("subject_did")
    if subject and not ctx.get("allow_delegated") and att["attester"] != subject:
        return _fail("unauthorized-signer", att.get("attester"))

    t = _time_check(att, _now(ctx))
    if t:
        return t
    return _result(True, "verified", None, att.get("attester"))


def verify_cell(cell: dict[str, Any], ctx: dict[str, Any] | None = None) -> dict[str, Any]:
    ctx = ctx or {}
    base = verify_attestation(cell["attestation"], cell["value"], ctx)
    if not base["ok"]:
        return base
    if cell.get("expires_at") and parse_iso(cell["expires_at"]) < _now(ctx):
        return _result(False, "expired", "cell-expired", base.get("attester"))
    return base


def verify_grid(grid: dict[str, Any], ctx: dict[str, Any] | None = None) -> dict[str, Any]:
    ctx = dict(ctx or {})
    ctx.setdefault("subject_did", grid["subject"]["did"])

    cells = [
        {"id": c["id"], "key": c["key"], "result": verify_cell(c, ctx)} for c in grid["cells"]
    ]
    root = _verify_root(grid, ctx)
    ok = root["ok"] and all(c["result"]["ok"] for c in cells)
    return {"ok": ok, "cells": cells, "root": root}


def _verify_root(grid: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
    att = grid["root_attestation"]
    algo = algo_for_format(att["format"])
    computed = merkle_root(algo, [c["attestation"]["uid"] for c in grid["cells"]])

    if computed != att["value_hash"]:
        return _fail("merkle-root-mismatch", att.get("attester"))
    if not att.get("payload"):
        return _result(False, "unsupported", "no inline root payload", att.get("attester"))

    try:
        bundle = decode_bundle(att["payload"])
        if _bound_hash(bundle) != computed:
            return _fail("root-bound-mismatch", att.get("attester"))
        if bundle["kind"] == "eip712":
            count = int(bundle["message"]["cellCount"])
        else:
            claims, _, _ = _decode_jws(bundle["jws"])
            count = int(claims["cellCount"])
        if count != len(grid["cells"]):
            return _fail("cell-count-mismatch", att.get("attester"))
        ok, recovered = _authenticate(bundle, att["attester"])
        if not ok:
            return _fail(recovered, att.get("attester"))
        if recovered != att["attester"]:
            return _fail("attester-mismatch", att.get("attester"))
    except Exception:
        return _fail("malformed-payload", att.get("attester"))

    subject = ctx.get("subject_did")
    if subject and not ctx.get("allow_delegated") and att["attester"] != subject:
        return _fail("unauthorized-signer", att.get("attester"))

    t = _time_check(att, _now(ctx))
    if t:
        return t
    return _result(True, "verified", None, att.get("attester"))
