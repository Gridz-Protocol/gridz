# Gridz Standard Keys — Field Registry

This is the canonical list of standard field keys. The same key string is used everywhere: TS SDK, Python SDK, CLI, MCP, YAML/JSON config, and ENS text records. Bikeshed once, here.

**Key syntax.** Every key matches `^[a-z0-9]([a-z0-9._\-\[\]])*[a-z0-9\]]$` (see `grid.schema.json#/$defs/key`). This is a superset of the ENS global-key rule (lowercase + digits + hyphen) and the ENS service-key rule (reverse-dot notation), and it additionally permits the `[...]` bracket parameter form used by agent keys.

**Dynamic keys are first-class.** Any key matching the regex round-trips losslessly through every component. Unknown keys are preserved; unknown `widget_type`s fall back to the `Generic` renderer.

**Provenance legend.** Each key notes its source so we never claim a standard we didn't inherit:
- `ENSIP-5` — global text records (avatar, description, email, …)
- `ENSIP-18` — profile text records (alias, header, theme, …)
- `ENSIP-25` — AI agent registry verification key
- `ENSIP-26` — agent text records (agent-context, agent-endpoint[...])
- `Gridz` — defined by this project under a namespaced prefix

---

## Tier 1 — Inherited / aliased from ENS

Direct passthrough so any ENS profile is a valid (minimal) Gridz. Values follow the ENS "void of prefix" rule: store the bare handle (`alice`), not the decorated form (`@alice` or a full URL), unless the service requires otherwise.

### Global keys (ENSIP-5)

| Key | Value | Notes |
|---|---|---|
| `avatar` | URL / NFT URI | ENSIP-12 avatar spec. If an `eip155:` NFT URI, import flow verifies ownership. |
| `description` | string | Biography / summary. |
| `display` | string | Canonical display capitalization of the name (ENSIP-5). |
| `email` | string | RFC 5322 address. |
| `keywords` | string | Comma-separated list. |
| `mail` | string | Physical mailing address. |
| `notice` | string | Notice regarding the name/profile. |
| `location` | string | Free-form location. |
| `phone` | string | E.164 format. |
| `url` | string | Website URL. |

### Profile keys (ENSIP-18)

| Key | Value | Notes |
|---|---|---|
| `alias` | string | Short display name (the brief's "name" maps here; ENS has no bare `name` text key). Max 50 chars by convention. |
| `header` | URL | Banner / header image (mirrors ENSIP-12 avatar handling). |
| `theme` | string/JSON | Source for the Grid `theme` object when present. |
| `timezone` | string | IANA tz identifier, e.g. `America/New_York`. |
| `language` | string | ISO 639-1 code. |
| `primary-contact` | string | Preferred contact channel. |

> `avatar`, `description`, `email`, `location`, `url` appear in both ENSIP-5 and ENSIP-18; they are listed once above.

### Service keys (ENSIP-5 reverse-dot convention)

Reverse-dot notation; must contain at least one dot. This is an open namespace — any service-owned reverse-dot key is valid. Commonly used:

| Key | Service |
|---|---|
| `com.github` | GitHub username |
| `com.twitter` | Twitter/X handle |
| `com.discord` | Discord handle |
| `com.reddit` | Reddit username |
| `org.telegram` | Telegram username |
| `xyz.farcaster` | Farcaster handle |
| `social.bsky` | Bluesky handle |
| `io.keybase` | Keybase username |

---

## Tier 2 — Agent keys

| Key | Provenance | Value | Notes |
|---|---|---|---|
| `agent-context` | ENSIP-26 | string (text/Markdown/YAML/JSON) | Free-form context for agentic systems. |
| `agent-endpoint[mcp]` | ENSIP-26 | URL (incl. `ipfs://`) | MCP server endpoint. The Gridz MCP server registers itself here. |
| `agent-endpoint[a2a]` | ENSIP-26 | URL | Agent-to-Agent protocol endpoint. |
| `agent-endpoint[web]` | ENSIP-26 | URL | Web interface. |
| `agent-registration[<registry>][<agentId>]` | ENSIP-25 | non-empty string (SHOULD be `"1"`) | `<registry>` is the **ERC-7930 interoperable address** of the registry contract (`0x…` hex). `<agentId>` is the registry's agent id and MUST NOT contain `[` or `]`. Presence = the name owner attests association; the value itself is meaningless. |
| `agent.capabilities` | Gridz | string[] (JSON) | Declared capabilities. |
| `agent.model` | Gridz | string | Backing model id. |
| `agent.version` | Gridz | string | Agent version. |
| `agent.operator` | Gridz | DID / string | Operating party. |
| `agent.oneclaw_id` | Gridz | string | Optional. Binds this Grid to a 1claw agent id; attested to link the Gridz identity to the HSM-managed identity. |

> **Correction vs. brief §2/§6:** ENSIP-26 defines only `agent-context` and `agent-endpoint[<protocol>]`. The `agent-registration[...]` key is defined by **ENSIP-25**, not ENSIP-26. The `agent.*` dotted keys are **Gridz-defined**, not ENS standards — they live under the `agent.` prefix to avoid colliding with the bracketed ENSIP keys.

---

## Tier 3 — Gridz widget keys (`gridz.*`)

Gridz-defined namespace. Each has a value schema (Zod in TS / Pydantic in Python) generated from a shared JSON Schema, and a 1:1 renderer component. These mirror the widget shapes of the Spritz reference page **aesthetically only** — no field _values_ are inherited.

| Key | Widget |
|---|---|
| `gridz.message_me` | Contact / DM button |
| `gridz.social_link` | Single social link card |
| `gridz.availability_status` | Available / busy indicator |
| `gridz.stats` | Stat tiles |
| `gridz.currently` | "Currently …" status |
| `gridz.text` | Rich text block |
| `gridz.countdown` | Countdown to a date |
| `gridz.clock` | Live clock (timezone-aware) |
| `gridz.weather` | Weather for a location |
| `gridz.tech_stack` | Tech / tool list |
| `gridz.poll` | Poll |
| `gridz.goals_checklist` | Checklist of goals |
| `gridz.fun_counter` | Arbitrary counter |
| `gridz.streak_counter` | Streak counter |
| `gridz.map` | Map pin |
| `gridz.random_fact` | Random fact |
| `gridz.fortune_cookie` | Fortune |
| `gridz.reaction_wall` | Reaction wall |
| `gridz.zodiac` | Zodiac sign |
| `gridz.pet` | Pet card |
| `gridz.guestbook` | Guestbook |
| `gridz.visitor_counter` | Visitor counter |

> A `gridz.*` key MAY also set `widget_type` explicitly; when omitted, the key string is the render hint. The per-widget value schemas are tracked in `packages/core-ts/src/widgets/` and `python/gridz/widgets/`, generated from `specs/widgets/*.schema.json` (added in the implementation phase, not this spec PR).
