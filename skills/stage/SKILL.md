---
name: stage
description: Weekend Stage practice from FDE Impromptu Coach - one famous TED talk per weekend (ten talks, ten subjects, easiest to hardest), studied off camera and then performed in three takes on camera (Take A mirrors the speaker, Take B uses the same delivery move on your own FDE material, Take C adds a twist). Use when the user types /stage or asks for weekend practice, TED talk practice, practising a famous speech, speech delivery, shadowing a speaker, this weekend's talk or its segment, or their weekend streak, status or history. Runs the fde-coach CLI on macOS. Impromptu, pronunciation and legato have their own skills.
argument-hint: "[start | prep | status | history | segment <M:SS> <M:SS> | talks | upload]"
compatibility: macOS with FDE Impromptu Coach installed (the fde-coach CLI), a camera, and a browser for TED's player.
---

# Weekend Stage (one TED talk a weekend, on camera)

One practice of FDE Impromptu Coach, once a week. Saturday 08:00 the deck is built and a
prep page opens; Sunday 08:00 catches a missed Saturday. The streak counts weekends.

1. **Study, off camera (about 25 minutes).** The prep page embeds TED's own player, names
   the segment, and walks three passes over it (normal, muted for the body, eyes closed for
   the voice). The learner writes a beat sheet (5 to 7 keywords, `/` for a pause, CAPS for
   stress) and shadows the segment twice with headphones.
2. **Three takes, on camera (about 10 minutes).** QuickTime records while the slides run:
   Take A mirrors the speaker, Take B uses the same move on the learner's own material for the
   listener on the slide, Take C brings a twist they see only on its slide. Stops and saves by
   itself; the video uploads privately.

`fde-coach stage talks` lists the curriculum: Cutts, Okamoto, Treasure, Sinek, Pink, Rosling,
Robinson, Brown, Adichie, Stevenson. Use it rather than opening the catalogue file, which holds
every Take C twist. The design note is `~/FDE-Impromptu/src/references/stage_design.md` once
installed.

Run the CLI as `~/FDE-Impromptu/bin/fde-coach` (written `fde-coach` below). If that file does not exist, the
coach is not installed: point the user to *Install* in the `fde-impromptu-coach` skill and stop.

## What to run

Slash arguments: `$ARGUMENTS`. When they are empty, or Claude picked this skill from the conversation, use the
user's own words. Take the first row that fits.

| Arguments or words | Run | Tell the user |
|---|---|---|
| empty, `start`, "record my weekend talk" | `fde-coach stage session --detach` | Three takes on camera, about 10 minutes, saves by itself. If they haven't studied this weekend's talk yet, offer `fde-coach stage prep` first. Check `fde-coach stage status` afterwards. |
| `prep`, "this weekend's talk", "what am I practising?" | `fde-coach stage prep` | The talk, the segment and the page that opened. Not Take C's twist. |
| `segment 2:05 5:10`, "the segment starts at 2:05" | `fde-coach stage segment --start <M:SS> --end <M:SS>` | The times now show on the prep page and the Take A slide. |
| `status`, `streak`, "is my weekend done?" | `fde-coach stage status` | |
| `history` | `fde-coach stage history` | |
| `talks`, "which talks are coming?" | `fde-coach stage talks` | |
| "a different talk this weekend" | `fde-coach stage talks`, then `fde-coach stage generate --replace --talk <id>` before recording | |
| "move it to Sunday 9:00" | `fde-coach config --set stage.time=09:00` (and `fde-coach config --set 'stage.days=["Sun"]'`) | The schedule is reinstalled. |
| `upload`, "the upload didn't happen" | `fde-coach stage upload` | |
| anything else | the table in the `fde-impromptu-coach` skill | |

## Rules

1. **Study before the stage.** Recording without the prep throws away the point of the
   practice. When they start cold, ask once whether they've done the prep.
2. **Keep the twist hidden.** Take C's twist stays off the prep page and out of the chat
   until the weekend is recorded. Don't read the deck or the state file to find it.
3. **Links, not text.** TED talks are CC BY-NC-ND 4.0. Never paste, summarise or rewrite a
   transcript, never download TED video or audio, and never put TED's words into a deck,
   a note or an upload. Point to ted.com instead. Coach notes describe delivery (pace,
   pauses, emphasis, gesture), not the words.
4. **Their beat sheet is theirs.** If they ask for help with it, ask what the beats are
   and tighten their own keywords; never supply the speaker's lines.
5. **Run it detached.** Always `--detach`, then check `fde-coach stage status`.
6. **One recording a weekend.** If this weekend is recorded, say so; record again only if
   they want another take (`fde-coach stage session --force --detach`).
7. **Videos stay private.** The upload is their own camera recording with a TED credit line.
