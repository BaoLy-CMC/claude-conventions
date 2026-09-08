#!/usr/bin/env python3
"""SessionStart hook — inject the always-on baseline, publish the session id,
resume flow state, and garbage-collect dead session files.

1. Always emits the compact FinX baseline (generated from canonical/).
2. Emits `FINX_SESSION_ID` — a skill is only a prompt and has no other way to
   learn which session it is running in, so every session-keyed skill depends on
   this line existing.
3. If this repo has a fresh resume breadcrumb, appends it under a RESUME banner
   so a session started after /clear (or resume/compact) picks up where the
   previous one left off.
4. Drops session state whose transcript is gone or that has aged out.

Fail-open: on any error, still emit the baseline so the always-on rules are
never lost.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import finxflow  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
BASELINE = os.path.join(HERE, "baseline-rules.md")


def emit_resume(root: str) -> None:
    """Offer the previous session's breadcrumb — auto only when unambiguous.

    Nothing on disk links a new session to the one it replaced: `/clear` mints a
    new id, and Claude Code keeps the old transcript, so "which transcript died"
    cannot answer it either. So: one fresh candidate is offered outright; several
    are listed for the engineer to pick by handle. Never guess.
    """
    cands = finxflow.list_breadcrumbs(root)
    if not cands:
        return

    fresh = [c for c in cands if c["age_min"] <= finxflow.BREADCRUMB_AUTO_MINUTES]
    if len(fresh) == 1:
        c = fresh[0]
        sys.stdout.write(
            f"\n\n---\n\n## Resuming previous session (`{c['handle']}`, "
            f"{c['age_min']}m ago)\n"
            "Read the summary below, run `/flow status`, continue from the "
            "recorded phase.\n\n"
        )
        sys.stdout.write(open(c["path"], encoding="utf-8").read())
        return

    sys.stdout.write(
        f"\n\n---\n\n## {len(cands)} saved session(s) in this repo\n"
        "More than one candidate, or none recent enough to pick safely — do NOT "
        "guess which belongs to this session. Show the engineer this list and let "
        "them choose:\n\n"
    )
    for c in cands[:5]:
        age = f"{c['age_min']}m" if c["age_min"] < 90 else f"{c['age_min'] // 60}h"
        sys.stdout.write(f"- `{c['handle']}` — {age} ago — {c['task'] or '(no task)'}\n")
    sys.stdout.write("\nLoad one with `/flow resume <handle>`.\n")


def main() -> int:
    session_id, cwd = finxflow.hook_input(sys.stdin)

    try:
        sys.stdout.write(open(BASELINE, encoding="utf-8").read())
    except Exception:
        pass

    if session_id:
        sys.stdout.write(
            "\n\n---\n\n"
            f"FINX_SESSION_ID={session_id}\n\n"
            "Flow state for this session lives at "
            f"`{finxflow.state_path(session_id)}`. The `/flow` skill reads and "
            "writes that file — never a repo-local `.finx/flow.json`.\n"
        )

    try:
        emit_resume(finxflow.repo_root(cwd))
    except Exception:
        pass

    try:
        finxflow.gc_sessions(session_id)
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
