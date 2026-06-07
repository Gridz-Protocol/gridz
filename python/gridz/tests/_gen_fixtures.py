"""Writes Python-signed grids to tests/cross-runtime/fixtures/py-*.json so the
TypeScript lane can verify the reverse direction. Run:

    uv run python tests/_gen_fixtures.py
"""

from __future__ import annotations

import json
from pathlib import Path

from gridz import build_grid
from data import (  # type: ignore[import-not-found]
    CHAIN_ID,
    NOW,
    POS,
    RESOLVER,
    THEME,
    example_ed25519_signer,
    example_eip712_signer,
)

OUT = Path(__file__).resolve().parents[3] / "tests" / "cross-runtime" / "fixtures"


def main() -> None:
    eip712 = example_eip712_signer()
    eip_grid = build_grid(
        eip712,
        subject={"type": "human", "did": eip712.did()},
        theme=THEME,
        chain_id=CHAIN_ID,
        verifying_contract=RESOLVER,
        now=NOW,
        cells=[
            {"id": "c1", "key": "alias", "value": "gridz-example", "position": POS, "size": "1x1"},
            {"id": "c2", "key": "url", "value": "https://gridz.dev", "position": POS, "size": "1x1"},
        ],
    )
    (OUT / "py-eip712-grid.json").write_text(json.dumps(eip_grid, indent=2) + "\n")

    ed = example_ed25519_signer()
    ed_grid = build_grid(
        ed,
        subject={"type": "agent", "did": ed.did()},
        theme=THEME,
        now=NOW,
        cells=[
            {"id": "a1", "key": "agent-context", "value": "example agent context", "position": POS, "size": "1x1"},
        ],
    )
    (OUT / "py-ed25519-grid.json").write_text(json.dumps(ed_grid, indent=2) + "\n")
    print("wrote py-eip712-grid.json, py-ed25519-grid.json")


if __name__ == "__main__":
    main()
