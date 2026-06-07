from __future__ import annotations

import re

from hypothesis import given, settings
from hypothesis import strategies as st

from gridz import hash_jcs, hash_utf8, jcs


def test_jcs_sorts_keys() -> None:
    assert jcs({"b": 1, "a": 2}) == b'{"a":2,"b":1}'
    assert jcs({"a": 2, "b": 1}) == b'{"a":2,"b":1}'


def test_jcs_no_whitespace() -> None:
    assert jcs({"x": [1, 2, 3]}) == b'{"x":[1,2,3]}'


def test_jcs_preserves_array_order() -> None:
    assert jcs([3, 1, 2]) == b"[3,1,2]"


def test_keccak_and_sha_differ() -> None:
    k = hash_jcs("keccak256", {"a": 1})
    s = hash_jcs("sha256", {"a": 1})
    assert re.fullmatch(r"0x[0-9a-f]{64}", k)
    assert re.fullmatch(r"0x[0-9a-f]{64}", s)
    assert k != s


def test_hash_utf8_empty_string() -> None:
    assert re.fullmatch(r"0x[0-9a-f]{64}", hash_utf8("keccak256", ""))


_json = st.recursive(
    st.none() | st.booleans() | st.integers(min_value=-(10**9), max_value=10**9) | st.text(),
    lambda children: st.lists(children) | st.dictionaries(st.text(), children),
    max_leaves=20,
)


@settings(max_examples=1000)
@given(_json)
def test_hash_is_stable_under_key_reordering(value: object) -> None:
    if isinstance(value, dict):
        reordered = dict(reversed(list(value.items())))
    else:
        reordered = value
    assert hash_jcs("keccak256", value) == hash_jcs("keccak256", reordered)
