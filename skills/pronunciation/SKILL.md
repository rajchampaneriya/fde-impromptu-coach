---
name: pronunciation
description: Pronunciation practice from FDE Impromptu Coach - the pen method, a 5-minute audio drill on the learner's hard words and a verbatim passage from a public-domain book. Use when the user types /pronunciation or says pronunciation (also misspelt "pronounciation", "pronunciaton"), pronounce, the pen method, hard words, add a hard word, clearer speech or articulation practice, or asks for their pronunciation streak, status or history. Runs the fde-coach CLI on macOS. Impromptu and legato have their own skills.
argument-hint: "[start | status | history | words | add <word> | remove <word> | passage <id> | upload]"
compatibility: macOS with FDE Impromptu Coach installed (the fde-coach CLI).
---

# Pronunciation practice (pen method)

One practice of FDE Impromptu Coach, at 05:45: warm-up words (up to 3 of the learner's due hard words, then the
passage's own), the passage read three times (Round 2 with a pen between the teeth), the words again. Audio only,
about 5 minutes; it stops and saves by itself. The text is a verbatim paragraph from a free public-domain book.
The umbrella skill `fde-impromptu-coach` covers set-up, settings, the passage library and troubleshooting.

Run the CLI as `~/FDE-Impromptu/bin/fde-coach` (written `fde-coach` below). If that file does not exist, the
coach is not installed: point the user to *Install* in the `fde-impromptu-coach` skill and stop.

## What to run

Slash arguments: `$ARGUMENTS`. When they are empty, or Claude picked this skill from the conversation, use the
user's own words. Take the first row that fits.

| Arguments or words | Run | Tell the user |
|---|---|---|
| empty, `start`, "pen method", "start pronunciation" | `fde-coach pronounce session --detach` | Warm-up words, 3 rounds (pen in Round 2), words again; about 5 minutes, audio only, saves by itself. Check `fde-coach pronounce status` afterwards. |
| `status`, `streak` | `fde-coach pronounce status` | |
| `history` | `fde-coach pronounce history` | |
| `words`, "which words are due?" | `fde-coach pronounce words` | The pool and what is due. |
| `add <word>`, "add a hard word" | `fde-coach pronounce words --add <word>` (once per word) | |
| `remove <word>` | `fde-coach pronounce words --remove <word>` | |
| `passage <id>`, "read Walden today" | `fde-coach library list` (filter with `--theme` or `--level`), then `fde-coach pronounce generate --replace --passage <id>` before recording | The passage's author and work, not its text. |
| `upload`, "the upload didn't happen" | `fde-coach pronounce upload` | |
| anything else | the table in the `fde-impromptu-coach` skill | |

Finishing pronunciation offers legato next.

## Rules

1. **Cold read.** Today's passage stays hidden until it is recorded: no reveal flag and no opening the deck,
   unless the user explicitly asks.
2. **Never write or rewrite a passage.** The text comes only from the passage library (built-in or imported from
   a free book). Claude's only part is coach notes for hard words. Never offer an AI-written paragraph.
3. **Run it detached.** Always `--detach`, then check `fde-coach pronounce status`.
4. **One take a day.** If today is already recorded, say so; record again only if they want another take
   (`fde-coach pronounce session --force --detach`).
