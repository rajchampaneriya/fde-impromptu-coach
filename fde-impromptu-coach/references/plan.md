# FDE Impromptu Coach — Design Plan

## 1. Goal

A daily, controlled practice routine that builds impromptu communication and
leadership skills for a Forward Deployed Engineer (FDE) role. Every morning the
learner gets five never-seen-before questions (one per slide, 60 seconds each),
records a ~5-minute video with macOS's built-in QuickTime Player, and the video
is uploaded to YouTube as a private video. The streak is protected with
escalating reminders.

## 2. Plan v1 (as requested)

1. Claude Code skill generates a .pptx: minimalist blue theme, Calibri font.
2. 5 impromptu questions, one per slide, 1-minute timer, auto-advance.
3. History file tracks past questions so every day is new and harder.
4. macOS schedule runs the skill daily at 05:30.
5. Deck opens automatically when ready.
6. User records with the default recording app; video uploaded privately to YouTube.
7. If the recording is missed, remind the user.
8. Deliver as a zip usable with Claude Code on macOS.

## 3. Validation of v1 — risks found and fixes

| # | Risk in v1 | Why it matters | Fix in v2 |
|---|-----------|----------------|-----------|
| 1 | A "timer" in PowerPoint needs animation XML; auto-advance and the timer can drift apart | Timer must match the slide change exactly | Timer is a 60-second linear wipe of a progress bar; the slide's auto-advance is also 60 s. PowerPoint waits for automatic animations, so both end together |
| 2 | Google Slides ignores per-slide auto-advance timings | User wants Google Slides compatibility | Only plain shapes/text/notes are used (import cleanly). Documented: in Google Slides use Slideshow ▸ Auto-play ▸ every minute |
| 3 | Screen recording (⌘⇧5) cannot be started reliably by script and captures no face | Body language is half of communication; automation is a goal | QuickTime **New Movie Recording** (camera + mic) is scriptable. Questions + YouTube chapters go into the video description, so the video stays self-explanatory |
| 4 | A 05:30 run when the Mac is asleep/lid closed | Job silently skipped | launchd runs missed calendar jobs on wake; a 15-minute "reminder" agent also self-heals (generates the deck if missing). Optional `pmset` wake schedule |
| 5 | Claude Code headless call can fail (offline right after wake, expired login, usage limits) | Streak would break for a tooling reason | Claude generates questions first; a curated 132-question FDE bank + constraint twists is the automatic fallback. Deck is always produced |
| 6 | Unattended macOS privacy prompts (camera, microphone, automation) block a 05:30 job | Hangs with nobody there | Installer runs a permission warm-up through launchd while the user is present |
| 7 | YouTube OAuth app in "Testing" mode — refresh token dies after 7 days | Uploads silently stop weekly | Setup guide publishes the OAuth app to "In production"; auth errors trigger a clear re-auth notification; failed uploads are queued and retried |
| 8 | Unverified YouTube API projects can only upload private videos | Could look like a limitation | It is exactly the requirement (private); no audit needed |
| 9 | Writing to ~/Documents or ~/Desktop from launchd triggers privacy blocks; QuickTime is sandboxed | Saves fail | Data in `~/FDE-Impromptu`, videos in `~/Movies/FDE-Impromptu` (QuickTime can write to Movies) |
| 10 | "Harder every day" needs a definition | Otherwise questions plateau | Levels 1–5 rise every N completed sessions; each day ramps (L, L, L+1, L+1, L+2); constraint twists from level 3; framework hints fade after level 2; one-tap "too easy / too hard" calibration |
| 11 | Missed recording only noticed at night | Streak lost | Escalating dialogs at configurable times + notification sound + Apple Reminders item that syncs to iPhone; snooze; "last call" wording |
| 12 | QuickTime AppleScript save is known to be fragile across macOS versions | Recording could be lost | Try save → export 1080p → export 720p; verify file size/duration; if all fail, guide user to ⌘S and watch the folder to finish automatically |
| 13 | Two processes (reminder + manual start) could start two sessions | Double recording | File locks for generation, prompts and sessions |

## 4. Plan v2 (implemented)

### Components
- `SKILL.md` — how Claude Code uses the skill (generate, author fresh questions, start sessions, status, setup, troubleshoot).
- `scripts/fde_coach.py` — CLI entry point (Python 3.9+ compatible, macOS system Python works).
- `scripts/fdecoach/` — modules: `config`, `state` (history, streak, locks), `questions` (bank, novelty, Claude generation), `deck` (python-pptx + animation XML), `macos` (osascript: notify, dialog, PowerPoint, QuickTime, Reminders), `recorder` (session flow), `youtube` (OAuth + resumable private upload), `scheduler` (launchd agents).
- `assets/question_bank.json` — 12 FDE competencies × 11 questions, difficulty 1–5, plus constraint twists.
- `references/question_design.md` — rubric used by Claude (interactive and headless).
- `install.sh` / `uninstall.sh` — venv, dependencies, data folders, launchd agents, warm-up.

