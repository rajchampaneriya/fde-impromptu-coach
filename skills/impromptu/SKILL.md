---
name: impromptu
description: Impromptu speaking practice from FDE Impromptu Coach - five surprise questions answered on camera (exec slots with a 25-second headline window), then the exec answer key to practise the correct response. Use when the user types /impromptu or says impromptu (also misspelt "impromptue", "impromtu"), impromptu response practice, start or record my practice, today's questions, did I practise, my streak, how should I have answered, model or exec answers, say it back, my one-breath headlines, too easy or too hard. Runs the fde-coach CLI on macOS. Pronunciation and legato have their own skills.
argument-hint: "[start | status | answers | headlines | harder | easier | brief <topic> | history]"
compatibility: macOS with FDE Impromptu Coach installed (the fde-coach CLI).
---

# Impromptu practice

One practice of FDE Impromptu Coach: five never-repeated questions, each naming its listener, answered on
camera; exec slots train the headline-first answer. After recording, the exec answer key shows a model answer
for every question so the learner can practise the correct response. The umbrella skill
`fde-impromptu-coach` covers set-up, settings, Google, troubleshooting and every other command.

Run the CLI as `~/FDE-Impromptu/bin/fde-coach` (written `fde-coach` below). If that file does not exist, the
coach is not installed: point the user to *Install* in the `fde-impromptu-coach` skill and stop.

## What to run

Slash arguments: `$ARGUMENTS`. When they are empty, or Claude picked this skill from the conversation, use the
user's own words. Take the first row that fits.

| Arguments or words | Run | Tell the user |
|---|---|---|
| empty, `start`, "record today", "let's practise" | `fde-coach session --detach` | QuickTime starts; a 10 s intro, then 5 questions (60 s each; exec slides 25 s, then a reply slide); it stops and saves by itself. Check `fde-coach status` afterwards. |
| `status`, `streak`, "did I practise today?" | `fde-coach status` | Recorded or not, and the streak. |
| `answers`, "how should I have answered?", "model answers", "response practice" | `fde-coach answers --open` | The key's status; `pending` and `partial` fill in by themselves. Before today is recorded it refuses: record first. |
| `say it back`, `headlines`, "all my one-breath lines" | `fde-coach answers --index --open` | Every day's one-breath lines on one page. |
| `harder` / `easier`, "too easy" / "too hard" | `fde-coach level --up` or `fde-coach level --down`, then `fde-coach generate --replace` if today is not recorded | The new categories and difficulty only. |
| `brief <topic>`, "make today about healthcare" | `fde-coach generate --replace --brief "<topic>"` | Categories and difficulty only. |
| `history` | `fde-coach history` | |
| `open`, "show me the deck" | `fde-coach open` | The thumbnail pane stays collapsed. |
| "I recorded it on my phone" | `fde-coach complete --video <path>` (or `fde-coach complete --no-video`) | The day counts. |
| anything else | the table in the `fde-impromptu-coach` skill | |

Finishing the session offers pronunciation and then legato; the answer key opens when that chain ends.

## Rules

1. **Keep the surprise.** Never show today's questions before today is recorded: no reveal flag, no reading the
   deck or the JSON, unless the user explicitly asks.
2. **Model answers come after the attempt.** Never ask `answers` to reveal early and never write model answers
   into the chat for an unrecorded day, unless the user explicitly asks.
3. **Run it detached.** A session takes about 5.5 minutes; always `--detach`, then check `fde-coach status`.
4. **One take a day.** If today is already recorded, say so; record again only if they want another take
   (`fde-coach session --force --detach`).
5. **Videos stay private.** Never change `youtube.privacy_status` unless asked.
