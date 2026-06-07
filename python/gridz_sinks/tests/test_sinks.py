"""Round-trip both sinks with real attestations; cells must still verify."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from gridz import Ed25519Signer, build_grid, hash_utf8, verify_cell
from gridz_sinks import MemorySink, SqliteSink

NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)
THEME = {
    "background_type": "solid",
    "background_value": "#000",
    "accent_color": "#fff",
    "text_color": "#fff",
    "card_style": "rounded",
    "card_background": "#111",
    "font_family": "mono",
}


def _probe_grid() -> dict:
    seed = bytes.fromhex(hash_utf8("sha256", "gridz/__probe__/pysink")[2:])
    signer = Ed25519Signer(seed)
    return build_grid(
        signer,
        subject={"type": "agent", "did": signer.did()},
        theme=THEME,
        now=NOW,
        cells=[
            {"id": "p1", "key": "gridz.__probe__", "value": {"n": 1}, "position": {"x": 0, "y": 0, "w": 1, "h": 1}, "size": "1x1"},
            {"id": "p2", "key": "alias", "value": "probe", "position": {"x": 1, "y": 0, "w": 1, "h": 1}, "size": "1x1"},
        ],
    )


@pytest.mark.parametrize("make_sink", [MemorySink, SqliteSink])
def test_round_trip(make_sink):
    grid = _probe_grid()
    subject = grid["subject"]
    sink = make_sink()

    assert sink.health()["ok"]
    results = sink.write(grid["cells"], subject)
    assert len(results) == len(grid["cells"])

    read = sink.read(subject["did"])
    assert len(read) == len(grid["cells"])
    for cell in read:
        assert verify_cell(cell, {"subject_did": subject["did"], "now": NOW})["ok"]

    subset = sink.read(subject["did"], ["alias"])
    assert [c["key"] for c in subset] == ["alias"]

    sink.delete([grid["cells"][0]["id"]])
    assert len(sink.read(subject["did"])) == len(grid["cells"]) - 1


def test_sqlite_upsert_no_duplicates():
    grid = _probe_grid()
    sink = SqliteSink()
    sink.write(grid["cells"], grid["subject"])
    sink.write(grid["cells"], grid["subject"])  # re-write
    assert len(sink.read(grid["subject"]["did"])) == len(grid["cells"])
