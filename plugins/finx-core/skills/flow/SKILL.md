---
name: flow
description: Drive and track the enforced FinX dev flow — explore → plan → execute → review → reset — with per-repo state in .finx/flow.json. Use when the user says "/flow", "start flow", "flow status", "next phase", "explore [task]", "move to execute", "review", "reset flow", or when beginning non-trivial work that should follow the disciplined flow. Named `flow` (single command with a phase arg) to avoid colliding with any personal explore/plan/execute/reset skills.
---

# FinX Dev Flow

A disciplined loop for non-trivial work: **explore → plan → execute → review → reset**. Trivial one-off edits don't need it (per the baseline principles). State lives in `.finx/flow.json`; plans are managed by the `plans` skill.

## State — `.finx/flow.json`

```json
{
  "phase": "idle",          // idle | explore | plan | execute | review
  "activePlan": null,        // path to .finx/plans/NNN-slug/plan.md
  "task": null,              // short description of current work
  "updated": "<ISO date>"
}
```

Create it on first use. Every phase transition rewrites `phase` + `updated`. The flow-gate reads this file.

## Phases — `/flow <phase>`

| Command | Sets phase | Does |
|---|---|---|
| `/flow status` (or `/flow`) | — | Print current phase, active plan, task. |
| `/flow explore [task]` | `explore` | Map scope: trace controller→service→repository, find similar prior work, list impacted files. **No edits.** Output a scope map. |
| `/flow plan` | `plan` | Via the `plans` skill: create/activate a plan (`.finx/plans/NNN-slug/plan.md`), write architecture + step blueprint with a verify per step. Ask the user to approve (native plan mode). On approval set the plan `status: approved`. |
| `/flow execute` | `execute` | **Precondition: `activePlan` exists and its `status` is `approved` or `in-progress`** — otherwise stop and tell the user to `/flow plan` first. Set plan `status: in-progress`. Implement per the plan, 1–2 files per batch, running the verify for each step. |
| `/flow review` | `review` | Run the `pre-ship` gate (build + Checkstyle + tests/coverage + review skills + Sonar) on the working diff. Fix CRITICAL/HIGH before proceeding. |
| `/flow reset` | `idle` | Save `.finx/state_summary.md` (see below) + MemPalace checkpoint; mark the active plan `done` and archive it (via `plans`); clear `phase`→`idle`, `activePlan`→null. |

## Transitions & discipline

- Normal order is explore → plan → execute → review → reset, but the user may jump (e.g. straight to `execute` on an approved plan). Never skip an **approved plan** before `execute` for non-trivial work — that's what the flow-gate enforces.
- Keep exactly **one active plan** (the `plans` skill guards max-active).
- On any concern mid-flow (scope creep, unclear requirement, risky change) → stop and ask with a recommendation (baseline principle).

## `state_summary.md` (written on reset / context save)

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
