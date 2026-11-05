# AGENTS.md: FDE Impromptu Coach

Daily practice for a Forward Deployed Engineer on macOS: three daily speaking practices (impromptu,
pronunciation, legato), a weekend one (Weekend Stage: a famous TED talk, three takes on camera) and a
first-principles learning track (FDE Learn). Two layers:

- **The runtime** is one CLI, `~/FDE-Impromptu/bin/fde-coach` (also `~/.local/bin/fde-coach`), installed by
  `fde-impromptu-coach/install.sh`. launchd runs it every morning (and on weekend mornings for Weekend Stage);
  the learner's data lives in `~/FDE-Impromptu/`.
  If the CLI is missing, nothing is installed yet: see *Install* in `fde-impromptu-coach/SKILL.md`.
- **The skills** turn what the learner says into the right `fde-coach` command. Each is linked into
  `~/.claude/skills/<name>/` by `fde-impromptu-coach/link_skills.sh`, so they work in every Claude Code session,
  not only in this repo.

Helping the learner practise? The next three sections are for you. Changing the code? Start at
[Where to find X](#where-to-find-x), [Runtime prompts](#runtime-prompts-treat-them-as-code) and
[Working on this repo](#working-on-this-repo).

## Skills and slash commands

| Skill | Slash command | For | First command |
|---|---|---|---|
| `impromptu` | `/impromptu [start\|status\|answers\|headlines\|harder\|easier\|brief <topic>\|history]` | 5 surprise on-camera questions (exec slots), then the exec answer key | `fde-coach session --detach` |
| `pronunciation` | `/pronunciation [start\|status\|history\|words\|add <word>\|passage <id>]` | Pen method on hard words and a public-domain passage | `fde-coach pronounce session --detach` |
| `legato` | `/legato [start\|status\|history\|passage <id>\|themes <theme>]` | Smooth, connected speech, then a 45-second impromptu response | `fde-coach legato session --detach` |
| `stage` | `/stage [start\|prep\|status\|history\|segment <M:SS> <M:SS>\|talks\|upload]` | Weekend Stage: one TED talk a weekend, studied, then three takes on camera | `fde-coach stage session --detach` |
| `fde-learn` | `/fde-learn [today\|hint\|check\|ship <link>\|next\|status]` | The 66-topic learning track, shipped in public | `fde-coach learn today --json` |
| `fde-impromptu-coach` | `/fde-impromptu-coach` | Install, settings, Google, the passage library, troubleshooting, anything else | `fde-coach doctor` |

A slash command with no arguments means *start* (for `fde-learn`: *today's topic*).

## What the learner says → skill → command

Match on meaning, not spelling: the learner often types "lagato", "pronounciation", "impromptue", "impromtu".

| The learner says | Skill | Run |
|---|---|---|
| "start my practice", "record today", "impromptu", "do all three" | `impromptu` | `fde-coach session --detach` (finishing it offers pronunciation, then legato) |
| "how should I have answered?", "model answers", "impromptu response practice", "exec answer key" | `impromptu` | `fde-coach answers --open` (only after today is recorded) |
| "say it back", "my one-breath lines" | `impromptu` | `fde-coach answers --index --open` |
| "too easy" / "too hard" | `impromptu` | `fde-coach level --up` / `fde-coach level --down`, then `fde-coach generate --replace` if not recorded |
| "make today about healthcare / a CISO" | `impromptu` | `fde-coach generate --replace --brief "healthcare, CISO audience"` |
| "pronunciation", "pen method", "clearer speech" | `pronunciation` | `fde-coach pronounce session --detach` |
| "add the hard word *entrepreneur*" | `pronunciation` | `fde-coach pronounce words --add entrepreneur` |
| "legato", "connected speech", "linking", "less choppy", "smoother" | `legato` | `fde-coach legato session --detach` |
| "TED talk practice", "this weekend's talk", "weekend practice", "shadow a speaker" | `stage` | `fde-coach stage prep` (study first), then `fde-coach stage session --detach` |
| "the segment starts at 2:05 and ends at 5:10" | `stage` | `fde-coach stage segment --start 2:05 --end 5:10` |
| "read Walden today" | `legato` or `pronunciation` | `fde-coach library list`, then `fde-coach legato generate --replace --passage <id>` |
| "what's my streak?" (no practice named) | `fde-impromptu-coach` | `fde-coach status`: every practice's streak in one view (each practice also has its own `status`) |
| "today's topic", "FDE learn", "what do I do today?" | `fde-learn` | `fde-coach learn today --json` |
| "I'm stuck", "hint" | `fde-learn` | next rung of the hint ladder in `fde-learn/references/coaching.md` |
| "ship it" | `fde-learn` | check, explain-back, then `fde-coach learn done --video <link>` |
| "add a book" | `fde-impromptu-coach` | `fde-coach library import-gutenberg <ebook number>` |
| "remind me at 6:15" | `fde-impromptu-coach` | `fde-coach config --set daily_time=06:15` |
| "something's broken", "/legato does nothing" | `fde-impromptu-coach` | `fde-coach doctor` (the *Claude Code skills* line), then `bash <clone>/fde-impromptu-coach/link_skills.sh` |

When the learner names no practice ("let's practise"), start impromptu: it is first in the morning chain
(impromptu 05:30 → pronunciation 05:45 → legato 06:00) and offers the other two when it ends. Weekend Stage is
separate: Saturday 08:00, with Sunday 08:00 as the catch-up. Each skill's `SKILL.md` has its full table; follow it.

## Ground rules (every skill, every time)

1. **Keep the surprise and the cold read.** Today's questions and passages stay hidden until today is recorded:
   no `--reveal`, no opening the deck or the JSON, unless the learner explicitly asks.
2. **Model answers come after the attempt.** `fde-coach answers` refuses before recording; never pass
   `--reveal` and never write model answers into the chat for an unrecorded day unless asked.
3. **Never write or rewrite reading passages.** Pronunciation and legato text comes only from the passage
   library (verbatim public-domain books). Claude writes coach notes for hard words, nothing else.
4. **Long commands run detached.** A session takes 5 to 10 minutes: always `--detach`, then check the status.
5. **The streak comes first.** If automation fails, help them practise another way, then
   `fde-coach complete --video <path>` (or `--no-video`).
6. **Videos stay private.** Never change `youtube.privacy_status` unless asked.
7. **FDE Learn: one task, no menus; hints, not answers; their words, lightly corrected.** Never reorder or skip
   topics, never write a TODO cell or an article paragraph for them (details in `fde-learn/SKILL.md`).
8. **Public repo safety.** No API keys, employer code or real customer data in the learning repo.
9. **Stage talks are links, not text.** TED talks are CC BY-NC-ND 4.0. Never download TED video or audio,
   commit or display a transcript, or put TED's words, audio or video into a deck, a note or an upload.
   `assets/talks.json` holds links, segment times and delivery notes in our own words; Take C's twist stays
   hidden until the weekend is recorded.

## Where to find X

Paths are inside `fde-impromptu-coach/` unless they start with `skills/` or `fde-learn/`, or name a file at the
repo root. `test_agent_navigation.py` fails if a file named here disappears.

| To find | Look in |
|---|---|
| A CLI command and its flags | `scripts/fde_coach.py`: `build_parser()`, then the command's `cmd_*` function |
| The impromptu flow: plan, deck, session, upload, status | `scripts/fdecoach/app.py`, with `questions.py`, `deck.py` and `recorder.py`; the exec answer key is `answers.py` |
| The engine pronunciation, legato and Weekend Stage share | `scripts/fdecoach/practice.py`: the `Practice` spec, and `_MODULES`, which registers each practice |
| One practice's code | `pronounce.py`, `pronounce_deck.py`, `pronounce_session.py`; `legato.py`, `legato_deck.py`, `legato_session.py`; `stage.py`, `stage_deck.py`, `stage_prep.py`, `stage_session.py` (each `*_session.py` holds its `SPEC`) |
| FDE Learn | `scripts/fdecoach/learn.py` and `learn_video.py`; the skill and curriculum are in `fde-learn/` |
| The passage library | `scripts/fdecoach/library.py` and `assets/passages.json`, built by `scripts/tools/build_passage_library.py` |
| Sessions, streaks, locks | `scripts/fdecoach/state.py` (lock order: session → generate → history) |
| Defaults, data paths, the skill list | `scripts/fdecoach/config.py`: `DEFAULTS`, `Paths`, `CLAUDE_SKILLS` |
| The launchd schedule | `scripts/fdecoach/scheduler.py`: `ALL_LABELS`, `build_plists()` |
| macOS, Google Calendar, YouTube, ffmpeg | `scripts/fdecoach/macos.py`, `gcal.py`, `youtube.py`, `audio.py` |
| Content | `assets/question_bank.json`, `assets/passages.json`, `assets/talks.json` (it holds every Take C twist: never open it while helping the learner), `assets/learning_path.json`, `assets/pronunciation_bank.json` |
| The test harness | `scripts/tests/test_coach.py` (`Home`: a dry-run home per test) and `scripts/tests/fake_claude.py` (stands in for `claude`) |
| BDD scenarios | `scripts/tests/features/`, one test per scenario in the matching `test_*.py` |
| Dry-run switches (`FDE_COACH_*`) | the table at the end of `references/troubleshooting.md`; `scripts/tools/sandbox.sh` sets them for you |
| Why something was built that way | `references/plan.md`, `references/pronunciation_plan.md`, `references/legato_design.md`, `references/stage_design.md`, `CHANGELOG.md` |
| The learner's manual and fixes | `README.md` in `fde-impromptu-coach/`, and `references/troubleshooting.md` |
| The learner's data, and the copy launchd runs | `~/FDE-Impromptu/` (state, logs, decks) and `~/FDE-Impromptu/src/` (refreshed by `install.sh`); videos in `~/Movies/FDE-Impromptu/` |

## Runtime prompts (treat them as code)

The code reads these files and sends them to Claude, so editing one changes what Claude writes for the learner.
The tests answer with `fake_claude.py`, so they can't judge a prompt edit: say so in the PR. Everything else in
`references/` is a design note or a learner page, and is never sent to Claude.

| File | Sent by | For |
|---|---|---|
| `references/question_design.md` | `scripts/fdecoach/questions.py` | the five daily questions, their listeners and exec slots |
| `references/answer_design.md` | `scripts/fdecoach/answers.py` | the exec answer key, after recording |
| `references/pronunciation_annotation.md` | `scripts/fdecoach/pronounce.py` | coach notes for hard words (library mode, the default) |
| `references/pronunciation_design.md` | `scripts/fdecoach/pronounce.py` | the legacy AI-written paragraph (`pronunciation.paragraph_source=claude`) |

## Working on this repo

- **Run the tests once, then read the log.** From the repo root, `make test` runs the whole suite dry, prints the
  failing tests and the summary, and keeps the full output with tracebacks in `.test-output.log`: read that
  instead of running the suite again. One module: `make test-one T=stage`. Python 3.9: `make py39` (needs uv).
  On a fresh machine, install `fde-impromptu-coach/requirements.txt` first (the Mac's venv already has it).
  Without make, from `fde-impromptu-coach/`: `FDE_COACH_DRYRUN=1 python3 -m unittest discover -s scripts/tests`
  (on the Mac, `~/FDE-Impromptu/venv/bin/python`). Always go through `discover`: the test modules import
  `test_coach` as a top-level module, so `python3 -m unittest scripts/tests/test_stage.py` fails.
- **A clean run is `OK` with a few skips.** The two ffmpeg video-length tests skip without macOS's Apple Symbols
  font (`pronounce_deck.SYMBOL_FONT`), and the clone-only tests skip in the copy `install.sh` deploys. Any
  failure or error is new: don't write it off as a known one.
- **Try a command without touching the Mac.** `make sandbox ARGS='stage status --json' NOW=2026-11-07T08:00:00`
  runs one `fde-coach` command in a throw-away dry-run home (`scripts/tools/sandbox.sh`): no launchd, QuickTime,
  Google or YouTube, and Claude is `fake_claude.py`. `ANSWERS='Start now,Later'` answers its dialogs in order.
- **BDD first.** A behaviour change starts as a scenario in `scripts/tests/features/*.feature`, with exactly one
  Given / When / Then test named after it; the sync test fails when the two drift apart.
- **Skills.** Frontmatter must parse as YAML: a colon followed by a space inside an unquoted `description`
  breaks it, and Claude Code then loads the skill with no description, so it never triggers. Keep each
  description under 1024 characters with the practice's name in the first sentence, and every `fde-coach`
  command a skill names must parse (`test_skill_routing.py` checks all of this). The umbrella skill's description
  is close to that limit: put a new practice's trigger words in its own skill.
- **Adding a skill.** Create `skills/<name>/SKILL.md`, then add it to `SKILLS` in `link_skills.sh`,
  `CLAUDE_SKILLS` in `scripts/fdecoach/config.py`, the skills table above, and `FOLDERS` and `LEADS` in
  `scripts/tests/test_skill_routing.py` (a practice goes in `PRACTICES` there, which feeds `FOLDERS`). The tests
  fail until they all agree.
- **Adding a practice.** Weekend Stage needed every one of these; a new practice will too:
  1. Code: `<name>.py` (content), `<name>_deck.py` and `<name>_session.py` (its `SPEC = practice.Practice(...)`
     and public functions), registered in `_MODULES` in `practice.py`.
  2. Settings and data: a `DEFAULTS` section and a `Paths` state file in `config.py`. Uploads read
     `youtube.<key>_playlist_id`.
  3. Schedule: a label constant, `ALL_LABELS` and a plist in `build_plists()` (`scheduler.py`), and the label in
     `uninstall.sh`'s removal loop (the docs test checks that one).
  4. CLI: `cmd_<name>` and its subparser in `fde_coach.py`, a line in `cmd_status`, an entry in `app.status()`,
     the slash command in `cmd_doctor`'s skills line, and checks in `cmd_config` for any time or day keys.
  5. Skill: everything under *Adding a skill*, plus `START` and `HIDDEN_RULE` in `test_skill_routing.py`, and
     the practice's name in the "… have their own skills" sentence of every other practice skill's description.
  6. Tests and evals: `features/<name>.feature` with `test_<name>.py`, one test per scenario; evals for the
     skill's rules in `evals/evals.json`.
  7. Docs: the umbrella `SKILL.md` (its routing rows and the *One skill per practice* paragraph), both READMEs,
     a row in `references/troubleshooting.md`, `references/<name>_design.md` and `CHANGELOG.md`.
- **Curriculum.** Edit `assets/learning_path.json`, then `python3 scripts/tools/build_curriculum.py`.
- **Talks.** `assets/talks.json` is the Weekend Stage curriculum: links, segment labels and times, delivery
  notes (60 words at most per talk), Take B prompts and Take C twists. `stage.validate_catalogue()` refuses a
  transcript field; `test_stage.py` runs it.
- **Passages.** Never hand-edit passage text; change `assets/passage_sources.json` and run
  `python3 scripts/tools/build_passage_library.py build` (`verify` re-checks every passage against its source).
- **Docs.** Don't write how many skills or launchd agents there are ("every skill", "all the agents"): the count
  goes stale with the next practice. Sizes of the question bank, passage library and learning path may be
  stated; `test_agent_navigation.py` checks them against the data. `architecture.png` is a picture of
  `architecture.drawio`: change both together (in diagrams.net, File → Export as → PNG at 200%).
  `CHANGELOG.md` and the design notes record the past, so their old numbers stay.
- **Shipping.** Python stays 3.9-compatible and shell scripts bash 3.2-compatible (macOS defaults). Add a
  `CHANGELOG.md` entry. launchd runs the copy in `~/FDE-Impromptu/src`, so re-run `install.sh` on the Mac after
  changing runtime code. Keep the `Claude-Session:` trailer on agent commits: it is how past sessions are found.
  In Claude's cloud sandbox `gh pr create` fails (GitHub's GraphQL API is blocked there); open the PR with
  `gh api repos/rajchampaneriya/fde-impromptu-coach/pulls -f title=… -f head=<branch> -f base=main -F body=@pr.md`.
