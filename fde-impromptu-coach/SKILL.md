---
name: fde-impromptu-coach
description: Daily impromptu-speaking coach for the Forward Deployed Engineer (FDE) role on macOS. Every morning at 05:30 it builds a minimalist blue, Calibri PowerPoint deck with 5 never-repeated, progressively harder impromptu questions (60-second timer per slide, auto-advance), records a ~5-minute QuickTime camera video, uploads it to YouTube as a private video, and protects the daily streak with escalating Mac reminders plus Google Calendar alerts that fire only on missed days. Use this skill whenever the user mentions impromptu practice, FDE or communication or leadership practice, today's questions or practice deck, starting or recording today's session, their practice streak, missed practice, practice reminders or calendar alerts, the 5:30 schedule, practice video uploads, making questions harder or easier or about a topic, or installing, configuring or troubleshooting this routine, even if they do not name the skill.
compatibility: macOS 12+ with Microsoft PowerPoint, QuickTime Player, Python 3.9+ and Claude Code. YouTube upload needs a Google Cloud OAuth desktop client.
---

# FDE Impromptu Coach

A daily, 5-minute, on-camera impromptu speaking routine that trains the
communication and leadership moments of a Forward Deployed Engineer: executive
updates, bad news, pushback, discovery, trade-offs, ethics, influence.

Everything is driven by one CLI. After installation it is at
`~/FDE-Impromptu/bin/fde-coach` (also linked as `~/.local/bin/fde-coach`).
Below, `fde-coach` means that path. If it does not exist, the skill is not
installed yet: see **Install** below.

## Ground rules (follow every time)

1. **Keep the surprise.** Never print or read out today's question texts before
   today is recorded, unless the user explicitly asks to see them. `status`,
   `generate` and `history` hide them on purpose; do not work around that (no
   `--reveal`, no opening the JSON or the deck text) unless asked.
2. **The streak comes first.** If automation fails, help the user record some
   other way today, then mark it with `fde-coach complete`. A day counts once it
   is marked recorded.
3. **Long commands run detached.** A session takes about 5.5 minutes plus saving,
   longer than a tool call should block. Always start it with
   `fde-coach session --detach`, then check `fde-coach status` afterwards.
4. **Videos stay private.** Never change `youtube.privacy_status` unless the user
   explicitly asks.
5. Today's questions can be replaced only **before** today is recorded.

## What the user says → what to run

| User intent | Command |
|---|---|
| "Start my practice", "record today" | `fde-coach session --detach` (tell them: QuickTime starts, slides run 10 s intro + 5 × 60 s, then everything stops and saves by itself) |
| "Did I practise today?", "what's my streak?" | `fde-coach status` |
| "Show past sessions / questions" | `fde-coach history` (add `--limit N`) |
| "New questions for today", "make today about healthcare / a CISO audience" | `fde-coach generate --replace --brief "…"` (questions stay hidden; report categories and difficulty only) |
| "Open today's deck" | `fde-coach open` |
| "Too easy" / "too hard" | `fde-coach level --up` / `--down` (then `generate --replace` if today is not recorded yet) |
| "Remind me at another time", "run at 6:15" | `fde-coach config --set daily_time=06:15` (reinstalls the schedule) or `--set 'reminders.times=["07:00","12:00","20:00"]'` |
| "I recorded it myself / on my phone" | `fde-coach complete --video /path/to/file` (or `--no-video` if no usable file) |
| "Upload didn't happen" | `fde-coach upload` |
| "Connect YouTube" | walk them through README.md → *Google setup*, then `fde-coach youtube-auth` |
| "Connect Google Calendar", "alert me if I miss" | README.md → *Google setup* (enable Google Calendar API), then `fde-coach calendar-auth` |
| "Change / stop the calendar alerts" | `fde-coach config --set 'google_calendar.popup_times=[…]'` or `google_calendar.enabled=false`, then `fde-coach calendar-sync` |
| "Something's broken" | `fde-coach doctor`, then `references/troubleshooting.md` |
| "Tell the coach about me" | `fde-coach config --set 'learner_context=…'` (background, target companies, weak spots; used for every future set) |

Settings live in `~/FDE-Impromptu/config.json`; `fde-coach config` prints them.

