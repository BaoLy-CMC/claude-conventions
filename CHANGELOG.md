# Changelog

All notable changes to the `finx-core` plugin are documented here. Follows [Semantic Versioning](https://semver.org/).

## [0.22.0] - 2026-07-09

### Added
- Hook `version-notice` (SessionStart) — records the installed finx-core version per engineer and, when it changes between sessions (Claude Code auto-updates plugins at startup via git pull), prints the new version and its changelog notes when reachable. Makes silent auto-updates visible.

### Changed
- `docs/*/releasing.md` — corrected the update model: plugins auto-update at startup (git pull of the marketplace); the manual commands only pull immediately without waiting for a restart.
- `docs/*/reference.md` — SessionStart now lists both `session-start.py` and `version-notice.py`.

## [0.21.0] - 2026-07-09

### Changed
- Version bump only (no functional change).

## [0.20.0] - 2026-07-09

### Changed
- **Tool-agnostic flow-gate.** The gate now opens on any of: `flow.json` `phase: execute`, `flow.json` `approved: true`, or an `activePlan` whose `plan.md` `status` is `approved`/`in-progress` (created by any tool). Lets other planning/execute tools integrate via the shared `.finx/` artifacts instead of the `/flow` commands. Documented the integration contract in `docs/flow.md`.

## [0.19.0] - 2026-07-09

### Added
- **Version-aware runtime rules.** Baseline no longer hardcodes Java 21; it now says versions vary per project (Java 21 or 25 LTS; Spring Boot 3 or 4), detected from build files, and forbids using features newer than the project's declared version.
- Skill `runtime-stack` — detects a project's Java + Spring Boot version and gives the per-version do/don't (Java 21 vs 25 language features; Spring Boot 3 vs 4: Jakarta EE 9/10 vs 11, Jackson 2 vs 3, removed deprecations, dropped Undertow/JUnit4, modular JARs) plus the 3→4 upgrade path. Cites the official migration guide.

## [0.18.0] - 2026-07-09

### Added
- `release.sh` — bumps the version in both manifests consistently and regenerates canonical artifacts in one step.
- `docs/releasing.md` — maintainer release workflow and engineer update workflow (versioning, `/plugin marketplace update`, reload, rollback).
- `docs/flow.md` — overview of the explore → plan → execute → review → reset flow, state, enforcement, and context-watch.

## [0.17.0] - 2026-07-09

### Added
- Skill `pre-ship` — single verification gate before PR/ship: compile, Checkstyle, tests + coverage (80% target on changed code), the finx review skills, SonarQube quality gate (if connected), and diff sanity, aggregated into one PASS/FAIL verdict (FAIL blocks on build/test/coverage/quality-gate/CRITICAL/HIGH). Wired into `/flow review`.

## [0.16.0] - 2026-07-09

### Changed
- `write-docs`: now asks **English or Vietnamese** (no default); requires **clear, complete** structure (no stub/TBD sections); **bans icons/emoji** in generated docs.

## [0.15.0] - 2026-07-09

### Added
- **Communication style** guardrail (Claude-baseline only, excluded from Kiro): lead with the answer, keep responses short/skimmable/no rambling, cite references (`file:line`, Confluence page id, URL) for claims.
- Skill `write-docs` — writes/updates documentation in a chosen format (Markdown / Confluence / HTML) and destination (repo `docs/`, Confluence via Atlassian MCP, local `.finx/docs/`, or custom path). Asks format + destination first; confirms before any Confluence publish.

## [0.14.0] - 2026-07-09

### Added
- **Flow F5 — `flow-setup` skill.** Per-engineer/per-project configuration written to `~/.finx/flow-config.json` (global) and/or `<repo>/.finx/flow-config.json` (project override, project wins). Covers enforcement, contextThreshold, contextLimit, trivialMaxLines, maxActivePlans, autoArchiveDays. Merges over standard defaults; setup is optional (missing file = defaults).

### Changed
- `flow-gate.py` now honors all four enforcement levels: `hybrid` (default), `hard` (no trivial exemption), `guided` (track, never block), `off` (disabled).

## [0.13.0] - 2026-07-09

### Added
- **Flow F4 — context-watch + auto-reset (3 hooks).**
  - `UserPromptSubmit` → `context-watch.py`: estimates context usage from the transcript's latest `usage` tokens ÷ model limit; at ≥ threshold (default 65%) injects a note telling Claude to ask the user (compact / save+clear+reload / continue). Warns once per 10% bucket per session.
  - `PreCompact` → `flow-reset.py`: safety-net snapshot of flow phase + active plan + `git diff --stat` into `.finx/state_summary.md` before an unattended compaction.
  - `SessionStart` → `session-start.py` (replaces `inject-baseline.sh`): emits the baseline and, if a fresh `.finx/state_summary.md` exists, appends it under a RESUME banner so a session after `/clear` resumes the exact phase.

### Changed
- `inject-baseline.sh` removed; baseline injection now handled by `session-start.py`.

## [0.12.0] - 2026-07-09

### Added
- **Flow F3 — flow-gate** (`hooks/flow-gate.py`, added to the PreToolUse chain). Hybrid enforcement: blocks edits to production Java (`/src/main/**.java`) when the repo is running a flow but is not in the `execute` phase (no approved plan) **and** the change is non-trivial (>30 changed lines). Opt-in — repos without `.finx/flow.json` are not gated. Reads thresholds from `.finx/flow-config.json` / `~/.finx/flow-config.json` (defaults baked in). Exempts tests; escape via `FINX_SKIP_HOOKS=1`.

## [0.11.0] - 2026-07-09

### Added
- **Flow F2 — `flow` skill.** Single `/flow <phase>` command driving explore → plan → execute → review → reset with per-repo state in `.finx/flow.json` (phase + activePlan). Named `flow` (not 5 separate commands) to avoid colliding with personal explore/plan/execute/reset commands. `execute` requires an approved active plan. Defines the `state_summary.md` resume schema.

### Changed
- Archived the superseded personal commands `explore/plan/execute/reset` from `~/.claude/commands/` to `~/.claude/_archived-commands/` (kept `check`, `ship`, `verify`, and the `explore` agent). Updated `~/.claude/rules/java-backend-standards.md` to point the Slash Kit at `/flow <phase>`.

## [0.10.0] - 2026-07-09

### Added
- **Flow F1 — plan management.** Skill `plans` (structured `.finx/plans/NNN-slug/plan.md` with frontmatter + lifecycle draft→approved→in-progress→done→archived, single `activePlan` in `.finx/flow.json`, guard max-3-active + auto-archive-14d) and skill `plan-tidy` (migrate loose root `plan*.md` into the structure, with confirmation, never deleting unmigrated files).

## [0.9.0] - 2026-07-09

### Added
- Guardrail: **"Think deep, ship simple"** — reason through full complexity (edge cases, trade-offs, failure modes, second-order effects) before deciding, then deliver the simplest correct solution; depth of thinking must not leak into complexity of output. Added to the baseline principles.

## [0.8.0] - 2026-07-09

### Added
- **Working principles & guardrails** section (Karpathy-style) at the top of the always-on baseline: think-first / never assume silently (ask with a recommendation on any concern), KISS not over-engineering, surgical changes, verifiable success criteria, honest reporting, reversible-first with confirmation on irreversible/outward-facing actions. Added to `canonical/conventions.json` → baseline + Kiro.

## [0.7.0] - 2026-07-09

### Added
- **Architecture-decision rule**: for significant choices (hexagonal vs onion vs layered, bounded-context boundaries, sync vs event-driven, saga vs 2PC), Claude must **ask the user with trade-offs + a recommendation** rather than silently pick. Added to `canonical/conventions.json` → baseline + Kiro, and to the `new-service-scaffold` skill (mandatory ask-first step, defaults to recommending hexagonal to match the fleet).

## [0.6.0] - 2026-07-09

### Added
- Skill `new-service-scaffold` — lays out a new service/module per the multi-module hexagonal structure (`common/core/application/infra/api/tests`) with cluster-correct envelope, error/logging, config, and persistence conventions baked in. Source: Confluence EN/514528555.
- `canonical/conventions.json` + `canonical/generate.py` — single source of truth generating **both** the Claude baseline (`hooks/baseline-rules.md`) and the Kiro steering files (`canonical/out/kiro/*.md`), eliminating drift between the two AI-convention channels.

### Changed
- `hooks/baseline-rules.md` is now **generated** from `canonical/conventions.json` (edit the source, run the generator; do not hand-edit).
- Dropped the empty `agents/` dir — standard agents are provided per-engineer, not by this plugin.

## [0.5.0] - 2026-07-09

### Added
- **PreToolUse guard** (`hooks/precheck.py`, wired in `hooks.json` for Write/Edit/MultiEdit) that **hard-blocks** high-confidence violations before the write lands: `System.out`/`printStackTrace`, `var` in new non-test code, `double`/`float` for monetary variables, hardcoded secret literals (Java + yml/properties). Fail-open on parse errors; escape hatch `FINX_SKIP_HOOKS=1`. Heuristic checks stay with the review skills.

## [0.4.0] - 2026-07-09

### Added
- Skill `create-liquibase-changeset` — scaffolds a changeset in `non-prod-liquibase` following the CI-enforced format (one `<changeSet>`, `<!-- changeset author:DD.MM.YYYY:slug -->`, required `<rollback>`, no raw `.sql`), validated with `make lint`.
- Skill `cross-repo-operations` — routes infra changes to the right non-prod GitOps repo (liquibase / kafka-gitops / application-workload / apigw+openapi), with a mandatory confirm-gate for important env vars.

## [0.3.0] - 2026-07-09

### Added
- Skill `logging-review` — reviews Java logging against the 14-point logging checklist (PII/mask, SLF4J parameterization, DEBUG-by-default, log-and-throw, empty catch). Source: Confluence EN/1448280077.
- Skill `error-handling-review` — reviews error codes (`ErrorCode` `DOMAIN.CODE`), HTTP status mapping (business→4xx), log-once-handle-once, and cluster-correct response envelope. Source: Confluence EN/1448247327.

## [0.2.0] - 2026-07-09

### Added
- **SessionStart hook** (`hooks/hooks.json` + `inject-baseline.sh`) that injects the always-on baseline convention block each session.
- `hooks/baseline-rules.md` — compact non-negotiable rules (Lombok/`var`, `BigDecimal`, envelope-by-cluster, error codes, logging/PII, API versioning, banking domain, cross-repo operations). Source: Confluence space EN.

## [0.1.0] - 2026-07-09

### Added
- Marketplace + plugin skeleton (`marketplace.json`, `plugin.json`).
- Directory structure: `skills/`, `agents/`, `hooks/`, `canonical/`.
- README with install steps and verified rule highlights.

_Skeleton only — no skills/hooks implemented yet._
