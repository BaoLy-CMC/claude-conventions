---
name: flow
description: Use when the user says "/flow", "start flow", "flow status", "next phase", "explore [task]", "move to execute", "review", "save before clearing", "resume my previous session", "reset flow", or when starting non-trivial work.
---

# FinX Dev Flow

A disciplined loop for non-trivial work: **explore → plan → execute → review → reset**. Trivial one-off edits don't need it (per the baseline principles). State is per session; plans are managed by the `plans` skill.

## State — `<hub>/sessions/<session_id>.json`

```json
{
  "sessionId": "<id>",
  "repo": "/abs/path/to/repo",
  "phase": "idle",           // idle | explore | plan | execute | review
  "activePlan": null,         // path relative to <hub>/plans/
  "task": null,               // short description of current work
  "approved": false,
  "updated": "<ISO date>"
}
```

**Keyed by session, not by directory.** Several sessions in the same repo each keep their own phase and plan — running many sessions at once is the normal case, not an edge case.

Get `<session_id>` from the `FINX_SESSION_ID` line injected by the SessionStart hook. If it is missing, tell the user the flow cannot track state rather than writing a repo-local file.

Resolve `<hub>` from the `hub` key in `flow-config.json` (project overrides global), default `~/.finx/hub`.

Create the file on first use. Every phase transition rewrites `phase` + `updated`. The flow-gate reads it.

> Legacy: a repo-local `.finx/flow.json` is still **read** as a fallback so flows in flight across the upgrade survive. Never write one. It is dropped after two releases.

## Phases — `/flow <phase>`

| Command | Sets phase | Does |
|---|---|---|
| `/flow status` (or `/flow`) | — | Print current phase, active plan, task. |
| `/flow explore [task]` | `explore` | Map scope: trace controller→service→repository, find similar prior work, list impacted files. **No edits.** Output a scope map. |
| `/flow plan` | `plan` | Via the `plans` skill: create/activate a plan (`<hub>/plans/<group>/<repo>/NNN-slug/plan.md`), write architecture + step blueprint with a verify per step. Ask the user to approve (native plan mode). On approval set the plan `status: approved`. |
| `/flow execute` | `execute` | **Precondition: `activePlan` exists and its `status` is `approved` or `in-progress`** — otherwise stop and tell the user to `/flow plan` first. Set plan `status: in-progress`. Implement per the plan, 1–2 files per batch, running the verify for each step. |
| `/flow review` | `review` | Run the `pre-ship` gate (build + Checkstyle + tests/coverage + review skills + Sonar) on the working diff. Fix CRITICAL/HIGH before proceeding. |
| `/flow save` | unchanged | Pause mid-work before `/clear`. Write the resume breadcrumb (see below) + MemPalace checkpoint. **Keeps** `phase` and `activePlan` — this is a break, not an ending. Report the handle back: `saved: k3f9 — resume with /flow resume k3f9 after /clear`. |
| `/flow resume <handle>` | unchanged | Load `<hub>/state/<repo-slug>/<handle>.md` into context and continue from the recorded phase. Without a handle, list the candidates and ask. |
| `/flow reset` | `idle` | Finish. Write the breadcrumb + MemPalace checkpoint; mark the active plan `done` and archive it (via `plans`); clear `phase`→`idle`, `activePlan`→null. |

## Transitions & discipline

- Normal order is explore → plan → execute → review → reset, but the user may jump (e.g. straight to `execute` on an approved plan). Never skip an **approved plan** before `execute` for non-trivial work — that's what the flow-gate enforces.
- Keep **one active plan per session**. Other sessions having their own open plans is expected — never close or repoint another session's state.
- On any concern mid-flow (scope creep, unclear requirement, risky change) → stop and ask with a recommendation (baseline principle).

## Resume breadcrumb — `<hub>/state/<repo-slug>/<handle>.md`

Keyed by repo **and** a short handle derived from the session id, so parallel sessions in one repo never overwrite each other.

**Why a handle and not automatic detection.** `/clear` mints a new session id, and Claude Code keeps the old transcript on disk — nothing links a new session to the one it replaced, and "which transcript died" cannot answer it either. Rather than guess wrong, the engineer carries four characters across. `SessionStart` offers a lone breadcrumb under 15 minutes old without one; with several candidates it lists them and waits.

Repeated saves from one session rewrite the same file — never append. An unattended `PreCompact` snapshot replaces only the part below the `<!-- finx-auto-snapshot -->` divider, so it cannot destroy a `/flow save`. Breadcrumbs older than 7 days age out.

Volatile pointer only — durable state stays in `plan.md` + `git diff` + code:

```markdown
# State summary — <task>
phase: <phase>        activePlan: <path>
Done: <tasks/files completed>
Remaining: <tasks/files left>
Next action: <the single next concrete step>
Assumptions/decisions: <...>
Open errors: <failing tests / blockers>
```

This is what a fresh session reloads (see the context-watch / reset hooks) to resume the exact phase.
