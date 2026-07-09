# FinX Dev Flow

The enforced development loop shipped by `finx-core`: **explore → plan → execute → review → reset**. It keeps non-trivial work disciplined (an approved plan before code) and survives long sessions (context-aware save/reset).

## Phases

Driven by one command, `/flow <phase>` (a single command to avoid colliding with personal `explore/plan/execute/reset` commands):

| Phase | Command | What happens |
|-------|---------|--------------|
| explore | `/flow explore [task]` | Map scope (controller → service → repository, prior art, impacted files). No edits. |
| plan | `/flow plan` | Create/activate a plan under `.finx/plans/`, write architecture + step blueprint, get it approved. |
| execute | `/flow execute` | Requires an approved active plan. Implement per plan, 1-2 files per batch. |
| review | `/flow review` | Run the `pre-ship` gate (build, Checkstyle, tests/coverage, review skills, Sonar). Fix CRITICAL/HIGH. |
| reset | `/flow reset` | Save `state_summary.md` + MemPalace, archive the done plan, return to idle. |
| status | `/flow status` | Show current phase, active plan, task. |

## State

Per repo, in `.finx/`:

- `flow.json` — `{ phase, activePlan, task, updated }`. The flow-gate reads this.
- `plans/NNN-slug/plan.md` — one directory per plan, with frontmatter (`status: draft|approved|in-progress|done|abandoned`). Managed by the `plans` skill; only one active plan at a time; guarded at max 3 active with auto-archive of done plans.
- `state_summary.md` — volatile resume pointer (phase, done, remaining, next action). Durable state stays in `plan.md`, `git diff`, and the code.

## Enforcement (the flow-gate)

A `PreToolUse` hook blocks edits to production Java (`**/src/main/**/*.java`) when a flow is active but not in `execute` and the change is non-trivial. Levels (set via `/flow-setup`):

- `hybrid` (default) — block non-trivial prod edits outside execute; trivial edits pass.
- `hard` — block all prod edits outside execute.
- `guided` — track the flow, never block.
- `off` — disabled.

Opt-in: a repo with no `.finx/flow.json` is never gated. Escape a false positive with `FINX_SKIP_HOOKS=1`.

## Long sessions: context-watch and reset

- `UserPromptSubmit` estimates context usage from the transcript. At the threshold (default 65%) it asks whether to `/compact`, save-and-clear-and-reload, or continue. Warns once per 10% bucket.
- Save-and-reload writes `state_summary.md`; after `/clear`, the `SessionStart` hook reloads it under a RESUME banner so the next session continues at the same phase.
- `PreCompact` writes a safety-net snapshot before an unattended auto-compaction.

Prefer `/compact` at the threshold when possible (native, keeps the phase automatically); use clear-and-reload when the context is polluted.

## Configuration

`/flow-setup` writes `~/.finx/flow-config.json` (per engineer) and/or `<repo>/.finx/flow-config.json` (per project, project wins). Keys: `enforcement`, `contextThreshold`, `contextLimit`, `trivialMaxLines`, `maxActivePlans`, `autoArchiveDays`. Missing file means standard defaults.

## Integration with other planning/execute tools

The flow integrates through shared state artifacts, not through owning the commands — so an engineer's own plugins or planning tools coexist with it.

- **Opt-in.** A repo with no `.finx/flow.json` is never gated; personal tooling is unaffected.
- **Flow-independent features** work regardless of how you plan/execute: the baseline rules, force-guard, review skills, `context-watch`, `write-docs`, and `runtime-stack`.
- **Gate contract.** The flow-gate opens on any one of these signals, whichever tool produces it:
  - `.finx/flow.json` has `"phase": "execute"`;
  - `.finx/flow.json` has `"approved": true`;
  - `.finx/flow.json.activePlan` points to a `plan.md` whose frontmatter `status` is `approved` or `in-progress` (created by any tool, not just `/flow`).
- **Disable per engineer.** Set `enforcement: guided` (track, never block) or `off` in `~/.finx/flow-config.json` to keep everything except the gate while using your own flow.

So another tool integrates by writing the shared `.finx/flow.json` / `.finx/plans/` artifacts; it does not need to be a finx-core command.

## Related skills

- `plans`, `plan-tidy` — plan lifecycle and migrating loose root `plan*.md` files.
- `pre-ship` — the verification gate used by `/flow review`.
- `logging-review`, `error-handling-review` — convention reviews invoked during review.