### Daily flow
1. **05:30** launchd → `fde-coach daily`: build today's 5 questions (Claude → bank fallback), novelty-check against history, build `.pptx` (+ `.ppsx` play copy), open in PowerPoint, notify, add iPhone-synced reminder, ask "Start now?".
2. **Start** (dialog button, `Start Practice.command`, or asking Claude): QuickTime movie recording starts → slideshow starts → 10 s intro + 5 × 60 s → recording stops and saves automatically → streak updated → private YouTube upload with chapters and questions in the description → notification with link.
3. **Every 15 min** launchd → `fde-coach remind`: catch-up generation, escalating reminders until recorded, upload retries.

### Deck spec
16:9, white background, navy text, blue accent, Calibri throughout. Slides: intro (day, date, level, streak, 10 s countdown bar) → 5 question slides (label, competency, difficulty dots, question, optional constraint, fading hint, 60 s progress bar with 0:15/0:30/0:45 ticks, "Wrap up" cue at 0:45, coaching notes in speaker notes) → closing slide with the day's questions for review.

### Validation plan
- Skill: `quick_validate.py` (frontmatter, naming), SKILL.md walkthrough of each workflow.
- Python: compile on Python 3.9 target, pyflakes, unit tests (novelty, streak, level, slot planning, Claude-output parsing, bank fallback), end-to-end dry-run of `daily`, `session`, `remind` with a fake `claude` binary.
- Deck: OOXML schema validation, render to images and inspect, check timing XML (60 s wipe, 45 s cue, 60 s advance).
- launchd plists: generated with `plistlib` and re-parsed; shell scripts: `bash -n` + shellcheck.

## 5. Refinements made while implementing (v2.1)

| Found during build | Change |
|---|---|
| Opening the deck at 05:30 shows every question in PowerPoint's thumbnail pane, spoiling the surprise | Deck opens in Normal view with the thumbnail pane collapsed (`viewProps.xml`); `status`, `generate` and `history` hide today's questions until recorded |
| A session (~5.5 min) is longer than a Claude Code tool call should block | `fde-coach session --detach`; uploads always run in a detached process |
| Claude-authored questions shown in a Claude Code chat are spoilers too | Default path stays headless (`generate --brief …` steers topic without revealing); hand-authoring only on request |
| Learner wants personal relevance | `learner_context` setting and per-day `--brief` feed into the generation prompt |
| Recording done outside the automation (phone, manual QuickTime) should still count | `fde-coach complete --video PATH` / `--no-video` |
| Reminder bursts after the Mac wakes (several missed times at once) | Only one prompt per tick; all due times marked fired; no re-prompt within 30 minutes of the last one |
| Learner has no iPhone, so Apple Reminders sync does not reach them away from the Mac | Google Calendar "missed practice" events (calendar.events scope, same OAuth client): one per unrecorded day for today + 2 days, 5 alerts (4 popup, 1 email); recording deletes the day's event, so alerts only fire on missed days and still arrive when the Mac is off |
| Tests on the user's Mac must never call the real Claude CLI, launchctl, camera or YouTube | `FDE_COACH_DRYRUN`, `FDE_COACH_NO_CLAUDE_DISCOVERY`, `FDE_COACH_AGENTS_DIR`, isolated data folder |

## 6. Validation results

- `quick_validate.py`: skill valid (name, description ≤ 1024 chars, allowed keys).
- Python: `py_compile`, `pyflakes` clean; `vermin` minimum version 3.7 (target 3.9 OK).
- Unit + end-to-end suite (`scripts/tests`, 32 tests, also run on Python 3.9): novelty, bank integrity, streak and level
  maths, 24-day no-repeat run, Claude output parsing, Claude failure modes (error, garbage,
  duplicates, partial, fenced) falling back to the bank, full daily → record → upload flow,
  reminder escalation / snooze / last call / quiet hours, missed-05:30 catch-up, replace
  rules, hand-authored build, manual completion, launchd plist contents, YouTube metadata,
  the real `googleapiclient` upload request (private, resumable, retry on 503) offline, and
  Google Calendar alerts (create/delete lifecycle, roll-forward, clear/disable, real
  insert/409-restore/delete requests offline).
- Deck: OOXML schema validation passed; rendered and inspected; timing XML checked
  (10 s intro, 60 s wipe + 60 s auto-advance, 45 s cue, Use Timings on); Calibri only.
- Shell scripts: `bash -n` and `shellcheck` clean.
- Not verifiable off-Mac: the AppleScript calls into QuickTime, PowerPoint and Reminders,
  launchd loading, and TCC prompts. They are isolated in `macos.py`/`scheduler.py`, every
  call degrades to a guided manual path, and `fde-coach doctor --warmup` checks them on the Mac.
