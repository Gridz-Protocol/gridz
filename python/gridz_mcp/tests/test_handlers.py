"""Unit tests for the Python MCP handlers, incl. the no-custody sign flow."""

from __future__ import annotations

from datetime import datetime, timezone

from gridz import LocalEip712Signer, build_grid, hash_utf8, verify_cell
from gridz.eip712 import GRIDZ_CELL
from gridz_mcp import (
    MemoryStore,
    bootstrap_from_template,
    bootstrap_list_templates,
    cell_attach_signature,
    cell_prepare_write,
    grid_verify,
    identity_list_signers,
    schema_suggest_key,
    sink_publish,
)

CHAIN_ID = 11155111
RESOLVER = "0x000000000000000000000000000000000000c0de"
NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)
THEME = {
    "background_type": "solid",
    "background_value": "#000",
    "accent_color": "#fff",
    "text_color": "#fff",
    "card_style": "rounded",
    "card_background": "#111",
    "font_family": "sans",
}


def _signer() -> LocalEip712Signer:
    return LocalEip712Signer(hash_utf8("keccak256", "gridz/__example__/mcp/1"), CHAIN_ID)


def test_prepare_sign_attach_verify():
    signer = _signer()
    did = signer.did()
    prepared = cell_prepare_write(
        subject_did=did, key="alias", value="gridz-agent", chain_id=CHAIN_ID, verifying_contract=RESOLVER
    )
    assert "next_action" not in prepared

    msg = prepared["typed_data"]["message"]
    typed = {**msg, "expiresAt": int(msg["expiresAt"]), "nonce": int(msg["nonce"])}
    sig, _ = signer.sign_typed_data(prepared["typed_data"]["domain"], {"GridzCell": GRIDZ_CELL}, "GridzCell", typed)

    cell = cell_attach_signature(prepared=prepared, signature=sig, attester=did, now=NOW)
    assert cell["key"] == "alias"
    assert verify_cell(cell, {"subject_did": did, "now": NOW})["ok"]


def test_oneclaw_hint():
    prepared = cell_prepare_write(
        subject_did="did:oneclaw:a1",
        key="agent-context",
        value="ctx",
        chain_id=CHAIN_ID,
        verifying_contract=RESOLVER,
        oneclaw={"agent_id": "a1"},
    )
    assert prepared["next_action"]["server"] == "1claw"


def test_store_and_publish():
    signer = _signer()
    did = signer.did()
    grid = build_grid(
        signer,
        subject={"type": "human", "did": did},
        theme=THEME,
        chain_id=CHAIN_ID,
        verifying_contract=RESOLVER,
        now=NOW,
        cells=[{"id": "c1", "key": "alias", "value": "a", "position": {"x": 0, "y": 0, "w": 1, "h": 1}, "size": "1x1"}],
    )
    store = MemoryStore()
    assert store.get_grid(did) is None
    store.put_grid(did, grid)
    assert store.get_cell(did, "alias")["value"] == "a"
    assert store.get_cell(did, "missing") is None
    assert grid_verify(grid)["ok"]

    assert sink_publish(store, subject=did, sink="memory")["ok"]
    assert not sink_publish(store, subject=did, sink="ens")["ok"]
    assert not sink_publish(store, subject="nope", sink="memory")["ok"]


def test_suggest_and_templates_and_identity():
    assert schema_suggest_key("my github")["suggested_key"] == "com.github"
    assert schema_suggest_key("a novel thing")["suggested_key"].startswith("gridz.")
    names = [t["name"] for t in bootstrap_list_templates()]
    assert "minimal" in names
    tmpl = bootstrap_from_template("minimal")
    assert all(c.get("_needs_input") for c in tmpl["cells"])
    assert bootstrap_from_template("nope") == {"error": "unknown_template"}
    assert identity_list_signers()["signers"] == []
