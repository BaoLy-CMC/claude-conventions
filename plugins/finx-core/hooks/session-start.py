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
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import finxflow  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
BASELINE = os.path.join(HERE, "baseline-rules.md")
SUMMARY_MAX_AGE_DAYS = 7


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
        root = finxflow.repo_root(cwd)
        summary = finxflow.summary_path(root)
        if os.path.exists(summary):
            age_days = (time.time() - os.path.getmtime(summary)) / 86400
            if age_days <= SUMMARY_MAX_AGE_DAYS:
                sys.stdout.write(
                    "\n\n---\n\n## Resuming previous session in this repo\n"
                    "There is an in-flight FinX flow here. Read the summary below, "
                    "run `/flow status`, and continue from the recorded phase.\n\n"
                )
                sys.stdout.write(open(summary, encoding="utf-8").read())
    except Exception:
        pass

    try:
        finxflow.gc_sessions(session_id)
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
