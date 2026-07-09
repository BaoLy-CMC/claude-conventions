#!/usr/bin/env python3
"""PreCompact hook — safety-net snapshot of flow state before compaction.

A hook can't summarize the conversation (no LLM), so the RICH state_summary is
written by Claude via `/flow reset` or the context-watch "save" choice. This hook
only guarantees a breadcrumb survives an unattended auto-compaction: it appends
the flow phase, active plan, and the working git diff stat to
`.finx/state_summary.md`. Best-effort, fail-open.
"""
import json
import os
import subprocess
import sys


def find_up(start: str, rel: str):
    d = start
    while True:
        if os.path.exists(os.path.join(d, rel)):
            return os.path.join(d, rel)
        parent = os.path.dirname(d)
        if parent == d:
            return None
        d = parent


def git(root: str, *args: str) -> str:
    try:
        out = subprocess.run(
            ["git", "-C", root, *args],
            capture_output=True, text=True, timeout=5,
        )
        return out.stdout.strip()
    except Exception:
        return ""


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0
    cwd = data.get("cwd", "") or os.getcwd()
    trigger = data.get("trigger", "auto")

    flow_path = find_up(cwd, os.path.join(".finx", "flow.json"))
    if not flow_path:
        return 0  # no flow in use
    root = os.path.dirname(os.path.dirname(flow_path))
    try:
        flow = json.load(open(flow_path, encoding="utf-8"))
    except Exception:
        flow = {}

    diffstat = git(root, "diff", "--stat")
    status = git(root, "status", "--short")
    summary_path = os.path.join(root, ".finx", "state_summary.md")

    block = [
        "",
        f"<!-- auto-snapshot at compaction ({trigger}) -->",
        f"## Auto-snapshot ({trigger} compaction)",
        f"- phase: {flow.get('phase', 'idle')}",
        f"- activePlan: {flow.get('activePlan')}",
        f"- task: {flow.get('task')}",
        "",
        "### git diff --stat",
        "```",
        diffstat or "(no changes)",
        "```",
        "### git status --short",
        "```",
        status or "(clean)",
        "```",
        "> Rich summary should come from `/flow reset`. Resume with `/flow status`.",
        "",
    ]
    try:
        os.makedirs(os.path.dirname(summary_path), exist_ok=True)
        with open(summary_path, "a", encoding="utf-8") as fh:
            fh.write("\n".join(block))
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
