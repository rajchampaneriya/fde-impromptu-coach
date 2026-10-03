---
name: fde-impromptu-coach
description: Daily speaking coach for the Forward Deployed Engineer (FDE) role on macOS, with three tracks: a 05:30 impromptu practice (minimalist blue Calibri PowerPoint deck, 5 never-repeated, progressively harder questions, 60 s each, QuickTime camera recording, private YouTube upload), a pen-method pronunciation practice, and a daily Software Factory / Gas City explainer with a real demo in every episode (day-before brief, recording-day kit, up to 3 voice takes, a faceless video under 3 minutes for the public channel). Mac reminders and Google Calendar alerts protect each streak. Use this skill whenever the user mentions impromptu, FDE, communication or pronunciation practice, today's questions or deck, the Software Factory or Gas City video series, tomorrow's topic, a brief, takes, publishing a video, the learning path, streaks, reminders, calendar alerts, practice video uploads, or installing, configuring or troubleshooting this routine, even if they do not name the skill.
compatibility: macOS 12+ with Microsoft PowerPoint, QuickTime Player, Python 3.9+ and Claude Code. ffmpeg for the pronunciation and Software Factory videos. YouTube upload needs a Google Cloud OAuth desktop client.
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
4. **Practice videos stay private.** Never change `youtube.privacy_status` unless
   the user explicitly asks. Software Factory videos are the exception: they are
   made for the user's public channel, but the user publishes them (YouTube
   Studio, `factory.publish_mode=studio`). Never switch to `api` publishing
   unless asked.
5. Today's questions can be replaced only **before** today is recorded.
6. **Software Factory: one video, one concept, one takeaway, under 3 minutes,
   at most 3 takes, a real demo every time, never the user's face.** Help the
   user explain, don't script them: give keywords and plain-language
   definitions, not paragraphs to read. Never process their voice (no noise
   reduction or loudness filters); a past audio clean-up hurt their recordings.
   Never publish a preview demo: capture it, or use their own clip.

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
| "No camera on this Mac", "practise without video" | `fde-coach config --set recording.mode=none` — session runs the deck show only, still counts for the streak, no QuickTime/YouTube |
| "Upload didn't happen" | `fde-coach upload` |
| "Connect YouTube" | walk them through README.md → *Google setup*, then `fde-coach youtube-auth` |
| "Connect Google Calendar", "alert me if I miss" | README.md → *Google setup* (enable Google Calendar API), then `fde-coach calendar-auth` |
| "Change / stop the calendar alerts" | `fde-coach config --set 'google_calendar.popup_times=[…]'` or `google_calendar.enabled=false`, then `fde-coach calendar-sync` |
| "What's tomorrow's video?", "send me tomorrow's brief" | `fde-coach factory brief` (prints it; `--open` opens the styled page). It also arrives by itself at `factory.brief_time` (19:00) and as a Google Calendar event |
| "Prepare today's video", "build my slides / outline" | `fde-coach factory prep --open` (slides, prep sheet, outline, checks to verify; built by itself at `factory.prep_time`) |
| "Record the video", "start take 1 / next take" | `fde-coach factory take --detach` (voice + auto-advancing slides, ~3 min; Take 1 Discovery, Take 2 Improve, Take 3 Publish; never more than 3) |
| "Set up the demos", "install Gas City for the videos" | install Gas City (`brew install gascity`) and Claude Code (`curl -fsSL https://claude.ai/install.sh \| bash`, then `claude` once to log in); then `fde-coach factory demo setup --store file` (Days 1–7) and `--store bd` (Day 8 on) |
| "Run / check today's demo" | `fde-coach factory demo capture` (`--date tomorrow`), `fde-coach factory demo status` |
| "Use my screen recording for the demo" | `fde-coach factory demo clip --file PATH` |
| "Publish today's video", "use take 2" | `fde-coach factory publish --take N` (assembles final.mp4, thumbnail, title/description/chapters; opens YouTube Studio) |
| "It's live: <link>" | `fde-coach factory published --url LINK` |
| "Show the learning path", "where am I in the series?" | `fde-coach factory plan` / `fde-coach factory status` |
| "Change today's wording / takeaway / visual" | write `~/FDE-Impromptu/factory/overrides/<topic-id>.json` (any of what, what_points, why, why_points, how, how_points, visual, analogy, jargon, takeaway, artifact, demo, verify), then `fde-coach factory prep --rebuild` |
| "Use my own intro/outro music" | `fde-coach factory music --intro FILE --outro FILE` (YouTube Audio Library tracks are a good source) |
| "Plan the next module" (after Day 35) | follow `references/factory_curriculum.md`: append days to `assets/factory_curriculum.json`, run the tests, re-run `install.sh` |
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

