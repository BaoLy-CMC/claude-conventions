#!/usr/bin/env python3
"""Shared flow-state helpers for the finx-core hooks, skills and statusline.

Flow state is keyed by **session**, not by directory. Two sessions in the same
repo working on different tasks each keep their own state:

    <hub>/sessions/<session_id>.json

The old per-repo `.finx/flow.json` is still read (never written) as a fallback,
so an in-flight flow survives the upgrade. It is dropped after two releases.

Resolution never walks up past the repo root. A repo without its own state gets
no state — it must not inherit a parent directory's flow.
"""
import glob
import hashlib
import json
import os
import re
import subprocess
import time

DEFAULT_HUB = "~/.finx/hub"
SESSION_TTL_DAYS = 30
GC_MIN_AGE_DAYS = 1          # never GC a session file this young (no transcript yet)
BREADCRUMB_TTL_DAYS = 7      # older resume breadcrumbs are not offered, and get GC'd
BREADCRUMB_AUTO_MINUTES = 15  # a lone breadcrumb this fresh is offered without a handle
CLAUDE_PROJECTS = "~/.claude/projects"

# No i/l/o/0/1 — a handle gets read off a screen and retyped.
HANDLE_ALPHABET = "abcdefghjkmnpqrstuvwxyz23456789"

DEFAULTS = {
    "enforcement": "hybrid",
    "trivialMaxLines": 30,
    "contextThreshold": 0.65,
    "gatedPathContains": "/src/main/",
    "gatedSuffix": ".java",
    "hub": DEFAULT_HUB,
}


# --------------------------------------------------------------- repo & config

