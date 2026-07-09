# Changing conventions, releasing, and updating

Tiếng Việt: [../vi/releasing.md](../vi/releasing.md) | Back to [README](../../README.md)

## How to change a convention

1. Decide where the change belongs:
   - A rule in the always-on baseline -> edit `plugins/finx-core/canonical/conventions.json`. Never hand-edit `hooks/baseline-rules.md` or `canonical/out/` - they are generated.
   - A skill -> `plugins/finx-core/skills/<name>/SKILL.md`.
   - A hook -> `plugins/finx-core/hooks/`.
2. Regenerate (only needed for canonical changes; `release.sh` also does this):
   ```bash
   python3 plugins/finx-core/canonical/generate.py
   ```
3. Cut a release (next section).

A canonical section carries a `kiro` list controlling which Kiro steering files it appears in; an empty list means Claude-baseline only (used for the communication style, which is not a Kiro code convention).

## Versioning

Semantic versioning `MAJOR.MINOR.PATCH`:

- `MAJOR` - a breaking change to a rule, hook behavior, or command that teams must react to.
- `MINOR` - a new skill, hook, or rule; backward compatible.
- `PATCH` - wording, a bug fix, a threshold tweak.

The version lives in two files and must match: `plugins/finx-core/.claude-plugin/plugin.json` and the `finx-core` entry in `.claude-plugin/marketplace.json`. Use `release.sh` so they never drift.

## Maintainer release workflow

1. Make the change (above).
2. Bump + regenerate in one step:
   ```bash
   ./release.sh 0.21.0
   ```
   This sets the version in both manifests and runs the generator.
3. Add a `[0.21.0]` section to `CHANGELOG.md` describing what changed and why.
4. Commit, tag, push:
   ```bash
   git add -A
   git commit -m "feat: <what changed> (finx-core 0.21.0)"
   git tag v0.21.0
   git push && git push --tags
   ```
5. Announce the version and the one-line reason.

## Engineer update workflow

Claude Code auto-updates plugins at startup: on restart it does a `git pull` of the marketplace and picks up the new version (because each release bumps the version string). So the normal path is simply **restart Claude Code**. The `version-notice` hook then prints, at session start, that finx-core moved to the new version and what changed.

To pull immediately, without waiting for a restart:

```
/plugin marketplace update finx-conventions
/plugin update finx-core
/reload-plugins
```

After either path, start a new session (or `/clear`) so the `SessionStart` hook re-injects the updated baseline. Hook and config reads (`flow-gate`, `context-watch`) take effect on the next tool call and need no reload.

## First-time install

```
/plugin marketplace add <internal-git-url>
/plugin install finx-core@finx-conventions
```

Optionally run `/flow-setup`; without it the standard defaults apply.

## What an update cannot do automatically

- The `SessionStart` baseline only refreshes on a new/cleared/resumed session, not mid-session.
- Personal `flow-config.json` overrides are never touched; new config keys fall back to defaults until the engineer opts in.
- Archived personal commands (`~/.claude/_archived-commands/`) are not restored.

## Rollback

Revert the release commit and cut a new patch version, or pin a previous tag. Do not delete published tags.
