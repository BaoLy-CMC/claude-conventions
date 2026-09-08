#!/usr/bin/env bash
# finx-statusline.sh — FinX flow-aware powerline statusline for Claude Code.
#
# Reads Claude Code's session JSON on stdin and the repo's .finx/ flow state.
# full mode = TWO powerline rows:
#   line 1 (work):    repo · phase · active-plan · enforcement · context%
#   line 2 (session): model · session% (5h usage) · reset countdown
# compact mode = ONE row: repo · phase · context%.
#
# Usage (from ~/.claude/settings.json):
#   "statusLine": { "type": "command",
#     "command": "bash /abs/path/finx-statusline.sh full", "padding": 0 }
#
# Modes:  full (default) | compact        Flags:  --plain (ASCII, no Nerd Font)
# Env:    FINX_STATUSLINE_MODE=full|compact   FINX_STATUSLINE_PLAIN=1
#
# Never errors out the status bar: any failure falls back to a minimal plain line.
set -uo pipefail

MODE="${FINX_STATUSLINE_MODE:-full}"
PLAIN="${FINX_STATUSLINE_PLAIN:-0}"
for arg in "$@"; do
  case "$arg" in
    full|compact) MODE="$arg" ;;
    --compact)    MODE="compact" ;;
    --full)       MODE="full" ;;
    --plain)      PLAIN=1 ;;
  esac
done

input="$(cat 2>/dev/null || true)"
has_jq=0; command -v jq >/dev/null 2>&1 && has_jq=1

jget() { # jget <jq-filter>  -> value or empty
  [ "$has_jq" -eq 1 ] || return 0
  printf '%s' "$input" | jq -r "$1 // empty" 2>/dev/null || true
}
fget() { # fget <file> <jq-filter> -> value or empty
  [ "$has_jq" -eq 1 ] && [ -f "$1" ] || return 0
  jq -r "$2 // empty" "$1" 2>/dev/null || true
}

# --- session data --------------------------------------------------------
CWD="$(jget '.workspace.current_dir')"; [ -z "$CWD" ] && CWD="$(jget '.cwd')"
[ -z "$CWD" ] && CWD="$PWD"
REPO="$(jget '.workspace.repo.name')"; [ -z "$REPO" ] && REPO="$(basename "$CWD")"
MODEL="$(jget '.model.display_name')"
PCT="$(jget '.context_window.used_percentage')"; PCT="${PCT%%.*}"
[ -z "$PCT" ] && PCT=0
# 5-hour rolling usage window = the current "session" (Pro/Max only; absent -> hidden)
FIVEH="$(jget '.rate_limits.five_hour.used_percentage')"; FIVEH="${FIVEH%%.*}"
# countdown to when the 5h window resets (next session)
RESET_LABEL=""
RESET_AT="$(jget '.rate_limits.five_hour.resets_at')"; RESET_AT="${RESET_AT%%.*}"
if [ -n "$RESET_AT" ] && [ "$RESET_AT" -eq "$RESET_AT" ] 2>/dev/null; then
  now="$(date +%s 2>/dev/null || echo 0)"
  d=$(( RESET_AT - now ))
  if [ "$d" -gt 0 ]; then
    h=$(( d / 3600 )); m=$(( (d % 3600) / 60 ))
    [ "$h" -gt 0 ] && rt="${h}h${m}m" || rt="${m}m"
  else
    rt="now"
  fi
  [ "$PLAIN" -eq 1 ] && RESET_LABEL="reset $rt" || RESET_LABEL="reset in $rt"
fi

