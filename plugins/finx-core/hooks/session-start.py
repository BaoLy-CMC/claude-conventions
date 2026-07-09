#!/usr/bin/env python3
"""SessionStart hook — inject the always-on baseline, and resume flow state.

1. Always emits the compact FinX baseline (generated from canonical/).
2. If the current repo has a fresh `.finx/state_summary.md`, appends it under a
   RESUME banner so a session started after /clear (or resume/compact) picks up
   exactly where the previous one left off.

Reads the hook payload (stdin) for `cwd`. Fail-open: on any error, still emit the
baseline so the always-on rules are never lost.
"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
BASELINE = os.path.join(HERE, "baseline-rules.md")
SUMMARY_MAX_AGE_DAYS = 7


def read_cwd() -> str:
    try:
        data = json.load(sys.stdin)
        return data.get("cwd", "") or os.getcwd()
    except Exception:
        return os.getcwd()


def find_up(start: str, rel: str):
    d = start
    while True:
        if os.path.exists(os.path.join(d, rel)):
            return os.path.join(d, rel)
        parent = os.path.dirname(d)
        if parent == d:
            return None
        d = parent


def main() -> int:
    cwd = read_cwd()

    try:
        sys.stdout.write(open(BASELINE, encoding="utf-8").read())
    except Exception:
        pass

    summary = find_up(cwd, os.path.join(".finx", "state_summary.md"))
    if summary:
        try:
            age_days = (time.time() - os.path.getmtime(summary)) / 86400
            if age_days <= SUMMARY_MAX_AGE_DAYS:
                sys.stdout.write(
                    "\n\n---\n\n## Resuming previous session (from .finx/state_summary.md)\n"
                    "You have an in-flight FinX flow. Read the summary below, run `/flow status`, "
                    "and continue from the recorded phase.\n\n"
                )
                sys.stdout.write(open(summary, encoding="utf-8").read())
        except Exception:
            pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
