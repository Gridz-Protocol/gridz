"""Sorted-pair merkle root over cell attestation UIDs.

Mirrors packages/core-ts/src/merkle.ts (OpenZeppelin-compatible on EVM).
"""

from __future__ import annotations

from .canonicalize import HashAlgo, hash_bytes, hash_utf8

ZERO32 = "0x" + "00" * 32


def _is_hex32(uid: str) -> bool:
    if not (uid.startswith("0x") and len(uid) == 66):
        return False
    try:
        int(uid, 16)
        return True
    except ValueError:
        return False


def normalize_leaf(algo: HashAlgo, uid: str) -> str:
    if _is_hex32(uid):
        return uid.lower()
    return hash_utf8(algo, uid)


def _hash_pair(algo: HashAlgo, a: str, b: str) -> str:
    lo, hi = (a, b) if a.lower() <= b.lower() else (b, a)
    return hash_bytes(algo, bytes.fromhex(lo[2:]) + bytes.fromhex(hi[2:]))


def merkle_root(algo: HashAlgo, uids: list[str]) -> str:
    if not uids:
        return ZERO32

    level = sorted(normalize_leaf(algo, u) for u in uids)
    while len(level) > 1:
        nxt: list[str] = []
        i = 0
        while i < len(level):
            if i + 1 == len(level):
                nxt.append(level[i])  # odd one out, promote unchanged
                i += 1
                continue
            nxt.append(_hash_pair(algo, level[i], level[i + 1]))
            i += 2
        level = nxt
    return level[0]