## How today's questions are made

- **Automatic (default, surprise preserved):** at 05:30 the scheduler runs
  `claude -p` headless with the rubric in `references/question_design.md`, the
  day's plan (5 competencies, least-practised first; difficulty ramp) and the
  full question history. Every candidate is novelty-checked against all past
  questions and the built-in bank; rejects are retried once, then backfilled from
  the 132-question curated bank (`assets/question_bank.json`). A deck is always
  produced, even offline.
- **Difficulty:** level 1–5, starting at 2 and rising one level every 6 recorded
  sessions; each day ramps L, L, L+1, L+1, L+2; constraint twists from level 3;
  framework hints disappear after level 2; the after-session "too easy / too
  hard" tap and `fde-coach level` shift the level.
- **Hand-authored (only when the user wants to write or see the questions):**
  1. `fde-coach plan` → JSON with today's slots, level, rubric path, recent past
     questions and the file path to write.
  2. Read `references/question_design.md`, then write
     `{"questions": [{slot, category, difficulty, format, text, constraint, coach_note}, …]}`
     to `write_json_to`, matching every slot's category and difficulty.
  3. Run the `then_run` command (`fde-coach build --questions … --replace`).
     It prints any rejected items (too similar to the past, wrong length); those
     slots are filled from the bank. Rewrite and rebuild if the user wants their
     own text in every slot.

## The daily flow (for explaining it to the user)

1. **05:30** launchd runs `fde-coach daily`: builds the deck
   (`~/FDE-Impromptu/decks/YYYY-MM-DD_FDE-Impromptu.pptx`), opens it in
   PowerPoint with the thumbnail pane collapsed (so the questions are not
   spoiled), posts a notification, adds an Apple Reminders item, makes sure the
   Google Calendar missed-practice events exist for today and the next two days,
   and asks **Start now / Snooze / Later**.
2. **Start** (dialog button, double-click `~/FDE-Impromptu/Start Practice.command`,
   or ask Claude): QuickTime starts a camera recording, the slide show starts,
   each slide's 60-second bar runs and auto-advances, the recording stops and is
   saved to `~/Movies/FDE-Impromptu/`, the streak updates, the Reminders item is
   completed, today's Google Calendar event is deleted (so its alerts never
   fire) and the video uploads privately to YouTube with the questions and
   chapter marks in the description.
3. **Every 15 minutes** a second agent catches up a missed 05:30 run (Mac was
   asleep), shows escalating reminders at the configured times until the day is
   recorded (last call at 22:00, quiet after 22:45), keeps the calendar events
   rolling forward and retries failed uploads. Google Calendar alerts
   (07:30, 12:30, 18:00, 21:30 + an email) reach the phone, browser or inbox
   only on unrecorded days, even when the Mac is closed.

## Install

From the unzipped skill folder (normally `~/.claude/skills/fde-impromptu-coach`):

```bash
bash ~/.claude/skills/fde-impromptu-coach/install.sh
```

It creates a Python virtual environment in `~/FDE-Impromptu/venv`, installs
`requirements.txt`, writes the launcher, installs the two launchd agents and
triggers every macOS permission prompt (Automation for QuickTime, PowerPoint and
Reminders; camera and microphone for QuickTime; notifications). Tell the user to
click **OK / Allow** on each. Then `fde-coach doctor` should be all `[ok]`
except YouTube until it is connected. README.md has the full guide, including
YouTube setup and an optional `pmset` wake schedule.

## Files

- `scripts/fde_coach.py` — CLI (`--help` lists all commands)
- `scripts/fdecoach/` — modules: `app` (flows), `questions`, `deck`, `recorder`,
  `macos` (AppleScript), `youtube`, `gcal` (Google Calendar missed-practice alerts),
  `scheduler` (launchd), `state`, `config`
- `scripts/tests/` — `~/FDE-Impromptu/venv/bin/python -m unittest discover -s scripts/tests` (dry-run, safe anywhere; needs the venv because the CLI imports `pptx`)
- `references/question_design.md` — question rubric and JSON schema
- `references/troubleshooting.md` — symptoms → fixes
- `references/plan.md` — design plan, risks found in validation, and fixes
