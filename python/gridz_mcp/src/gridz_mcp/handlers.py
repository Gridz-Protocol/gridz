"""Gridz MCP tool handlers (Python). Mirrors packages/mcp-ts/src/handlers.ts.

The server never signs: cell_prepare_write returns an unsigned EIP-712 payload;
cell_attach_signature stitches in a signature produced by the agent host.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from gridz import SCHEMA_VERSION, grid_id, value_hash, verify_grid, widget_type_hash
from gridz.canonicalize import hash_bytes
from gridz.eip712 import GRIDZ_CELL, gridz_domain
from gridz.util import encode_bundle, iso_z

TEMPLATES_DIR = Path(__file__).resolve().parents[4] / "templates"


class MemoryStore:
    def __init__(self) -> None:
        self._grids: dict[str, dict] = {}

    def get_grid(self, subject: str) -> dict | None:
        return self._grids.get(subject)

    def put_grid(self, subject: str, grid: dict) -> None:
        self._grids[subject] = grid

    def get_cell(self, subject: str, key: str) -> dict | None:
        grid = self._grids.get(subject)
        if not grid:
            return None
        return next((c for c in grid["cells"] if c["key"] == key), None)


def cell_prepare_write(
    *,
    subject_did: str,
    key: str,
    value: Any,
    chain_id: int,
    verifying_contract: str,
    widget_type: str | None = None,
    size: str = "1x1",
    position: dict | None = None,
    nonce: int = 0,
    expires_at: str | None = None,
    oneclaw: dict | None = None,
) -> dict:
    algo = "keccak256"
    gid = grid_id(algo, subject_did, SCHEMA_VERSION)
    vhash = value_hash(algo, value)
    whash = widget_type_hash(algo, widget_type)
    expires = int(datetime.fromisoformat(expires_at.replace("Z", "+00:00")).timestamp()) if expires_at else 0
    domain = gridz_domain(chain_id, verifying_contract)
    prepared: dict[str, Any] = {
        "typed_data": {
            "domain": domain,
            "types": {"GridzCell": GRIDZ_CELL},
            "primaryType": "GridzCell",
            "message": {
                "gridId": gid,
                "key": key,
                "valueHashHex": vhash,
                "widgetTypeHash": whash,
                "expiresAt": str(expires),
                "nonce": str(int(nonce)),
            },
        },
        "cell_meta": {
            "key": key,
            "value": value,
            **({"widget_type": widget_type} if widget_type else {}),
            "size": size,
            "position": position or {"x": 0, "y": 0, "w": 1, "h": 1},
        },
        "value_hash": vhash,
    }
    if oneclaw:
        prepared["next_action"] = {
            "next_action": "sign_typed_data",
            "server": "1claw",
            "args": {"agent_id": oneclaw["agent_id"], "typed_data": prepared["typed_data"]},
        }
    return prepared


def cell_attach_signature(*, prepared: dict, signature: str, attester: str, now: datetime | None = None) -> dict:
    m = prepared["typed_data"]["message"]
    serialized = {
        "gridId": m["gridId"],
        "key": m["key"],
        "valueHashHex": m["valueHashHex"],
        "widgetTypeHash": m["widgetTypeHash"],
        "expiresAt": str(int(m["expiresAt"])),
        "nonce": str(int(m["nonce"])),
    }
    payload = encode_bundle(
        {
            "kind": "eip712",
            "domain": prepared["typed_data"]["domain"],
            "types": {"GridzCell": GRIDZ_CELL},
            "primaryType": "GridzCell",
            "message": serialized,
            "signature": signature,
        }
    )
    uid = hash_bytes("keccak256", bytes.fromhex(signature[2:]))
    ts = now or datetime.now(timezone.utc)
    att = {
        "format": "eip712-raw",
        "uid": uid,
        "uri": f"data://inline/{uid}",
        "attester": attester,
        "iat": iso_z(ts),
        "value_hash": m["valueHashHex"],
        "payload": payload,
    }
    if int(m["expiresAt"]) > 0:
        att["exp"] = iso_z(datetime.fromtimestamp(int(m["expiresAt"]), tz=timezone.utc))
    meta = prepared["cell_meta"]
    cell = {
        "id": f"cell-{meta['key']}",
        "key": meta["key"],
        "value": meta["value"],
        "position": meta["position"],
        "size": meta["size"],
        "is_visible": True,
        "attestation": att,
    }
    if meta.get("widget_type"):
        cell["widget_type"] = meta["widget_type"]
    return cell


def grid_verify(grid: dict) -> dict:
    return verify_grid(grid)


def sink_publish(store: MemoryStore, *, subject: str, sink: str, cell_ids: list[str] | None = None) -> dict:
    if sink != "memory":
        return {"ok": False, "error": "only the in-process memory sink is publishable from the MCP server"}
    grid = store.get_grid(subject)
    if not grid:
        return {"ok": False, "error": "grid_not_found"}
    cells = [c for c in grid["cells"] if not cell_ids or c["id"] in cell_ids]
    return {"ok": True, "results": [{"cell_id": c["id"], "sink_id": "memory"} for c in cells]}


_SUGGESTIONS = [
    ("github", "com.github"),
    ("twitter", "com.twitter"),
    ("telegram", "org.telegram"),
    ("discord", "com.discord"),
    ("farcaster", "xyz.farcaster"),
    ("bluesky", "social.bsky"),
    ("poll", "gridz.poll"),
    ("weather", "gridz.weather"),
    ("clock", "gridz.clock"),
    ("website", "url"),
    ("bio", "description"),
    ("display name", "alias"),
    ("mcp", "agent-endpoint[mcp]"),
    ("context", "agent-context"),
]
_KNOWN = {k for _, k in _SUGGESTIONS}


def schema_suggest_key(description: str) -> dict:
    d = description.lower()
    for kw, key in _SUGGESTIONS:
        if kw in d:
            return {"suggested_key": key, **({"existing": key} if key in _KNOWN else {})}
    slug = "".join(ch if ch.isalnum() else "." for ch in d).strip(".") or "custom"
    return {"suggested_key": f"gridz.{slug}"}


def _load_template(name: str) -> dict | None:
    path = TEMPLATES_DIR / name / "gridz.yaml"
    if not path.exists():
        return None
    return yaml.safe_load(path.read_text())


def bootstrap_list_templates() -> list[dict]:
    out = []
    for d in sorted(TEMPLATES_DIR.iterdir()) if TEMPLATES_DIR.exists() else []:
        cfg = _load_template(d.name)
        if cfg:
            out.append({"name": d.name, "subject_type": cfg["subject"]["type"], "cells": len(cfg["cells"])})
    return out


def bootstrap_from_template(name: str) -> dict:
    cfg = _load_template(name)
    return cfg if cfg else {"error": "unknown_template"}


def identity_list_signers() -> dict:
    return {"signers": [], "note": "Gridz never custodies keys; configure a signer in your client."}
