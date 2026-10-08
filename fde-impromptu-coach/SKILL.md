---
name: fde-impromptu-coach
description: Daily speaking coach for the Forward Deployed Engineer (FDE) role on macOS. At 05:30 a timed PowerPoint deck of 5 never-repeated, progressively harder impromptu questions is recorded on camera and uploaded privately to YouTube; at 05:45 a pen-method pronunciation drill and at 06:00 a legato (smooth, connected speech) drill read verbatim passages from free public-domain books, never AI-written text. Each practice keeps a streak protected by Mac reminders and Google Calendar alerts. Use whenever the user mentions impromptu, FDE, communication or leadership practice, pronunciation, the pen method, legato, linking words, breath or fluency practice, reading passages or adding a book, today's deck, starting or recording a session, streaks, missed practice, reminders, calendar alerts, uploads, making practice harder or easier, or installing, configuring or troubleshooting this routine, even if they do not name the skill.
compatibility: macOS 12+ with Microsoft PowerPoint, QuickTime Player, Python 3.9+ and Claude Code. YouTube upload needs a Google Cloud OAuth desktop client.
---

# FDE Impromptu Coach

A daily, 5-minute, on-camera impromptu speaking routine that trains the
communication and leadership moments of a Forward Deployed Engineer: executive
updates, bad news, pushback, discovery, trade-offs, ethics, influence. Two
5-minute audio practices follow it, both reading **verbatim paragraphs from
free public-domain books** (Thoreau, Twain, Tagore, Franklin, Gibran, Marcus
Aurelius, *The Art of Public Speaking* and more; `assets/passages.json`):

* **Pronunciation (pen method), 05:45**: the learner's due hard words plus the
  passage's own hard words, read three times (Round 2 with a pen between the teeth).
* **Legato, 06:00**: breath and hum warm-up, a linking drill built from the
  passage ("turn it off" → tur-ni-toff), three reads (phrase map with breath
  marks and underlined joins, intoned, spoken clean), then a 45-second
  impromptu response to the author.

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
6. **Never write or rewrite reading passages.** Pronunciation and legato text
   comes only from the passage library (built-in, verified against its source
   editions, or imported by the learner from a free book). Claude's only job
   there is coach notes for hard words. Don't paraphrase, shorten or "improve"
   a passage, and don't offer AI-written paragraphs unless the user explicitly
   asks for the legacy mode (`pronunciation.paragraph_source=claude`).
