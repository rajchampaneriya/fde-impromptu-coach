# FDE Impromptu Coach

A Claude skill that trains you to speak clearly, on camera, without a script. Five minutes every morning. Forever.

Plus two short voice drills that read **real passages by human writers from free, public-domain books** (never AI-written text): **pronunciation** with the pen method, and **legato**, smooth connected speech.

![Architecture](architecture.png)

## The Problem

Customer meetings throw surprise questions at you. Interviews demand instant, structured answers. Bad news needs a calm voice.

Most engineers never practice unscripted speaking. The skill rusts.

## Why This Skill Exists

Great communicators practice daily. Daily practice needs discipline nobody has.

This skill removes the discipline tax. It builds the deck, runs the timer, records the video, tracks the streak, and nags you when you skip — all by itself.

## How to Use It

1. **Install** — clone this repo outside `~/.claude/skills` (e.g. `~/Code/fde-impromptu-coach`), then run
   `bash fde-impromptu-coach/install.sh`. It links every skill into `~/.claude/skills`, so the slash commands below work
   in any Claude Code session
2. **Every morning at 05:30** — a deck with 5 surprise questions opens itself
3. **Click Start** — QuickTime records you; each question gets 60 seconds; everything stops and saves automatically
4. **Your video uploads privately** to YouTube, with chapter marks
5. **Talk to Claude any time** — "start my practice", "what's my streak?", "make today harder", or type a slash command:

| Command | Practice |
|---|---|
| `/impromptu` (`status`, `answers`, `harder`, `brief <topic>` …) | 5 surprise on-camera questions, then the exec answer key |
| `/pronunciation` (`status`, `words`, `add <word>` …) | the pen method |
| `/legato` (`status`, `history`, `passage <id>` …) | smooth, connected speech |
| `/fde-learn` (`today`, `hint`, `ship <link>` …) | the daily learning track |
| `/fde-impromptu-coach` | set-up, settings, Google, the passage library, troubleshooting |

A command missing? `fde-coach doctor` checks the skills, and `bash fde-impromptu-coach/link_skills.sh` links them.
[`AGENTS.md`](AGENTS.md) maps what you say to the skill and command, for Claude Code and other coding agents.

Then, if you want, keep going:

6. **Pronunciation (05:45)**: your hard words plus a passage from Thoreau, Twain, Tagore, Franklin… read three times, once with a pen between your teeth
7. **Legato (06:00)**: breath and hum, a linking drill from the passage (*turn it off → tur-ni-toff*), three reads with breath marks, then a 45-second impromptu response to the author
8. **Add any free book**: `fde-coach library import-gutenberg <number>`

Miss a day? Reminders escalate on your Mac, iPhone, and calendar until you record.

## New: exec slots and the exec answer key

Deep, careful answers win technical peers. Executives and account leaders want something else: **what has to
happen (or has happened), and an offer to go into detail.** Two of each morning's five questions now train that:

- **The listener is on the slide**: *TO CFO · cares about return on the money spent*.
- **A 25-second headline window** with the shape on screen: *Headline → So what → What I need → Offer detail*.
- **Then they reply**, on a slide of its own: *"Thanks, that's all I needed."* (stop, and hold the silence),
  *"What's the biggest risk?"* or *"What do you need from me?"* (one level deeper, then stop).

After you record, **the exec answer key** opens in your browser: for every question, the one-breath headline, the
25-second answer with each sentence tagged by its move, the detail to hold back and offer if asked, and the trap (what
the technical-peer answer gets wrong for this listener). **Say it back** blurs the answer and runs the timer while you
say it in your own words. Every day's one-breath lines collect on one revision page.

```bash
fde-coach answers --open                          # today's answer key (after you record)
fde-coach config --set exec_mode.focus_slots=3    # more exec practice
```

## New: FDE Learn, a daily first-principles learning track

A second skill in this repo, [`fde-learn`](fde-learn/README.md). At **05:50** a topic drops into your public
learning repo, and at **06:00** Google Calendar shows the whole task. You learn it, build it (a notebook, code or
an Excalidraw diagram) and explain it on a ≤5-minute YouTube video, then ship with
`fde-coach learn done --video <link>`. Each topic gets the mornings its estimate needs (one to three), and each
project ends with an article published on rajc.work. 66 topics in 6 projects take you from "measure your agent"
through embeddings, gradient descent, micrograd and a tiny GPT back to a customer-ready architecture
recommendation: about 128 hours, or 4 to 5 months at 8 hours a week. Maths arrives only when a project needs it,
and everything runs locally for free except one optional, capped final run on a stronger model.

```bash
fde-coach learn init --repo ~/Code/continuous-learning
```

## Supported Tools

- Claude Code
- Microsoft PowerPoint (full automation) or Apple Keynote (manual advance)
- QuickTime Player (camera + microphone required)
- YouTube — private uploads only
- ffmpeg for the audio practices' videos (`brew install ffmpeg`)
- Standard Ebooks and Project Gutenberg for the reading passages (public domain)
- Apple Reminders + Google Calendar for streak protection
- For FDE Learn: git (a clone of your public learning repo), Ollama, uv, VS Code + Jupyter, Excalidraw
- **macOS only**
