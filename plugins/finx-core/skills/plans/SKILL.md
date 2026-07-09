---
name: plans
description: Manage development plans for a repo under a single structured location. Use when the user says "list plans", "show plans", "which plan is active", "plan status", "too many plans", "new plan", "archive plan", or when a plan needs creating/activating/closing. Keeps plans out of the repo root and enforces a one-active-plan-at-a-time lifecycle.
---

# Plan Management

All dev plans live under **`.finx/plans/`** in the working repo — never as loose `plan*.md` at the repo root.

## Structure

```
.finx/
├── flow.json                 # { "phase": "...", "activePlan": ".finx/plans/003-slug/plan.md" }
└── plans/
    ├── INDEX.md              # auto-maintained table of all plans + status
    ├── 001-otp-qr-refactor/plan.md
    ├── 003-claude-conventions/plan.md
    └── archive/
        └── 002-saga-architecture/plan.md
```

Each `plan.md` starts with frontmatter:

```yaml
---
id: 003
title: Claude conventions plugin
status: approved        # draft | approved | in-progress | done | abandoned
created: 2026-07-09
ticket: VWFP-000        # optional Jira id
source: session|confluence|manual
---
```

## Lifecycle

`draft → approved → in-progress → done → abandoned`. `done`/`abandoned` plans are moved to `.finx/plans/archive/`.

## Single active plan

`.finx/flow.json.activePlan` points to the one plan currently being worked. This is the signal the flow-gate reads for "plan approved" (an active plan with `status: approved` or `in-progress`). Creating/activating a plan updates this pointer.

## Operations

- **list**: read `INDEX.md` (or scan dirs); show id, title, status, active marker. Rebuild `INDEX.md` if stale.
- **new**: check the active-plan guard first (below); create `NNN-slug/plan.md` with frontmatter (`NNN` = next zero-padded id), set it active, add to `INDEX.md`.
- **activate `<id>`**: set `flow.json.activePlan`; only one active at a time.
- **done / archive `<id>`**: set status, move dir to `archive/`, clear `activePlan` if it was active, update `INDEX.md`.

## Guards ("too many plans")

- **Max active plans = 3** (default, configurable via `/flow-setup`). Before creating a new plan, if active (non-archived) plans ≥ max, **stop and ask** the user to close/archive one first — list the candidates.
- **Auto-archive**: plans `status: done` older than **14 days** (default) are moved to `archive/`; mention what was archived.
- First use in a repo: ensure `.finx/` is git-ignored (add to `.gitignore` if missing) — plans are personal working artifacts; durable design docs get promoted to Confluence.

Keep it simple: don't create empty plan scaffolding "for later"; a plan exists only for real in-flight work.
