from __future__ import annotations

from datetime import datetime, timezone

import pytest

from gridz import (
    Ed25519Signer,
    ZERO32,
    build_cell_attestation,
    build_grid,
    build_root_attestation,
    public_key_from_did_key,
    value_hash,
    verify_attestation,
    verify_cell,
    verify_grid,
)
from .data import CHAIN_ID, NOW, POS, RESOLVER, THEME


def _eip_cell(signer, value="x", **kw):
    return build_cell_attestation(
        signer,
        subject_did=signer.did(),
        key="alias",
        value=value,
        chain_id=CHAIN_ID,
        verifying_contract=RESOLVER,
        now=NOW,
        **kw,
    )


def test_eip712_roundtrip(eip712_signer) -> None:
    att = _eip_cell(eip712_signer, "gridz-example")
    assert att["format"] == "eip712-raw"
    r = verify_attestation(att, "gridz-example", {"subject_did": eip712_signer.did()})
    assert r["ok"] and r["status"] == "verified"


def test_tampered_value_fails(eip712_signer) -> None:
    att = _eip_cell(eip712_signer, "original")
    r = verify_attestation(att, "tampered")
    assert not r["ok"] and r["reason"] == "value-hash-mismatch"


def test_unauthorized_signer(eip712_signer) -> None:
    att = _eip_cell(eip712_signer)
    r = verify_attestation(att, "x", {"subject_did": "did:pkh:eip155:1:0xother"})
    assert not r["ok"] and r["reason"] == "unauthorized-signer"


def test_expired(eip712_signer) -> None:
    att = _eip_cell(eip712_signer, expires_at=datetime(2026, 2, 1, tzinfo=timezone.utc))
    r = verify_attestation(att, "x", {"now": datetime(2026, 3, 1, tzinfo=timezone.utc)})
    assert not r["ok"] and r["status"] == "expired"


def test_not_yet_valid(eip712_signer) -> None:
    att = _eip_cell(eip712_signer)
    att["nbf"] = "2030-01-01T00:00:00.000Z"
    r = verify_attestation(att, "x", {"now": NOW})
    assert r["reason"] == "not-yet-valid"


def test_unsupported_without_payload() -> None:
    att = {
        "format": "eas-onchain",
        "uid": "0x" + "ab" * 32,
        "uri": "eas://11155111/0x" + "ab" * 32,
        "attester": "did:pkh:eip155:1:0x01",
        "iat": NOW.isoformat(),
        "value_hash": value_hash("keccak256", {"a": 1}),
    }
    assert verify_attestation(att, {"a": 1})["status"] == "unsupported"


def test_malformed_payload_does_not_raise(eip712_signer) -> None:
    att = _eip_cell(eip712_signer)
    att["payload"] = "!!!not-base64!!!"
    r = verify_attestation(att, "x")
    assert not r["ok"]


def test_ed25519_roundtrip(ed25519_signer) -> None:
    att = build_cell_attestation(
        ed25519_signer,
        subject_did=ed25519_signer.did(),
        key="agent-context",
        value={"role": "example"},
        now=NOW,
    )
    assert att["format"] == "jws-ed25519"
    r = verify_attestation(att, {"role": "example"}, {"subject_did": ed25519_signer.did()})
    assert r["ok"]


def test_ed25519_bad_signature(ed25519_signer) -> None:
    import base64
    import json

    att = build_cell_attestation(
        ed25519_signer, subject_did=ed25519_signer.did(), key="alias", value="v", now=NOW
    )
    bundle = json.loads(base64.urlsafe_b64decode(att["payload"] + "==").decode())
    header, claims, sig = bundle["jws"].split(".")
    raw = bytearray(base64.urlsafe_b64decode(sig + "=="))
    raw[0] ^= 0xFF
    bundle["jws"] = f"{header}.{claims}.{base64.urlsafe_b64encode(raw).rstrip(b'=').decode()}"
    att["payload"] = base64.urlsafe_b64encode(json.dumps(bundle).encode()).rstrip(b"=").decode()
    r = verify_attestation(att, "v")
    assert not r["ok"] and r["reason"] == "bad-signature"


def test_cell_level_expiry(eip712_signer) -> None:
    att = _eip_cell(eip712_signer)
    cell = {
        "id": "c1",
        "key": "alias",
        "value": "x",
        "position": POS,
        "size": "1x1",
        "is_visible": True,
        "attestation": att,
        "expires_at": "2026-02-01T00:00:00.000Z",
    }
    r = verify_cell(cell, {"subject_did": eip712_signer.did(), "now": datetime(2026, 3, 1, tzinfo=timezone.utc)})
    assert r["status"] == "expired" and r["reason"] == "cell-expired"


def test_full_grid_and_dropped_cell(eip712_signer) -> None:
    grid = build_grid(
        eip712_signer,
        subject={"type": "human", "did": eip712_signer.did()},
        theme=THEME,
        chain_id=CHAIN_ID,
        verifying_contract=RESOLVER,
        now=NOW,
        cells=[
            {"id": "c1", "key": "alias", "value": "a", "position": POS, "size": "1x1"},
            {"id": "c2", "key": "url", "value": "https://gridz.dev", "position": POS, "size": "1x1"},
        ],
    )
    assert verify_grid(grid)["ok"]
    grid["cells"] = grid["cells"][:1]
    bad = verify_grid(grid)
    assert not bad["ok"] and not bad["root"]["ok"]


def test_ed25519_full_grid_with_widgets(ed25519_signer) -> None:
    grid = build_grid(
        ed25519_signer,
        subject={"type": "agent", "did": ed25519_signer.did()},
        theme=THEME,
        now=NOW,
        cells=[
            {
                "id": "c1",
                "key": "gridz.poll",
                "value": {"q": "ship?", "options": ["yes"]},
                "widget_type": "gridz.poll",
                "position": POS,
                "size": "2x2",
                "is_visible": False,
                "expires_at": datetime(2030, 1, 1, tzinfo=timezone.utc),
                "nonce": 7,
            },
            {"id": "c2", "key": "agent-context", "value": "ctx", "position": POS, "size": "1x1"},
        ],
    )
    assert verify_grid(grid)["ok"]


def test_empty_grid(eip712_signer) -> None:
    grid = build_grid(
        eip712_signer,
        subject={"type": "human", "did": eip712_signer.did()},
        theme=THEME,
        chain_id=CHAIN_ID,
        verifying_contract=RESOLVER,
        now=NOW,
        cells=[],
    )
    assert verify_grid(grid)["ok"]


def test_signer_and_authoring_errors(eip712_signer, ed25519_signer) -> None:
    with pytest.raises(ValueError):
        Ed25519Signer(b"\x00" * 31)
    with pytest.raises(ValueError):
        public_key_from_did_key("did:web:gridz.dev")
    with pytest.raises(ValueError):
        build_cell_attestation(eip712_signer, subject_did=eip712_signer.did(), key="alias", value="x", now=NOW)
    with pytest.raises(ValueError):
        build_root_attestation(eip712_signer, subject_did=eip712_signer.did(), merkle_root=ZERO32, cell_count=0, now=NOW)


def test_reverse_python_fixtures_verify(fixtures_dir) -> None:
    import json

    for name in ("py-eip712-grid.json", "py-ed25519-grid.json"):
        grid = json.loads((fixtures_dir / name).read_text())
        assert verify_grid(grid, {"now": NOW})["ok"]
