---
name: statusline-setup
description: Enable the FinX flow-aware powerline statusline for this engineer. Wires finx-statusline.sh into the user's own ~/.claude/settings.json. Use when the user says "finx statusline", "setup statusline", "enable status bar", "show flow phase in the bar", or asks how to turn on the FinX status line. Never overwrites an existing statusLine without asking.
---

# FinX Statusline Setup

Opt-in, per-engineer. Wires the shipped `scripts/finx-statusline.sh` into **the user's own** `~/.claude/settings.json`. It shows `repo · phase · active-plan · enforcement · context%` as a powerline bar, coloured by flow phase and context usage. Everything is the member's choice — nothing is forced.

## Steps

1. **Resolve the absolute script path.** `${CLAUDE_PLUGIN_ROOT}` is NOT available in the statusLine shell, so a literal absolute path must be written. Find it:
   ```bash
   find "$HOME/.claude/plugins" -name finx-statusline.sh -type f 2>/dev/null | head -1
   ```
   If empty, the plugin may be run from a dev checkout — ask the user for the repo path and use `<repo>/plugins/finx-core/scripts/finx-statusline.sh`. Confirm the file exists before continuing.

2. **Ask the engineer (AskUserQuestion), each with the recommended default first:**
   - **Richness**: `full` (two lines — line 1: repo · phase · plan · enforcement · ctx%; line 2: model · session% · reset countdown) — recommended — or `compact` (one line: repo · phase · ctx%). `session%` + reset = 5-hour rolling usage window (Pro/Max only; hidden when absent).
   - **Nerd Font installed?** The powerline glyphs (``) and phase icons need a Nerd Font (most engineers running claude-hud already have one). If not, use `--plain` (ASCII `>` separators, no glyphs).

3. **Check for an existing statusLine — do NOT clobber.** Read `~/.claude/settings.json`:
   - If there is **no** `statusLine` key → offer to add it (recommended).
   - If a `statusLine` **already exists** (e.g. claude-hud) → STOP and present three options:
     - (a) **Skip** — leave the current statusline as-is (recommended if they like claude-hud);
     - (b) **Replace** — overwrite with the FinX one (confirm explicitly first);
     - (c) **Compose manually** — print the exact command string so they can add a FinX segment to their existing statusline themselves.
   Never overwrite silently.

4. **Write, merging only the `statusLine` key.** Read the full settings JSON, set just `statusLine`, write it back — never drop other keys. The value:
   ```json
   {
     "statusLine": {
       "type": "command",
       "command": "bash <ABS_PATH>/finx-statusline.sh <full|compact> [--plain]",
       "padding": 0
     }
   }
   ```
   Use the resolved absolute path and the chosen mode/flags. (Env alternative: `FINX_STATUSLINE_MODE`, `FINX_STATUSLINE_PLAIN=1`.)

5. **Verify and report.** Run the script once with a sample stdin to show the rendered line, and tell the user it takes effect on the next render (no `/reload-plugins` needed — statusLine is a user setting, not a plugin component):
   ```bash
   echo '{"model":{"display_name":"opus-4.8"},"workspace":{"current_dir":"'"$PWD"'","repo":{"name":"demo"}},"context_window":{"used_percentage":42}}' | bash <ABS_PATH>/finx-statusline.sh full
   ```

## Notes

- Behaviour lives in the script; this skill only wires it up. With no flow state for the current session the flow segments hide automatically (shows repo + context only).
- To turn it off: remove the `statusLine` key (or restore the previous value) from `~/.claude/settings.json`.
- Missing `jq` → the script prints a minimal plain line rather than erroring; installing `jq` is recommended for the full bar.
