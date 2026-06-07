"""Gridz sink adapters (Python). Sinks are projections, never sources of truth.

Mirrors the @gridz/sinks contract. Ships the in-memory and SQLite (stdlib
sqlite3) sinks; Postgres/MySQL/Mongo/Redis/Neo4j/S3 follow the same protocol and
are validated by docker-backed integration tests (see the TS package's docker/).
"""

from __future__ import annotations

from .memory import MemorySink
from .sqlite import SqliteSink

__all__ = ["MemorySink", "SqliteSink"]
