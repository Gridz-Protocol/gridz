"""SQLite sink (stdlib sqlite3). Real and offline-testable — the reference SQL
projection, mirroring @gridz/sinks SqliteCellStore."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from typing import Any


class SqliteSink:
    name = "sqlite"
    capabilities = {"read": True, "write": True, "delete": True, "project": False, "enumerate": True}

    def __init__(self, path: str = ":memory:") -> None:
        self._db = sqlite3.connect(path)
        self._db.execute(
            """CREATE TABLE IF NOT EXISTS gridz_cells (
                 subject TEXT NOT NULL, key TEXT NOT NULL, id TEXT NOT NULL,
                 value_hash TEXT NOT NULL, cell_json TEXT NOT NULL, written_at TEXT NOT NULL,
                 PRIMARY KEY (subject, key))"""
        )
        self._db.execute("CREATE INDEX IF NOT EXISTS gridz_cells_key ON gridz_cells (key)")
        self._db.commit()

    def health(self) -> dict[str, Any]:
        ok = self._db.execute("SELECT 1").fetchone() is not None
        return {"ok": ok, "latency_ms": 0}

    def write(self, cells: list[dict], subject: dict) -> list[dict]:
        now = datetime.now(timezone.utc).isoformat()
        out = []
        for cell in cells:
            self._db.execute(
                """INSERT INTO gridz_cells (subject, key, id, value_hash, cell_json, written_at)
                   VALUES (?, ?, ?, ?, ?, ?)
                   ON CONFLICT(subject, key) DO UPDATE SET
                     id=excluded.id, value_hash=excluded.value_hash,
                     cell_json=excluded.cell_json, written_at=excluded.written_at""",
                (subject["did"], cell["key"], cell["id"], cell["attestation"]["value_hash"], json.dumps(cell), now),
            )
            out.append(
                {
                    "cell_id": cell["id"],
                    "sink_id": self.name,
                    "written_at": now,
                    "sink_native_uri": f"sqlite://gridz_cells/{subject['did']}/{cell['key']}",
                }
            )
        self._db.commit()
        return out

    def read(self, subject: str, keys: list[str] | None = None) -> list[dict]:
        if keys:
            placeholders = ",".join("?" for _ in keys)
            rows = self._db.execute(
                f"SELECT cell_json FROM gridz_cells WHERE subject=? AND key IN ({placeholders})",
                (subject, *keys),
            ).fetchall()
        else:
            rows = self._db.execute("SELECT cell_json FROM gridz_cells WHERE subject=?", (subject,)).fetchall()
        return [json.loads(r[0]) for r in rows]

    def delete(self, ids: list[str]) -> None:
        if not ids:
            return
        placeholders = ",".join("?" for _ in ids)
        self._db.execute(f"DELETE FROM gridz_cells WHERE id IN ({placeholders})", tuple(ids))
        self._db.commit()
