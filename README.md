# FinX Claude Conventions

Tiếng Việt: [README.vi.md](README.vi.md)

A shared [Claude Code](https://claude.com/claude-code) plugin (`finx-core`) that encodes FinX backend engineering standards as machine-checkable rules, skills, and hooks, so every engineer's Claude Code behaves the same way. Java 21/25, Spring Boot 3/4, SBV-compliant banking.

## Quickstart

```
/plugin marketplace add https://github.com/BaoLy-CMC/claude-conventions.git
/plugin install finx-core@finx-conventions
/reload-plugins
```

Start a new session so the always-on baseline loads, then run `/finx-core:onboarding` — a ~2 minute tour of what runs automatically, what is opt-in, and how the flow works. The first sessions after install point at it too.

## At a glance

| Layer | What it does | Where |
|-------|--------------|-------|
| Baseline | Always-on rules injected every session | `SessionStart` hook (generated from canonical) |
| Guards | Block bad edits before they land | `PreToolUse` hooks |
| Skills | On-demand playbooks (reviews, flow, authoring) | `skills/` |
| Flow | `explore -> plan -> execute -> review -> reset` | `flow` skill + `.finx/` state |
| Per-engineer | Opt-in presentation: 3 output styles + a flow-aware statusline | `output-styles/`, `statusline-setup` |
| Onboarding | First-run guided tour, then wires up the chosen opt-ins | `onboarding` skill + `SessionStart` notice |

## Architecture (one picture)

```
Confluence space EN            <- source of truth (humans read)
        |
        v
canonical/conventions.json --generate.py--> Kiro steering (canonical/out/kiro/*.md)
        |                                    Claude baseline (hooks/baseline-rules.md)
        v
+------------------- finx-core plugin -------------------+
|  baseline : SessionStart injects rules each session    |
|  hooks    : PreToolUse guard + flow-gate;              |
|             UserPromptSubmit context-watch; PreCompact |
|  skills   : reviews / flow / authoring (on-demand)     |
|  flow     : explore->plan->execute->review->reset      |
+--------------------------------------------------------+
```

## Documentation

- [Overview](docs/en/overview.md) - the mental model and how the pieces fit.
- [Rules](docs/en/rules.md) - the always-on baseline conventions.
- [Reference](docs/en/reference.md) - every skill and hook.
- [Flow](docs/en/flow.md) - the development flow, gate, context-watch, plan management.
- [Releasing](docs/en/releasing.md) - how to change a convention, release, and update.

## Source of truth

The authoritative prose lives in Confluence, space `EN` (Engineering), hub "Backend - Conventions & Standards". This plugin encodes the enforceable parts and cites the source page. To change a rule, edit `canonical/conventions.json`, run the generator, and cut a release - see [Releasing](docs/en/releasing.md).

## Status

`1.0.0`. 19 skills, 4 hook events, the full flow with a tool-agnostic gate, plan management, version-update notice, the canonical -> Kiro/Claude generator, plus per-engineer opt-in presentation (3 output styles + a flow-aware statusline). History in [CHANGELOG.md](CHANGELOG.md).
