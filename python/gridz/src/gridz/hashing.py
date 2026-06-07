"""Derived hashes (gridId, value_hash, widgetTypeHash) and format→algo mapping.

Mirrors packages/core-ts/src/hash.ts.
"""

from __future__ import annotations

from typing import Any

from .canonicalize import HashAlgo, hash_jcs, hash_utf8

SCHEMA_VERSION = "gridz/1.0.0"

_EVM_FORMATS = {"eas-onchain", "eas-offchain", "eip712-raw", "eip712-oneclaw"}
_NON_EVM_FORMATS = {"jws-ed25519", "cose-webauthn"}


def algo_for_format(fmt: str) -> HashAlgo:
    if fmt in _EVM_FORMATS:
        return "keccak256"
    if fmt in _NON_EVM_FORMATS:
        return "sha256"
    raise ValueError(f"unknown attestation format: {fmt}")


def value_hash(algo: HashAlgo, value: Any) -> str:
    return hash_jcs(algo, value)


def grid_id(algo: HashAlgo, did: str, schema_version: str = SCHEMA_VERSION) -> str:
    return hash_jcs(algo, {"did": did, "schema_version": schema_version})


def widget_type_hash(algo: HashAlgo, widget_type: str | None) -> str:
    return hash_utf8(algo, widget_type or "")
