"""RFC 8785 JCS canonicalization and the keccak256/sha256 hash domains.

Byte-for-byte compatible with @gridz/core (TypeScript). We do not hand-roll JCS.
"""

from __future__ import annotations

import hashlib
from typing import Any, Literal

import rfc8785
from Crypto.Hash import keccak as _keccak

HashAlgo = Literal["keccak256", "sha256"]


def jcs(value: Any) -> bytes:
    """RFC 8785 canonical JSON serialization (returns UTF-8 bytes)."""
    return rfc8785.dumps(value)


def _digest(algo: HashAlgo, data: bytes) -> bytes:
    if algo == "keccak256":
        h = _keccak.new(digest_bits=256)
        h.update(data)
        return h.digest()
    return hashlib.sha256(data).digest()


def hash_bytes(algo: HashAlgo, data: bytes) -> str:
    """Hash raw bytes; returns lowercase 0x-hex (32 bytes)."""
    return "0x" + _digest(algo, data).hex()


def hash_utf8(algo: HashAlgo, s: str) -> str:
    """Hash the UTF-8 bytes of a string (not JCS — input is already primitive)."""
    return hash_bytes(algo, s.encode("utf-8"))


def hash_jcs(algo: HashAlgo, value: Any) -> str:
    """Hash JCS(value). The canonical 'hash a JSON value' primitive."""
    return hash_bytes(algo, jcs(value))
