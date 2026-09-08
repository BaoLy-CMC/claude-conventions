---
name: release-workload
description: Drive a production release through the platform-release-processes repo — the three stages (release_uat cuts the branch, pre_release tags, release opens the workload PR and publishes the Confluence checklist), the YAML an engineer adds per date and team, the .done idempotency marker, and the tag-immutability / roll-forward rule. Use when asked to release a service to production, cut a release branch, tag a version, re-run a release folder, or when a release stage did nothing after merge. Source: Confluence EN/1908572168 (v1.0).
---

# Release Workload

Production releases are driven by the **`platform-release-processes`** repo. An engineer's unit of work is **adding one YAML file** under a dated folder and opening a PR. Never edit the Python.

```
<stage_root>/<yyyy-MM-dd>/<team>/<config>.yaml
<stage_root>/<yyyy-MM-dd>/<team>/.done      # marker, committed by the system
```

| Stage | Root | Config | Does |
|---|---|---|---|
| 1 | `release_uat/` | `repo_info.yaml` (`name`, optional `from_branch`, default `main`) | Cuts `release/<date>` |
| 2 | `pre_release/` | `repos.yaml` (`name`, `tag`, `branch`, `process`) | Tags `vX.Y.Z` |
| 3 | `release/` | `release-note.yaml` | Opens the `prod-application-workload` PR + publishes the Confluence checklist |

## Invariants

- **Nothing changes before merge.** CI runs `--mode ci` on the pull request and only validates (`contents: read`); CD runs `--mode cd` on push to `main`.
- **The release branch name comes from the date folder.** `release_uat/2026-05-15/...` cuts `release/2026-05-15`. Never declare the target branch in YAML.
- **The team folder is the isolation unit.** One team failing does not block another. The team name only scopes `.done` and the workload PR head branch (`release-<date>-<team>`) — it never affects the release branch name.
- **Engineers declare; the system does not discover.** Only repos listed in the YAML are touched.
- **`.done` is idempotency.** Only its existence matters. To re-run a folder, delete `.done` and commit it **in the same PR** as the config change — never hand-create it.
- **A merged tag is immutable.** If the workload PR is already `MERGED`, stage 2 answers `REFUSE_REQUIRE_ROLL_FORWARD` for that repo: roll forward with a new tag, never overwrite in place. `PRMergeState.MERGED` is evaluated first, always.
- `process: true` only exists in stages 2 and 3.
- `--mode cd` **has no `--dry-run`** and mutates production GitHub state. Never run it locally to "try" a config change; `--mode ci` is the read-only mode. To check work, read the YAML diff and run `python3 -m pytest -q`.

## Preflight (fail-fast, shared by CI and CD)

- Date folder must be a real date (`strptime`) — `2026-13-45` is rejected.
- Branch names must be valid git refs (a `release/` prefix is deliberately not enforced, so tagging from `main` or a hotfix branch stays legal).
- Stage 1: every `from_branch` must exist **before** anything is cut. One missing source branch fails CI and nothing is cut.
- Stage 2: for every `process: true` repo the tag must match `^v\d+\.\d+\.\d+(-hotfix)?$` **and** the branch must exist. One bad tag → nothing is tagged.
- Stage 3 CI validates deterministically: schema, tag format, tag exists on GitHub, `tag > previous-tag`, `valueFrom.secretKeyRef` structure, risky SQL in `manual-ops`, and that every `process: true` repo has an entry in `workload-repos-mapping.yaml`. Any `Severity.ERROR` → exit 1. The Copilot review step afterwards is advisory only (three layers of `continue-on-error`); the deterministic validation is the merge gate.
- A team folder missing its config file is a warning; that team is skipped.

## Stage 3 CD order (4 steps, order matters)

1. **Confluence preflight, before any GitHub call.** A failed `check_connection()` (missing credential, dead host, 401/403, wrong space) exits `4 EXIT_CONFLUENCE_ERROR` and creates no PR — so a workload PR never exists without documentation.
2. Create or update the `prod-application-workload` PR (already merged → refuse, roll forward).
3. Insert the PR `html_url` into the Workload row of the checklist's Pre-Flight table.
4. Publish the Confluence page (same title → `find_page` then `update_page`, version + 1, to refresh the PR link).

`mark_done` requires **both** the PR and the published page. A skipped or failed page means no `.done`, so the folder stays re-runnable while other teams continue; exit 4 is returned at the end.

## How the workload PR edits `values.yaml`

- Path resolved from `workload-repos-mapping.yaml` (`repo → directory → <directory>/values.yaml`). A `process: true` repo with no mapping is refused — CI fails before merge, CD logs and skips the team. Never guess a path.
- **Line surgery, not YAML round-trip.** `application.global.image.tag` is replaced; `application.deployment.extraEnvs` is upserted by `name` (`valueFrom.secretKeyRef` blocks copied whole). `yaml.safe_load` + `safe_dump` would strip every comment and turn a one-line release into a several-hundred-line diff.
- Envs not declared in the release note are **never** removed.
- No change → no commit (re-running a finished release creates no empty commit).

## Confluence checklist page

Render order: auto-generated banner → info table → Approvals → Changelogs → Feature Flags (only when declared) → Pre-Flight (Services row links `previous-tag...tag`, Workload row links the PR) → In-Flight → Post-Flight.

- Title `[<environments>][<Date_Folder>] <Team_Folder> - Deployment Checklist` (default env `PROD`) is the dedup key — changing the title or environments after the page exists creates a second page.
- Expected start/end time default from the date folder; `checklist.expected-*-time` only overrides.
- `confluence-parent-page-id` comes from `release-note.yaml`, not from the environment.
- Requester and the Release PR row are read from the config PR (`GITHUB_REPOSITORY` / `GITHUB_SHA` → which PR contains that commit). Missing env, a direct push to main, or an API error leave the cells blank — this metadata must never break a release.
- `feature-flags` go to Confluence only, never into `prod-application-workload`, rendered as an Old Value → New Value table.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| CI green, nothing happened after merge | Folder still has `.done` — CD skips it | Delete `.done` in the same PR as the config change |
| Need to re-cut or re-tag a folder | `.done` exists | Delete `.done` and commit; do not edit content, do not hand-create `.done` |
| Repo refused with `REFUSE_REQUIRE_ROLL_FORWARD` | Workload PR already merged to production | Roll forward with a new tag |
| Stage 3 CD exits 4, no PR created | Confluence preflight failed | Fix credential/space, re-run — the folder is still re-runnable |
| Stage 3 CI reports a missing mapping | `process: true` repo absent from `workload-repos-mapping.yaml` | Add the `repo → directory` entry at the repo root |
| Two Confluence pages with the same content | Title or environments changed after the page existed | Keep the original title; delete the extra page manually |

## Environment

`GIT_TOKEN` is required by every entrypoint (workflows use `secrets.FINX_BOT_TOKEN`). Stage 3 CD also needs `CONFLUENCE_BASE_URL`, `_SPACE`, `_USER`, `_PARENT_PAGE_ID` from `vars.*` and `CONFLUENCE_API_TOKEN` from `secrets.*`. `MODELS_TOKEN` / `AI_VERIFY_MODE` belong to the AI verify step, currently off. Jobs run on self-hosted runners. Logs redact secrets — a `valueFrom.secretKeyRef` value must never reach a log.

Per-stage `README.md` files inside the repo are the most precise reference at field level; `examples/` holds copy-paste templates and is never scanned by the processors.
