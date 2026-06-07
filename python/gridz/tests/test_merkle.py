from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st

from gridz import ZERO32, merkle_root, normalize_leaf
from gridz.canonicalize import hash_bytes, hash_utf8


def _uid(s: str) -> str:
    return "0x" + s.rjust(64, "0")


def test_empty_tree_is_zero32() -> None:
    assert merkle_root("keccak256", []) == ZERO32


def test_single_leaf_is_itself() -> None:
    leaf = _uid("ab")
    assert merkle_root("keccak256", [leaf]) == leaf


def test_two_leaves_sorted_pair() -> None:
    a, b = _uid("01"), _uid("02")
    expected = hash_bytes("keccak256", bytes.fromhex(a[2:]) + bytes.fromhex(b[2:]))
    assert merkle_root("keccak256", [a, b]) == expected
    assert merkle_root("keccak256", [b, a]) == expected


def test_non_hex_uid_is_hashed() -> None:
    assert normalize_leaf("keccak256", "eas:abc") == hash_utf8("keccak256", "eas:abc")


def test_odd_node_promoted() -> None:
    a, b, c = _uid("01"), _uid("02"), _uid("03")
    ab = hash_bytes("keccak256", bytes.fromhex(a[2:]) + bytes.fromhex(b[2:]))
    lo, hi = (ab, c) if ab < c else (c, ab)
    top = hash_bytes("keccak256", bytes.fromhex(lo[2:]) + bytes.fromhex(hi[2:]))
    assert merkle_root("keccak256", [a, b, c]) == top


@settings(max_examples=1000)
@given(st.lists(st.from_regex(r"[0-9a-f]{64}", fullmatch=True), min_size=1, max_size=20, unique=True))
def test_order_independence(hexes: list[str]) -> None:
    uids = ["0x" + h for h in hexes]
    assert merkle_root("keccak256", uids) == merkle_root("keccak256", list(reversed(uids)))