7. **Cold read.** Today's passage stays hidden until recorded (`generate` and
   `history` hide it); show it only when asked (`--reveal`).

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
| "Pronunciation practice", "pen method", "start pronunciation" | `fde-coach pronounce session --detach` (audio only, ~5 min: warm-up words, 3 rounds with the pen in Round 2, words again; auto-stops and saves) |
| "Add a hard word" (pronunciation) | `fde-coach pronounce words --add WORD` (repeat per word; `--remove WORD`, bare `words` lists the pool and what's due) |
| "Pronunciation streak / status / history" | `fde-coach pronounce status` / `pronounce history` |
| "Legato practice", "connected speech", "linking practice", "start legato" | `fde-coach legato session --detach` (audio only, ~5 min: breath & hum, linking drill, 3 reads, 45 s response; auto-stops and saves) |
| "Legato streak / status / history" | `fde-coach legato status` / `legato history` (add `--reveal` to show today's passage before recording) |
| "Use a specific passage", "read Walden today" | `fde-coach library list` (filter `--theme speaking\|story\|reflection\|india\|nature`, `--level 1-3`), then `fde-coach legato generate --replace --passage ID` (or `pronounce generate --replace --passage ID`) before recording |
| "Only speeches / Indian authors" | `fde-coach config --set 'legato.themes=["speaking"]'` (same key under `pronunciation`) |
| "Add a book", "use passages from <free book>" | Project Gutenberg: `fde-coach library import-gutenberg <ebook number>` (from gutenberg.org/ebooks/N; `--max 20 --theme speaking --year 1903`). Any text the user has the right to use: `fde-coach library import-file PATH --author A --title T [--url U]` |
| "Show a passage / where is it from" | `fde-coach library show ID` (credit, source link, text, target words) |
| "Flow felt choppy / too easy" (legato) | the after-session tap does it; it moves the flow level (1 short sentences … 3 long, winding ones) |
| "Turn legato off / move it" | `fde-coach config --set legato.enabled=false` or `--set legato.daily_time=06:15` |
| "No camera on this Mac", "practise without video" | `fde-coach config --set recording.mode=none` — session runs the deck show only, still counts for the streak, no QuickTime/YouTube |
| "Upload didn't happen" | `fde-coach upload` |
| "Connect YouTube" | walk them through README.md → *Google setup*, then `fde-coach youtube-auth` |
| "Upload legato / pronunciation" | `fde-coach legato upload` / `fde-coach pronounce upload` |
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

## How the reading passages are chosen

- **Library** (`fdecoach/library.py`): 56 built-in passages (50–130 words, pre-1929
  works whose authors and translators died before 1956), each with author,
  work, year, section, source link (Standard Ebooks or Project Gutenberg),
  theme, level and five hand-written pronunciation notes. Learners add more with
  `library import-gutenberg` / `import-file` (stored in `~/FDE-Impromptu/library/`).
  `scripts/tools/build_passage_library.py verify` re-downloads the source
  editions and checks every built-in passage is verbatim.
- **Legato**: never-read passages first (then the least recently read third),
  nearest to the learner's flow level (starts at 1, +1 every 7 recorded
  sessions, nudged by the Choppy/Smooth tap). Breath marks and linking chains
  are computed from the text (`fdecoach/legato.py`), not generated.
- **Pronunciation** (default `paragraph_source=library`): prefers a passage that
  contains the learner's due words; up to 3 due words lead the warm-up list,
  then the passage's own hard words (6 words total). Coach notes come from the
  library; Claude is called only to mark up words that have none
  (`references/pronunciation_annotation.md`). Offline it still works (plain words).

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
3. **05:45 / 06:00** the pronunciation and legato agents build their decks and
   ask to start. Finishing one practice offers the next (FDE → pronunciation →
   legato), so one "Start now" can run all three back to back.
4. **Every 15 minutes** a second agent catches up a missed 05:30 run (Mac was
   asleep), shows escalating reminders at the configured times until the day is
   recorded (last call at 22:00, quiet after 22:45), keeps every practice's
   calendar events rolling forward and retries failed uploads. Google Calendar alerts
   (07:30, 12:30, 18:00, 21:30 + an email) reach the phone, browser or inbox
   only on unrecorded days, even when the Mac is closed.

## Install

From the unzipped skill folder (normally `~/.claude/skills/fde-impromptu-coach`):

```bash
bash ~/.claude/skills/fde-impromptu-coach/install.sh
```

It creates a Python virtual environment in `~/FDE-Impromptu/venv`, installs
`requirements.txt`, writes the launcher, installs the four launchd agents and
triggers every macOS permission prompt (Automation for QuickTime, PowerPoint and
Reminders; camera and microphone for QuickTime; notifications). Tell the user to
click **OK / Allow** on each. Then `fde-coach doctor` should be all `[ok]`
except YouTube until it is connected. README.md has the full guide, including
YouTube setup and an optional `pmset` wake schedule.

## Files

- `scripts/fde_coach.py` — CLI (`--help` lists all commands)
- `scripts/fdecoach/` — modules: `app` (flows), `questions`, `deck`, `recorder`,
  `macos` (AppleScript), `youtube`, `gcal` (Google Calendar missed-practice alerts),
  `scheduler` (launchd), `state`, `config`; the audio practices share
  `practice` (build/record/video/upload/calendar engine) and `audio` (ffmpeg);
  pronunciation: `pronounce` (words + passage), `pronounce_deck`,
  `pronounce_session`; legato: `legato` (breath groups, links, choice),
  `legato_deck`, `legato_session`; `library` (public-domain passages, imports)
- `scripts/tools/build_passage_library.py` — builds and `verify`s `assets/passages.json`
  from `assets/passage_sources.json` + `assets/passage_annotations.json`
- `scripts/tests/` — `~/FDE-Impromptu/venv/bin/python -m unittest discover -s scripts/tests` (dry-run, safe anywhere; needs the venv because the CLI imports `pptx`)
- `references/question_design.md` — question rubric and JSON schema
- `references/pronunciation_design.md` — legacy (AI-written) paragraph rubric and JSON schema
- `references/pronunciation_annotation.md` — coach-note rubric for library mode (Claude marks up words only)
- `references/legato_design.md` — legato practice design: drills, marks, levels, research basis
- `references/passage_sources.md` — passage library policy, sources, licences, verifying and importing
- `references/pronunciation_plan.md` — pronunciation practice design plan
- `references/troubleshooting.md` — symptoms → fixes
- `references/plan.md` — design plan, risks found in validation, and fixes
