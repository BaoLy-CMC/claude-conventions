---
name: onboarding
description: Guided first-run tour of the finx-core plugin — what is always on, what loads on demand, how the flow works, and which per-engineer options are opt-in — then wires up the chosen options. Use when finx-core was just installed, when the session-start onboarding notice appears, or when an engineer asks "what does this plugin do", "how do I use finx-core", "onboarding", "getting started", or wants a refresher on the flow and the available skills.
---

# finx-core Onboarding

A ~2 minute tour, then optional setup. The goal is a correct mental model — which parts act automatically, which parts must be invoked, and which parts are personal choice — not a feature list.

State: `~/.finx/.finx-core-onboarding` holds `done` from the moment the tour starts, or when it is declined. The session-start notice reads it and never nudges again — the marker lives in the engineer's home directory, so a plugin update or reinstall does not resurrect it.

## Steps

1. **Mark the tour done first, then confirm the install is healthy.** Writing the marker up front — not at the end — means an interrupted or abandoned tour still silences the notice for good; invoking the skill at all is the signal that the engineer has been onboarded.
   ```bash
   mkdir -p ~/.finx && printf done >| ~/.finx/.finx-core-onboarding
   ```
   Then check the install (a broken install makes the tour confusing):
   ```bash
   ls "$CLAUDE_PLUGIN_ROOT/skills" | wc -l && python3 -c "import json,sys;print(json.load(open('$CLAUDE_PLUGIN_ROOT/hooks/hooks.json'))['hooks'].keys())"
   ```
   If `CLAUDE_PLUGIN_ROOT` is unset here, locate the plugin under `~/.claude/plugins/`. Report a missing/failed install and stop — the fix is `/plugin install finx-core@finx-conventions` then `/reload-plugins` and a fresh session.

2. **Give the tour in four short blocks**, in the engineer's language, no more than a few lines each. Do not paste the whole reference; link to it.

   | Block | The point to land |
   |-------|-------------------|
   | Always on | A `SessionStart` hook injects the FinX baseline (Java/Spring conventions, banking domain rules, logging and error-handling defaults) into every session. Nothing to invoke — it is already in this conversation. |
   | Guards | `PreToolUse` hooks block a small set of high-confidence violations before a write lands: `var` in new code, `double`/`float` for money, `System.out`/`printStackTrace`, hardcoded secrets. Escape hatch for a false positive: `FINX_SKIP_HOOKS=1`. |
   | On demand | 19 skills load only when the context matches, or when called by name — reviews (`logging-review`, `error-handling-review`, `api-response-standards`, `pre-ship`), authoring (`create-liquibase-changeset`, `new-service-scaffold`, `cross-repo-operations`), ops (`ops-runtime`, `release-workload`). Full list: `docs/en/reference.md` in the conventions repo. |
   | The flow | `explore -> plan -> execute -> review -> reset`. State is **per session**, in `<hub>/sessions/<id>.json` — run ten sessions at once and each keeps its own phase and plan. Plans for every repo live together in `<hub>/plans/`. On a repo with enforcement on, non-trivial production-Java edits are gated until a plan is approved. Start with `/flow explore <task>`. Details: `docs/en/flow.md`. |

3. **Show it once, concretely.** Run `/flow status` in the current repo and read the result back: either the active phase, or "no flow yet — `/flow explore <task>` starts one". A single real command beats another paragraph.

4. **Offer the opt-ins (AskUserQuestion, multi-select, all genuinely optional).** Nothing here is forced; an engineer who picks none keeps stock behaviour.
   - **Flow setup** — run `flow-setup` to choose the **hub** (where plans and session state live — ask this even if they skip everything else, since moving it later is expensive), the enforcement level `hard` / `hybrid` / `guided` / `off`, and the context-watch threshold. Recommended for a service repo; skip for a scratch repo.
   - **Output style** — `FinX Quick` / `FinX Standard` / `FinX Deep` in `/config` -> Output style. Changes explanation depth only.
   - **Statusline** — run `statusline-setup` for a powerline bar showing repo, phase, active plan, enforcement, context%. Never overwrites an existing statusline without asking.

   Invoke the chosen setup skills in turn. Do not run any of them unprompted.

5. **Close out.** State the two commands worth remembering: `/flow explore <task>` to start work, `/finx-core:pre-ship` before a PR. The done marker was already written in step 1, so the session-start notice is now permanently quiet.

## Notes

- Mark done when the engineer declines the tour too — the point is to ask at most once, not to nag.
- Re-running the skill is always allowed and re-offers every opt-in; it is the refresher path for an engineer who set nothing up the first time.
- A convention itself is never changed here. To change a rule: edit `canonical/conventions.json`, regenerate, release — see `docs/en/releasing.md`.
