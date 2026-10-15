# Changelog

## v6 — Learning repo: tracking files move into .learn/

**Changed**

- The coach's tracking files (`TODAY.md`, `progress.json`, `later.md`) now live in `.learn/` inside the track
  folder instead of at its root, so the public repo shows only content: the README with its progress table, the
  topic folders, `data/` and the notebook scaffolding. The coach migrates the old root-level files into `.learn/`
  automatically on first touch after the upgrade; links inside `TODAY.md` now point one level up (`../`) to the
  topic folders. Nothing else changes: the files stay committed and pushed as the track's public memory.

## v5 — FDE Learn: articles as finish lines, a realistic pace, a stronger-model check

**New**

- **An article ends every project.** Six new topics, one at the end of each project: about 300 words written
  from memory first (no notes, no AI: the test of understanding), then 800 to 1,500 words with your real numbers,
  published on rajc.work from a Hugo-ready `article.md` starter. Ship with `fde-coach learn done --article <link>`;
  the link must be live on your site (`learn.article_site`, default `rajc.work`), and an article cannot ship
  partial. Each article topic teaches one Technical Writing One lesson.
- **Realistic pace.** Every topic now carries a time estimate calculated from its content (resource minutes × 1.5,
  minutes per build step by artifact, set-up, new maths, explaining) and gets the mornings it needs: one to three.
  80 minutes a morning, 6 mornings a week = 8 hours a week. The track is about 128 hours: 16 to 21 weeks, plan on
  4 to 5 months. A topic stays open across its mornings (TODAY.md shows "morning 2 of 2"), the evening nudge comes
  only on its last morning, a missed topic returns with half the mornings, and streaks count every morning of a
  shipped topic.
- **`fde-coach learn next`**: finished early? Drop the next topic now. The 15-minute tick never does this on its own.
- **Professional YouTube details for every topic video.** When you ship with `--video`, the coach writes the topic's
  `video/` folder and sets on your video: the title ("Day 7 · Why 30 test cases can lie: error bars | FDE First
  Principles"), a description built from what the video says (your three "In my words" answers, what surprised
  you, the maths, the free resources, your GitHub folder, the previous video, the open-source coach repo and
  rajc.work) and a 1280×720 thumbnail in the impromptu title card's minimalist blue look (topic title, project,
  streak card, track progress bar). Only the snippet and thumbnail change, never the privacy; offline or
  disconnected updates are retried by the tick and `learn sync`. `fde-coach learn video` prepares them before you
  upload, or refreshes a shipped video. The topic README shows the same card. Optional
  `youtube.learn_playlist_id`; `learn.youtube_update=false` turns it off.
- The article starters link the coach's repository under "Explore the project".
- **Final run with a stronger model** (project 6, step 7): the same test set on a bigger local model (free) or a
  paid model behind any OpenAI-compatible API. Cap first, a cost estimate before the run, a free dry run against
  your own Ollama, cached answers, a call limit against runaway loops, and paired differences to decide whether the
  stronger model is really better. `lab/llm.py` gains `use()`, the API path (`.env`: `LLM_BASE_URL`,
  `LLM_API_KEY`) and `api_usage()`. The final ADR template has rows for both models.
- **A bigger test set.** Day 3 asks for 50+ reviewed cases (minimum 30): 10 hard ones by hand, 40 drafted by your
  local model and reviewed by hand (`"reviewed": false` until you do). Day 7 shows the ± range for 30, 50, 100 and
  your own set.
- **`scripts/tools/build_curriculum.py`** recalculates every estimate and renders `fde-learn/references/
  curriculum.md` (pace, method, rules, per-project hours); the tests fail if either file is out of date.

**Changed**

- Day 1 is now "One model call: tokens, time and randomness" (same folder, same work).
- 66 topics (59 + 6 articles + the final run); project 6's later topics moved one step (starter `p6-07` →
  `p6-08`). Notebook titles follow the new day numbers.
- Own-data reruns (your communication agent, your notes) are suggested as private parking items, never in the
  public repo.
- 8 new learn tests (multi-morning drops, the article finish line, `learn next`, streaks, article checks, video
  details before and after shipping, the YouTube switch, the description) and a stricter curriculum check.

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
