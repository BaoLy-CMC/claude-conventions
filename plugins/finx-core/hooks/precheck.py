#!/usr/bin/env python3
"""PreToolUse guard for the finx-core plugin.

Blocks a Write/Edit BEFORE it lands when the new content contains a
high-confidence FinX convention violation. Only deterministic, low-false-positive
rules are hard-blocked; heuristic checks (PII-in-log, free-form error codes,
envelope-by-cluster) are left to the review skills.

Escape hatch: set FINX_SKIP_HOOKS=1 to bypass (for a legitimate false positive).
Exit 0 = allow. Exit 2 = block (stderr shown to Claude).
"""
import json
import os
import re
import sys


def new_content(tool_input: dict) -> str:
    """Extract the text being written across Write / Edit / MultiEdit."""
    if "content" in tool_input:
        return tool_input.get("content") or ""
    if "edits" in tool_input and isinstance(tool_input["edits"], list):
        return "\n".join(e.get("new_string", "") for e in tool_input["edits"])
    return tool_input.get("new_string") or ""


# (label, compiled regex) — each match is a hard block.
JAVA_RULES = [
    ("System.out/err or printStackTrace (use SLF4J)",
     re.compile(r"System\.(out|err)\.print|\.printStackTrace\s*\(")),
    ("`var` in new code — declare explicit types",
     re.compile(r"(?m)^\s*var\s+\w+\s*=")),
    ("double/float for a monetary variable — use BigDecimal",
     re.compile(r"\b(double|float)\s+\w*(?i:amount|balance|money|price|fee|total|currency)\w*")),
    ("@Autowired on a field — constructor injection only",
     re.compile(r"@Autowired\s+(?:public|protected|private)?\s*(?:final\s+)?"
                r"[\w.$<>,\[\]\s]+\s+\w+\s*(?:=[^;()]*)?;")),
    ("empty catch block — handle, translate, or log it",
     re.compile(r"catch\s*\([^)]*\)\s*\{\s*\}")),
    ("string concatenation in a log message — use SLF4J placeholders",
     re.compile(r"log(?:ger)?\.(?:trace|debug|info|warn|error)\(\s*\"[^\"]*\"\s*\+")),
]

# Hardcoded secret literal (not an ${ENV} placeholder / empty). Java + config.
SECRET_RULE = re.compile(
    r'(?i)\b(password|secret|api[_-]?key|token|private[_-]?key|access[_-]?key)\b\s*[=:]\s*"?(?!\s*"?\$\{)([^"\s#]{6,})',
)


def main() -> int:
    if os.environ.get("FINX_SKIP_HOOKS"):
        return 0
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0  # never break the tool call on a parse error

    tool_input = data.get("tool_input", {}) or {}
    path = tool_input.get("file_path", "") or ""
    content = new_content(tool_input)
    if not content:
        return 0

    is_test = "/test/" in path or path.endswith("Test.java")
    violations = []

    if path.endswith(".java") and not is_test:
        for label, rx in JAVA_RULES:
            if rx.search(content):
                violations.append(label)

    if path.endswith((".java", ".yml", ".yaml", ".properties")):
        if SECRET_RULE.search(content):
            violations.append("hardcoded secret literal — use ${ENV_VAR} / secret manager")

    if violations:
        sys.stderr.write(
            "BLOCKED by finx-core convention guard:\n"
            + "\n".join(f"  - {v}" for v in violations)
            + f"\n  file: {path}\n"
            "Fix the above, or set FINX_SKIP_HOOKS=1 if this is a false positive.\n"
        )
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
