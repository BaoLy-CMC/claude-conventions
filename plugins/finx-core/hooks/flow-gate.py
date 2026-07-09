#!/usr/bin/env python3
"""PreToolUse flow-gate for the finx-core plugin (hybrid enforcement).

Blocks edits to production Java when the repo is running a FinX flow but is NOT
in the `execute` phase (i.e. no approved plan yet) AND the change is non-trivial.
This enforces explore -> plan -> (approve) -> execute for real work, while letting
trivial one-off edits through.

Opt-in by design: if the repo has no `.finx/flow.json`, the flow isn't in use and
nothing is blocked. Escape hatch: FINX_SKIP_HOOKS=1, or `/flow execute` on an
approved plan, or keep the change trivial.

Exit 0 = allow. Exit 2 = block (stderr shown to Claude).
"""
import json
import os
import sys

DEFAULTS = {
    "enforcement": "hybrid",      # hybrid | off
    "trivialMaxLines": 30,         # <= this many changed lines = trivial, allowed
    "gatedPathContains": "/src/main/",
    "gatedSuffix": ".java",
}


def new_content(ti: dict) -> str:
    if "content" in ti:
        return ti.get("content") or ""
    if isinstance(ti.get("edits"), list):
        return "\n".join(e.get("new_string", "") for e in ti["edits"])
    return ti.get("new_string") or ""


def find_up(start: str, rel: str):
    """Walk up from start dir looking for a file at <dir>/<rel>."""
    d = start
    while True:
        candidate = os.path.join(d, rel)
        if os.path.exists(candidate):
            return candidate
        parent = os.path.dirname(d)
        if parent == d:
            return None
        d = parent


def load_config(repo_root: str) -> dict:
    cfg = dict(DEFAULTS)
    for path in (
        os.path.expanduser("~/.finx/flow-config.json"),
        os.path.join(repo_root, ".finx", "flow-config.json"),
    ):
        try:
            with open(path, encoding="utf-8") as fh:
                cfg.update(json.load(fh))
        except Exception:
            pass
    return cfg


def main() -> int:
    if os.environ.get("FINX_SKIP_HOOKS"):
        return 0
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0

    ti = data.get("tool_input", {}) or {}
    path = ti.get("file_path", "") or ""
    if not path:
        return 0

    start_dir = os.path.dirname(os.path.abspath(path))
    flow_path = find_up(start_dir, os.path.join(".finx", "flow.json"))
    if not flow_path:
        return 0  # flow not in use in this repo -> don't gate

    repo_root = os.path.dirname(os.path.dirname(flow_path))
    cfg = load_config(repo_root)
    # off = gate disabled; guided = track flow but never block.
    if cfg.get("enforcement") in ("off", "guided"):
        return 0

    # Only gate production Java.
    is_test = "/test/" in path or path.endswith("Test.java")
    if not (cfg["gatedPathContains"] in path and path.endswith(cfg["gatedSuffix"])) or is_test:
        return 0

    try:
        with open(flow_path, encoding="utf-8") as fh:
            flow = json.load(fh)
    except Exception:
        return 0

    if flow.get("phase") == "execute" and flow.get("activePlan"):
        return 0  # in execute with an active plan -> allowed

    # Trivial changes pass even outside execute — unless enforcement is "hard".
    content = new_content(ti)
    changed_lines = content.count("\n") + 1 if content else 0
    if cfg.get("enforcement") != "hard" and changed_lines <= int(cfg["trivialMaxLines"]):
        return 0

    sys.stderr.write(
        "BLOCKED by finx-core flow-gate:\n"
        f"  Editing production code ({os.path.basename(path)}, ~{changed_lines} lines) "
        f"but the flow phase is '{flow.get('phase', 'idle')}', not 'execute'.\n"
        "  Non-trivial work needs an approved plan first.\n"
        "  -> Run `/flow plan`, get it approved, then `/flow execute`.\n"
        "  (Trivial edits <= {} lines pass; or set FINX_SKIP_HOOKS=1 for a one-off.)\n".format(
            cfg["trivialMaxLines"]
        )
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
