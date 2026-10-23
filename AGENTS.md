# AGENTS.md: FDE Impromptu Coach

Daily practice for a Forward Deployed Engineer on macOS: three speaking practices (impromptu, pronunciation,
legato) and a first-principles learning track (FDE Learn). Two layers:

- **The runtime** is one CLI, `~/FDE-Impromptu/bin/fde-coach` (also `~/.local/bin/fde-coach`), installed by
  `fde-impromptu-coach/install.sh`. launchd runs it every morning; the learner's data lives in `~/FDE-Impromptu/`.
  If the CLI is missing, nothing is installed yet: see *Install* in `fde-impromptu-coach/SKILL.md`.
- **The skills** turn what the learner says into the right `fde-coach` command. Each is linked into
  `~/.claude/skills/<name>/` by `fde-impromptu-coach/link_skills.sh`, so they work in every Claude Code session,
  not only in this repo.

## Skills and slash commands

| Skill | Slash command | For | First command |
|---|---|---|---|
| `impromptu` | `/impromptu [start\|status\|answers\|headlines\|harder\|easier\|brief <topic>\|history]` | 5 surprise on-camera questions (exec slots), then the exec answer key | `fde-coach session --detach` |
| `pronunciation` | `/pronunciation [start\|status\|history\|words\|add <word>\|passage <id>]` | Pen method on hard words and a public-domain passage | `fde-coach pronounce session --detach` |
| `legato` | `/legato [start\|status\|history\|passage <id>\|themes <theme>]` | Smooth, connected speech, then a 45-second impromptu response | `fde-coach legato session --detach` |
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
| "read Walden today" | `legato` or `pronunciation` | `fde-coach library list`, then `fde-coach legato generate --replace --passage <id>` |
| "what's my streak?" (no practice named) | each practice | `fde-coach status`, `fde-coach pronounce status`, `fde-coach legato status`, `fde-coach learn status` |
| "today's topic", "FDE learn", "what do I do today?" | `fde-learn` | `fde-coach learn today --json` |
| "I'm stuck", "hint" | `fde-learn` | next rung of the hint ladder in `fde-learn/references/coaching.md` |
| "ship it" | `fde-learn` | check, explain-back, then `fde-coach learn done --video <link>` |
| "add a book" | `fde-impromptu-coach` | `fde-coach library import-gutenberg <ebook number>` |
| "remind me at 6:15" | `fde-impromptu-coach` | `fde-coach config --set daily_time=06:15` |
| "something's broken", "/legato does nothing" | `fde-impromptu-coach` | `fde-coach doctor` (the *Claude Code skills* line), then `bash <clone>/fde-impromptu-coach/link_skills.sh` |

When the learner names no practice ("let's practise"), start impromptu: it is first in the morning chain
(impromptu 05:30 → pronunciation 05:45 → legato 06:00) and offers the other two when it ends. Each skill's
`SKILL.md` has its full table; follow it.

## Ground rules (every skill, every time)

1. **Keep the surprise and the cold read.** Today's questions and passages stay hidden until today is recorded:
   no `--reveal`, no opening the deck or the JSON, unless the learner explicitly asks.
2. **Model answers come after the attempt.** `fde-coach answers` refuses before recording; never pass
   `--reveal` and never write model answers into the chat for an unrecorded day unless asked.
3. **Never write or rewrite reading passages.** Pronunciation and legato text comes only from the passage
   library (verbatim public-domain books). Claude writes coach notes for hard words, nothing else.
4. **Long commands run detached.** Sessions take about 5 minutes: always `--detach`, then check the status.
5. **The streak comes first.** If automation fails, help them practise another way, then
   `fde-coach complete --video <path>` (or `--no-video`).
6. **Videos stay private.** Never change `youtube.privacy_status` unless asked.
7. **FDE Learn: one task, no menus; hints, not answers; their words, lightly corrected.** Never reorder or skip
   topics, never write a TODO cell or an article paragraph for them (details in `fde-learn/SKILL.md`).
8. **Public repo safety.** No API keys, employer code or real customer data in the learning repo.

## Repo layout

```
AGENTS.md, CLAUDE.md            this file; CLAUDE.md imports it
skills/impromptu|pronunciation|legato/SKILL.md   one-practice entry points (thin routers to the CLI)
fde-impromptu-coach/            umbrella skill + the runtime
  SKILL.md                      full intent table, daily flow, install
  install.sh, uninstall.sh      install (venv, launchd, permissions, skill links) / remove
  link_skills.sh                links all five skills into ~/.claude/skills (--check, --remove)
  scripts/fde_coach.py          the CLI (build_parser() lists every command)
  scripts/fdecoach/             modules (app, questions, deck, answers, pronounce*, legato*, library, learn, ...)
  scripts/tests/                unittest suite + features/*.feature (BDD scenarios)
  scripts/tools/                build_curriculum.py, build_passage_library.py
  assets/                       question bank, passages, learning path, learn starters
  references/                   rubrics and design notes the skills load on demand
fde-learn/                      the learning-track skill (SKILL.md, references/curriculum.md, coaching.md)
```

## Working on this repo

- **Tests.** From `fde-impromptu-coach/`: `python3 -m unittest discover -s scripts/tests` (on the Mac,
  `~/FDE-Impromptu/venv/bin/python`). Everything runs dry (`FDE_COACH_DRYRUN=1` in an isolated home), so it is
  safe anywhere; the two ffmpeg video-length tests need macOS fonts.
- **BDD first.** A behaviour change starts as a scenario in `scripts/tests/features/*.feature`, with exactly one
  Given / When / Then test named after it; the sync test fails when the two drift apart.
- **Skills.** Frontmatter must parse as YAML: a colon followed by a space inside an unquoted `description`
  breaks it, and Claude Code then loads the skill with no description, so it never triggers. Keep each
  description under 1024 characters with the practice's name in the first sentence, and every `fde-coach`
  command a skill names must parse (`test_skill_routing.py` checks all of this).
- **Adding a skill.** Create `skills/<name>/SKILL.md`, then add it to `SKILLS` in `link_skills.sh`,
  `CLAUDE_SKILLS` in `scripts/fdecoach/config.py` and the tables above. The tests fail until all four agree.
- **Curriculum.** Edit `assets/learning_path.json`, then `python3 scripts/tools/build_curriculum.py`.
- **Passages.** Never hand-edit passage text; change `assets/passage_sources.json` and run
  `python3 scripts/tools/build_passage_library.py build` (`verify` re-checks every passage against its source).
- **Shipping.** Python stays 3.9-compatible and shell scripts bash 3.2-compatible (macOS defaults). Add a
  `CHANGELOG.md` entry. launchd runs the copy in `~/FDE-Impromptu/src`, so re-run `install.sh` on the Mac after
  changing runtime code.
