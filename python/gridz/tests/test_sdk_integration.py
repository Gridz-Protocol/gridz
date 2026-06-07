"""Cross-language integration: Python SDK ↔ the TypeScript Fastify server.

Launches the built Node server as a subprocess. Skipped (not faked) when the
server isn't built or `node` is unavailable — run `pnpm --filter @gridz/server
build` first. This proves a grid signed by Python `gridz` verifies inside the TS
server and round-trips through the HTTP surface.
"""

from __future__ import annotations

import os
import shutil
import socket
import subprocess
import time
import urllib.request
from pathlib import Path

import pytest

from gridz import GridzClient, build_grid
from .data import CHAIN_ID, NOW, POS, RESOLVER, THEME, example_eip712_signer

REPO_ROOT = Path(__file__).resolve().parents[3]
SERVER_JS = REPO_ROOT / "packages" / "server" / "dist" / "server.js"


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def server() -> str:
    if not SERVER_JS.exists():
        pytest.skip("server not built; run `pnpm --filter @gridz/server build`")
    if shutil.which("node") is None:
        pytest.skip("node not on PATH")

    port = _free_port()
    proc = subprocess.Popen(
        ["node", str(SERVER_JS)],
        env={**os.environ, "PORT": str(port), "HOST": "127.0.0.1"},
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    base = f"http://127.0.0.1:{port}"
    try:
        for _ in range(50):
            try:
                urllib.request.urlopen(base + "/healthz", timeout=0.2)
                break
            except Exception:
                time.sleep(0.1)
        else:
            pytest.skip("server did not become ready")
        yield base
    finally:
        proc.terminate()
        proc.wait(timeout=5)


def test_python_grid_round_trips_through_ts_server(server: str) -> None:
    signer = example_eip712_signer()
    did = signer.did()
    grid = build_grid(
        signer,
        subject={"type": "human", "did": did},
        theme=THEME,
        chain_id=CHAIN_ID,
        verifying_contract=RESOLVER,
        now=NOW,
        cells=[{"id": "c1", "key": "alias", "value": "gridz-example", "position": POS, "size": "1x1"}],
    )

    client = GridzClient(server)
    put = client.put_grid(grid)
    assert put["ok"] is True and put["verify"]["ok"] is True

    got = client.get_grid(did)
    assert got["subject"]["did"] == did

    assert client.verify({"grid": grid})["ok"] is True
    assert client.publish("memory", {"subject": did})["results"]
