#!/usr/bin/env python3
"""SessionStart hook — point a newly-installed engineer at the onboarding tour.

A plugin that installs silently is a plugin nobody understands: the baseline and
the guards start acting on the very first session with no explanation of what is
always on, what is opt-in, and how the flow works. This hook surfaces the
`onboarding` skill for the first few sessions after install.

State lives in `~/.finx/.finx-core-onboarding`: either the literal `done` (the
skill finished, or the engineer opted out) or the number of nudges shown. The
nudge stops after MAX_NUDGES so it can never become noise. Fail-open and silent
on any error.
"""
import os
import sys

STATE = os.path.expanduser("~/.finx/.finx-core-onboarding")
MAX_NUDGES = 3

NUDGE = """

---

## finx-core is installed — onboarding not done yet

Tell the engineer, briefly and once, before answering anything else: finx-core is
active and its FinX baseline rules are already loaded into this session, and the
`/finx-core:onboarding` tour (~2 minutes) explains what runs automatically, what
is opt-in, and how the `explore -> plan -> execute -> review` flow works.

Offer to run it now. On an explicit decline, silence this notice for good by
running `mkdir -p ~/.finx && printf done >| ~/.finx/.finx-core-onboarding`, then
drop the subject. If the engineer simply ignores it, do not raise it again in
this session. Run the `onboarding` skill only when asked.
"""


def read_state() -> str:
    try:
        with open(STATE, encoding="utf-8") as fh:
            return fh.read().strip()
    except Exception:
        return ""


def write_state(value: str) -> None:
    try:
        os.makedirs(os.path.dirname(STATE), exist_ok=True)
        with open(STATE, "w", encoding="utf-8") as fh:
            fh.write(value)
    except Exception:
        pass


def main() -> int:
    state = read_state()
    if state == "done":
        return 0

    try:
        shown = int(state)
    except ValueError:
        shown = 0
    if shown >= MAX_NUDGES:
        return 0

    write_state(str(shown + 1))
    sys.stdout.write(NUDGE)
    return 0


if __name__ == "__main__":
    sys.exit(main())
