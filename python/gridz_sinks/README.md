# gridz-sinks (Python)

Sink adapters mirroring `@gridz/sinks`. Ships `MemorySink` and `SqliteSink`
(stdlib sqlite3, real + offline-tested). Other databases follow the same
protocol and are validated by the docker stack in the TS package.

```bash
uv sync --extra dev && uv run pytest
```
