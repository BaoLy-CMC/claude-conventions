---
name: flow-setup
description: Configure the FinX dev flow per engineer (or per project) — enforcement level, context-watch threshold, trivial-change threshold, plan guards. Use when the user says "flow setup", "configure flow", "set enforcement", "change context threshold", "customize flow", or on first adoption of the flow in a repo. Writes flow-config.json; the flow-gate and context-watch hooks read it, falling back to standard defaults.
---

# Flow Setup

Customize the flow for this engineer or project. The plugin ships **standard defaults** (below); this skill only records the overrides an engineer wants.

## Config file locations (both optional; project wins over global)

- `~/.finx/flow-config.json` — per-engineer, applies to every repo.
- `<repo>/.finx/flow-config.json` — per-project override. `.finx/` is git-ignored by default; a team that wants a **shared** project policy can commit just this file.

Hooks read global then project, merging over the built-in defaults. A missing file simply means "use defaults" — setup is optional.

## Schema + standard defaults

```json
{
  "enforcement": "hybrid",       // hybrid | hard | guided | off
  "contextThreshold": 0.65,       // 0..1 — context-watch prompt point
  "contextLimit": "auto",         // "auto" (detect from model) or integer tokens
  "trivialMaxLines": 30,          // <= this many changed lines = trivial (gate skips)
  "maxActivePlans": 3,            // guard before creating a new plan
  "autoArchiveDays": 14,          // auto-archive done plans older than this
  "gatedPathContains": "/src/main/",  // advanced — which paths the gate governs
  "gatedSuffix": ".java"              // advanced
}
```

**Enforcement levels:**
- `hybrid` (recommended) — block non-trivial prod-code edits outside `execute`; trivial edits pass.
- `hard` — block **all** prod-code edits outside `execute` (no trivial exemption).
- `guided` — never block; flow is tracked and commands work, but the gate stays silent.
- `off` — gate disabled entirely.

## Steps

1. Ask the engineer (use AskUserQuestion) for the choices that matter, each with the recommended default pre-selected:
   - **Scope**: global (`~/.finx`) or this project (`.finx`)?
   - **Enforcement**: hybrid / hard / guided / off.
   - **Context threshold**: 65% (default) / 60 / 70 / off.
   - Optional advanced: trivialMaxLines, maxActivePlans, autoArchiveDays.
2. **Read any existing** config at the chosen location and **merge** — never clobber keys the user didn't change.
3. Write the JSON (create `~/.finx/` or `<repo>/.finx/` if needed). Ensure `<repo>/.finx/` is git-ignored unless the user explicitly wants to commit a shared project policy.
4. Print the effective resulting config and a one-line reminder that hooks pick it up on the next tool call (context-watch) / next `/reload-plugins` is not needed for these file reads.

Keep it minimal — only write keys the engineer actually chose to change; everything else falls back to the documented defaults.
