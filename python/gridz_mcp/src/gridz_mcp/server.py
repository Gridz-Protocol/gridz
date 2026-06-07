"""Gridz MCP server (Python, jlowin/fastmcp). Same tool surface as @gridz/mcp."""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from . import handlers as h

_store = h.MemoryStore()
mcp = FastMCP("gridz")


@mcp.tool
def grid_read(subject: str) -> dict | None:
    """Read a Grid by subject (DID or ENS)."""
    return _store.get_grid(subject)


@mcp.tool
def grid_verify(grid: dict) -> dict:
    """Verify a Grid; returns per-cell and root status."""
    return h.grid_verify(grid)


@mcp.tool
def cell_read(subject: str, key: str) -> dict | None:
    """Read a single cell by subject + key."""
    return _store.get_cell(subject, key)


@mcp.tool
def cell_prepare_write(
    subject_did: str,
    key: str,
    value: Any,
    chain_id: int,
    verifying_contract: str,
    widget_type: str | None = None,
    size: str = "1x1",
    nonce: int = 0,
    expires_at: str | None = None,
) -> dict:
    """Prepare an unsigned EIP-712 payload for a cell. Signing is client-side."""
    return h.cell_prepare_write(
        subject_did=subject_did,
        key=key,
        value=value,
        chain_id=chain_id,
        verifying_contract=verifying_contract,
        widget_type=widget_type,
        size=size,
        nonce=nonce,
        expires_at=expires_at,
    )


@mcp.tool
def cell_attach_signature(prepared: dict, signature: str, attester: str) -> dict:
    """Attach a detached signature to a prepared payload, yielding a verifiable cell."""
    return h.cell_attach_signature(prepared=prepared, signature=signature, attester=attester)


@mcp.tool
def sink_publish(subject: str, sink: str, cell_ids: list[str] | None = None) -> dict:
    """Publish a stored grid's cells to a sink (memory only server-side)."""
    return h.sink_publish(_store, subject=subject, sink=sink, cell_ids=cell_ids)


@mcp.tool
def schema_suggest_key(description: str) -> dict:
    """Suggest a standard key for a free-text field description."""
    return h.schema_suggest_key(description)


@mcp.tool
def identity_list_signers() -> dict:
    """List server-side signers (always empty — no key custody)."""
    return h.identity_list_signers()


@mcp.tool
def bootstrap_list_templates() -> list[dict]:
    """List bootstrap templates (shape only)."""
    return h.bootstrap_list_templates()


@mcp.tool
def bootstrap_from_template(template_name: str) -> dict:
    """Return a template's config draft (shape only)."""
    return h.bootstrap_from_template(template_name)


@mcp.resource("grid://{subject}")
def grid_resource(subject: str) -> dict | None:
    return _store.get_grid(subject)


@mcp.resource("grid-cell://{subject}/{key}")
def grid_cell_resource(subject: str, key: str) -> dict | None:
    return _store.get_cell(subject, key)


@mcp.resource("bootstrap-template://{name}")
def template_resource(name: str) -> dict:
    return h.bootstrap_from_template(name)


@mcp.prompt
def compose_profile(subject_type: str) -> str:
    """Draft a starter Grid for a subject. Asks before inventing any value."""
    return (
        f"You are composing a Gridz profile for a {subject_type}. Offer field SHAPE suggestions only. "
        "Do NOT invent values (names, bios, links). Ask the operator for each value and confirm before writing."
    )


@mcp.prompt
def verify_and_explain(subject: str) -> str:
    """Verify a Grid and explain failures in plain English."""
    return f"Read grid://{subject}, call grid_verify, and explain each cell's status plainly."


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
