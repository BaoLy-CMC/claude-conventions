---
name: write-changelog
description: Refine a drafted CHANGELOG entry for a release - turn terse conventional-commit lines into clear, user-facing notes that say what changed and why. Use after running changelog.sh (or release.sh), when preparing a release, or when the user says "write changelog", "refine changelog", "changelog for this release". Report the refined entry for approval; do not commit or tag.
---

# Write Changelog (refine step)

`changelog.sh` produces a deterministic first draft grouped by Keep-a-Changelog section (Added / Changed / Fixed / Docs) from conventional commits. This skill turns that draft into notes a reader actually understands. It is the "refine" half of the hybrid workflow; the script is the "draft" half.

## Steps

1. Read the drafted `## [<version>]` block at the top of `CHANGELOG.md` (run `changelog.sh <version>` first if it is missing).
2. For context, read the commits and diff since the last tag:
   ```bash
   git log $(git describe --tags --abbrev=0)..HEAD --stat
   ```
3. Rewrite each bullet to be **user-facing**: what changed and, briefly, **why** it matters - not just the commit subject. Merge duplicates; drop noise (pure `chore`/`ci`/`test` that has no user impact).
4. Keep the sections and order: `Added`, `Changed`, `Fixed`, `Docs`. Flag any breaking change clearly (a `**BREAKING**` bullet plus a one-line migration note).
5. Keep the `## [<version>] - <date>` heading and date from the draft.
6. Show the refined entry and ask the user to approve before it is committed.

## Style

- One bullet per change; concrete subject; the "why" in a short clause.
- No icons or emoji. Reference `file:line`, ticket, or PR where it clarifies.
- Match the tone of existing entries in `CHANGELOG.md`.

## Guardrails

- Do not invent changes that are not in the commits/diff. If a change lacks a clear reason, ask rather than guess.
- Do not commit or tag - that is the human/`release.sh` step. This skill only edits the `CHANGELOG.md` entry.
