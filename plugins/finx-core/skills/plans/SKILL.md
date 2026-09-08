---
name: plans
description: Manage development plans across all repos under a single hub. Use when the user says "list plans", "show plans", "which plan is active", "plan status", "too many plans", "new plan", "archive plan", or when a plan needs creating/activating/closing. Keeps plans out of repo roots and tracks one active plan per session.
---

# Plan Management

All dev plans live in the **hub**, not in the working repo — never as loose `plan*.md` at a repo root.

The hub location comes from `hub` in `flow-config.json` (project overrides global), defaulting to `~/.finx/hub`. Resolve it before doing anything; do not hardcode a path.

## Structure

```
<hub>/
├── sessions/<session_id>.json    # flow state, one file per session
├── state/<repo-slug>/<handle>.md # resume breadcrumb, one per session
└── plans/
    ├── INDEX.md                  # auto-maintained, every plan of every repo
    ├── cross-repo/               # plans spanning several repos
    │   └── 009-pre-login-satellite/plan.md
    └── <group>/<repo>/           # e.g. bff/galaxy-g-bff-service/
        ├── 001-active-cif-lookup/plan.md
        ├── archive/
        │   └── 004-qr-login/plan.md
        └── _loose/               # unstructured notes: state_summary, scope-map
```

`activePlan` in session state is stored **relative to `<hub>/plans/`** — e.g. `bff/galaxy-g-bff-service/001-active-cif-lookup/plan.md`.

Each `plan.md` starts with frontmatter:

```yaml
---
id: 003
title: Claude conventions plugin
status: approved        # draft | approved | in-progress | done | abandoned
created: 2026-07-09
repo: bff/galaxy-g-bff-service   # owning repo, or "cross-repo"
ticket: VWFP-000        # optional Jira id
source: session|confluence|manual
---
```

## Lifecycle

`draft → approved → in-progress → done → abandoned`. `done`/`abandoned` plans move to the owning repo's `archive/`.

## Active plan is per session, not per repo

The `activePlan` in `<hub>/sessions/<session_id>.json` points to the one plan **this session** is working. Parallel sessions each hold their own — several plans open at once across repos is normal and supported. This is the signal the flow-gate reads for "plan approved" (an active plan with `status: approved` or `in-progress`).

Get the session id from the `FINX_SESSION_ID` line the SessionStart hook injects. Without it, state cannot be written — say so rather than falling back to a repo-local file.

## Operations

- **list**: read `INDEX.md`; show repo, id, title, status, active marker. Regenerate if stale.
- **new**: check the active-plan guard first (below); create `<group>/<repo>/NNN-slug/plan.md` with frontmatter (`NNN` = next free id **within that repo**), set it active for this session, update `INDEX.md`.
- **activate `<id>`**: set `activePlan` in this session's state file; one active per session.
- **done / archive `<id>`**: set status, move the dir to the repo's `archive/`, clear `activePlan` if it was this session's, update `INDEX.md`.

## Guards ("too many plans")

- **Max active plans = 3** (default, configurable via `/flow-setup`) counted **per repo across all sessions**, not globally — a machine running many sessions legitimately has many open plans. Before creating a new plan for a repo that is already at the max, stop and ask the user to close/archive one; list the candidates.
- **Auto-archive**: plans `status: done` older than **14 days** (default) move to `archive/`; mention what was archived.
- The hub holds every engineer's working plans. If it lives inside a git repo, make sure it is ignored — plans are personal working artifacts; durable design docs get promoted to Confluence.

Keep it simple: don't create empty plan scaffolding "for later"; a plan exists only for real in-flight work.
