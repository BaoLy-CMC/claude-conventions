#!/usr/bin/env bash
# Draft a CHANGELOG entry for <version> from the conventional commits since the
# last tag. Deterministic first pass; refine the prose (the "why") with the
# `write-changelog` skill before committing. Safe to re-run: skips if the
# version section already exists.
#
# Usage: ./changelog.sh <version>
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
VERSION="${1:-}"
if [[ -z "$VERSION" ]]; then
  echo "Usage: $0 <version>" >&2
  exit 1
fi
DATE="$(date +%F)"

python3 - "$VERSION" "$DATE" "$ROOT" <<'PY'
import re, subprocess, sys, os

version, date, root = sys.argv[1], sys.argv[2], sys.argv[3]
changelog = os.path.join(root, "CHANGELOG.md")

text = open(changelog, encoding="utf-8").read()
if f"## [{version}]" in text:
    print(f"CHANGELOG already has [{version}] - not regenerating.")
    sys.exit(0)

try:
    last_tag = subprocess.run(
        ["git", "-C", root, "describe", "--tags", "--abbrev=0"],
        capture_output=True, text=True).stdout.strip()
except Exception:
    last_tag = ""
rng = (f"{last_tag}..HEAD") if last_tag else "HEAD"
raw = subprocess.run(
    ["git", "-C", root, "log", rng, "--no-merges", "--pretty=format:%s"],
    capture_output=True, text=True).stdout.splitlines()

# type -> Keep-a-Changelog section. chore/ci/test/build/style are omitted.
SECTION = {"feat": "Added", "fix": "Fixed", "perf": "Changed",
           "refactor": "Changed", "revert": "Changed", "docs": "Docs"}
groups = {"Added": [], "Changed": [], "Fixed": [], "Docs": []}
# An optional "[JIRA-123] " prefix is accepted and dropped: the commit convention puts the
# ticket in the subject so `git log --oneline` stays greppable per ticket, but a CHANGELOG
# is read by people outside the tracker, to whom an internal key means nothing. Without
# this the whole subject fails to match and the commit vanishes from the release notes.
pat = re.compile(r"^(?:\[[A-Z][A-Z0-9]*-\d+\]\s*)?(\w+)(\([^)]*\))?(!)?:\s*(.+)$")

for subj in raw:
    m = pat.match(subj.strip())
    if not m:
        continue
    typ, scope, bang, desc = m.groups()
    section = SECTION.get(typ)
    if not section:
        continue
    bullet = desc
    if scope:
        bullet = f"{scope.strip('()')}: {desc}"
    if bang:
        bullet = "**BREAKING** " + bullet
    groups[section].append(bullet)

lines = [f"## [{version}] - {date}", ""]
any_entry = False
for section in ("Added", "Changed", "Fixed", "Docs"):
    items = groups[section]
    if not items:
        continue
    any_entry = True
    lines.append(f"### {section}")
    lines += [f"- {b}" for b in items]
    lines.append("")
if not any_entry:
    lines += ["### Changed", "- (describe this release - no conventional commits found)", ""]

block = "\n".join(lines)

# Insert before the first existing version section, else after the file header.
idx = text.find("\n## [")
if idx != -1:
    new = text[:idx + 1] + block + "\n" + text[idx + 1:]
else:
    new = text.rstrip() + "\n\n" + block + "\n"
open(changelog, "w", encoding="utf-8").write(new)
print(f"Drafted CHANGELOG [{version}] from {rng} ({len([l for g in groups.values() for l in g])} entries).")
print("Refine the prose (add the why) with the write-changelog skill, then commit.")
PY
