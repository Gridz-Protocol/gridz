# minimal-cli

The whole Gridz flow in one function (`src/publish.ts`): load a `gridz.yaml`, sign
every cell with a local key, publish to a sink, verify, and render static HTML.

**Bring your own data.** This example ships no pre-filled profile. Scaffold and
fill your own:

```bash
npx gridz init --template minimal      # writes gridz.yaml (shape only)
# fill in the alias/description/url values yourself, then:
gridz identity import --from keystore ./my-keystore.json   # or --from oneclaw
export GRIDZ_SIGNER_KEY=0x...          # CI-only path; never committed
node bin.ts gridz.yaml grid.html
open grid.html
```

`bin.ts` publishes to a local SQLite sink. To publish to **ENS Sepolia** instead,
swap `sqliteSink()` for an `EnsSink` wired to a `ViemEnsBackend` (an RPC URL + a
wallet you control) — see `@gridz/sinks`. Gridz never holds your key.

Every rendered cell carries a verification badge a stranger can re-check with only
`@gridz/core` and a public RPC.
