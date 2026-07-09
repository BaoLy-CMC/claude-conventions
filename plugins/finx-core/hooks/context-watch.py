#!/usr/bin/env python3
"""UserPromptSubmit hook — warn when context usage crosses a threshold.

Estimates current context from the transcript's latest assistant `usage`
(input + cache_read + cache_creation tokens) divided by the model's context
limit. When it crosses the threshold (default 65%), it injects a note telling
Claude to ASK the user whether to /compact, save-state+clear+reload, or continue.

Cannot read live token % directly and cannot run /clear or /compact itself —
those are user actions; this only detects and prompts. Warns once per bucket
(per session) to avoid nagging. Fail-open and silent on any error.
"""
import json
import os
import sys

DEFAULT_THRESHOLD = 0.65


def load_threshold(cwd: str) -> float:
    for path in (
        os.path.expanduser("~/.finx/flow-config.json"),
        os.path.join(cwd, ".finx", "flow-config.json"),
    ):
        try:
            with open(path, encoding="utf-8") as fh:
                v = json.load(fh).get("contextThreshold")
                if v:
                    return float(v)
        except Exception:
            pass
    return DEFAULT_THRESHOLD


def context_limit(model: str, cwd: str) -> int:
    for path in (
        os.path.expanduser("~/.finx/flow-config.json"),
        os.path.join(cwd, ".finx", "flow-config.json"),
    ):
        try:
            with open(path, encoding="utf-8") as fh:
                v = json.load(fh).get("contextLimit")
                if isinstance(v, int):
                    return v
        except Exception:
            pass
    m = (model or "").lower()
    if "1m" in m or "[1m]" in m:
        return 1_000_000
    return 200_000


def latest_usage(transcript_path: str):
    """Return (total_input_tokens, model) from the last assistant msg with usage."""
    total, model = 0, ""
    try:
        with open(transcript_path, encoding="utf-8") as fh:
            lines = fh.readlines()
    except Exception:
        return 0, ""
    for line in reversed(lines):
        try:
            obj = json.loads(line)
        except Exception:
            continue
        msg = obj.get("message", {})
        usage = msg.get("usage") if isinstance(msg, dict) else None
        if usage:
            total = (
                usage.get("input_tokens", 0)
                + usage.get("cache_read_input_tokens", 0)
                + usage.get("cache_creation_input_tokens", 0)
            )
            model = msg.get("model", "")
            break
    return total, model


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0
    transcript = data.get("transcript_path", "")
    cwd = data.get("cwd", "") or os.getcwd()
    if not transcript or not os.path.exists(transcript):
        return 0

    total, model = latest_usage(transcript)
    if total <= 0:
        return 0
    limit = context_limit(model, cwd)
    ratio = total / limit
    threshold = load_threshold(cwd)
    if ratio < threshold:
        return 0

    # Warn once per 10% bucket per session (state next to the transcript).
    bucket = int(ratio * 10)
    warn_file = os.path.join(os.path.dirname(transcript), ".finx-context-warn")
    try:
        last = int(open(warn_file).read().strip())
    except Exception:
        last = -1
    if bucket <= last:
        return 0
    try:
        with open(warn_file, "w") as fh:
            fh.write(str(bucket))
    except Exception:
        pass

    pct = round(ratio * 100)
    sys.stdout.write(
        f"⚠️ finx-core context-watch: context is at ~{pct}% "
        f"(~{total:,}/{limit:,} tokens, threshold {round(threshold*100)}%).\n"
        "Per the FinX flow, ASK the user now (AskUserQuestion) whether to:\n"
        "  (a) /compact  — summarize in place, keep going (recommended, lightest);\n"
        "  (b) save + clear + reload — write .finx/state_summary.md (+ MemPalace), "
        "then user runs /clear; the session-start hook reloads the summary;\n"
        "  (c) continue — proceed without compacting.\n"
        "Then act on their choice before continuing other work.\n"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
