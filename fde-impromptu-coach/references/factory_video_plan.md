# Software Factory Daily Video — Design Plan

Third daily routine alongside the impromptu practice and the pronunciation
practice. Same CLI, same install, same reminder agent; its own streak.

## Goal

From 10 October 2026, publish one short technical video every day on the
public YouTube channel **rajcwork**, while learning Software Factory concepts
through the Gas City project (https://github.com/gastownhall/gascity).

Rule for every video: **one video → one concept → one clear takeaway**, under
three minutes. Loop: Understand → Explain → Demonstrate → Publish → Repeat.

## The daily rhythm

| When | What happens | Where |
|---|---|---|
| Day before, `factory.brief_time` (19:00) | Brief: topic, WHAT, WHY, HOW, repository references, existing diagrams, artifact or demo, 3-minute outline, and a 10-minute evening routine | Mac notification + styled page; Google Calendar event (phone and email) |
| Recording day, `factory.prep_time` (07:00) | Kit: slides, prep sheet (keyword outline, diagram, demo, points to verify, final flow, the three takes) | Mac notification + prep page |
| Any time that day | Up to 3 takes, then publish | `fde-coach factory take`, `Start Video.command`, or Claude Code |
| `factory.reminder_times` (12:30, 18:30) | Nudge, only while unpublished | Mac notification |
| `factory.publish_event_time` (21:00) | Safety-net event, deleted when published | Google Calendar |

Everything runs from the existing 15-minute reminder agent (`remind`), so a
sleeping Mac catches up on wake. No new launchd agent.

## Video format (2:50 by default): see it, group it, name it

Faceless, demo-first, in the order Greg Tang teaches maths: show something
concrete, group it into a picture, then name the rule.

| Section | Seconds | On screen | Voice |
|---|---|---|---|
| Intro | 4 | Brand card: channel, series, day, title, module; simple music | silent |
| What & why | 25 | The concept, its one-sentence definition, why it matters | set it up |
| **See it** | 100 | The demo: real commands typing out in a terminal, real output, the key line highlighted, slow agent work as "2 min later" cards | narrate |
| **Group it** | 22 | One picture of the pattern: a Gas City diagram, a flow, a comparison, a hub, layers or code | map the demo onto it |
| **Name it** | 12 | The takeaway sentence | say it |
| Outro | 7 | "Thanks for watching", tomorrow's topic, channel; soft music | silent |

Visual system: white, navy text, one blue accent, Calibri (from Microsoft Office
when installed; Carlito, Arial or DejaVu otherwise), letter-spaced section
labels, a WHAT & WHY · SEE IT · GROUP IT · TAKEAWAY tracker on every content
slide, a navy terminal panel for demos. Slides carry keywords, never
paragraphs to read aloud.

## Demos: real commands, no screen recording

- **Two demo cities** under `factory.demo_root` (`~/rajcwork-demo`), each with
  the rig `hello-factory` (a small git repo that grows across the series):
  `file/` uses the file-based bead store (Days 1–7: no Dolt, no `bd`);
  `default/` uses the default setup, bd + Dolt (Day 8 on, when `bd` commands
  start). `fde-coach factory demo setup --store file|bd` creates them.
- **Each day's demo** is 2–7 visible steps in the curriculum: `run` (a command;
  values such as bead IDs can be saved from its output and reused as
  `@{name}`), `wait_for` (poll until text appears; shown as a time-lapse card),
  hidden `write` steps (files the demo needs), and optional teardown.
- **Capture** (`fde-coach factory demo capture`) runs the steps for real and
  stores the cleaned output (no colour codes, paths shortened, long output
  trimmed). It runs in the background with the evening brief, and again in the
  morning if it is missing; a failure notifies you with the failing command
  the evening before, with time to fix it.
- **Rendering:** each command types out, its real output appears, the
  highlighted line is marked, and time-lapses show the real elapsed time. The
  100 seconds are split across steps by how much there is to read. The take
  deck has one slide per demo step with the same timing, so your narration
  lines up with the video.
- **Guards:** until a capture succeeds the slides say PREVIEW and publishing
  refuses. `fde-coach factory demo clip --file PATH` uses your own screen
  recording for the demo section instead (scaled, padded, trimmed to 100 s).
- Agent demos spend Claude Code usage; about half the days use an agent.

## Recording: voice over slides, three takes

- **Voice only, over the slides; the face is never recorded.** The viewer sees
  the demo and the picture; the speaker sees the same frames as a timed deck.
  The video is assembled from the exact frames shown during the take.
