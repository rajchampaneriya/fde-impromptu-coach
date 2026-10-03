# Writing Days for the Software Factory Learning Path

The path lives in `assets/factory_curriculum.json`. Use this rubric when the
user asks to plan the next module, add a day, or rework a topic. The test suite
(`TestCurriculum`) enforces the mechanical rules.

## Principles

1. **One video, one concept, one takeaway.** If a day needs "and" in its
   concept, split it.
2. **Progressive.** Each day builds on earlier ones (`builds_on`). Introduce a
   term before using it. Repeat a concept only to go one level deeper (the
   weekly demo days do this on purpose).
3. **Grounded.** Every claim comes from the Gas City repository
   (https://github.com/gastownhall/gascity). Read the files before writing;
   cite them in `references` (paths relative to the repository root) and list
   the exact claims to re-check in `verify`. Never invent commands or flags:
   check `docs/reference/cli.md`.
4. **Plain words.** Write for a software engineer who has never used Gas City.
   Short sentences. Any jargon goes in `jargon` with a plain definition, so the
   speaker explains it the moment they say it.
5. **Picture over words.** The HOW slide is one visual. Prefer an existing
   diagram from `docs/diagrams/excalidraw-rendered/`; otherwise choose the
   simplest generated visual that shows the mechanism.
6. **Keywords, not a script.** Slide points are cues for an impromptu
   explanation, not sentences to read.

## Fields

| Field | Rule |
|---|---|
| `day` | 1, 2, 3 … with no gaps |
| `module` | an id from `modules` (add a module with `id`, `title`, `goal`) |
| `id` | unique kebab-case topic id (also the override file name) |
| `title` | ≤ 60 characters; the video title |
| `concept` | ≤ 40 characters; the WHAT headline |
| `what`, `why`, `how` | one sentence each, ≤ 150 characters |
| `what_points`, `why_points` | 2–3 slide cards, ≤ 40 characters each |
| `how_points` | 2–5 cues, ≤ 60 characters each |
| `visual` | see below |
| `analogy` | one everyday comparison |
| `jargon` | `[{"term", "plain"}]`, may be empty |
| `takeaway` | one sentence ending with a full stop, ≤ 130 characters |
| `references` | repository-relative paths, at least one |
| `diagrams` | names of PNGs in `assets/factory_diagrams/` worth looking at |
| `artifact` | what to prepare: a sketch, a file, a transcript |
| `demo` | optional commands (shown as code) |
| `verify` | claims to check against the references before Take 1 |
| `builds_on` | ids of earlier days |

## Visuals

| `type` | Shape | Fields |
|---|---|---|
| `image` | a Gas City diagram | `diagram` (PNG name) |
| `flow` | 2–5 boxes left to right, optional return arrow | `nodes` (strings or `{label, sub}`, labels ≤ 28 chars), optional `arrows` (one label per gap), `loop`, `loop_label` |
| `compare` | two panels, the right one highlighted | `left` / `right`: `{title, points (1–4)}` |
| `hub` | a centre with 3–6 spokes | `center`, `spokes` |
| `layers` | 2–5 stacked bands | `layers`: `[{label, sub}]` |
| `code` | a terminal or config panel | `lang`, `lines` (≤ 12 lines, ≤ 72 chars) |

Every visual takes an optional `caption`. New repository diagrams: render the
SVG to a white PNG at twice its size into `assets/factory_diagrams/` and keep
the MIT notice (`NOTICE.md`).

## After editing

```bash
cd ~/.claude/skills/fde-impromptu-coach
~/FDE-Impromptu/venv/bin/python -m unittest discover -s scripts/tests -p 'test_factory.py' -v
~/FDE-Impromptu/bin/fde-coach factory plan --markdown --write references/factory_learning_path.md
bash install.sh   # the schedule runs from the copy in ~/FDE-Impromptu/src
```

Preview a day before it airs: `fde-coach factory prep --date YYYY-MM-DD --open`.

## Ideas for the next modules

- Running a city: the dashboard, `gc status`, troubleshooting a stuck agent,
  JSON output for scripts (`json-discover-validate` diagram).
- Gas Town as a pack: mayor, deacon, witness, refinery, polecats, crew.
- Building your own factory: a review pack, a planning formula, a nightly order.
- Production concerns: trust boundaries, remote and hardened cities, storage.
