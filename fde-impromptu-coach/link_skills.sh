#!/bin/bash
# Links this repo's Claude Code skills into ~/.claude/skills, where Claude Code looks for them
# (~/.claude/skills/<name>/SKILL.md, one level down). Then /impromptu, /pronunciation, /legato,
# /fde-learn and /fde-impromptu-coach work in every Claude Code session on this Mac.
#
# Usage: bash link_skills.sh            link every skill (safe to re-run; never touches a real folder)
#        bash link_skills.sh --check    report each skill; exit 1 if any is not linked to this clone
#        bash link_skills.sh --remove   remove only the links that point into this clone
# CLAUDE_SKILLS_DIR overrides ~/.claude/skills (the tests use it).
#
# bash 3.2 compatible (macOS /bin/bash): no associative arrays, no readlink -f.
set -uo pipefail

MODE="${1:-link}"
case "$MODE" in link|--check|--remove) ;; *) echo "Usage: bash link_skills.sh [--check|--remove]" >&2; exit 2 ;; esac

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
DEST="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"

# name:folder (relative to the repo root). Keep in sync with CLAUDE_SKILLS in
# scripts/fdecoach/config.py and the skills table in AGENTS.md (the tests check all three).
SKILLS="fde-impromptu-coach:fde-impromptu-coach
fde-learn:fde-learn
impromptu:skills/impromptu
pronunciation:skills/pronunciation
legato:skills/legato"

real() { (cd "$1" 2>/dev/null && pwd -P); }

status=0
if [ "$MODE" = "link" ]; then
  mkdir -p "$DEST"
  dest_real="$(real "$DEST")"
  case "$REPO/" in
    "$dest_real"/?*)
      echo "Note: this clone is inside $DEST. Claude Code only looks one level down, so it cannot see"
      echo "      skills nested in a clone there. Move the clone (for example to ~/Code/fde-impromptu-coach)"
      echo "      and run its fde-impromptu-coach/install.sh again." ;;
  esac
fi

while IFS= read -r entry; do
  name="${entry%%:*}"
  src="$REPO/${entry#*:}"
  dst="$DEST/$name"
  if [ ! -f "$src/SKILL.md" ]; then
    echo "[!!] $name: $src/SKILL.md not found. Clone the whole repo and run install.sh from the clone."
    status=1
    continue
  fi
  src_real="$(real "$src")"
  dst_real="$(real "$dst")"
  case "$MODE" in
    --check)
      if [ "$dst_real" = "$src_real" ]; then
        echo "[ok] /$name -> $src_real"
      elif [ -e "$dst" ]; then
        echo "[!!] /$name: $dst is not this clone's skill"; status=1
      else
        echo "[!!] /$name: not linked ($dst missing)"; status=1
      fi
      ;;
    --remove)
      if [ -L "$dst" ] && [ "$dst_real" = "$src_real" ]; then
        rm -f "$dst" && echo "Removed the /$name skill link"
      fi
      ;;
    link)
      if [ "$dst_real" = "$src_real" ]; then
        echo "[ok] /$name already linked"
      elif [ -L "$dst" ]; then
        old="$(readlink "$dst")"
        rm -f "$dst" && ln -s "$src_real" "$dst" && echo "[ok] /$name relinked to this clone (was $old)"
      elif [ -e "$dst" ]; then
        echo "[!!] /$name: $dst is a real folder (a copy?), left as it is. Rename or remove it, then run this again."
        status=1
      else
        ln -s "$src_real" "$dst" && echo "[ok] /$name linked"
      fi
      ;;
  esac
done <<EOF
$SKILLS
EOF

if [ "$MODE" = "link" ] && [ "$status" -eq 0 ]; then
  echo "Skills ready. In Claude Code type /impromptu, /pronunciation, /legato or /fde-learn, or just say what you want"
  echo "(\"start legato\"). If a session was already open and the command is missing, start a new session."
fi
exit "$status"
