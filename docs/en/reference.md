# Reference: skills and hooks

Tiếng Việt: [../vi/reference.md](../vi/reference.md) | Back to [README](../../README.md)

## Skills

Skills load on demand: Claude invokes one when the context matches its description, or you can call it by name.

### Getting started

| Skill | Purpose | Trigger |
|-------|---------|---------|
| `onboarding` | Guided first-run tour: what is always on, what loads on demand, how the flow works, then wires up the chosen opt-ins | Right after install; the session-start onboarding notice; "how do I use finx-core", "getting started" |

### Reviews

| Skill | Purpose | Trigger |
|-------|---------|---------|
| `logging-review` | Check logging against the 14-point logging convention (PII/mask, SLF4J parameterization, DEBUG default, no log-and-throw, no empty catch) | Reviewing or writing log statements; "review logging" |
| `error-handling-review` | Check error codes (`DOMAIN.CODE`), HTTP mapping (business -> 4xx), log-once, cluster-correct envelope | Reviewing exceptions, error handlers, envelopes |
| `api-response-standards` | The ARB contract: status/payload/meta envelope, 422/409/428 mapping, empty vs 404, idempotent replay, downstream-timeout handling, W3C tracing | Writing/reviewing a controller or money endpoint; choosing a status code |
| `integration-test` | The org integration-test standard: opt-in source set that skips unconfigured, containers over shared infra, value/shape/behaviour assertions, marker+watermark cleanup, separate coverage gate | Adding/reviewing an integration test; flaky or duplicate-dropped tests |
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
| `ops-runtime` | Workload `values.yaml` (probes, heap flags, HPA, drain), actuator/metrics wiring, and creating an index on a production table | Editing a workload; OOMKill/rollout downtime; `CREATE INDEX` on prod |
| `release-workload` | The three release stages in `platform-release-processes`, `.done` idempotency, tag immutability and roll-forward | Releasing to production; a stage did nothing after merge |

### Presentation (per-engineer)

| Skill | Purpose | Trigger |
|-------|---------|---------|
| `statusline-setup` | Wire the FinX flow-aware powerline statusline into the engineer's own `~/.claude/settings.json` (asks first; never clobbers an existing statusline) | "finx statusline", "setup statusline", "show flow phase in the bar" |

## Output styles

Opt-in per engineer. Each is a selectable option in `/config` -> **Output style**; picking one changes how Claude presents its work (not what it knows). None is forced (`force-for-plugin` is not set), so an engineer who selects nothing is unaffected. All keep Claude's coding behaviour (`keep-coding-instructions: true`) and only change explanation depth. Takes effect after `/clear` or a new session.

| Style (in `/config`) | For | Behaviour |
|------|-----|-----------|
| `FinX Quick` | Urgent work | Result + diff only; no options/analysis unless asked. |
| `FinX Standard` | Know the principle, move fast | Implements directly, adds a 1-2 line option/trade-off only where a real decision exists. |
| `FinX Deep` | Learn while doing | Explains the reasoning, lays out options + concrete trade-offs, cites the FinX convention/Confluence. |

The always-on baseline still applies underneath; a style only adjusts depth/tone for the engineer who opts in.

## Statusline

Opt-in per engineer, enabled via the `statusline-setup` skill. A plugin cannot set the main statusline (only user/project settings can), so this wires `scripts/finx-statusline.sh` into the engineer's own `~/.claude/settings.json` and never overwrites an existing one (e.g. claude-hud) without asking.

- Shows (powerline, coloured by flow phase explore/plan/execute/review and usage green < 60 < yellow < 80 < red):
  - `full` = two lines — line 1 (work) `repo · phase · active-plan · enforcement · context%`; line 2 (session) `model · session% · reset countdown`. `session%` + reset come from the 5-hour rolling usage window (`rate_limits.five_hour`, Pro/Max only; hidden when absent — line 2 then shows model only).
  - `compact` = one line `repo · phase · context%`.
- Needs a Nerd Font for glyphs; `--plain` falls back to ASCII.
- In a repo without `.finx/flow.json`, the flow segments hide automatically (shows repo + context only). Fails safe: any error prints a minimal line rather than breaking the bar.

## Scripts

| Script | Does | Run it |
|--------|------|--------|
| `canonical/generate.py` | Regenerate the baseline + Kiro steering files from `canonical/conventions.json` | After editing a convention |
| `scripts/check-skills.py` | Lint every `SKILL.md` against the Agent Skills authoring limits (name matches directory, description <= 1024 chars and says when to use it, body < 500 lines, references one level deep with a table of contents over 100 lines, no XML tags, third person) | Before releasing a skill change; step 7 of `pre-ship` |
| `scripts/finx-statusline.sh` | Render the flow-aware powerline statusline | Wired by `statusline-setup` |

## Hooks

Four lifecycle events. All fail-open (never break a tool call on error). Escape hatch for a false positive: `FINX_SKIP_HOOKS=1`.

| Event | Script | What it does |
|-------|--------|--------------|
| `SessionStart` | `session-start.py` | Inject the baseline; if `.finx/state_summary.md` is fresh, append it under a RESUME banner |
| `SessionStart` | `version-notice.py` | When the installed finx-core version changed since last session, print the new version and its changelog notes |
| `SessionStart` | `onboarding-notice.py` | Until the onboarding tour is done (or declined), point the engineer at `/finx-core:onboarding` — at most 3 sessions, state in `~/.finx/.finx-core-onboarding` |
| `PreToolUse` (Write/Edit) | `precheck.py` | Hard-block high-confidence violations: `var` in new code, `double`/`float` for money, `System.out`/`printStackTrace`, hardcoded secrets |
| `PreToolUse` (Write/Edit) | `flow-gate.py` | Block non-trivial production-Java edits unless a ready-to-execute signal is present (see [Flow](flow.md)) |
| `UserPromptSubmit` | `context-watch.py` | Estimate context usage; at ~65% ask whether to compact, save+reset, or continue |
| `PreCompact` | `flow-reset.py` | Snapshot flow phase + active plan + `git diff --stat` into `.finx/state_summary.md` before compaction |

### Force-guard vs flow-gate

- The **force-guard** (`precheck.py`) is about code content and always applies to production Java writes.
- The **flow-gate** (`flow-gate.py`) is about workflow state and only applies when the repo runs a flow (`.finx/flow.json` present) with `enforcement` not `off`/`guided`.
