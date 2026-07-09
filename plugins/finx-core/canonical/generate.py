#!/usr/bin/env python3
"""Generate Claude + Kiro artifacts from the single canonical convention source.

One source (conventions.json) -> two outputs, so the Claude plugin and the AWS
Kiro steering files never drift:
  1. hooks/baseline-rules.md          — Claude SessionStart always-on baseline
  2. canonical/out/kiro/<file>.md     — Kiro steering files (per Confluence EN/894730262)

Run: python3 canonical/generate.py   (from the plugin root, or anywhere)
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN_ROOT = os.path.dirname(HERE)
SRC = os.path.join(HERE, "conventions.json")
BASELINE_OUT = os.path.join(PLUGIN_ROOT, "hooks", "baseline-rules.md")
KIRO_OUT_DIR = os.path.join(HERE, "out", "kiro")


def render_baseline(data: dict) -> str:
    m = data["meta"]
    out = [
        "# FinX Backend Conventions — always-on baseline",
        "",
        f"Applies to new/modified code in {m['product']} ({m['stack']}). "
        f"Source of truth: {m['source']}. For detail, the `finx-core` plugin skills load on demand.",
        "",
        "> Generated from `canonical/conventions.json` — edit there, then run `canonical/generate.py`. Do not hand-edit.",
    ]
    for s in data["sections"]:
        out += ["", f"## {s['title']}"]
        out += [f"- {line}" for line in s["lines"]]
    return "\n".join(out) + "\n"


def render_kiro(data: dict, key: str, title: str) -> str:
    m = data["meta"]
    out = [
        f"# {title} — FinX Steering",
        "",
        f"Product: {m['product']}. Stack: {m['stack']}. Source: {m['source']}.",
        "",
        "> Generated from the FinX canonical convention source. Do not hand-edit.",
    ]
    for s in data["sections"]:
        if key in s.get("kiro", []):
            out += ["", f"## {s['title']}"]
            out += [f"- {line}" for line in s["lines"]]
    return "\n".join(out) + "\n"


def main() -> None:
    with open(SRC, encoding="utf-8") as fh:
        data = json.load(fh)

    with open(BASELINE_OUT, "w", encoding="utf-8") as fh:
        fh.write(render_baseline(data))
    print(f"wrote {os.path.relpath(BASELINE_OUT, PLUGIN_ROOT)}")

    os.makedirs(KIRO_OUT_DIR, exist_ok=True)
    for key, title in data["kiroFiles"].items():
        path = os.path.join(KIRO_OUT_DIR, f"{key}.md")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(render_kiro(data, key, title))
        print(f"wrote {os.path.relpath(path, PLUGIN_ROOT)}")


if __name__ == "__main__":
    main()
