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
if git -C "$ROOT" rev-parse -q --verify "refs/tags/v$VERSION" >/dev/null; then
  echo "Tag v$VERSION already exists — pick another version, or delete it first." >&2
  exit 1
fi
# The release commit is built from specific paths, so unrelated work in the tree
# is fine — but a dirty version file means someone already hand-edited it.
if ! git -C "$ROOT" diff --quiet -- .claude-plugin/marketplace.json \
     plugins/finx-core/.claude-plugin/plugin.json; then
  echo "Version manifests already modified — commit or revert them first." >&2
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

echo "committing + tagging (local only)..."
git -C "$ROOT" add \
  .claude-plugin/marketplace.json \
  plugins/finx-core/.claude-plugin/plugin.json \
  CHANGELOG.md \
  plugins/finx-core/hooks/baseline-rules.md \
  plugins/finx-core/canonical/out
if git -C "$ROOT" diff --cached --quiet; then
  echo "nothing to commit — already at $VERSION?" >&2
  exit 1
fi
git -C "$ROOT" commit -q -m "chore: release finx-core $VERSION"
git -C "$ROOT" tag "v$VERSION"
echo "  committed $(git -C "$ROOT" rev-parse --short HEAD), tagged v$VERSION"

cat <<EOF

NOT pushed. Nothing is released yet.

The marketplace clone tracks **main**, not tags — so pushing main is what
ships this to every engineer. The tag is a local marker until then.

  1. Refine the [$VERSION] CHANGELOG entry (write-changelog skill) if it was
     auto-drafted; amend the release commit.
  2. Release when ready:  git push origin main && git push origin v$VERSION
  3. Engineers pick it up on restart, or with
     /plugin marketplace update finx-conventions
EOF
