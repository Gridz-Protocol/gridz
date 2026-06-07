"""High-level Grid builder. Mirrors packages/core-ts/src/grid.ts."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from .attest import build_cell_attestation, build_root_attestation
from .hashing import SCHEMA_VERSION, algo_for_format
from .merkle import merkle_root


def build_grid(
    signer: Any,
    *,
    subject: dict[str, Any],
    theme: dict[str, Any],
    cells: list[dict[str, Any]],
    chain_id: int | None = None,
    verifying_contract: str | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    subject_did = subject["did"]
    algo = algo_for_format(signer.format())

    out_cells: list[dict[str, Any]] = []
    for d in cells:
        attestation = build_cell_attestation(
            signer,
            subject_did=subject_did,
            key=d["key"],
            value=d["value"],
            widget_type=d.get("widget_type"),
            expires_at=d.get("expires_at"),
            nonce=d.get("nonce", 0),
            chain_id=chain_id,
            verifying_contract=verifying_contract,
            now=now,
        )
        cell: dict[str, Any] = {
            "id": d["id"],
            "key": d["key"],
            "value": d["value"],
            "position": d["position"],
            "size": d["size"],
            "is_visible": d.get("is_visible", True),
            "attestation": attestation,
        }
        if d.get("widget_type"):
            cell["widget_type"] = d["widget_type"]
        if d.get("expires_at"):
            cell["expires_at"] = attestation["exp"]
        out_cells.append(cell)

    root = merkle_root(algo, [c["attestation"]["uid"] for c in out_cells])
    root_attestation = build_root_attestation(
        signer,
        subject_did=subject_did,
        merkle_root=root,
        cell_count=len(out_cells),
        chain_id=chain_id,
        verifying_contract=verifying_contract,
        now=now,
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "subject": subject,
        "theme": theme,
        "cells": out_cells,
        "root_attestation": root_attestation,
    }
