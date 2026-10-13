# Changelog

## v4 — FDE Learn: a daily first-principles learning track

**New**

- **`fde-learn` skill** (new folder next to `fde-impromptu-coach/`; `install.sh` links it into
  `~/.claude/skills`). One topic a day, no menus, hints instead of answers, explain-back in your own words,
  two takes for the video, ideas parked in `later.md`.
- **`fde-coach learn`**: `init`, `drop`, `today`, `done`, `status`, `pause`, `resume`, `sync`. State lives in
  your public learning repo (`fde-first-principles/progress.json`, `TODAY.md`, one folder per topic with a
  journal README and the embedded YouTube video). Only the files the coach writes are committed at the drop;
  `done` commits the track folder after a secret and file-size check, then pushes (failed pushes are retried).
- **Schedule**: a 05:50 `com.fdecoach.learn` agent, catch-up by the 15-minute reminder agent, Sundays off.
  The deadline is the next drop; missed topics return at minimum scope (never skipped); partial work ships
  labelled partial.
- **Google Calendar**: a 06:00 event with the whole task, a 21:00 "not shipped yet" event (alerts 18:00 and
  21:00) deleted when you ship, and tomorrow's event created as soon as you ship. Same OAuth as before.
- **Curriculum**: 59 topics in 6 projects (`assets/learning_path.json`), 50 starter notebooks with TODO cells
  and self-checks, the fictional Acme Fibre dataset and small `lab/` helpers (`assets/learn_starters/`).
  Every starter notebook was run end to end with reference solutions against a simulated Ollama.
- 7 new tests (`scripts/tests/test_learn.py`): full drop → ship → miss → partial → rest-day cycle against a
  local git remote, secret scan, push retry, missed-drop catch-up, launchd agent, curriculum integrity.

## v3 — Legato practice and human-written passages

**New**

- **Legato practice** (06:00, own streak, about 5 minutes, audio only): breath & hum,
  a linking drill from the day's passage (*turn it off → tur-ni-toff*), three reads
  (phrase map with `/` breath marks and underlined joins, intoned, spoken clean), and a
  45-second impromptu response to the author. Flow level 1–3 adapts to a
  Choppy / Smooth tap. `fde-coach legato session|status|history|generate|upload`.
- **Passage library**: 56 verbatim paragraphs from 34 public-domain works by 29
  writers (Standard Ebooks / Project Gutenberg), each credited with a link on the
  slides and in the video description. `fde-coach library list|show|import-gutenberg|import-file|remove`.
  `scripts/tools/build_passage_library.py verify` re-checks every passage against its source.
- **Pronunciation uses real passages by default**: chosen to contain your due words,
  with hand-written coach notes; Claude only marks up words without notes and never
  writes text. The AI-written paragraph is still available:
  `config --set pronunciation.paragraph_source=claude`.
- One "Start now" can run all three: FDE → pronunciation → legato.

**Fixed**

- The "Pronunciation practice next?" prompt after the FDE session never appeared.
- `uninstall.sh` left the 05:45 pronunciation agent running.
- `calendar-sync --clear` (and turning alerts off) left pronunciation alerts behind.
- Pending pronunciation uploads were never shown or retried automatically.
- YouTube playlist adds always failed (NameError).
- `pronounce history` revealed today's paragraph before recording; `pronounce status` printed an empty date.
- The warm-up slide's instruction overlapped the timer label.

**Internals**

- `fdecoach/practice.py`: one engine for the audio practices (build, record, video,
  upload, calendar, status); `pronounce_session` keeps its public API.
- 84 tests (26 new), passing on Python 3.9 and 3.13.