- Audio is captured straight from the AVFoundation input with ffmpeg (as in the
  pronunciation practice), with QuickTime audio recording as the fallback.
  Device: `factory.audio_device`, else `pronunciation.audio_device`.
- **Take 1 — Discovery:** explain it naturally, don't stop. **Take 2 — Improve:**
  fix unclear explanations, cut words, check timing and accuracy. **Take 3 —
  Publish:** clean and conversational. After each take: next take, listen first,
  or publish. After Take 3: publish take 3 or choose an earlier one. A fourth
  take is refused (`factory.max_takes`).
- A take shorter than `factory.min_take_seconds` (60) doesn't count.

## Audio: the voice is never processed

A previous pronunciation-focused clean-up (denoise + loudness) degraded the
user's recordings. Here the voice is only:

1. trimmed to the slide show (offset measured when the show starts),
2. copied to both channels at full level when the microphone is mono,
3. faded out over its last second, under the outro card.

Music is mixed only under the intro and outro cards, at `factory.music_volume`
(0.5). Default music is a generated soft chord (C add9 intro, Fmaj7 outro);
`fde-coach factory music --intro FILE --outro FILE` installs the user's own
tracks (the YouTube Audio Library is a good royalty-free source). The test
suite checks that the voice level in the final video matches the take within
0.6 dB.

## Publishing

| Mode | What happens | When to use |
|---|---|---|
| `studio` (default) | final.mp4, thumbnail.png and youtube.txt (title, description with chapters and references, tags) in one folder; the description is copied to the clipboard; the folder and YouTube Studio open; a dialog asks for the link | Always works for a public channel |
| `api` | Uploads with `factory.privacy_status` (public) | Only for a Google Cloud project that passed YouTube's API audit: videos uploaded by unaudited projects are locked private |

Chapters start at 0:00 and each lasts at least 10 s (YouTube's rule): what and
why (with the intro folded in), demo, picture, takeaway.

## Learning path

35 days in six modules, each day building on the one before; every seventh day
is a hands-on demo that recaps the week with a deeper, practical repetition:

1. The Big Picture (1–7): software factory, Gas City, six primitives,
   machinery, loop vs. orchestrator, toolbelt, city and rig.
2. Work: Beads (8–14): sling, bead, everything is a bead, dependencies,
   convoys, pull model, demo.
3. Workers (15–21): agents, harnesses, sessions, coordination, hooks, pools,
   demo.
4. Methods: Formulas (22–28): formula, cook vs. sling, variables, v1 vs. v2,
   check and retry, drain, demo.
5. Automation and Operations (29–32): orders, exec orders, health patrol,
   events.
6. Composition: Packs (33–35): packs, imports, the whole job end to end.

Each day cites the Gas City files it was verified against (commit
e244b16f3a, 2 October 2026) and lists the claims to re-check before recording.
13 days use a repository diagram as the HOW visual and 15 of the 16 diagrams
appear in a brief; the other days get a simple generated visual (flow, code,
comparison, layers or hub). Topics are consumed in order: an unpublished day
carries over instead of being skipped. `references/factory_curriculum.md`
explains how to write more days.

## State and files

| What | Where |
|---|---|
| Sessions, takes, publish state, streak | `~/FDE-Impromptu/state/factory.json` |
| Briefs | `~/FDE-Impromptu/factory/briefs/` |
| Kits (frames, take decks, prep sheet) | `~/FDE-Impromptu/factory/kits/<date>_DayNN_<topic>/` |
| Your music, per-day overrides | `~/FDE-Impromptu/factory/music/`, `~/FDE-Impromptu/factory/overrides/` |
| Takes and the final video | `~/Movies/FDE-Impromptu/factory/<date>_DayNN_<topic>/` |

## Validation

- Unit: curriculum rules (lengths, 2–3 slide points, visuals, references,
  diagrams on disk, ordering), one-sentence takeaways, video ≤ 180 s, chapter
  lengths, planning (start, carry-over, projection), document sections,
  overrides, event ids.
- Rendering: every day's WHAT, WHY, HOW and Takeaway frames render at 1920x1080.
- Dry-run end-to-end through the CLI: evening brief + calendar events, morning
  kit, takes with every dialog branch, three-take limit, studio and API
  publishing, carry-over, deck timings and notes.
- Real ffmpeg: assembled length and unchanged voice level.
- Not verifiable off-Mac: AVFoundation capture, PowerPoint show control and
  opening YouTube Studio. They reuse the paths the other practices already use.
