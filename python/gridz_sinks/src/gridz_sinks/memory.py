"""In-memory reference sink."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


class MemorySink:
    name = "memory"
    capabilities = {"read": True, "write": True, "delete": True, "project": False, "enumerate": True}

    def __init__(self) -> None:
        self._store: dict[tuple[str, str], dict] = {}
        self._by_id: dict[str, tuple[str, str]] = {}

    def health(self) -> dict[str, Any]:
        return {"ok": True, "latency_ms": 0}

    def write(self, cells: list[dict], subject: dict) -> list[dict]:
        now = datetime.now(timezone.utc).isoformat()
        out = []
        for cell in cells:
            k = (subject["did"], cell["key"])
            self._store[k] = cell
            self._by_id[cell["id"]] = k
            out.append({"cell_id": cell["id"], "sink_id": self.name, "written_at": now, "sink_native_uri": f"memory://{subject['did']}/{cell['key']}"})
        return out

    def read(self, subject: str, keys: list[str] | None = None) -> list[dict]:
        return [
            cell
            for (did, key), cell in self._store.items()
            if did == subject and (keys is None or key in keys)
        ]

    def delete(self, ids: list[str]) -> None:
        for cid in ids:
            k = self._by_id.pop(cid, None)
            if k:
                self._store.pop(k, None)
