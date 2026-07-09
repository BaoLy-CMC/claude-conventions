# Reference: skills and hooks

Tiếng Việt: [../vi/reference.md](../vi/reference.md) | Back to [README](../../README.md)

## Skills

Skills load on demand: Claude invokes one when the context matches its description, or you can call it by name.

### Reviews

| Skill | Purpose | Trigger |
|-------|---------|---------|
| `logging-review` | Check logging against the 14-point logging convention (PII/mask, SLF4J parameterization, DEBUG default, no log-and-throw, no empty catch) | Reviewing or writing log statements; "review logging" |
| `error-handling-review` | Check error codes (`DOMAIN.CODE`), HTTP mapping (business -> 4xx), log-once, cluster-correct envelope | Reviewing exceptions, error handlers, envelopes |
| `pre-ship` | One verification gate: compile, Checkstyle, tests + coverage, the review skills, SonarQube quality gate, diff sanity -> single PASS/FAIL | Before a PR/ship; the review phase of the flow |

### Flow

| Skill | Purpose | Trigger |
|-------|---------|---------|
| `flow` | Drive `explore -> plan -> execute -> review -> reset` with state in `.finx/flow.json` | `/flow <phase>`; starting non-trivial work |
| `plans` | Manage plans under `.finx/plans/` (lifecycle, single active plan, guards) | "list plans", "new plan", "too many plans" |
| `plan-tidy` | Migrate loose root `plan*.md` into the structure, with confirmation | "tidy plans", loose plan files at root |
| `flow-setup` | Configure the flow per engineer/project (enforcement, thresholds) | "flow setup", "configure flow" |

### Authoring

| Skill | Purpose | Trigger |
|-------|---------|---------|
| `create-liquibase-changeset` | Scaffold a changeset in `non-prod-liquibase` in the enforced format | "create migration/changeset" |
| `cross-repo-operations` | Route infra changes to the right non-prod GitOps repo; confirm-gate for important env | Adding a Kafka topic, env var, or public API |
| `new-service-scaffold` | Lay out a new service/module (asks architecture first) | "new service", "scaffold" |
| `write-docs` | Write docs in a chosen format and destination; asks English or Vietnamese; no icons | "write docs", "document this" |
| `runtime-stack` | Detect Java + Spring Boot version and apply the per-version rules | Writing/upgrading code; mentions of Java 21/25 or Spring Boot 3/4 |

## Hooks

Four lifecycle events. All fail-open (never break a tool call on error). Escape hatch for a false positive: `FINX_SKIP_HOOKS=1`.

| Event | Script | What it does |
|-------|--------|--------------|
| `SessionStart` | `session-start.py` | Inject the baseline; if `.finx/state_summary.md` is fresh, append it under a RESUME banner |
| `SessionStart` | `version-notice.py` | When the installed finx-core version changed since last session, print the new version and its changelog notes |
| `PreToolUse` (Write/Edit) | `precheck.py` | Hard-block high-confidence violations: `var` in new code, `double`/`float` for money, `System.out`/`printStackTrace`, hardcoded secrets |
| `PreToolUse` (Write/Edit) | `flow-gate.py` | Block non-trivial production-Java edits unless a ready-to-execute signal is present (see [Flow](flow.md)) |
| `UserPromptSubmit` | `context-watch.py` | Estimate context usage; at ~65% ask whether to compact, save+reset, or continue |
| `PreCompact` | `flow-reset.py` | Snapshot flow phase + active plan + `git diff --stat` into `.finx/state_summary.md` before compaction |

### Force-guard vs flow-gate

- The **force-guard** (`precheck.py`) is about code content and always applies to production Java writes.
- The **flow-gate** (`flow-gate.py`) is about workflow state and only applies when the repo runs a flow (`.finx/flow.json` present) with `enforcement` not `off`/`guided`.