# --- flow state (walk up for .finx) --------------------------------------
find_up() { # find_up <start> <relpath>
  local d="$1"
  while :; do
    [ -e "$d/$2" ] && { printf '%s' "$d/$2"; return 0; }
    [ "$d" = "/" ] && return 1
    d="$(dirname "$d")"
  done
}
PHASE=""; PLAN=""; ENF=""
FLOW_JSON="$(find_up "$CWD" ".finx/flow.json" 2>/dev/null || true)"
if [ -n "$FLOW_JSON" ]; then
  ROOT="$(dirname "$(dirname "$FLOW_JSON")")"
  PHASE="$(fget "$FLOW_JSON" '.phase')"
  PLAN_PATH="$(fget "$FLOW_JSON" '.activePlan')"
  [ -n "$PLAN_PATH" ] && { PLAN="$(basename "$PLAN_PATH")"; PLAN="${PLAN%.md}"; }
  # enforcement: project overrides global; default hybrid
  ENF="$(fget "$ROOT/.finx/flow-config.json" '.enforcement')"
  [ -z "$ENF" ] && ENF="$(fget "$HOME/.finx/flow-config.json" '.enforcement')"
  [ -z "$ENF" ] && ENF="hybrid"
fi

# --- rendering -----------------------------------------------------------
if [ "$PLAIN" -eq 1 ]; then SEP=">"; GIT="git:"; else SEP=$''; GIT=$''; fi

phase_icon() {
  [ "$PLAIN" -eq 1 ] && return   # no glyph in ASCII mode
  case "$1" in
    explore) printf $'' ;;   # magnifier
    plan)    printf $'' ;;   # checklist
    execute) printf $'' ;;   # gear
    review)  printf $'' ;;   # eye
    *)       printf $'' ;;   # dot
  esac
}
phase_bg()  { case "$1" in explore) echo 37;; plan) echo 136;; execute) echo 28;; review) echo 90;; *) echo 240;; esac; }
enf_bg()    { case "$1" in hard) echo 160;; hybrid) echo 25;; guided) echo 240;; off) echo 238;; *) echo 25;; esac; }
ctx_bg()    { if [ "$1" -ge 80 ]; then echo 160; elif [ "$1" -ge 60 ]; then echo 136; else echo 28; fi; }

# segment arrays + powerline renderer (reads the current seg* globals)
segT=(); segFg=(); segBg=()
seg()        { segT+=("$1"); segFg+=("$2"); segBg+=("$3"); }
reset_segs() { segT=(); segFg=(); segBg=(); }
render_line() {
  local out="" n=${#segT[@]} i bg fg txt
  for ((i=0; i<n; i++)); do
    bg="${segBg[i]}"; fg="${segFg[i]}"; txt="${segT[i]}"
    out+=$'\033'"[48;5;${bg}m"$'\033'"[38;5;${fg}m ${txt} "
    if (( i+1 < n )); then
      out+=$'\033'"[48;5;${segBg[i+1]}m"$'\033'"[38;5;${bg}m${SEP}"
    else
      out+=$'\033[0m'$'\033'"[38;5;${bg}m${SEP}"$'\033[0m'
    fi
  done
  printf '%s' "$out"
}

# LINE 1 — work: repo · phase · plan · enforcement · context%
reset_segs
seg "$GIT $REPO" 15 24
if [ -n "$PHASE" ]; then
  seg "$(phase_icon "$PHASE") $PHASE" 15 "$(phase_bg "$PHASE")"
  if [ "$MODE" = "full" ]; then
    [ -n "$PLAN" ] && seg "$PLAN" 252 238
    seg "$ENF" 15 "$(enf_bg "$ENF")"
  fi
fi
seg "${PCT}% ctx" 15 "$(ctx_bg "$PCT")"
L1="$(render_line)"

# compact = single line, work only.
if [ "$MODE" = "compact" ]; then
  printf '%s\n' "$L1"
  exit 0
fi

# LINE 2 — session / usage: model · session% · reset countdown
reset_segs
[ -n "$MODEL" ] && seg "$MODEL" 250 236
[ -n "$FIVEH" ] && seg "session ${FIVEH}%" 15 "$(ctx_bg "$FIVEH")"
[ -n "$RESET_LABEL" ] && seg "$RESET_LABEL" 252 238
L2="$(render_line)"

if [ -n "$L2" ]; then
  printf '%s\n%s\n' "$L1" "$L2"
else
  printf '%s\n' "$L1"
fi
