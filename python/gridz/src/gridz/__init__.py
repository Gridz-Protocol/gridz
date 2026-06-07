"""Gridz core (Python) — cross-runtime compatible with @gridz/core.

A Grid signed in TypeScript verifies here and vice versa.
"""

from __future__ import annotations

from .canonicalize import hash_bytes, hash_jcs, hash_utf8, jcs
from .hashing import (
    SCHEMA_VERSION,
    algo_for_format,
    grid_id,
    value_hash,
    widget_type_hash,
)
from .merkle import ZERO32, merkle_root, normalize_leaf
from .eip712 import (
    EAS_SCHEMAS,
    EIP712_DOMAIN_TYPE,
    GRIDZ_CELL,
    GRIDZ_ROOT,
    PRIMARY_TYPE_CELL,
    PRIMARY_TYPE_ROOT,
    gridz_domain,
)
from .signer import (
    Ed25519Signer,
    LocalEip712Signer,
    public_key_from_did_key,
    verify_ed25519,
)
from .attest import build_cell_attestation, build_root_attestation
from .grid import build_grid
from .verify import verify_attestation, verify_cell, verify_grid

__all__ = [
    "jcs",
    "hash_bytes",
    "hash_utf8",
    "hash_jcs",
    "SCHEMA_VERSION",
    "algo_for_format",
    "value_hash",
    "grid_id",
    "widget_type_hash",
    "merkle_root",
    "normalize_leaf",
    "ZERO32",
    "gridz_domain",
    "GRIDZ_CELL",
    "GRIDZ_ROOT",
    "EIP712_DOMAIN_TYPE",
    "PRIMARY_TYPE_CELL",
    "PRIMARY_TYPE_ROOT",
    "EAS_SCHEMAS",
    "LocalEip712Signer",
    "Ed25519Signer",
    "public_key_from_did_key",
    "verify_ed25519",
    "build_cell_attestation",
    "build_root_attestation",
    "build_grid",
    "verify_attestation",
    "verify_cell",
    "verify_grid",
]
