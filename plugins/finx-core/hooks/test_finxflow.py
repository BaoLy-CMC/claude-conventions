#!/usr/bin/env python3
"""Self-check for session-keyed flow state.  Run: python3 test_finxflow.py

Covers the four failures that motivated the redesign:
  1. two sessions in one repo must not share state
  2. a repo without its own state must not inherit a parent's
  3. GC must drop dead sessions and only those
  4. the legacy per-repo flow.json must still be readable
"""
import json
import os
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import finxflow  # noqa: E402


def setup(tmp):
    """Pin the module to a throwaway hub.

    Patching DEFAULTS is not enough: load_config() reads the engineer's real
    ~/.finx/flow-config.json on top of the defaults, so the real hub would win
    and the test would write into it.
    """
    hub = os.path.join(tmp, "hub")
    os.makedirs(os.path.join(hub, "sessions"))
    finxflow.hub = lambda root="": hub
    return hub


def mkrepo(tmp, name):
    d = os.path.join(tmp, name)
    os.makedirs(os.path.join(d, "sub", "src", "main", "java"), exist_ok=True)
    subprocess.run(["git", "init", "-q", d], check=True)
    return d


def main():
    tmp = tempfile.mkdtemp(prefix="finxflow-test-")
    hub = setup(tmp)
    repo = mkrepo(tmp, "repo-a")
    child = mkrepo(tmp, "repo-a/nested")   # a repo inside another repo's tree
    fails = []

    def check(name, cond):
        print(f"  {'PASS' if cond else 'FAIL'}  {name}")
        if not cond:
            fails.append(name)

    print("1. two sessions, one repo, independent state")
    finxflow.write_state("sess-1", repo, phase="execute", activePlan="a/plan.md", task="A")
    finxflow.write_state("sess-2", repo, phase="explore", activePlan="b/plan.md", task="B")
    s1 = finxflow.read_state("sess-1", repo)
    s2 = finxflow.read_state("sess-2", repo)
    check("sess-1 keeps execute/A", s1["phase"] == "execute" and s1["task"] == "A")
    check("sess-2 keeps explore/B", s2["phase"] == "explore" and s2["task"] == "B")
    check("no cross-contamination", s1["activePlan"] != s2["activePlan"])

    print("2. no inheritance from a parent directory")
    inner = finxflow.repo_root(os.path.join(child, "sub", "src", "main", "java"))
    check("repo_root stops at the nested repo", inner == child)
    check("unknown session in child sees nothing", finxflow.read_state("sess-none", child) == {})

    print("3. legacy per-repo flow.json still readable")
    os.makedirs(os.path.join(child, ".finx"), exist_ok=True)
    with open(os.path.join(child, ".finx", "flow.json"), "w") as fh:
        json.dump({"phase": "review", "activePlan": ".finx/plans/x/plan.md"}, fh)
    legacy = finxflow.read_state("", child)
    check("legacy read works", legacy.get("phase") == "review" and legacy.get("_legacy"))
    check("parent repo does NOT see the child's legacy file",
          finxflow.read_state("", repo).get("phase") is None)

    print("4. GC")
    live = os.path.join(hub, "sessions", "sess-live.json")
    dead = os.path.join(hub, "sessions", "sess-dead.json")
    for p in (live, dead):
        with open(p, "w") as fh:
            json.dump({"phase": "idle"}, fh)
    old = time.time() - 5 * 86400
    os.utime(live, (old, old))
    os.utime(dead, (old, old))
    finxflow._live_session_ids = lambda: {"sess-live"}
    removed = finxflow.gc_sessions(current_id="sess-1")
    check("dead session removed", not os.path.exists(dead))
    check("live session kept", os.path.exists(live))
    check("current session kept", os.path.exists(os.path.join(hub, "sessions", "sess-1.json")))
    check("young files kept", os.path.exists(os.path.join(hub, "sessions", "sess-2.json")))
    check("removed exactly 1", removed == 1)

    print("5. plan label resolution")
    plans = os.path.join(hub, "plans", "grp", "repo", "007-slug")
    os.makedirs(plans, exist_ok=True)
    open(os.path.join(plans, "plan.md"), "w").write("status: approved\n")
    st = {"activePlan": "grp/repo/007-slug/plan.md"}
    check("resolves under hub/plans", finxflow.resolve_plan(st, repo) == os.path.join(plans, "plan.md"))
    check("label uses the slug dir", finxflow.plan_label(st, repo) == "007-slug")

    print("6. flow-gate fails CLOSED when the harness sends no session_id")
    gate = os.path.join(os.path.dirname(os.path.abspath(__file__)), "flow-gate.py")
    java = os.path.join(repo, "src", "main", "java", "X.java")

    def run_gate(lines, enforcement="hybrid", session=None, target=java):
        home = tempfile.mkdtemp(prefix="finxflow-home-")
        os.makedirs(os.path.join(home, ".finx"))
        with open(os.path.join(home, ".finx", "flow-config.json"), "w") as fh:
            json.dump({"enforcement": enforcement, "hub": os.path.join(home, "hub")}, fh)
        payload = {"cwd": repo, "tool_input": {"file_path": target, "content": "x\n" * lines}}
        if session:
            payload["session_id"] = session
        env = dict(os.environ, HOME=home)
        env.pop("FINX_SKIP_HOOKS", None)
        out = subprocess.run([sys.executable, gate], input=json.dumps(payload),
                             capture_output=True, text=True, env=env)
        return out.returncode

    check("no session_id + non-trivial prod java -> BLOCK", run_gate(80) == 2)
    check("no session_id + hard -> BLOCK", run_gate(80, "hard") == 2)
    check("no session_id + trivial -> allow", run_gate(5) == 0)
    check("no session_id + guided -> allow (escape hatch intact)", run_gate(80, "guided") == 0)
    check("no session_id + off -> allow (escape hatch intact)", run_gate(80, "off") == 0)
    check("no session_id + test file -> allow",
          run_gate(80, target=os.path.join(repo, "src", "test", "java", "XTest.java")) == 0)
    check("no session_id + non-java -> allow",
          run_gate(80, target=os.path.join(repo, "README.md")) == 0)

    print(f"\n{'ALL PASS' if not fails else str(len(fails)) + ' FAILED: ' + ', '.join(fails)}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
