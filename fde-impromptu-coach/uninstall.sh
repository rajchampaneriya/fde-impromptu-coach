#!/bin/bash
# Removes the daily schedule and the launcher. Your history, decks and videos are kept.
# Usage: bash uninstall.sh [--purge]   (--purge also deletes ~/FDE-Impromptu; videos in ~/Movies are never deleted)
set -euo pipefail
DATA_DIR="${FDE_COACH_HOME:-$HOME/FDE-Impromptu}"
SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

for label in com.fdecoach.daily com.fdecoach.reminder; do
  launchctl bootout "gui/$(id -u)/$label" >/dev/null 2>&1 || true
  rm -f "$HOME/Library/LaunchAgents/$label.plist"
  echo "Removed $label"
done
# Remove upcoming Google Calendar missed-practice alerts (best effort; needs the launcher)
if [ -x "$DATA_DIR/bin/fde-coach" ]; then
  "$DATA_DIR/bin/fde-coach" calendar-sync --clear >/dev/null 2>&1 && echo "Removed upcoming Google Calendar alerts" || true
fi
if [ -L "$HOME/.local/bin/fde-coach" ]; then
  rm -f "$HOME/.local/bin/fde-coach"
fi
if [ "${1:-}" = "--purge" ]; then
  rm -rf "$DATA_DIR"
  echo "Deleted $DATA_DIR (recordings in ~/Movies/FDE-Impromptu were kept)."
else
  echo "Kept your data in $DATA_DIR. Re-install any time with: bash \"$SKILL_DIR/install.sh\""
fi
