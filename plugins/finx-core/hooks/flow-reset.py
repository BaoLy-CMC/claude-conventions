#!/usr/bin/env python3
"""PreCompact hook — safety-net snapshot of flow state before compaction.

A hook can't summarize the conversation (no LLM), so the RICH summary is written
by Claude via `/flow reset` or the context-watch "save" choice. This hook only
guarantees a breadcrumb survives an unattended auto-compaction: it appends the
flow phase, active plan, and the working git diff stat to the repo's resume
breadcrumb in the hub. Best-effort, fail-open.
"""
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import finxflow  # noqa: E402


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
    session_id, cwd = finxflow.hook_input(sys.stdin)
    root = finxflow.repo_root(cwd)
    state = finxflow.read_state(session_id, root)
    if not state:
        return 0  # no flow in use

    if not session_id:
        return 0  # no handle to file it under

    diffstat = git(root, "diff", "--stat")
    status = git(root, "status", "--short")
    task = state.get("task") or ""

    handle = finxflow.handle_for(session_id)
    kept = finxflow.breadcrumb_body(
        finxflow.summary_path(root, handle), drop_snapshot=True)

    snapshot = "\n".join([
        finxflow.SNAPSHOT_MARK,
        f"## Auto-snapshot before compaction — {task or '(no task)'}",
        "",
        f"- phase: {state.get('phase', 'idle')}",
        f"- activePlan: {finxflow.plan_label(state, root) or state.get('activePlan')}",
        "",
        "### git diff --stat",
        "```",
        diffstat or "(no changes)",
        "```",
        "### git status --short",
        "```",
        status or "(clean)",
        "```",
        "> Crude breadcrumb only — a hook cannot summarize a conversation.",
        "> A richer one comes from `/flow save`.",
    ])
    body = (kept + "\n\n" + snapshot) if kept else snapshot
    try:
        finxflow.write_breadcrumb(root, session_id, task, body)
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
