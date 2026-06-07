"""base64url (no pad), bundle (de)serialization, and ISO timestamps."""

from __future__ import annotations

import base64
import json
from datetime import datetime, timezone
from typing import Any


def b64u_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def b64u_decode(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def encode_bundle(bundle: dict[str, Any]) -> str:
    return b64u_encode(json.dumps(bundle, separators=(",", ":")).encode("utf-8"))


def decode_bundle(payload: str) -> dict[str, Any]:
    return json.loads(b64u_decode(payload).decode("utf-8"))


def iso_z(dt: datetime) -> str:
    """Format as YYYY-MM-DDTHH:MM:SS.mmmZ (matches JS Date.toISOString())."""
    dt = dt.astimezone(timezone.utc)
    return f"{dt:%Y-%m-%dT%H:%M:%S}.{dt.microsecond // 1000:03d}Z"


def parse_iso(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))