def repo_root(start: str) -> str:
    """Git top-level for `start`, else `start` itself. Never walks past it."""
    start = os.path.abspath(start)
    if not os.path.isdir(start):
        start = os.path.dirname(start)
    try:
        out = subprocess.run(
            ["git", "-C", start, "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, timeout=5,
        )
        if out.returncode == 0 and out.stdout.strip():
            return out.stdout.strip()
    except Exception:
        pass
    return start


def load_config(root: str = "") -> dict:
    cfg = dict(DEFAULTS)
    paths = [os.path.expanduser("~/.finx/flow-config.json")]
    if root:
        paths.append(os.path.join(root, ".finx", "flow-config.json"))
    for path in paths:
        try:
            with open(path, encoding="utf-8") as fh:
                cfg.update(json.load(fh))
        except Exception:
            pass
    return cfg


def hub(root: str = "") -> str:
    return os.path.expanduser(load_config(root).get("hub") or DEFAULT_HUB)


def sessions_dir(root: str = "") -> str:
    return os.path.join(hub(root), "sessions")


# ---------------------------------------------------------------------- state

def state_path(session_id: str, root: str = "") -> str:
    return os.path.join(sessions_dir(root), f"{session_id}.json")


def repo_slug(root: str) -> str:
    return os.path.abspath(root).strip("/").replace("/", "-")


def breadcrumb_dir(root: str) -> str:
    return os.path.join(hub(root), "state", repo_slug(root))


def handle_for(session_id: str) -> str:
    """Short, stable, human-retypable id for a session's resume breadcrumb.

    Derived from the session id, so every save from one session lands in the same
    file. Keyed by repo AND handle rather than repo alone: `/clear` mints a new
    session id, so nothing on disk links a new session to its predecessor — the
    engineer carries the handle across instead of the tool guessing.
    """
    n = int.from_bytes(hashlib.sha1(session_id.encode()).digest()[:5], "big")
    out = ""
    for _ in range(4):
        out += HANDLE_ALPHABET[n % len(HANDLE_ALPHABET)]
        n //= len(HANDLE_ALPHABET)
    return out


def summary_path(root: str, handle: str) -> str:
    return os.path.join(breadcrumb_dir(root), f"{handle}.md")


_HEADER = re.compile(r"<!--\s*finx-breadcrumb\s+(.*?)-->")

# Divider between an engineer-authored `/flow save` and the crude PreCompact
# snapshot. The snapshot replaces everything below it and never touches above,
# so an auto-compaction cannot destroy a rich save.
SNAPSHOT_MARK = "<!-- finx-auto-snapshot -->"


def breadcrumb_body(path: str, drop_snapshot: bool = False) -> str:
    """Existing body without the header line, optionally without the snapshot."""
    try:
        with open(path, encoding="utf-8") as fh:
            lines = fh.readlines()
    except OSError:
        return ""
    if lines and _HEADER.search(lines[0]):
        lines = lines[1:]
    text = "".join(lines)
    if drop_snapshot and SNAPSHOT_MARK in text:
        text = text.split(SNAPSHOT_MARK)[0]
    return text.strip()


def breadcrumb_header(path: str) -> dict:
    """Parse the machine-readable first line: session, handle, task, updated."""
    out = {}
    try:
        with open(path, encoding="utf-8") as fh:
            m = _HEADER.search(fh.readline())
    except OSError:
        return out
    if m:
        for k, v in re.findall(r'(\w+)="([^"]*)"', m.group(1)):
            out[k] = v
    return out


def list_breadcrumbs(root: str) -> list:
    """Resume candidates for this repo, newest first, within the TTL.

    Each entry: {handle, path, age_min, session, task}.
    """
    out = []
    now = time.time()
    for path in glob.glob(os.path.join(breadcrumb_dir(root), "*.md")):
        try:
            age_min = (now - os.path.getmtime(path)) / 60
        except OSError:
            continue
        if age_min > BREADCRUMB_TTL_DAYS * 1440:
            continue
        h = breadcrumb_header(path)
        out.append({
            "handle": os.path.splitext(os.path.basename(path))[0],
            "path": path,
            "age_min": int(age_min),
            "session": h.get("session", ""),
            "task": h.get("task", ""),
        })
    return sorted(out, key=lambda c: c["age_min"])


def write_breadcrumb(root: str, session_id: str, task: str, body: str) -> tuple:
    """Write/replace this session's breadcrumb. Returns (handle, path).

    Idempotent: keyed by handle, rewritten whole, never appended — repeated saves
    from one session replace rather than pile up.
    """
    handle = handle_for(session_id)
    path = summary_path(root, handle)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    header = (f'<!-- finx-breadcrumb session="{session_id}" handle="{handle}" '
              f'task="{task[:80].replace(chr(34), "")}" '
              f'updated="{time.strftime("%Y-%m-%dT%H:%M:%S")}" -->\n')
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(header + body.rstrip() + "\n")
    os.replace(tmp, path)
    return handle, path


def _legacy_state(root: str) -> dict:
    """Old per-repo flow.json — read-only, and only at the repo root itself."""
    try:
        with open(os.path.join(root, ".finx", "flow.json"), encoding="utf-8") as fh:
            data = json.load(fh)
        data["_legacy"] = True
        return data
    except Exception:
        return {}


def read_state(session_id: str, root: str) -> dict:
    """Session state if present, else the legacy per-repo file, else {}."""
    if session_id:
        try:
            with open(state_path(session_id, root), encoding="utf-8") as fh:
                return json.load(fh)
        except Exception:
            pass
    return _legacy_state(root)


def write_state(session_id: str, root: str, **fields) -> str:
    """Merge `fields` into this session's state and persist. Idempotent on retry:
    the key is the session id and the file is rewritten whole, never appended."""
    if not session_id:
        raise ValueError("session_id required to write flow state")
    data = {}
    try:
        with open(state_path(session_id, root), encoding="utf-8") as fh:
            data = json.load(fh)
    except Exception:
        pass
    data.update(fields)
    data["sessionId"] = session_id
    data["repo"] = root
    data["updated"] = time.strftime("%Y-%m-%d")
    path = state_path(session_id, root)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    os.replace(tmp, path)
    return path


def resolve_plan(state: dict, root: str) -> str:
    """activePlan -> absolute path. Session state stores it relative to
    <hub>/plans/; legacy state stores it relative to the repo root."""
    rel = state.get("activePlan")
    if not rel:
        return ""
    if os.path.isabs(rel):
        return rel if os.path.exists(rel) else ""
    for base in (os.path.join(hub(root), "plans"), root):
        cand = os.path.normpath(os.path.join(base, rel))
        if os.path.exists(cand):
            return cand
    return ""


def plan_label(state: dict, root: str) -> str:
    """Human-facing plan name: the slug directory for <slug>/plan.md layouts."""
    path = resolve_plan(state, root) or (state.get("activePlan") or "")
    if not path:
        return ""
    base = os.path.basename(path)
    if base in ("plan.md", "plan"):
        return os.path.basename(os.path.dirname(path))
    return os.path.splitext(base)[0]


# ------------------------------------------------------------------------- gc

def _live_session_ids() -> set:
    ids = set()
    for p in glob.glob(os.path.join(os.path.expanduser(CLAUDE_PROJECTS), "*", "*.jsonl")):
        ids.add(os.path.splitext(os.path.basename(p))[0])
    return ids


def gc_sessions(current_id: str = "") -> int:
    """Age out session state and stale resume breadcrumbs.

    In practice this is TTL-driven. Claude Code keeps a transcript on disk after
    `/clear`, so the "transcript disappeared" test almost never fires — it only
    catches sessions whose transcript the engineer pruned. Kept because it is
    still correct when that happens, and because `live and ...` makes it fail
    toward keeping state rather than deleting live work.

    Best-effort and idempotent: unlink races are ignored. The current session and
    anything younger than GC_MIN_AGE_DAYS are always kept.
    """
    now = time.time()
    removed = 0

    d = sessions_dir()
    if os.path.isdir(d):
        live = _live_session_ids()
        for path in glob.glob(os.path.join(d, "*.json")):
            sid = os.path.splitext(os.path.basename(path))[0]
            if sid == current_id:
                continue
            try:
                age_days = (now - os.path.getmtime(path)) / 86400
            except OSError:
                continue
            if age_days < GC_MIN_AGE_DAYS:
                continue
            if age_days > SESSION_TTL_DAYS or (live and sid not in live):
                try:
                    os.unlink(path)
                    removed += 1
                except OSError:
                    pass

    keep = handle_for(current_id) if current_id else None
    for path in glob.glob(os.path.join(hub(), "state", "*", "*.md")):
        if keep and os.path.splitext(os.path.basename(path))[0] == keep:
            continue
        try:
            if (now - os.path.getmtime(path)) / 86400 > BREADCRUMB_TTL_DAYS:
                os.unlink(path)
                removed += 1
        except OSError:
            pass
    return removed


# ---------------------------------------------------------------------- stdin

def hook_input(stdin) -> tuple:
    """(session_id, cwd) from a hook payload. Fail-open to ('', os.getcwd())."""
    try:
        data = json.load(stdin)
    except Exception:
        return "", os.getcwd()
    return data.get("session_id", "") or "", data.get("cwd", "") or os.getcwd()
