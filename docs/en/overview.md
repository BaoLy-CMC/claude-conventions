# Overview

Tiếng Việt: [../vi/overview.md](../vi/overview.md) | Back to [README](../../README.md)

This page is the mental model: what the plugin is made of and how the parts fit together.

## The idea

Confluence holds the authoritative standards (prose, for humans). This plugin does not duplicate that prose; it **encodes the enforceable parts** so Claude Code applies them automatically and identically for everyone. One source generates two consumers: the Claude baseline and the AWS Kiro steering files.

```
Confluence space EN            <- source of truth (humans read)
        |
        v
canonical/conventions.json
        |
        +-- generate.py --> canonical/out/kiro/*.md      (Kiro steering)
        |               --> hooks/baseline-rules.md      (Claude always-on baseline)
        v
finx-core plugin
```

Edit the convention once in `canonical/conventions.json`; the generator keeps the Claude baseline and the Kiro files in sync. No drift between the two AI channels.

## The four layers

```
+------------------------------------------------------------+
| 1. BASELINE (always-on)                                    |
|    A short rule block injected at the start of every        |
|    session by the SessionStart hook. Principles, coding     |
|    rules, banking rules, runtime-version rules.             |
+------------------------------------------------------------+
| 2. GUARDS (hooks, automatic)                               |
|    PreToolUse blocks bad edits before they land            |
|    (var in new code, double for money, System.out,         |
|    secrets) and enforces the flow (flow-gate).             |
|    UserPromptSubmit watches context; PreCompact snapshots. |
+------------------------------------------------------------+
| 3. SKILLS (on-demand)                                      |
|    Playbooks Claude loads by context: reviews, the flow,   |
|    authoring (scaffolds, docs, changesets).                |
+------------------------------------------------------------+
| 4. FLOW (opt-in per repo)                                  |
|    explore -> plan -> execute -> review -> reset, with     |
|    state in .finx/ and a gate that requires an approved    |
|    plan before non-trivial production code.                |
+------------------------------------------------------------+
```

## Why hooks, not CLAUDE.md

Claude Code plugins do not auto-load a `CLAUDE.md`. So the always-on baseline is delivered by a `SessionStart` hook that prints the generated `baseline-rules.md` into the session. Detailed material is not always-on; it loads only when a skill is triggered, which keeps context small.

## What is always-on vs on-demand

- **Always-on** (every session): the baseline rules.
- **Automatic** (on the relevant action): the guards and context-watch hooks.
- **On-demand** (when relevant or asked): the skills.

## Opt-in and integration

The flow is opt-in per session: a session with no flow state is never gated, so personal tools and other plugins coexist. Non-flow features (baseline, guards, reviews, docs, runtime rules) apply regardless of how you plan or execute. See [Flow](flow.md), section "Integration with other planning/execute tools".

## Where to go next

- The rules themselves: [Rules](rules.md).
- Every skill and hook: [Reference](reference.md).
- The development flow: [Flow](flow.md).
- Changing a convention and releasing: [Releasing](releasing.md).
