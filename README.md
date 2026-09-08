# FinX Claude Conventions

Tiếng Việt: [README.vi.md](README.vi.md)

Shared [Claude Code](https://claude.com/claude-code) plugin (`finx-core`). FinX backend standards as rules, skills and hooks — so every engineer's Claude behaves the same. Java 21/25, Spring Boot 3/4, SBV-compliant banking.

## Install

```
/plugin marketplace add https://github.com/BaoLy-CMC/claude-conventions.git
/plugin install finx-core@finx-conventions
/reload-plugins
```

Open a new session, then run **`/finx-core:onboarding`** — 2-minute tour, sets up your hub and options.

Commands worth remembering:

| | |
|---|---|
| `/flow explore <task>` | start non-trivial work |
| `/flow save` | pause before `/clear` — returns a handle |
| `/finx-core:pre-ship` | before a PR |

## How it works

```mermaid
flowchart TD
    C["Confluence EN<br/><i>source of truth</i>"] --> J["canonical/conventions.json"]
    J -->|generate.py| B["hooks/baseline-rules.md<br/><i>Claude</i>"]
    J -->|generate.py| K["canonical/out/kiro/*.md<br/><i>Kiro</i>"]
    B --> P
    subgraph P["finx-core plugin"]
        direction LR
        H1["<b>SessionStart</b><br/>inject baseline"]
        H2["<b>PreToolUse</b><br/>guard + flow-gate"]
        H3["<b>UserPromptSubmit</b><br/>context-watch"]
        SK["<b>19 skills</b><br/>on-demand"]
    end
```

- **Baseline** — always on, nothing to invoke.
- **Guards** — block `var`, `double` for money, `System.out`, hardcoded secrets. Escape: `FINX_SKIP_HOOKS=1`.
- **Skills** — load when relevant, or by name: reviews, authoring, ops. See [Reference](docs/en/reference.md).
- **Per-engineer opt-ins** — 3 output styles + a flow-aware statusline. Never forced.

## The flow

```mermaid
flowchart LR
    E[explore] --> P[plan] --> X[execute] --> R[review] --> Z[reset]
    Z -.-> E
```

Non-trivial production Java is gated until a plan is approved. State is **per session**, so many sessions can run at once:

```
<hub>/plans/<group>/<repo>/NNN-slug/plan.md   every repo's plans, one place
<hub>/sessions/<session_id>.json              flow state, one file per session
<hub>/state/<repo-slug>/<handle>.md           resume point for /flow save
```

Hub is configurable (`hub` in `flow-config.json`, default `~/.finx/hub`). Details: [Flow](docs/en/flow.md).

## Docs

[Overview](docs/en/overview.md) · [Rules](docs/en/rules.md) · [Reference](docs/en/reference.md) · [Flow](docs/en/flow.md) · [Releasing](docs/en/releasing.md)

## Changing a rule

Prose lives in Confluence space `EN`, hub "Backend - Conventions & Standards". To change a rule: edit `canonical/conventions.json`, run the generator, cut a release — see [Releasing](docs/en/releasing.md).

## Status

`2.1.0` · 19 skills · 4 hook events · [CHANGELOG](CHANGELOG.md)
