#!/usr/bin/env python3
"""SessionStart hook — tell the engineer when finx-core changed under them.

Claude Code auto-updates plugins at startup (git pull of the marketplace), so a
new version arrives silently. This hook makes that visible: it records the
installed version per engineer and, when it changes between sessions, prints the
new version and — when the CHANGELOG is reachable — that version's notes.

Reads only `plugin.json` (always present in the plugin, even from the marketplace
cache); the CHANGELOG read is best-effort. Fail-open and silent on any error.
"""
import json
import os
import sys

ROOT = os.environ.get(
    "CLAUDE_PLUGIN_ROOT",
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
)
STATE = os.path.expanduser("~/.finx/.finx-core-version")


def installed_version() -> str:
    try:
        with open(os.path.join(ROOT, ".claude-plugin", "plugin.json"), encoding="utf-8") as fh:
            return json.load(fh).get("version", "")
    except Exception:
        return ""


def changelog_section(version: str) -> str:
    """Best-effort: return the '## [version]' block if a CHANGELOG is reachable."""
    for path in (
        os.path.join(ROOT, "..", "..", "CHANGELOG.md"),
        os.path.join(ROOT, "CHANGELOG.md"),
    ):
        try:
            with open(path, encoding="utf-8") as fh:
                lines = fh.readlines()
        except Exception:
            continue
        out, capturing = [], False
        for line in lines:
            if line.startswith(f"## [{version}]"):
                capturing = True
                continue
            if capturing and line.startswith("## ["):
                break
            if capturing:
                out.append(line.rstrip())
        text = "\n".join(l for l in out if l.strip())
        if text:
            return text
    return ""


def main() -> int:
    version = installed_version()
    if not version:
        return 0
    try:
        last = open(STATE, encoding="utf-8").read().strip()
    except Exception:
        last = ""

    # Record current version for next time.
    try:
        os.makedirs(os.path.dirname(STATE), exist_ok=True)
        with open(STATE, "w", encoding="utf-8") as fh:
            fh.write(version)
    except Exception:
        pass

    # First run, or unchanged -> stay silent.
    if not last or last == version:
        return 0

    notes = changelog_section(version)
    sys.stdout.write(
        f"\n\n---\n\n## finx-core updated: {last} -> {version}\n"
    )
    if notes:
        sys.stdout.write(notes + "\n")
    else:
        sys.stdout.write(
            "See the changelog / `releasing.md` docs for what changed.\n"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
