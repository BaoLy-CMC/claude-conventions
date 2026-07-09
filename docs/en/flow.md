# Flow

Tiếng Việt: [../vi/flow.md](../vi/flow.md) | Back to [README](../../README.md)

The enforced development loop: `explore -> plan -> execute -> review -> reset`. It keeps non-trivial work disciplined (an approved plan before code) and survives long sessions (context-aware save and resume).

## Phases

Driven by one command, `/flow <phase>` - a single command so it does not collide with any personal `explore/plan/execute/reset` commands.

| Phase | Command | What happens |
|-------|---------|--------------|
| explore | `/flow explore [task]` | Map scope (controller -> service -> repository, prior art, impacted files). No edits. |
| plan | `/flow plan` | Create/activate a plan under `.finx/plans/`, write architecture + step blueprint, get it approved. |
| execute | `/flow execute` | Requires a ready-to-execute signal (below). Implement per plan, 1-2 files per batch. |
| review | `/flow review` | Run the `pre-ship` gate. Fix CRITICAL/HIGH. |
| reset | `/flow reset` | Save `state_summary.md` + MemPalace, archive the done plan, return to idle. |
| status | `/flow status` | Show phase, active plan, task. |

## State (in `.finx/`)

- `flow.json` - `{ phase, activePlan, task, updated }`. The flow-gate reads this.
- `plans/NNN-slug/plan.md` - one directory per plan, frontmatter `status: draft|approved|in-progress|done|abandoned`. One active plan at a time; guarded at max 3 active with auto-archive of done plans (see the `plans` skill).
- `state_summary.md` - a volatile resume pointer (phase, done, remaining, next action). Durable state stays in `plan.md`, `git diff`, and the code.

## Enforcement (the flow-gate)

A `PreToolUse` hook blocks edits to production Java (`**/src/main/**/*.java`) when a flow is active but not ready and the change is non-trivial (more than `trivialMaxLines`, default 30). Levels (set via `/flow-setup`):

- `hybrid` (default) - block non-trivial production edits when not ready; trivial edits pass.
- `hard` - block all production edits when not ready.
- `guided` - track the flow, never block.
- `off` - disabled.

Opt-in: a repo with no `.finx/flow.json` is never gated. Escape a false positive with `FINX_SKIP_HOOKS=1`.

## Long sessions: context-watch and reset

- `UserPromptSubmit` estimates context usage from the transcript. At the threshold (default 65%) it asks whether to `/compact`, save-and-clear-and-reload, or continue. It warns once per 10% bucket.
- Save-and-reload writes `state_summary.md`; after `/clear`, the `SessionStart` hook reloads it under a RESUME banner so the next session continues at the same phase.
- `PreCompact` writes a safety-net snapshot before an unattended auto-compaction.

Prefer `/compact` at the threshold when possible (native, keeps the phase automatically); use clear-and-reload when the context is polluted.

## Integration with other planning/execute tools

The flow integrates through shared state artifacts, not by owning the commands, so personal plugins and tools coexist with it.

- **Opt-in**: no `.finx/flow.json` means no gate.
- **Flow-independent features** work regardless of how you plan/execute: baseline rules, force-guard, review skills, context-watch, `write-docs`, `runtime-stack`.
- **Gate contract** - the gate opens on any one of these signals, whichever tool produces it:
  - `.finx/flow.json` has `"phase": "execute"`;
  - `.finx/flow.json` has `"approved": true`;
  - `.finx/flow.json.activePlan` points to a `plan.md` whose `status` is `approved` or `in-progress` (any origin).
- **Disable per engineer**: `enforcement: guided` or `off` in `~/.finx/flow-config.json`.

Another tool integrates by writing the shared `.finx/flow.json` / `.finx/plans/` artifacts; it does not need to be a finx-core command.

## Configuration

`/flow-setup` writes `~/.finx/flow-config.json` (per engineer) and/or `<repo>/.finx/flow-config.json` (per project, project wins). Keys: `enforcement`, `contextThreshold`, `contextLimit`, `trivialMaxLines`, `maxActivePlans`, `autoArchiveDays`. A missing file means standard defaults.

## Related skills

`plans`, `plan-tidy` (plan lifecycle and migration), `pre-ship` (the review gate), `logging-review` and `error-handling-review` (reviews used during review).
