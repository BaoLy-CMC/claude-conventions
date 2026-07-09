---
name: plan-tidy
description: Migrate scattered plan files at the repo root into the structured .finx/plans/ layout. Use when the user says "tidy plans", "organize plans", "clean up plan files", "migrate plans", or when loose plan*.md / *-plan.md files are cluttering the repo root. Moves files with confirmation — never deletes or overwrites silently.
---

# Plan Tidy — migrate loose root plans

Consolidate scattered plan files (`plan.md`, `plan-*.md`, `*-plan.md`, `sync-matrix.md`-style companions) at the repo root into `.finx/plans/` (see the `plans` skill for the structure).

## Steps

1. **Find** candidates at the repo root: `plan*.md`, `*-plan.md`, and obvious companions. List them.
2. **Read the first lines** of each to infer `title` and `status` (active work vs finished vs abandoned). Do not guess blindly — open each file.
3. **Propose a mapping** and show it to the user before touching anything:
   ```
   plan-otp-qr-refactor.md    -> .finx/plans/001-otp-qr-refactor/plan.md   (status: in-progress?)
   plan-saga-architecture.md  -> .finx/plans/002-saga-architecture/plan.md (status: done?)
   plan.md                    -> .finx/plans/003-<infer>/plan.md           (unrelated? confirm)
   ```
4. **CONFIRM with the user** — this touches existing files. Ask about any file whose status/ownership is unclear (e.g. an unrelated `plan.md`). Do not assume.
5. **Migrate** each approved file:
   - `git mv` (if a git repo) into `.finx/plans/NNN-slug/plan.md`, preserving history; else move.
   - Prepend the frontmatter block (id, title, status, created, source) if missing.
   - Move finished ones straight to `.finx/plans/archive/`.
6. **Update** `.finx/plans/INDEX.md` and set `flow.json.activePlan` to the one in-flight plan (ask if more than one looks active — only one active allowed).
7. Ensure `.finx/` is in `.gitignore`.
8. Report what moved where; leave originals removed only after a successful move (never delete unmigrated files).

## Guardrails

- Never overwrite an existing `.finx/plans/` entry — pick the next free `NNN`.
- Never delete a file you did not migrate.
- If a root file is clearly NOT a plan (e.g. a data dump), leave it and note it.
