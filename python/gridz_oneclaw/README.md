# gridz-oneclaw (Python)

Optional 1claw HSM adapter mirroring `@gridz/oneclaw`: `OneClawSigner` (HSM-backed
EIP-712 signing), key provisioner, and `oneclaw://vault/...` secret resolver.

```bash
uv sync --extra dev && uv run pytest
```

Live tests require `GRIDZ_ONECLAW_API_KEY` and are skipped (never mocked) without
it. The `MockOneClawSigner` test fixture only activates with `GRIDZ_ONECLAW_MOCK=1`.