## The Software Factory video series

A daily explainer for the user's public YouTube channel (`factory.channel`,
default rajcwork), starting `factory.start_date` (2026-10-10). The learning path
(`assets/factory_curriculum.json`, readable copy in
`references/factory_learning_path.md`) has 35 days in six modules, grounded in
https://github.com/gastownhall/gascity: the big picture, beads, agents and
sessions, formulas, orders and operations, packs. Topics are consumed in order;
a day that isn't published carries its topic over.

- **Day before, 19:00:** the brief (topic, WHAT, WHY, HOW, repository references,
  existing diagrams, artifact or demo, 3-minute outline) opens on the Mac, and a
  Google Calendar event with the same brief alerts the phone and inbox.
- **Every video teaches Greg Tang style:** see it (a real demo), group it (one
  picture of the pattern), name it (the takeaway). Format, 2:50: intro 4 s,
  what & why 25 s, demo 100 s, picture 22 s, takeaway 12 s, outro 7 s.
- **Demos are real and faceless.** Each day's commands run in a demo city
  (`~/rajcwork-demo`: a file-store city for Days 1–7, the default bd + Dolt
  city from Day 8) with the rig `hello-factory`. `factory demo capture` saves
  the real output; the video shows it as an animated terminal (slow agent work
  becomes a time-lapse card). The capture runs with the evening brief, and in
  the morning if it is missing. Publishing refuses a preview demo.
- **Recording day, 07:00:** the kit is built and its prep sheet opens: speaking
  outline (keywords), slides, the demo and its capture status, the picture,
  points to verify, final flow.
- **Takes:** `factory take` records voice only while the slides run. After each
  take a dialog offers the next take, listening back, or publishing. Three takes
  maximum.
- **Publish:** the final video (intro card with music, hook, demo, picture,
  takeaway, outro card with soft music) plus thumbnail and description with
  chapters and references. Default `studio` mode: the user uploads in YouTube Studio and
  pastes the link (`factory published --url`). API uploads from unaudited
  Google Cloud projects are locked private, so `api` mode is only for audited
  projects.
- Reminders at `factory.reminder_times` and a "not published yet" calendar event
  at 21:00 run only until the day is published.

When helping by hand, read today's prep sheet (`fde-coach factory status` shows
its path) and coach from it: short sentences, explain jargon right away, one
takeaway. Verify technical claims against the cited Gas City files before the
user records.

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
  `scheduler` (launchd), `state`, `config`, plus the pronunciation practice:
  `pronounce` (words + paragraph), `pronounce_deck` (deck + slide PNGs),
  `pronounce_session` (record/upload flows), `audio` (ffmpeg clean-up)
- `scripts/tests/` — `~/FDE-Impromptu/venv/bin/python -m unittest discover -s scripts/tests` (dry-run, safe anywhere; needs the venv because the CLI imports `pptx`)
- `references/question_design.md` — question rubric and JSON schema
- `references/pronunciation_design.md` — pronunciation paragraph rubric and JSON schema
- `references/pronunciation_plan.md` — pronunciation practice design plan
- `references/troubleshooting.md` — symptoms → fixes
- `references/factory_video_plan.md` — Software Factory video series design
- `references/factory_curriculum.md` — how to write more days of the learning path
- `references/factory_learning_path.md` — the 35-day path (generated)
- `assets/factory_curriculum.json`, `assets/factory_diagrams/` — the path and the Gas City diagrams (MIT)
- `scripts/fdecoach/factory*.py` — `factory` (curriculum, planning, briefs), `factory_demo` (demo cities, capture), `factory_deck` (slides, terminal animation, take deck, thumbnail), `factory_session` (kit, takes, video, publish, reminders, calendar)
- `references/plan.md` — design plan, risks found in validation, and fixes
