"""Forward cross-runtime gate: grids signed by @gridz/core (TS) verify here."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from gridz import build_grid, verify_grid
from .data import CHAIN_ID, NOW, POS, RESOLVER, THEME


def _load(fixtures_dir: Path, name: str) -> dict:
    return json.loads((fixtures_dir / name).read_text())


def test_ts_eip712_grid_verifies(fixtures_dir: Path) -> None:
    grid = _load(fixtures_dir, "ts-eip712-grid.json")
    result = verify_grid(grid, {"now": NOW})
    assert result["ok"], result
    assert all(c["result"]["ok"] for c in result["cells"])
    assert result["root"]["ok"]


def test_ts_ed25519_grid_verifies(fixtures_dir: Path) -> None:
    grid = _load(fixtures_dir, "ts-ed25519-grid.json")
    result = verify_grid(grid, {"now": NOW})
    assert result["ok"], result


def test_tampering_a_ts_cell_value_fails(fixtures_dir: Path) -> None:
    grid = _load(fixtures_dir, "ts-eip712-grid.json")
    grid["cells"][0]["value"] = "tampered"
    result = verify_grid(grid, {"now": NOW})
    assert not result["ok"]
    assert result["cells"][0]["result"]["reason"] == "value-hash-mismatch"


def test_python_eip712_signature_matches_ts_bit_for_bit(fixtures_dir: Path, eip712_signer) -> None:
    """Deterministic ECDSA + identical EIP-712 digest => identical signatures.

    This proves the two runtimes encode the typed data identically, not merely
    that each can verify the other.
    """
    pos = POS
    grid = build_grid(
        eip712_signer,
        subject={"type": "human", "did": eip712_signer.did()},
        theme=THEME,
        chain_id=CHAIN_ID,
        verifying_contract=RESOLVER,
        now=NOW,
        cells=[
            {"id": "c1", "key": "alias", "value": "gridz-example", "position": pos, "size": "1x1"},
            {
                "id": "c2",
                "key": "description",
                "value": "a seed-derived example grid",
                "position": {**pos, "x": 1},
                "size": "2x1",
            },
            {
                "id": "c3",
                "key": "gridz.poll",
                "value": {"q": "ship it?", "options": ["yes", "also yes"]},
                "widget_type": "gridz.poll",
                "position": {**pos, "y": 1},
                "size": "2x2",
            },
        ],
    )
    ts = _load(fixtures_dir, "ts-eip712-grid.json")
    assert grid["cells"][0]["attestation"]["uid"] == ts["cells"][0]["attestation"]["uid"]
    assert grid["root_attestation"]["uid"] == ts["root_attestation"]["uid"]
