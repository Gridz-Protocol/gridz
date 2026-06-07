from __future__ import annotations

from datetime import datetime, timezone

import pytest

from gridz import LocalEip712Signer, build_cell_attestation, hash_utf8, verify_attestation
from gridz.eip712 import GRIDZ_CELL, coerce_message
from gridz_oneclaw import (
    OneClawError,
    OneClawKeyProvisioner,
    OneClawResolver,
    OneClawSigner,
    eip712_domain_allowlist_snippet,
    load_config,
)

CHAIN_ID = 11155111
RESOLVER = "0x000000000000000000000000000000000000c0de"
NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)

hsm = LocalEip712Signer(hash_utf8("keccak256", "gridz/__example__/oneclaw"), CHAIN_ID)


def _fake_transport(method, url, headers, body):
    if body and body.get("intent_type") == "typed_data":
        td = body["typed_data"]
        msg = coerce_message(GRIDZ_CELL, td["message"])
        sig, _ = hsm.sign_typed_data(td["domain"], {"GridzCell": GRIDZ_CELL}, "GridzCell", msg)
        return 200, {"signature": sig, "from": hsm.address}
    if body and body.get("intent_type") == "personal_sign":
        return 200, {"signature": "0x" + "ab" * 65, "from": hsm.address}
    return 400, {"error": "unknown"}


def _config() -> dict:
    return {"agent_id": "a", "api_key": "ocv_x", "address": hsm.address, "chain_id": CHAIN_ID, "api_base": "https://api.1claw.xyz"}


def test_signer_produces_verifiable_attestation():
    signer = OneClawSigner(_config(), transport=_fake_transport)
    assert signer.format() == "eip712-oneclaw"
    assert signer.did() == f"did:pkh:eip155:{CHAIN_ID}:{hsm.address.lower()}"

    att = build_cell_attestation(
        signer,
        subject_did=signer.did(),
        key="agent-context",
        value="via HSM",
        chain_id=CHAIN_ID,
        verifying_contract=RESOLVER,
        now=NOW,
    )
    assert att["format"] == "eip712-oneclaw"
    assert verify_attestation(att, "via HSM", {"subject_did": signer.did(), "now": NOW})["ok"]


def test_allowlist_error_has_pointer():
    signer = OneClawSigner(_config(), transport=lambda *a: (403, {"error": "eip712_domain_allowlist denied"}))
    with pytest.raises(OneClawError) as exc:
        signer.sign_typed_data({}, {"GridzCell": GRIDZ_CELL}, "GridzCell", {"expiresAt": 0, "nonce": 0})
    assert exc.value.code == "eip712_domain_allowlist"
    assert "dashboard.1claw.xyz" in (exc.value.hint or "")


def test_sign_failed_generic():
    signer = OneClawSigner(_config(), transport=lambda *a: (500, {"message": "boom"}))
    with pytest.raises(OneClawError) as exc:
        signer.sign_typed_data({}, {"GridzCell": GRIDZ_CELL}, "GridzCell", {"expiresAt": 0, "nonce": 0})
    assert exc.value.code == "sign_failed"


def test_personal_sign():
    signer = OneClawSigner(_config(), transport=_fake_transport)
    assert signer.sign_message("hi").startswith("0x")
    assert signer.sign_message(b"\x01\x02").startswith("0x")


def test_provisioner():
    prov = OneClawKeyProvisioner({"agent_id": "a", "api_key": "ocv_x"}, transport=lambda *a: (200, {"address": hsm.address, "public_key": "0xpub"}))
    assert prov.provision("ethereum") == {"address": hsm.address, "public_key": "0xpub"}
    bad = OneClawKeyProvisioner({"agent_id": "a", "api_key": "ocv_x"}, transport=lambda *a: (500, {"error": "x"}))
    with pytest.raises(OneClawError):
        bad.provision("solana")


def test_resolver_caches():
    calls = {"n": 0}

    def transport(method, url, headers, body):
        calls["n"] += 1
        return 200, {"value": "secret"}

    r = OneClawResolver({"api_key": "ocv_x"}, transport=transport)
    assert OneClawResolver.is_oneclaw_uri("oneclaw://vault/v1/db")
    assert not OneClawResolver.is_oneclaw_uri("env://X")
    assert r.resolve("oneclaw://vault/v1/db") == "secret"
    assert r.resolve("oneclaw://vault/v1/db") == "secret"
    assert calls["n"] == 1
    with pytest.raises(OneClawError):
        r.resolve("oneclaw://bad")


def test_signing_host_routing():
    seen = {}

    def transport(method, url, headers, body):
        seen["url"] = url
        return _fake_transport(method, url, headers, body)

    cfg = {**_config(), "signing_host": "https://shroud.1claw.xyz"}
    OneClawSigner(cfg, transport=transport).sign_typed_data(
        {"name": "Gridz", "version": "1", "chainId": CHAIN_ID, "verifyingContract": RESOLVER},
        {"GridzCell": GRIDZ_CELL},
        "GridzCell",
        {"gridId": b"\x00" * 32, "key": "k", "valueHashHex": "0x" + "00" * 32, "widgetTypeHash": b"\x00" * 32, "expiresAt": 0, "nonce": 0},
    )
    assert "shroud.1claw.xyz" in seen["url"]


def test_allowlist_snippet_and_config():
    snip = eip712_domain_allowlist_snippet(RESOLVER, CHAIN_ID)
    assert snip["domain"] == {"name": "Gridz", "version": "1", "chainId": CHAIN_ID, "verifyingContract": RESOLVER}
    assert load_config({}) is None
    cfg = load_config({
        "ONECLAW_AGENT_ID": "a",
        "ONECLAW_AGENT_KEY": "ocv_x",
        "ONECLAW_ADDRESS": hsm.address,
        "ONECLAW_SIGNING_HOST": "https://intents.1claw.xyz",
        "ONECLAW_CHAIN_ID": "8453",
    })
    assert cfg["chain_id"] == 8453 and cfg["signing_host"] == "https://intents.1claw.xyz"
