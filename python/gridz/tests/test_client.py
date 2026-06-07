"""Unit tests for GridzClient against a stdlib fake server (no Node needed)."""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urlparse

import pytest

from gridz import GridzApiError, GridzClient


class _Handler(BaseHTTPRequestHandler):
    store: dict[str, dict] = {}

    def log_message(self, *args):  # silence
        pass

    def _send(self, status: int, body) -> None:
        payload = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _read(self):
        length = int(self.headers.get("content-length", 0))
        return json.loads(self.rfile.read(length)) if length else None

    def _parts(self):
        return [unquote(p) for p in urlparse(self.path).path.strip("/").split("/")]

    def do_GET(self):
        p = self._parts()
        if p == ["sinks"]:
            return self._send(200, {"sinks": [{"name": "memory", "capabilities": {}}]})
        if p == ["templates"]:
            return self._send(200, {"templates": [{"name": "minimal", "keys": ["alias"]}]})
        if p[:1] == ["templates"]:
            return self._send(200, {"name": p[1]}) if p[1] == "minimal" else self._send(404, {})
        if p[:1] == ["schemas"]:
            return self._send(200, {"source": "ensip-18"}) if p[1] == "alias" else self._send(404, {})
        if len(p) == 4 and p[0] == "grids" and p[2] == "cells":
            grid = self.store.get(p[1])
            cell = next((c for c in (grid or {}).get("cells", []) if c["key"] == p[3]), None)
            return self._send(200, cell) if cell else self._send(404, {})
        if len(p) == 2 and p[0] == "grids":
            grid = self.store.get(p[1])
            return self._send(200, grid) if grid else self._send(404, {})
        return self._send(404, {})

    def do_POST(self):
        p, body = self._parts(), self._read()
        if len(p) == 2 and p[0] == "grids":
            self.store[p[1]] = body
            return self._send(200, {"ok": True, "verify": {"ok": True}})
        if p == ["verify"]:
            return self._send(200, {"ok": True})
        if len(p) == 3 and p[0] == "sinks" and p[2] == "publish":
            return self._send(200, {"ok": True, "results": [{"cell_id": "c1"}]})
        return self._send(404, {})

    def do_PUT(self):
        p, body = self._parts(), self._read()
        grid = self.store.setdefault(p[1], {"cells": []})
        grid["cells"] = [c for c in grid["cells"] if c["key"] != p[3]] + [body]
        return self._send(200, {"ok": True, "result": {"ok": True}})

    def do_DELETE(self):
        p = self._parts()
        self._read()
        grid = self.store.get(p[1], {"cells": []})
        grid["cells"] = [c for c in grid["cells"] if c["key"] != p[3]]
        return self._send(200, {"ok": True, "deleted": True})


@pytest.fixture(scope="module")
def base_url():
    _Handler.store = {}
    server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()


def test_full_client_surface(base_url):
    client = GridzClient(base_url)
    did = "did:pkh:eip155:1:0xabc"
    grid = {"subject": {"type": "human", "did": did}, "cells": [{"key": "alias", "value": "a"}]}

    assert client.put_grid(grid)["ok"] is True
    assert client.get_grid(did)["subject"]["did"] == did
    assert client.get_grid("did:web:absent") is None

    client.put_cell(did, {"key": "url", "value": "https://gridz.dev"})
    assert client.get_cell(did, "url")["value"] == "https://gridz.dev"
    assert client.get_cell(did, "missing") is None

    assert client.delete_cell(did, "url", {"attestation": {}, "value": {"revoke": "url"}})["deleted"] is True
    assert client.get_cell(did, "url") is None

    assert client.verify({"grid": grid})["ok"] is True
    assert any(s["name"] == "memory" for s in client.list_sinks()["sinks"])
    assert client.publish("memory", {"subject": did})["results"]
    assert client.get_schema("alias")["source"] == "ensip-18"
    assert client.get_schema("unknown") is None
    assert client.list_templates()["templates"][0]["name"] == "minimal"
    assert client.get_template("minimal")["name"] == "minimal"
    assert client.get_template("nope") is None


def test_api_error(base_url):
    # A path the fake server 404s on a POST raises GridzApiError.
    with pytest.raises(GridzApiError) as exc:
        GridzClient(base_url)._req("POST", "/nonexistent", {"x": 1})
    assert exc.value.status == 404
