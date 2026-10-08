#!/bin/bash
# FDE Impromptu Coach installer (macOS).
# Usage: bash install.sh [--time HH:MM] [--no-warmup]
# Safe to re-run: upgrades dependencies and reinstalls the schedule; keeps your history.
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="${FDE_COACH_HOME:-$HOME/FDE-Impromptu}"
VENV="$DATA_DIR/venv"

say() { printf '\n\033[1;34m==>\033[0m %s\n' "$1"; }

if [ "$(uname -s)" != "Darwin" ]; then
  echo "This installer is for macOS." >&2
  exit 1
fi

# Pick a Python >= 3.9. Apple's Command Line Tools Python is preferred because
# Homebrew upgrades can break a virtual environment (re-run this script if so).
PY=""
candidates=()
[ -n "${FDE_PYTHON:-}" ] && candidates+=("$FDE_PYTHON")
if xcode-select -p >/dev/null 2>&1; then candidates+=("/usr/bin/python3"); fi
candidates+=("/opt/homebrew/bin/python3" "/usr/local/bin/python3")
for c in "${candidates[@]}"; do
  if [ -x "$c" ] && "$c" -c 'import sys, venv; sys.exit(0 if sys.version_info >= (3, 9) else 1)' >/dev/null 2>&1; then
    PY="$c"
    break
  fi
done
if [ -z "$PY" ]; then
  echo "Python 3.9+ not found. Install Apple's command line tools (xcode-select --install) or Homebrew Python, then re-run." >&2
  exit 1
fi
say "Using $("$PY" -c 'import sys; print(sys.executable, sys.version.split()[0])')"

mkdir -p "$DATA_DIR"
if [ -x "$VENV/bin/python" ] && ! "$VENV/bin/python" -c 'import sys' >/dev/null 2>&1; then
  say "Existing virtual environment is broken; recreating it"
  rm -rf "$VENV"
fi
if [ ! -x "$VENV/bin/python" ]; then
  say "Creating virtual environment in $VENV"
  "$PY" -m venv "$VENV"
fi

say "Installing Python packages"
"$VENV/bin/python" -m pip install --quiet --upgrade pip
"$VENV/bin/python" -m pip install --quiet --upgrade -r "$SKILL_DIR/requirements.txt"

# Deploy the runtime scripts into the data folder. macOS TCC blocks
# launchd agents from reading ~/Downloads (and other protected folders),
# so the schedule must run from a copy outside them.
SRC_DIR="$DATA_DIR/src"
if [ "$(cd "$SKILL_DIR" && pwd)" != "$(cd "$SRC_DIR" 2>/dev/null && pwd)" ]; then
  say "Deploying scripts to $SRC_DIR"
  mkdir -p "$SRC_DIR"
  rsync -a --delete --exclude '__pycache__' \
    "$SKILL_DIR/scripts" "$SKILL_DIR/references" "$SKILL_DIR/assets" "$SRC_DIR/"
fi

say "Running self-tests (simulated, nothing is recorded or uploaded)"
if (cd "$SRC_DIR" && "$VENV/bin/python" -m unittest discover -s scripts/tests >/dev/null 2>&1); then
  echo "Self-tests passed."
else
  echo "Warning: self-tests failed. Details: cd \"$SRC_DIR\" && \"$VENV/bin/python\" -m unittest discover -s scripts/tests -v"
fi

say "Setting up data folder, launcher and the daily schedule"
FDE_COACH_HOME="$DATA_DIR" "$VENV/bin/python" "$SRC_DIR/scripts/fde_coach.py" setup "$@"

mkdir -p "$HOME/.local/bin"
ln -sf "$DATA_DIR/bin/fde-coach" "$HOME/.local/bin/fde-coach"

cat <<MSG

Installed.

Next steps
  1. Approve the macOS prompts that appear in the next minute (Automation for
     QuickTime / PowerPoint / Reminders, Camera + Microphone for QuickTime,
     Notifications). A QuickTime camera preview opens for 3 seconds - that is the check.
  2. Check everything:        $DATA_DIR/bin/fde-coach doctor
  3. Connect Google (once):   see README.md "Google setup", then
                              $DATA_DIR/bin/fde-coach youtube-auth
                              $DATA_DIR/bin/fde-coach calendar-auth   (missed-practice alerts)
  4. Try a session now:       double-click "$DATA_DIR/Start Practice.command"
                              (it offers pronunciation and legato practice afterwards)
  5. Browse the reading passages (public-domain books): $DATA_DIR/bin/fde-coach library list

Tip: add ~/.local/bin to your PATH to type just 'fde-coach'.
MSG
