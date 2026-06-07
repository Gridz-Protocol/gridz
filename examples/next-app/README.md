# next-app

A reference Next.js 15 app that renders **any** Gridz subject at `/[subject]` in
the Spritz aesthetic, with live verification badges. Reads from ENS (the
`GridzResolver`) first, falls back to a Postgres projection.

**Standalone** — not part of the monorepo install. Run it on its own:

```bash
cd examples/next-app
pnpm install
export GRIDZ_RPC_URL=https://...        # an Ethereum RPC for ENS resolution
export GRIDZ_RESOLVER=0x...             # your deployed GridzResolver
# optional cache:
export GRIDZ_PG_DSN=postgres://...
pnpm dev
```

The home page is a setup screen — there is **no hard-coded subject**. Enter an ENS
name like `kevin.gridz.eth` (a gridz.eth subname) or a DID, and it renders that
profile. Every cell carries a badge a stranger can re-verify with `@gridz/core`.
