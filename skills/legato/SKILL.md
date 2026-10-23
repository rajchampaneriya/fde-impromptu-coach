---
name: legato
description: Legato practice from FDE Impromptu Coach - smooth, connected speech in a 5-minute audio drill (breath and hum, a linking drill, three reads of a public-domain passage, then a 45-second impromptu response to the author). Use when the user types /legato or says legato (also misspelt "lagato", "legatto"), connected speech, linking words, sounding less choppy or smoother, breath or fluency practice, or asks for their legato streak, status or history. Runs the fde-coach CLI on macOS. Impromptu and pronunciation have their own skills.
argument-hint: "[start | status | history | passage <id> | themes <theme> | upload]"
compatibility: macOS with FDE Impromptu Coach installed (the fde-coach CLI).
---

# Legato practice (smooth, connected speech)

One practice of FDE Impromptu Coach, at 06:00: breath and hum warm-up, a linking drill built from the passage
("turn it off" → tur-ni-toff), three reads (phrase map with breath marks and underlined joins, intoned, spoken
clean), then a 45-second impromptu response to the author. Audio only, about 5 minutes; it stops and saves by
itself. The text is a verbatim paragraph from a free public-domain book. The umbrella skill
`fde-impromptu-coach` covers set-up, settings, the passage library and troubleshooting.

Run the CLI as `~/FDE-Impromptu/bin/fde-coach` (written `fde-coach` below). If that file does not exist, the
coach is not installed: point the user to *Install* in the `fde-impromptu-coach` skill and stop.

## What to run

Slash arguments: `$ARGUMENTS`. When they are empty, or Claude picked this skill from the conversation, use the
user's own words. Take the first row that fits.

| Arguments or words | Run | Tell the user |
|---|---|---|
| empty, `start`, "connected speech", "linking practice" | `fde-coach legato session --detach` | Breath and hum, linking drill, 3 reads, 45 s response; about 5 minutes, audio only, saves by itself. Check `fde-coach legato status` afterwards. |
| `status`, `streak` | `fde-coach legato status` | |
| `history` | `fde-coach legato history` | |
| `passage <id>`, "read Walden today" | `fde-coach library list` (filter with `--theme` or `--level`), then `fde-coach legato generate --replace --passage <id>` before recording | The passage's author and work, not its text. |
| `themes <theme>`, "only speeches" | `fde-coach config --set 'legato.themes=["speaking"]'` (themes: speaking, story, reflection, india, nature) | |
| `upload`, "the upload didn't happen" | `fde-coach legato upload` | |
| "felt choppy" / "too easy" | nothing to run: the Choppy / Smooth tap after the session moves the flow level | |
| anything else | the table in the `fde-impromptu-coach` skill | |

Legato is the last practice of the morning chain; the impromptu answer key opens when it ends.

## Rules

1. **Cold read.** Today's passage stays hidden until it is recorded: no reveal flag and no opening the deck,
   unless the user explicitly asks.
2. **Never write or rewrite a passage.** The text comes only from the passage library; breath marks and linking
   chains are computed from it. Never paraphrase, shorten or "improve" a passage.
3. **Run it detached.** Always `--detach`, then check `fde-coach legato status`.
4. **One take a day.** If today is already recorded, say so; record again only if they want another take
   (`fde-coach legato session --force --detach`).
