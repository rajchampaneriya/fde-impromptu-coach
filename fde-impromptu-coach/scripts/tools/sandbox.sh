#!/bin/bash
# Runs one fde-coach command in a throw-away, dry-run home, the way the tests do
# (scripts/tests/test_coach.py, class Home): nothing touches ~/FDE-Impromptu, launchd,
# QuickTime, PowerPoint, Google or YouTube, and Claude is the test double fake_claude.py.
#
# Usage: bash scripts/tools/sandbox.sh <fde-coach arguments>
#   NOW=2026-11-07T08:00:00 ...   pretend it is that time (FDE_COACH_NOW)
#   ANSWERS='Start now,Later' ... answer the dialogs in order (FDE_COACH_DRYRUN_ANSWERS)
#   SANDBOX=/tmp/my-box ...       keep the home there (default: $TMPDIR/fde-coach-sandbox, reused across calls)
#   SANDBOX_RESET=1 ...           start again from an empty home
#   PYTHON=... ...                the interpreter (default: the Mac's venv if installed, else python3)
# From the repo root, `make sandbox ARGS='stage status --json'` does the same.
#
# bash 3.2 compatible (macOS /bin/bash).
set -euo pipefail

if [ "$#" -eq 0 ]; then
  echo "Usage: bash scripts/tools/sandbox.sh <fde-coach arguments>   (for example: stage status --json)" >&2
  exit 2
fi

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd -P)"
CLI="$SKILL_DIR/scripts/fde_coach.py"
FAKE_CLAUDE="$SKILL_DIR/scripts/tests/fake_claude.py"
BOX="${SANDBOX:-${TMPDIR:-/tmp}/fde-coach-sandbox}"
BOX="${BOX%/}"

PY="${PYTHON:-}"
if [ -z "$PY" ]; then
  if [ -x "$HOME/FDE-Impromptu/venv/bin/python" ]; then PY="$HOME/FDE-Impromptu/venv/bin/python"; else PY=python3; fi
fi

# Only ever use or delete a folder this script made (it leaves a .fde-coach-sandbox marker).
if [ -d "$BOX" ] && [ ! -f "$BOX/.fde-coach-sandbox" ] && [ -n "$(ls -A "$BOX" 2>/dev/null)" ]; then
  echo "sandbox: $BOX already holds other files; choose another folder with SANDBOX=..." >&2
  exit 2
fi
if [ "${SANDBOX_RESET:-0}" = "1" ] && [ -f "$BOX/.fde-coach-sandbox" ]; then
  rm -rf "$BOX"
fi

export FDE_COACH_HOME="$BOX/home"
export FDE_COACH_DRYRUN=1
export FDE_COACH_AGENTS_DIR="$BOX/agents"
export FDE_COACH_RECORDINGS="$BOX/movies"
export FDE_COACH_SKIP_NETWORK_WAIT=1
export FDE_COACH_NO_CLAUDE_DISCOVERY=1
export FDE_COACH_DRYRUN_ANSWERS="${ANSWERS:-}"
unset FDE_COACH_TODAY
if [ -n "${NOW:-}" ]; then export FDE_COACH_NOW="$NOW"; else unset FDE_COACH_NOW; fi

if [ ! -f "$BOX/.fde-coach-sandbox" ]; then
  mkdir -p "$BOX"
  "$PY" "$CLI" setup --no-warmup >/dev/null
  "$PY" "$CLI" config --set "claude_path=$FAKE_CLAUDE" >/dev/null
  touch "$BOX/.fde-coach-sandbox"
  echo "sandbox: a new dry-run home in $BOX (SANDBOX_RESET=1 starts again)" >&2
fi

exec "$PY" "$CLI" "$@"
