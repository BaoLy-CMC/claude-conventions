# FinX Claude Conventions — Overview (English)

A shared Claude Code plugin (`finx-core`) that encodes FinX backend engineering standards as machine-checkable rules, skills, and hooks, so every engineer's Claude Code behaves the same way.

Vietnamese version: [`overview.vi.md`](overview.vi.md).

## Purpose

- One source of engineering conventions for the FinX / Vikki banking platform (Java 21 + Spring Boot).
- The authoritative prose lives in Confluence, space `EN` (Engineering). This plugin does not duplicate it — it encodes the enforceable parts so they are applied automatically and consistently.

## First-time install

```
/plugin marketplace add <internal-git-url>
/plugin install finx-core@finx-conventions
/reload-plugins
```

Start a new session afterwards so the always-on baseline loads. Optionally run `/flow-setup` to personalize enforcement and thresholds; without it, standard defaults apply.

## What you get

### 1. Always-on baseline (injected every session)

A compact rule block is injected at session start via a hook (plugins do not auto-load `CLAUDE.md`). It covers:

- Working principles: think first and never assume silently (raise concerns with a recommendation), KISS over over-engineering, think deep and ship simple, surgical changes, verifiable success criteria, honest reporting, reversible-first.
- Communication: lead with the answer, concise and skimmable, cite references.
- Non-negotiables: Google Java Style, Lombok allowed, no `var` in new code, `BigDecimal` for money, constructor injection, externalized config, secrets via env/secret manager.
- Response envelope by cluster: `fsap-*` → `com.finx.common.fsap.pojo.FsapApiResponse`; non-fsap → `com.finx.spring.service.api.ResponseApi`.
- Errors and logging: `ErrorCode` enum in `DOMAIN.CODE` format, business rules map to 4xx, log once at `GlobalExceptionHandler`, SLF4J parameterized, DEBUG by default, never log PII, mask sensitive identifiers.
- API versioning: `/{resource}/v{N}/...`, no DTO sharing across versions.
- Banking domain: ledger-only balance changes, idempotency key on mutations, saga/outbox for distributed transactions, OTP/SBV block after N failures with full audit.
- Cross-repo operations (non-prod): DB migrations to `non-prod-liquibase`, important env to `non-prod-application-workload` (with confirmation), Kafka topics to `non-prod-kafka-gitops`, public APIs to `non-prod-apigw-configs` and `non-prod-openapi-configs`.
- Architecture decisions (hexagonal vs onion vs layered, sync vs event, saga vs 2PC) must be asked with trade-offs and a recommendation.

### 2. Skills (loaded on demand)

- Reviews: `logging-review`, `error-handling-review`, `pre-ship` (full verify gate: build, Checkstyle, tests/coverage, reviews, SonarQube).
- Flow: `flow` (`/flow <phase>`), `plans`, `plan-tidy`, `flow-setup`.
- Authoring: `create-liquibase-changeset`, `cross-repo-operations`, `new-service-scaffold`, `write-docs`.

### 3. Hooks (four events)

- `SessionStart`: inject baseline and resume `.finx/state_summary.md`.
- `PreToolUse`: force-guard (block `var` in new code, `double`/`float` for money, `System.out`/`printStackTrace`, hardcoded secrets) and flow-gate (block non-trivial production-Java edits outside the `execute` phase).
- `UserPromptSubmit`: context-watch — at about 65% context, ask whether to compact, save-and-reset, or continue.
- `PreCompact`: snapshot flow state before compaction.

Escape hatch for a false positive: `FINX_SKIP_HOOKS=1`.

## The development flow

`explore → plan → execute → review → reset`, driven by `/flow <phase>`. Non-trivial production work requires an approved plan before code (enforced by the flow-gate). See [`flow.md`](flow.md) for phases, state, and enforcement levels.

## Configuration

`/flow-setup` writes `~/.finx/flow-config.json` (per engineer) and/or `<repo>/.finx/flow-config.json` (per project, project wins). Keys: `enforcement` (hybrid/hard/guided/off), `contextThreshold`, `contextLimit`, `trivialMaxLines`, `maxActivePlans`, `autoArchiveDays`. A missing file means standard defaults.

## Updating

Maintainers cut a release with `./release.sh <version>` (bumps both manifests and regenerates artifacts), then commit, tag, and push. Engineers update with `/plugin marketplace update finx-conventions`, `/plugin update finx-core`, `/reload-plugins`, then a new session. Full detail in [`releasing.md`](releasing.md).

## Source of truth

Confluence space `EN`, hub page "Backend - Conventions & Standards". Each skill and rule cites its source page. When a Confluence standard changes, update `canonical/conventions.json` (or the relevant skill) and cut a new version.
