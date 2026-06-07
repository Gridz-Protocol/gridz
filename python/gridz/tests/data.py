"""Shared deterministic, seed-derived test constants. No mock data."""

from __future__ import annotations

from datetime import datetime, timezone

from gridz import Ed25519Signer, LocalEip712Signer, hash_utf8

CHAIN_ID = 11155111
RESOLVER = "0x000000000000000000000000000000000000c0de"
NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)

THEME = {
    "background_type": "solid",
    "background_value": "#0b0b0f",
    "accent_color": "#7c5cff",
    "text_color": "#f4f4f5",
    "card_style": "rounded",
    "card_background": "#16161c",
    "font_family": "sans",
    "show_gridz_badge": True,
}

POS = {"x": 0, "y": 0, "w": 1, "h": 1}


def hex_to_bytes(h: str) -> bytes:
    return bytes.fromhex(h[2:])


def example_eip712_signer() -> LocalEip712Signer:
    return LocalEip712Signer(hash_utf8("keccak256", "gridz/__example__/signer/1"), CHAIN_ID)


def example_ed25519_signer() -> Ed25519Signer:
    return Ed25519Signer(hex_to_bytes(hash_utf8("sha256", "gridz/__example__/ed/1")))
