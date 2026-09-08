# Flow

Tiếng Việt: [../vi/flow.md](../vi/flow.md) | Back to [README](../../README.md)

The enforced development loop: `explore -> plan -> execute -> review -> reset`. It keeps non-trivial work disciplined (an approved plan before code) and survives long sessions (context-aware save and resume).

## Phases

Driven by one command, `/flow <phase>` - a single command so it does not collide with any personal `explore/plan/execute/reset` commands.

| Phase | Command | What happens |
|-------|---------|--------------|
| explore | `/flow explore [task]` | Map scope (controller -> service -> repository, prior art, impacted files). No edits. |
| plan | `/flow plan` | Create/activate a plan under `<hub>/plans/<group>/<repo>/`, write architecture + step blueprint, get it approved. |
| execute | `/flow execute` | Requires a ready-to-execute signal (below). Implement per plan, 1-2 files per batch. |
| review | `/flow review` | Run the `pre-ship` gate. Fix CRITICAL/HIGH. |
| save | `/flow save` | Pause before `/clear`. Write the breadcrumb + MemPalace, **keep** phase and plan, report a handle. |
| resume | `/flow resume <handle>` | Load that breadcrumb and continue from the recorded phase. |
| reset | `/flow reset` | Finish. Breadcrumb + MemPalace, archive the done plan, return to idle. |
| status | `/flow status` | Show phase, active plan, task. |

## State (in the hub)

Everything lives in one hub directory, set by the `hub` key in `flow-config.json` (default `~/.finx/hub`). Nothing is stored in the working repo.

- `sessions/<session_id>.json` - `{ sessionId, repo, phase, activePlan, task, approved, updated }`. The flow-gate reads this.
- `plans/<group>/<repo>/NNN-slug/plan.md` - one directory per plan, frontmatter `status: draft|approved|in-progress|done|abandoned`. `activePlan` is stored relative to `plans/`. Max 3 active per repo, with auto-archive of done plans (see the `plans` skill).
- `state/<repo-slug>/<handle>.md` - a volatile resume pointer (phase, done, remaining, next action), one per session. Durable state stays in `plan.md`, `git diff`, and the code.

### Why per session, not per repo

State used to be a single `.finx/flow.json` per repo, found by walking up the directory tree. Two things broke:

- **Inheritance.** A repo with no `.finx/` of its own picked up the nearest ancestor's, so dozens of unrelated repos displayed and were gated by someone else's plan.
- **Collision.** Engineers routinely run many sessions at once; every session in a repo shared one file, so the last writer won and the others showed the wrong plan.

Work is bounded by a session, not by a directory, so the state is now keyed that way. Several plans open at once across several repos is the normal case. Resolution never walks above the repo root (`git rev-parse --show-toplevel`).

The session id comes from the `FINX_SESSION_ID` line that the `SessionStart` hook injects - a skill is only a prompt and has no other way to know which session it is in.

Session files are garbage-collected on `SessionStart`: dropped when the matching transcript under `~/.claude/projects/` is gone, or after 30 days. The current session and anything under a day old are always kept.

> **Legacy.** A repo-local `.finx/flow.json` is still *read* (repo root only, never written) so flows in flight across the upgrade survive. It is dropped after two releases.

## Enforcement (the flow-gate)

A `PreToolUse` hook blocks edits to production Java (`**/src/main/**/*.java`) when a flow is active but not ready and the change is non-trivial (more than `trivialMaxLines`, default 30). Levels (set via `/flow-setup`):

- `hybrid` (default) - block non-trivial production edits when not ready; trivial edits pass.
- `hard` - block all production edits when not ready.
- `guided` - track the flow, never block.
- `off` - disabled.

Opt-in: a session with no flow state is never gated. Escape a false positive with `FINX_SKIP_HOOKS=1`.

**Fail-closed on a missing session id.** `session_id` comes from the harness, not from this plugin. If it stops arriving, state can be neither read nor written, and a gate that silently allowed everything would look installed while enforcing nothing. Under `hybrid`/`hard` the gate blocks non-trivial production-Java edits with an explicit "no session id" message instead. `guided`, `off`, `FINX_SKIP_HOOKS=1` and the trivial-change exemption are unaffected.

## Long sessions: context-watch and reset

- `UserPromptSubmit` estimates context usage from the transcript. At the threshold (default 65%) it asks whether to `/compact`, save-and-clear-and-reload, or continue. It warns once per 10% bucket.
- `/flow save` writes `<hub>/state/<repo-slug>/<handle>.md` and reports the handle. After `/clear`, `SessionStart` reloads it under a RESUME banner.

**How the new session finds the old one.** It cannot, on its own. `/clear` mints a new session id, and Claude Code keeps the old transcript on disk, so neither an id nor a "which transcript died" test links them — every field in the transcript was checked, and `parentUuid` only threads messages inside one session. So the rule is: exactly one breadcrumb under 15 minutes old is offered automatically; anything else is listed with handle, age and task, and the engineer picks with `/flow resume <handle>`. Four characters carried across beats a guess that loads someone else's context.

Repeated saves rewrite the same file. An unattended `PreCompact` snapshot replaces only the part below the `<!-- finx-auto-snapshot -->` divider, so it never destroys a `/flow save`. Breadcrumbs age out after 7 days.
- `PreCompact` writes a safety-net snapshot before an unattended auto-compaction.

Prefer `/compact` at the threshold when possible (native, keeps the phase automatically); use clear-and-reload when the context is polluted.

## Integration with other planning/execute tools

The flow integrates through shared state artifacts, not by owning the commands, so personal plugins and tools coexist with it.

- **Opt-in**: no session state means no gate.
- **Flow-independent features** work regardless of how you plan/execute: baseline rules, force-guard, review skills, context-watch, `write-docs`, `runtime-stack`.
- **Gate contract** - the gate opens on any one of these signals, whichever tool produces it:
  - the session state has `"phase": "execute"`;
  - the session state has `"approved": true`;
  - `activePlan` points to a `plan.md` whose `status` is `approved` or `in-progress` (any origin).
- **Disable per engineer**: `enforcement: guided` or `off` in `~/.finx/flow-config.json`.

Another tool integrates by writing the shared `<hub>/sessions/<id>.json` / `<hub>/plans/` artifacts; it does not need to be a finx-core command.

## Configuration

`/flow-setup` writes `~/.finx/flow-config.json` (per engineer) and/or `<repo>/.finx/flow-config.json` (per project, project wins). Keys: `hub`, `enforcement`, `contextThreshold`, `contextLimit`, `trivialMaxLines`, `maxActivePlans`, `autoArchiveDays`. Choose `hub` early - moving it later means rewriting `activePlan` in every session file. A missing file means standard defaults.

## Related skills

`plans`, `plan-tidy` (plan lifecycle and migration), `pre-ship` (the review gate), `logging-review` and `error-handling-review` (reviews used during review).
