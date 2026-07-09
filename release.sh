#!/usr/bin/env bash
# Release helper for the finx-core plugin.
# Bumps the version in BOTH manifests (they must match), regenerates the
# canonical artifacts, and prints the remaining manual steps.
#
# Usage: ./release.sh <new-version>     e.g. ./release.sh 0.18.0
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
VERSION="${1:-}"
if [[ -z "$VERSION" ]]; then
  echo "Usage: $0 <new-version>   (e.g. 0.18.0)" >&2
  exit 1
fi
if ! [[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "Version must be semver X.Y.Z (got: $VERSION)" >&2
  exit 1
fi

MARKET="$ROOT/.claude-plugin/marketplace.json"
PLUGIN="$ROOT/plugins/finx-core/.claude-plugin/plugin.json"

python3 - "$VERSION" "$MARKET" "$PLUGIN" <<'PY'
import json, sys
version, market, plugin = sys.argv[1], sys.argv[2], sys.argv[3]

with open(plugin) as fh:
    p = json.load(fh)
p["version"] = version
with open(plugin, "w") as fh:
    json.dump(p, fh, indent=2); fh.write("\n")

with open(market) as fh:
    m = json.load(fh)
for entry in m.get("plugins", []):
    if entry.get("name") == "finx-core":
        entry["version"] = version
with open(market, "w") as fh:
    json.dump(m, fh, indent=2); fh.write("\n")
print(f"version -> {version} in plugin.json + marketplace.json")
PY

echo "regenerating canonical artifacts..."
python3 "$ROOT/plugins/finx-core/canonical/generate.py"

echo "drafting CHANGELOG from conventional commits..."
"$ROOT/changelog.sh" "$VERSION"

echo
echo "Next (manual):"
echo "  1. Refine the drafted [$VERSION] CHANGELOG entry (write-changelog skill), then approve."
echo "  2. git add -A && git commit -m \"chore: release finx-core $VERSION\""
echo "  3. git tag v$VERSION && git push && git push --tags"
echo "  4. Announce (optional): engineers auto-update on restart; /plugin marketplace update finx-conventions to pull now."
