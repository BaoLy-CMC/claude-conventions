#!/usr/bin/env python3
"""Regenerate <hub>/plans/INDEX.md — every plan of every repo, plus which
session holds which plan open.

    python3 "$CLAUDE_PLUGIN_ROOT/scripts/plans-index.py"

The hub comes from the `hub` key in flow-config.json (default ~/.finx/hub).
"""
import json
import os
import sys
from datetime import date, datetime

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "hooks"))
import finxflow  # noqa: E402

TODAY = date.today()


def age(ts) -> int:
    return (TODAY - datetime.fromtimestamp(ts).date()).days


def sessions(hub: str) -> list:
    """Open sessions: (session_id, repo, phase, abs plan path, state age)."""
    out = []
    d = os.path.join(hub, "sessions")
    if not os.path.isdir(d):
        return out
    for name in sorted(os.listdir(d)):
        if not name.endswith(".json"):
            continue
        try:
            st = json.load(open(os.path.join(d, name), encoding="utf-8"))
        except Exception:
            continue
        repo = st.get("repo", "")
        plan = finxflow.resolve_plan(st, repo) if repo else ""
        a = None
        if st.get("updated"):
            try:
                a = (TODAY - date.fromisoformat(st["updated"])).days
            except ValueError:
                pass
        out.append((name[:-5], repo, st.get("phase", "idle"), plan, a))
    return out


def kind_of(rel_parts) -> str:
    if "archive" in rel_parts:
        return "archive"
    if "_loose" in rel_parts:
        return "loose"
    return "active"


def main() -> int:
    hub = finxflow.hub()
    plans = os.path.join(hub, "plans")
    if not os.path.isdir(plans):
        print(f"no plans directory at {plans}", file=sys.stderr)
        return 1

    open_sessions = sessions(hub)
    pointed = {s[3] for s in open_sessions if s[3]}

    groups = {}
    for root, _dirs, files in os.walk(plans):
        for f in sorted(files):
            if not f.endswith(".md"):
                continue
            full = os.path.join(root, f)
            rel = os.path.relpath(full, plans)
            if rel == "INDEX.md":
                continue
            parts = rel.split(os.sep)
            owner = "/".join(parts[:2]) if len(parts) > 2 else parts[0]
            groups.setdefault(owner, []).append((full, rel, parts))

    total = sum(len(v) for v in groups.values())
    L = [
        "# Plans — every repo, one index",
        "",
        f"Generated {TODAY} by `plans-index.py`. Do not hand-edit.",
        "",
        f"Hub: `{hub}` · {total} files · {len(groups)} owners · "
        f"{len(open_sessions)} session state files",
        "",
        "## Open sessions",
        "",
        "| Session | Repo | Phase | Plan | State age |",
        "|---|---|---|---|---|",
    ]
    live = [s for s in open_sessions if s[2] != "idle" or s[3]]
    for sid, repo, phase, plan, a in live:
        name = os.path.basename(os.path.dirname(plan)) if plan.endswith("plan.md") else (
            os.path.splitext(os.path.basename(plan))[0] if plan else "—")
        warn = " ⚠" if a is not None and a >= 14 else ""
        L.append(f"| `{sid[:8]}` | `{os.path.basename(repo) or '—'}` | {phase} | {name} | "
                 f"{'—' if a is None else str(a) + 'd'}{warn} |")
    if not live:
        L.append("| — | — | — | — | — |")
    L += ["", f"*{len(open_sessions) - len(live)} idle session files.*",
          "", "## Plans by owner", ""]

    for owner, files in sorted(groups.items()):
        counts = {"active": 0, "archive": 0, "loose": 0}
        for _f, _r, parts in files:
            counts[kind_of(parts)] += 1
        L += [f"### `{owner}`", "",
              f"{counts['active']} active · {counts['archive']} archive · {counts['loose']} loose",
              "", "| Plan | Kind | Last touched |", "|---|---|---|"]
        for full, rel, parts in sorted(files, key=lambda x: -os.path.getmtime(x[0])):
            base = os.path.basename(full)
            name = os.path.basename(os.path.dirname(full)) if base == "plan.md" \
                else os.path.splitext(base)[0]
            mark = " ← **open**" if full in pointed else ""
            L.append(f"| [{name}]({rel}){mark} | {kind_of(parts)} | {age(os.path.getmtime(full))}d |")
        L.append("")

    with open(os.path.join(plans, "INDEX.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")
    print(f"{plans}/INDEX.md — {total} plans, {len(groups)} owners, "
          f"{len(live)} open sessions")
    return 0


if __name__ == "__main__":
    sys.exit(main())
