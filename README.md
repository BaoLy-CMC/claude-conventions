# FinX Claude Conventions

Company-wide [Claude Code](https://claude.com/claude-code) conventions for the **FinX banking platform** (SBV-compliant, Java 21 + Spring Boot microservices).

This repo is a **Claude Code plugin marketplace**. It ships one plugin — `finx-core` — that encodes the company's engineering standards as **machine-checkable skills and hooks**, so every engineer's Claude Code applies the same rules.

## Source of truth

The authoritative standards live in **Confluence, space `EN` (Engineering)** — hub: *Backend - Conventions & Standards*. This plugin does **not** duplicate that prose; it encodes the enforceable parts. Each skill/hook cites its `Source: <Confluence page id>`.

## Install

```bash
# In Claude Code
/plugin marketplace add <git-url-or-local-path>
/plugin install finx-core@finx-conventions
```

Local test before publishing:

```bash
claude --plugin-dir ./plugins/finx-core
```

## What's inside (`plugins/finx-core/`)

| Dir | Purpose |
|---|---|
| `skills/` (reviews) | `logging-review`, `error-handling-review`, `pre-ship` (full verify gate) |
| `skills/` (flow) | `flow` (`/flow <phase>` explore→plan→execute→review→reset), `plans`, `plan-tidy`, `flow-setup` (per-engineer config) |
| `skills/` (authoring) | `create-liquibase-changeset`, `cross-repo-operations`, `new-service-scaffold`, `write-docs` |
| `hooks/` | `hooks.json` — **SessionStart** injects the baseline + resumes `.finx/state_summary.md`; **PreToolUse** runs the force-guard (`var`/money-`double`/`System.out`/secrets) and the flow-gate (block non-trivial prod-Java edits outside `execute`); **UserPromptSubmit** context-watch (ask to compact/reset at ~65%); **PreCompact** snapshots flow state. Escape hatch: `FINX_SKIP_HOOKS=1`. |
| `canonical/` | `conventions.json` + `generate.py` — single source that generates **both** the Claude baseline (`hooks/baseline-rules.md`) and the Kiro steering files (`out/kiro/*.md`) |

> **Note on always-on rules:** Claude Code plugins do **not** auto-load `CLAUDE.md`. The non-negotiable baseline is injected each session via a **SessionStart hook** (generated from `canonical/conventions.json`); detailed rules load on-demand as skills. Standard subagents are provided per-engineer, not by this plugin.

## Rule highlights (verified against the codebase)

- **Working principles (always-on):** think first / never assume silently (ask with a recommendation), KISS not over-engineering, think deep + ship simple, surgical changes, verifiable success, honest reporting, reversible-first. Significant architecture choices (hexagonal/onion/layered, sync vs event, saga vs 2PC) must be asked with trade-offs + a recommendation.
- **Communication:** lead with the answer, concise and skimmable, cite references; no rambling.
- **Lombok: allowed.** `var`: banned in **new/modified** code only (no mass refactor).
- **Currency: `BigDecimal`**, never `double`.
- **Response envelope by cluster:** `fsap-*` repos → `com.finx.common.fsap.pojo.FsapApiResponse`; non-fsap repos → `com.finx.spring.service.api.ResponseApi` (no new local copies).
- **Error codes:** `ErrorCode` enum, `DOMAIN.CODE` format — no free-form strings.
- **Cross-repo operations (non-prod):** DB migrations → `non-prod-liquibase`; important env → ask + confirm, then `non-prod-application-workload`; Kafka topics → `non-prod-kafka-gitops`; public (mobile) APIs → `non-prod-apigw-configs` + `non-prod-openapi-configs`. Prod goes through a separate release process.

## Docs

- [`docs/overview.en.md`](docs/overview.en.md) / [`docs/overview.vi.md`](docs/overview.vi.md) — team overview (English / Vietnamese).
- [`docs/flow.md`](docs/flow.md) — the explore → plan → execute → review → reset flow, state, enforcement, context-watch.
- [`docs/releasing.md`](docs/releasing.md) — release workflow (maintainers) and update workflow (engineers).

## Governance

SemVer in `plugin.json`; every version bump recorded in `CHANGELOG.md`. Use `./release.sh <version>` to bump both manifests consistently and regenerate. Reviewed quarterly.

## Regenerate artifacts

```bash
python3 plugins/finx-core/canonical/generate.py
```
Edit `canonical/conventions.json`, run the generator, commit the regenerated `baseline-rules.md` + `out/kiro/*.md`.

## Status

**0.18.0.** 11 skills, 4 hook events (SessionStart, PreToolUse, UserPromptSubmit, PreCompact), the full explore→plan→execute→review→reset flow with gate + context-watch, plan management, `write-docs`, `pre-ship` gate, and the canonical → Kiro/Claude generator. See `CHANGELOG.md`.
