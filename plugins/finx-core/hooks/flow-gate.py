#!/usr/bin/env python3
"""PreToolUse flow-gate for the finx-core plugin (hybrid enforcement).

Blocks edits to production Java when this **session** is running a FinX flow but
is NOT in the `execute` phase (i.e. no approved plan yet) AND the change is
non-trivial. This enforces explore -> plan -> (approve) -> execute for real work,
while letting trivial one-off edits through.

State is per session (`<hub>/sessions/<id>.json`), so parallel sessions never
gate each other. Opt-in by design: a session with no flow state blocks nothing.
Escape hatch: FINX_SKIP_HOOKS=1, or `/flow execute` on an approved plan, or keep
the change trivial.

Exit 0 = allow. Exit 2 = block (stderr shown to Claude).
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import finxflow  # noqa: E402


def new_content(ti: dict) -> str:
    if "content" in ti:
        return ti.get("content") or ""
    if isinstance(ti.get("edits"), list):
        return "\n".join(e.get("new_string", "") for e in ti["edits"])
    return ti.get("new_string") or ""


def active_plan_ready(state: dict, root: str) -> bool:
    """True if the active plan exists and is approved/in-progress.

    Integration contract: any tool can satisfy the gate by pointing activePlan at
    a plan whose frontmatter status is approved or in-progress — it does not have
    to be created by the `/flow` commands.
    """
    path = finxflow.resolve_plan(state, root)
    if not path:
        return False
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                s = line.strip().lower()
                if s.startswith("status:"):
                    return s.split(":", 1)[1].strip() in ("approved", "in-progress")
    except Exception:
        return False
    return False


def gate_open(state: dict, root: str) -> bool:
    """Tool-agnostic 'ready to execute' check — any one signal is enough."""
    return (
        state.get("phase") == "execute"        # the finx /flow execute phase
        or state.get("approved") is True        # generic marker any tool can set
        or active_plan_ready(state, root)       # an approved active plan (any origin)
    )


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

    session_id = data.get("session_id", "") or ""
    root = finxflow.repo_root(os.path.dirname(os.path.abspath(path)))

    cfg = finxflow.load_config(root)
    # off = gate disabled; guided = track flow but never block.
    if cfg.get("enforcement") in ("off", "guided"):
        return 0

    # Only gate production Java.
    is_test = "/test/" in path or path.endswith("Test.java")
    if not (cfg["gatedPathContains"] in path and path.endswith(cfg["gatedSuffix"])) or is_test:
        return 0

    # Trivial changes pass even outside execute — unless enforcement is "hard".
    content = new_content(ti)
    changed_lines = content.count("\n") + 1 if content else 0
    trivial = (cfg.get("enforcement") != "hard"
               and changed_lines <= int(cfg["trivialMaxLines"]))

    # `session_id` is supplied by the harness, not by this plugin. If it ever
    # stops arriving, state cannot be read OR written and the gate would silently
    # allow everything — the failure mode that looks installed and does nothing.
    # Fail closed and loudly instead. Same posture as gc_sessions, which also
    # degrades safe when a harness-owned assumption breaks.
    if not session_id:
        if trivial:
            return 0
        sys.stderr.write(
            "BLOCKED by finx-core flow-gate: no session id.\n"
            f"  Editing production code ({os.path.basename(path)}, ~{changed_lines} lines), "
            "but the hook payload carried no `session_id`, so this session's flow "
            "state can be neither read nor written.\n"
            "  The gate fails closed rather than pretend to be enforcing.\n"
            "  -> Likely a Claude Code schema change. Report it, then unblock with "
            "FINX_SKIP_HOOKS=1 or `enforcement: guided` in ~/.finx/flow-config.json.\n"
        )
        return 2

    state = finxflow.read_state(session_id, root)
    if not state:
        return 0  # no flow in this session -> don't gate

    if gate_open(state, root):
        return 0  # a ready-to-execute signal is present -> allowed

    if trivial:
        return 0

    sys.stderr.write(
        "BLOCKED by finx-core flow-gate:\n"
        f"  Editing production code ({os.path.basename(path)}, ~{changed_lines} lines) "
        f"but this session's flow phase is '{state.get('phase', 'idle')}', not 'execute'.\n"
        "  Non-trivial work needs an approved plan first.\n"
        "  Gate opens on any of: phase=execute, an approved active plan "
        "(status approved/in-progress, any tool), or approved:true.\n"
        "  -> Run `/flow plan` + approve, then `/flow execute`.\n"
        "  (Trivial edits <= {} lines pass; or set FINX_SKIP_HOOKS=1 for a one-off.)\n".format(
            cfg["trivialMaxLines"]
        )
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
