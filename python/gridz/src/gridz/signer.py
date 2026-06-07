"""Signers: LocalEip712Signer (did:pkh) and Ed25519Signer (did:key/JWS).

Mirrors packages/core-ts/src/signer.ts. Gridz never custodies a private key.
"""

from __future__ import annotations

from typing import Any

import base58
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from eth_account import Account
from eth_account.messages import encode_typed_data

from .eip712 import EIP712_DOMAIN_TYPE
from .util import b64u_encode

_MULTICODEC_ED25519 = bytes([0xED, 0x01])


class LocalEip712Signer:
    """secp256k1 signer producing did:pkh:eip155 identities."""

    def __init__(self, private_key_hex: str, chain_id: int) -> None:
        self._acct = Account.from_key(private_key_hex)
        self.chain_id = chain_id

    @property
    def address(self) -> str:
        return self._acct.address

    def did(self) -> str:
        return f"did:pkh:eip155:{self.chain_id}:{self._acct.address.lower()}"

    def sign_typed_data(
        self,
        domain: dict[str, Any],
        types: dict[str, list[dict[str, str]]],
        primary_type: str,
        message: dict[str, Any],
    ) -> tuple[str, str]:
        full = {
            "types": {**types, "EIP712Domain": EIP712_DOMAIN_TYPE},
            "domain": domain,
            "primaryType": primary_type,
            "message": message,
        }
        signable = encode_typed_data(full_message=full)
        signed = self._acct.sign_message(signable)
        return "0x" + bytes(signed.signature).hex(), self._acct.address

    def format(self) -> str:
        return "eip712-raw"


class Ed25519Signer:
    """Ed25519 signer producing did:key identities and compact JWS (EdDSA)."""

    def __init__(self, seed: bytes) -> None:
        if len(seed) != 32:
            raise ValueError("ed25519 seed must be 32 bytes")
        self._sk = Ed25519PrivateKey.from_private_bytes(seed)

    @property
    def public_key(self) -> bytes:
        return self._sk.public_key().public_bytes_raw()

    def did(self) -> str:
        return "did:key:z" + base58.b58encode(_MULTICODEC_ED25519 + self.public_key).decode("ascii")

    def sign_jws(self, claims: dict[str, Any]) -> str:
        import json

        header = {"alg": "EdDSA", "typ": "JWT", "kid": self.did()}
        enc = lambda o: b64u_encode(json.dumps(o, separators=(",", ":")).encode("utf-8"))
        signing_input = f"{enc(header)}.{enc(claims)}"
        sig = self._sk.sign(signing_input.encode("utf-8"))
        return f"{signing_input}.{b64u_encode(sig)}"

    def format(self) -> str:
        return "jws-ed25519"


def public_key_from_did_key(did: str) -> bytes:
    if not did.startswith("did:key:z"):
        raise ValueError(f"not a did:key: {did}")
    decoded = base58.b58decode(did[len("did:key:z") :])
    if decoded[0] != 0xED or decoded[1] != 0x01:
        raise ValueError("did:key is not ed25519 (expected 0xed01 multicodec)")
    return decoded[2:]


def verify_ed25519(public_key: bytes, message: bytes, signature: bytes) -> bool:
    try:
        Ed25519PublicKey.from_public_bytes(public_key).verify(signature, message)
        return True
    except Exception:
        return False
