---
name: plan-tidy
description: Migrate scattered plan files into the hub's structured plans layout. Use when the user says "tidy plans", "organize plans", "clean up plan files", "migrate plans", "gather plans from every repo", or when loose plan*.md / *-plan.md files are cluttering repo roots. Moves files with confirmation — never deletes or overwrites silently.
---

# Plan Tidy — gather loose plans into the hub

Consolidate scattered plan files (`plan.md`, `plan-*.md`, `*-plan.md`, `state_summary.md`, `scope-map*.md` companions) into `<hub>/plans/` (see the `plans` skill for the structure). Resolve `<hub>` from `flow-config.json` before starting.

Works on one repo, or across every repo on the machine when asked.

## Steps

1. **Survey** — do not move anything yet:
   - loose candidates at each repo root: `plan*.md`, `*-plan.md`, and obvious companions;
   - existing per-repo `.finx/plans/` trees left over from before the hub;
   - any `.finx/` directory at a *workspace* level (a directory above repos) — those bleed confusion and should be folded in as `<group>/_workspace/`.
   Exclude anything inside a source tree (`src/main/...`) — documentation that lives next to code is not a flow plan.
2. **Read the first lines** of each to infer `title` and `status` (active work vs finished vs abandoned). Do not guess blindly — open each file.
3. **Propose a mapping** and show it before touching anything:
   ```
   fsap/fsap-auth/plan-openapi-docs.md -> <hub>/plans/fsap/fsap-auth/_loose/plan-openapi-docs.md
   bff/gg-bff/.finx/plans/001-cif/     -> <hub>/plans/bff/gg-bff/001-cif/       (status: in-progress?)
   vikki/.finx/plans/002-profile/      -> <hub>/plans/vikki/_workspace/002-profile/
   ```
4. **CONFIRM with the user** — this touches existing files. Ask about any file whose status/ownership is unclear. Do not assume.
5. **Back up first**: `tar czf ~/finx-plans-backup-<date>.tar.gz` over everything about to move. Report the path.
6. **Dry-run the whole migration and show the count** before applying. A move script that has not been dry-run is not ready.
7. **Migrate** each approved file:
   - `git mv` inside a repo where it applies (preserves history); else move.
   - Structured plans keep their `NNN-slug/plan.md` shape; unstructured notes go to the repo's `_loose/`.
   - Prepend the frontmatter block (id, title, status, created, repo, source) if missing.
   - Finished ones go straight to the repo's `archive/`.
8. **Repoint state**: rewrite `activePlan` in each session file (and any legacy `.finx/flow.json` left in place) to the new hub-relative path. **Verify every rewritten path resolves to a real file** — print an OK/BROKEN line per repo.
9. **Regenerate** `<hub>/plans/INDEX.md`.
10. Ensure leftover `.finx/` dirs are ignored — prefer `.git/info/exclude` (local, leaves the repo's tracked `.gitignore` alone) unless the team wants it committed.
11. Report what moved where, and list anything deliberately left behind with the reason.

## Guardrails

- Never overwrite an existing entry in the hub — on a name clash, compare content (`md5sum`); if they differ, keep both under distinct names, never silently skip one and leave the user thinking it moved.
- Never delete a file that was not migrated.
- If a file is clearly NOT a plan (a data dump, docs inside `src/`), leave it and say so.
- Watch for shell `noclobber`: a bare `>` over an existing file fails silently in zsh and the stale content survives. Use `>|` when writing fixtures or generated files.
