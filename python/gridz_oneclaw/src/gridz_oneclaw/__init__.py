"""Optional 1claw HSM adapter (Python). Mirrors @gridz/oneclaw.

HSM-backed EIP-712 signing via 1claw's unified sign endpoint. Verification is
byte-identical to a local signer — `format()` reports eip712-oneclaw as provenance
only, never as a trust assumption.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any, Callable

DEFAULT_API_BASE = "https://api.1claw.xyz"

# transport(method, url, headers, body) -> (status, json)
Transport = Callable[[str, str, dict, "dict | None"], "tuple[int, dict]"]


class OneClawError(Exception):
    def __init__(self, message: str, code: str, hint: str | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.hint = hint


def _urllib_transport(method: str, url: str, headers: dict, body: dict | None) -> tuple[int, dict]:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:  # noqa: S310
            return resp.status, json.loads(resp.read().decode() or "{}")
    except urllib.error.HTTPError as err:
        return err.code, json.loads(err.read().decode() or "{}")


def _serialize_message(message: dict) -> dict:
    out = {}
    for k, v in message.items():
        if isinstance(v, bytes):
            out[k] = "0x" + v.hex()
        elif isinstance(v, int) and not isinstance(v, bool):
            out[k] = str(v)
        else:
            out[k] = v
    return out


EIP712_DOMAIN_TYPE = [
    {"name": "name", "type": "string"},
    {"name": "version", "type": "string"},
    {"name": "chainId", "type": "uint256"},
    {"name": "verifyingContract", "type": "address"},
]


class OneClawSigner:
    """The third first-class signer alongside local wallets and WebAuthn."""

    def __init__(self, config: dict, transport: Transport = _urllib_transport) -> None:
        self.config = config
        self._base = (config.get("signing_host") or config.get("api_base") or DEFAULT_API_BASE).rstrip("/")
        self._transport = transport

    def format(self) -> str:
        return "eip712-oneclaw"

    def did(self) -> str:
        return f"did:pkh:eip155:{self.config['chain_id']}:{self.config['address'].lower()}"

    def _sign(self, intent: dict) -> dict:
        status, body = self._transport(
            "POST",
            f"{self._base}/v1/agents/{self.config['agent_id']}/sign",
            {"content-type": "application/json", "authorization": f"Bearer {self.config['api_key']}"},
            intent,
        )
        if status < 200 or status >= 300:
            msg = str(body.get("error") or body.get("message") or f"1claw sign failed ({status})")
            if status == 403 or "allowlist" in msg.lower() or "domain" in msg.lower():
                raise OneClawError(
                    msg,
                    "eip712_domain_allowlist",
                    "Add the Gridz EIP-712 domain to this agent's eip712_domain_allowlist on dashboard.1claw.xyz.",
                )
            raise OneClawError(msg, "sign_failed")
        return body

    def sign_typed_data(self, domain: dict, types: dict, primary_type: str, message: dict) -> tuple[str, str]:
        body = self._sign(
            {
                "intent_type": "typed_data",
                "typed_data": {
                    "domain": domain,
                    "types": {"EIP712Domain": EIP712_DOMAIN_TYPE, **types},
                    "primaryType": primary_type,
                    "message": _serialize_message(message),
                },
            }
        )
        return body["signature"], body.get("from", self.config["address"])

    def sign_message(self, message: str | bytes) -> str:
        raw = message.encode() if isinstance(message, str) else message
        body = self._sign({"intent_type": "personal_sign", "message": "0x" + raw.hex()})
        return body["signature"]


class OneClawKeyProvisioner:
    def __init__(self, config: dict, transport: Transport = _urllib_transport) -> None:
        self.config = config
        self._base = (config.get("api_base") or DEFAULT_API_BASE).rstrip("/")
        self._transport = transport

    def provision(self, chain: str) -> dict:
        status, body = self._transport(
            "POST",
            f"{self._base}/v1/agents/{self.config['agent_id']}/signing-keys",
            {"content-type": "application/json", "authorization": f"Bearer {self.config['api_key']}"},
            {"chain": chain},
        )
        if status < 200 or status >= 300:
            raise OneClawError(str(body.get("error") or "provision failed"), "provision_failed")
        return {"address": body["address"], "public_key": body["public_key"]}


class OneClawResolver:
    """Resolve oneclaw://vault/<vaultId>/<path> to a short-lived secret (cached in-process)."""

    def __init__(self, config: dict, transport: Transport = _urllib_transport) -> None:
        self.config = config
        self._base = (config.get("api_base") or DEFAULT_API_BASE).rstrip("/")
        self._transport = transport
        self._cache: dict[str, str] = {}

    @staticmethod
    def is_oneclaw_uri(uri: str) -> bool:
        return uri.startswith("oneclaw://vault/")

    def resolve(self, uri: str) -> str:
        import re

        m = re.match(r"^oneclaw://vault/([^/]+)/(.+)$", uri)
        if not m:
            raise OneClawError(f"not a oneclaw vault URI: {uri}", "bad_uri")
        if uri in self._cache:
            return self._cache[uri]
        vault_id, path = m.group(1), m.group(2)
        status, body = self._transport(
            "GET",
            f"{self._base}/v1/vaults/{vault_id}/secrets/{path}",
            {"authorization": f"Bearer {self.config['api_key']}"},
            None,
        )
        if status < 200 or status >= 300:
            raise OneClawError(str(body.get("error") or "secret fetch failed"), "secret_failed")
        secret = str(body.get("value") or body.get("secret"))
        self._cache[uri] = secret
        return secret


def eip712_domain_allowlist_snippet(verifying_contract: str, chain_id: int) -> dict:
    domain = {"name": "Gridz", "version": "1", "chainId": chain_id, "verifyingContract": verifying_contract}
    return {
        "domain": domain,
        "instructions": "On dashboard.1claw.xyz → your agent → EIP-712 domain allowlist, add this entry, then continue:",
        "json": json.dumps(domain, indent=2),
    }


def load_config(env: dict[str, str]) -> dict | None:
    agent_id = env.get("ONECLAW_AGENT_ID")
    api_key = env.get("ONECLAW_AGENT_KEY") or env.get("GRIDZ_ONECLAW_API_KEY")
    address = env.get("ONECLAW_ADDRESS")
    if not (agent_id and api_key and address):
        return None
    cfg = {
        "agent_id": agent_id,
        "api_key": api_key,
        "address": address,
        "chain_id": int(env.get("ONECLAW_CHAIN_ID", "11155111")),
        "api_base": env.get("ONECLAW_API_BASE", DEFAULT_API_BASE),
    }
    if env.get("ONECLAW_SIGNING_HOST"):
        cfg["signing_host"] = env["ONECLAW_SIGNING_HOST"]
    return cfg


__all__ = [
    "OneClawError",
    "OneClawSigner",
    "OneClawKeyProvisioner",
    "OneClawResolver",
    "eip712_domain_allowlist_snippet",
    "load_config",
    "DEFAULT_API_BASE",
]
