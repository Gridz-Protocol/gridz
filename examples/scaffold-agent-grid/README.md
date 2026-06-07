# scaffold-agent-grid

Adds a Gridz profile to a [scaffold-agent](https://scaffoldagent.xyz) project: the
agent publishes its **own** grid (via `agent-context` + `agent-endpoint[mcp]`) and
reads another agent's grid over MCP.

**Standalone** — generated downstream of scaffold-agent, not part of the monorepo
install.

```bash
npx scaffold-agent@latest grid-demo
cd grid-demo
pnpm add @gridz/react @gridz/sinks @gridz/mcp
```

Drop the agent's grid onto the home page (see `snippet.page.tsx`):

```tsx
import { Grid } from "@gridz/react";
import "@gridz/react/styles.css";
// operatorEns comes from your env / agent config — e.g. "myagent.gridz.eth"
<Grid grid={grid} />
```

## What it demonstrates

1. **Publish** — the agent signs `agent-context` and `agent-endpoint[mcp]` cells
   with its own signer (local key, passkey, or 1claw) and publishes to a sink.
2. **Read another agent over MCP** — connect to a peer's `agent-endpoint[mcp]`
   (discovered from its grid) and call `grid.read` to reason over a *verified*
   profile, not a scraped one.
3. **A `--with-grids` post-install** wires `@gridz/react` and an ENS sink into the
   generated app.

See `snippet.page.tsx` and `snippet.publish.ts` for the integration code.
