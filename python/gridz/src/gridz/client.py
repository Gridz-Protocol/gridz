"""High-level HTTP client for the Gridz API. Stdlib-only (urllib) so importing
the client never adds a dependency. Mirrors @gridz/sdk's GridzClient.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any
from urllib.parse import quote


class GridzApiError(Exception):
    def __init__(self, status: int, body: Any) -> None:
        super().__init__(f"Gridz API error {status}")
        self.status = status
        self.body = body


def _enc(s: str) -> str:
    return quote(s, safe="")


class GridzClient:
    def __init__(self, base_url: str) -> None:
        self.base = base_url.rstrip("/")

    def _req(
        self, method: str, path: str, body: Any = None, ok: tuple[int, ...] = (200,)
    ) -> tuple[int, Any]:
        data = json.dumps(body).encode("utf-8") if body is not None else None
        headers = {"content-type": "application/json"} if data is not None else {}
        req = urllib.request.Request(self.base + path, data=data, method=method, headers=headers)
        try:
            with urllib.request.urlopen(req) as resp:  # noqa: S310 (trusted base_url)
                status, text = resp.status, resp.read().decode("utf-8")
        except urllib.error.HTTPError as err:
            status, text = err.code, err.read().decode("utf-8")
        parsed = json.loads(text) if text else None
        if status not in ok:
            raise GridzApiError(status, parsed)
        return status, parsed

    def get_grid(self, subject: str) -> dict[str, Any] | None:
        status, data = self._req("GET", f"/grids/{_enc(subject)}", ok=(200, 404))
        return None if status == 404 else data

    def put_grid(self, grid: dict[str, Any]) -> dict[str, Any]:
        subject = grid["subject"].get("ens") or grid["subject"]["did"]
        _, data = self._req("POST", f"/grids/{_enc(subject)}", grid)
        return data

    def get_cell(self, subject: str, key: str) -> dict[str, Any] | None:
        status, data = self._req("GET", f"/grids/{_enc(subject)}/cells/{_enc(key)}", ok=(200, 404))
        return None if status == 404 else data

    def put_cell(self, subject: str, cell: dict[str, Any]) -> dict[str, Any]:
        _, data = self._req("PUT", f"/grids/{_enc(subject)}/cells/{_enc(cell['key'])}", cell)
        return data

    def delete_cell(self, subject: str, key: str, revocation: dict[str, Any]) -> dict[str, Any]:
        _, data = self._req("DELETE", f"/grids/{_enc(subject)}/cells/{_enc(key)}", revocation)
        return data

    def verify(self, payload: dict[str, Any]) -> Any:
        _, data = self._req("POST", "/verify", payload)
        return data

    def list_sinks(self) -> dict[str, Any]:
        _, data = self._req("GET", "/sinks")
        return data

    def publish(self, sink: str, body: dict[str, Any]) -> dict[str, Any]:
        _, data = self._req("POST", f"/sinks/{_enc(sink)}/publish", body)
        return data

    def get_schema(self, key: str) -> Any | None:
        status, data = self._req("GET", f"/schemas/{_enc(key)}", ok=(200, 404))
        return None if status == 404 else data

    def list_templates(self) -> dict[str, Any]:
        _, data = self._req("GET", "/templates")
        return data

    def get_template(self, name: str) -> Any | None:
        status, data = self._req("GET", f"/templates/{_enc(name)}", ok=(200, 404))
        return None if status == 404 else data
