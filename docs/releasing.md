# Releasing and Updating `finx-core`

How a new version of the plugin is cut (maintainers) and how engineers pull it (consumers).

## Versioning

- Semantic versioning `MAJOR.MINOR.PATCH`.
- `MAJOR` — a breaking change to a rule, hook behavior, or command that teams must react to.
- `MINOR` — a new skill, hook, or rule; backward compatible.
- `PATCH` — wording, bug fix, threshold tweak.
- The version lives in two files and **must match**: `plugins/finx-core/.claude-plugin/plugin.json` and the `finx-core` entry in `.claude-plugin/marketplace.json`. Use `release.sh` so they never drift.

## Maintainer release workflow

1. Make the change:
   - Rules/principles → edit `plugins/finx-core/canonical/conventions.json` (never hand-edit `hooks/baseline-rules.md` or `canonical/out/` — they are generated).
   - Skills → `plugins/finx-core/skills/<name>/SKILL.md`.
   - Hooks → `plugins/finx-core/hooks/`.
2. Bump + regenerate in one step:
   ```bash
   ./release.sh 0.18.0
   ```
   This updates both manifests and runs `canonical/generate.py` (regenerating `baseline-rules.md` and `canonical/out/kiro/*.md`).
3. Add a `[0.18.0]` section to `CHANGELOG.md` describing what changed and why.
4. Sanity-check:
   ```bash
   python3 -c "import json,glob; [json.load(open(f)) for f in ['.claude-plugin/marketplace.json','plugins/finx-core/.claude-plugin/plugin.json','plugins/finx-core/hooks/hooks.json']]; print('json ok')"
   ```
5. Commit with a conventional message, tag, push:
   ```bash
   git add -A
   git commit -m "feat: <what changed> (finx-core 0.18.0)"
   git tag v0.18.0
   git push && git push --tags
   ```
6. Announce the version and the one-line reason in the team channel.

## Engineer update workflow

When a new version is announced:

```
/plugin marketplace update finx-conventions
/plugin update finx-core
/reload-plugins
```

Then **start a new session** (or `/clear`) so the `SessionStart` hook re-injects the updated baseline. Hook and config reads (`flow-gate`, `context-watch`) take effect on the next tool call; they do not need a reload.

## First-time install

```
/plugin marketplace add <git-url-of-this-repo>
/plugin install finx-core@finx-conventions
```

Optionally personalize the flow (`/flow-setup`) to set enforcement level and thresholds; without it the standard defaults apply.

## What updates cannot do automatically

- `SessionStart` baseline only refreshes on a new/cleared/resumed session, not mid-session.
- Personal `flow-config.json` overrides are never touched by an update; new config keys fall back to defaults until the engineer opts in.
- Archived personal commands (`~/.claude/_archived-commands/`) are not restored by an update.

## Rollback

Install a previous tag:

```
/plugin marketplace update finx-conventions
/plugin install finx-core@finx-conventions   # after the maintainer re-points main, or
```
or, maintainer side, revert the release commit and cut a new patch version. Do not delete published tags.
