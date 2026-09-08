#!/usr/bin/env python3
"""Validate every SKILL.md against the Agent Skills authoring rules.

Limits come from Anthropic's skill-authoring guide (name <= 64 chars,
description <= 1024 chars, SKILL.md body < 500 lines, reference files one level
deep, table of contents for reference files over 100 lines). Everything else
here is a FinX house rule: the skill name must equal its directory, the
description must say when to use the skill, and the body must not address a
human reader in first or second person.

Usage: python3 scripts/check-skills.py [skills_dir]
Exit 0 = pass (warnings allowed). Exit 1 = at least one error.
"""
import os
import re
import sys

NAME_MAX = 64
DESC_MAX = 1024
BODY_MAX_LINES = 500
TOC_REQUIRED_OVER_LINES = 100

RESERVED = ("anthropic", "claude")
WHEN_MARKERS = ("use when", "use for", "use during", "use before", "use after", "use if")
PRONOUNS = re.compile(r"\bI\b|\bI'm\b|\b(?:[Ww]e|[Ww]e're|[Oo]ur|[Oo]urs|[Yy]ou|[Yy]our|[Yy]ours)\b")
XML_TAG = re.compile(r"<[a-zA-Z/][^>]*>")
MD_LINK = re.compile(r"\[[^\]]+\]\(([^)#]+\.md)[^)]*\)")


def frontmatter(text: str) -> tuple[str, str]:
    """Split a SKILL.md into (frontmatter, body). Empty frontmatter if malformed."""
    if not text.startswith("---\n"):
        return "", text
    parts = text.split("---", 2)
    return (parts[1], parts[2]) if len(parts) == 3 else ("", text)


def field(fm: str, key: str) -> str:
    m = re.search(rf"^{key}:\s*(.+)$", fm, re.M)
    return m.group(1).strip() if m else ""


def check_skill(path: str) -> tuple[list[str], list[str]]:
    directory = os.path.dirname(path)
    slug = os.path.basename(directory)
    errors: list[str] = []
    warnings: list[str] = []

    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    fm, body = frontmatter(text)
    if not fm:
        return [f"{slug}: missing or malformed YAML frontmatter"], warnings

    name, desc = field(fm, "name"), field(fm, "description")

    if not name:
        errors.append(f"{slug}: frontmatter has no name")
    else:
        if name != slug:
            errors.append(f"{slug}: name '{name}' does not match the directory")
        if len(name) > NAME_MAX:
            errors.append(f"{slug}: name is {len(name)} chars (max {NAME_MAX})")
        if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", name):
            errors.append(f"{slug}: name must be lowercase letters, numbers and single hyphens")
        if any(word in name for word in RESERVED):
            errors.append(f"{slug}: name contains a reserved word {RESERVED}")

    if not desc:
        errors.append(f"{slug}: frontmatter has no description")
    else:
        if len(desc) > DESC_MAX:
            errors.append(f"{slug}: description is {len(desc)} chars (max {DESC_MAX})")
        if XML_TAG.search(desc):
            errors.append(f"{slug}: description contains an XML tag")
        if not any(marker in desc.lower() for marker in WHEN_MARKERS):
            errors.append(f"{slug}: description never says when to use the skill")
        if re.match(r"\s*(I |I'|You |Your |We |Our )", desc):
            errors.append(f"{slug}: description must be third person")

    body_lines = body.count("\n")
    if body_lines >= BODY_MAX_LINES:
        errors.append(f"{slug}: body is {body_lines} lines (keep under {BODY_MAX_LINES})")

    if "\\" in "".join(MD_LINK.findall(body)):
        errors.append(f"{slug}: use forward slashes in file paths")

    for human_doc in ("README.md", "CHANGELOG.md"):
        if os.path.exists(os.path.join(directory, human_doc)):
            errors.append(f"{slug}: {human_doc} does not belong inside a skill")

    for link in MD_LINK.findall(body):
        if link.startswith(("http://", "https://")):
            continue
        target = os.path.normpath(os.path.join(directory, link))
        if not os.path.exists(target):
            errors.append(f"{slug}: broken reference '{link}'")
            continue
        if link.count("/") > 1:
            errors.append(f"{slug}: reference '{link}' is more than one level deep")
        with open(target, encoding="utf-8") as fh:
            ref = fh.read()
        if ref.count("\n") > TOC_REQUIRED_OVER_LINES and "## Contents" not in ref:
            errors.append(
                f"{slug}: reference '{link}' is over {TOC_REQUIRED_OVER_LINES} lines "
                "and needs a '## Contents' table of contents"
            )

    for number, line in enumerate(body.split("\n"), 1):
        if line.lstrip().startswith(("|", "```")) or line.startswith(">"):
            continue
        hit = PRONOUNS.search(line)
        if hit:
            warnings.append(f"{slug}:{number}: writes to a human ('{hit.group(0)}') — use third person")

    return errors, warnings


def main() -> int:
    here = os.path.dirname(os.path.abspath(__file__))
    skills_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(here), "skills")
    paths = sorted(
        os.path.join(skills_dir, entry, "SKILL.md")
        for entry in os.listdir(skills_dir)
        if os.path.isfile(os.path.join(skills_dir, entry, "SKILL.md"))
    )
    if not paths:
        print(f"no SKILL.md found under {skills_dir}", file=sys.stderr)
        return 1

    all_errors: list[str] = []
    all_warnings: list[str] = []
    for path in paths:
        errors, warnings = check_skill(path)
        all_errors += errors
        all_warnings += warnings

    for warning in all_warnings:
        print(f"WARN  {warning}")
    for error in all_errors:
        print(f"ERROR {error}")
    print(f"\n{len(paths)} skills checked — {len(all_errors)} errors, {len(all_warnings)} warnings")
    return 1 if all_errors else 0


if __name__ == "__main__":
    sys.exit(main())
