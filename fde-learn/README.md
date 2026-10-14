# FDE Learn

A project-based path from software architect to first-principles AI engineer, for the Forward Deployed
Engineer role. **A topic every morning or two: learn it, build it, explain it on video, ship it. Each project
ends with an article on [rajc.work](https://rajc.work).**

```
05:50  topic drops into your public repo  ──►  06:00 Google Calendar event with the whole task
       learn → build (notebook / code / Excalidraw) → record ≤ 5 min (2 takes); each topic shows its own minutes
       fde-coach learn done --video <YouTube link>  ──►  journal + video + progress table pushed to GitHub,
                                                        title, description and thumbnail set on the video
       finished early? fde-coach learn next
deadline: the drop after the topic's last morning (1 to 3 mornings); a missed topic comes back at minimum scope
end of each project: fde-coach learn done --article <live link on rajc.work>  ──►  the project's finish line
```

**Pace.** 8 hours a week (80 minutes a morning, Monday to Saturday). About 128 hours of work in total, estimated
topic by topic from its content: 16 weeks if you pull topics forward when you finish early, 21 weeks if you use
every morning the schedule allows. Plan on 4 to 5 months. The method is in the curriculum.

## The track: 66 topics in 6 projects

| # | Project | What you build | Maths you meet |
|---|---|---|---|
| 1 | Measure before you believe | A support assistant for a fictional broadband company, three ways (rules, one call, an agent loop from scratch), measured with error bars | fractions, error bars, percentiles |
| 2 | Meaning as numbers | Semantic search in NumPy, recall@k, chunking, a vector DB comparison, RAG measured | vectors, dot product, cosine |
| 3 | Learn a formula from data | Your hosting-cost formula and a yes/no classifier by gradient descent | slopes, loss, derivatives, sigmoid |
| 4 | Backprop by hand | micrograd: an autograd engine and a tiny neural-net library | the chain rule |
| 5 | Tiny GPT | From counting letters to a Transformer, plus tokens and cost in Indian languages | probability, log, softmax, attention |
| 6 | Back to the customer | Root causes, a final run with a stronger model, tool calls, context, prompt injection, human-in-the-loop, the final recommendation | paired differences |

Every project ends with an **article**: about 300 words from memory first (no notes, no AI), then 800 to 1,500
words with your real numbers, published on rajc.work from a Hugo-ready starter.

The full map with every resource and time estimate: [references/curriculum.md](references/curriculum.md).
Resources are free and chosen for clear English and visuals: 3Blue1Brown (lessons have text versions), Andrej
Karpathy's lectures (split into ~20-minute chapters), Google's ML Crash Course and Technical Writing One,
Anthropic's engineering posts, Hamel Husain on evals. Models run locally with Ollama. The only optional cost is
project 6's final run on a stronger model: set a hard monthly spending cap first, estimate before you run, dry-run
the API path for free against your own Ollama, and cached answers make re-runs free.

## Setup

See **Setup** in [SKILL.md](SKILL.md). In short:

```bash
bash fde-impromptu-coach/install.sh                      # also links this skill into ~/.claude/skills
git clone https://github.com/<you>/continuous-learning ~/Code/continuous-learning
fde-coach learn init --repo ~/Code/continuous-learning   # add --start today to begin now
cd ~/Code/continuous-learning/fde-first-principles && uv sync && ollama pull qwen3:4b
```

Then ask Claude Code: **"what's today's topic?"** · **"I'm stuck"** · **"ship it"**.

## Commands

| Command | What it does |
|---|---|
| `fde-coach learn today` | Today's task, hours left, what is still missing to ship |
| `fde-coach learn done --video URL` | Ship: checks, journal, commit, push, calendar (`--partial`, `--no-video`) |
| `fde-coach learn done --article URL` | Ship a project's article (the live link on rajc.work; no partial) |
| `fde-coach learn next` | Finished early: drop the next topic now |
| `fde-coach learn video` | Your video's title, description and blue title-card thumbnail (set on YouTube when you ship) |
| `fde-coach learn status` | Topics shipped, streak, current topic, push/calendar state |
| `fde-coach learn pause --until DATE` · `resume` | Travel or illness: nothing counts as missed |
| `fde-coach learn drop` | Drop today's topic now (the 05:50 agent runs this) |
| `fde-coach learn sync` | Retry a failed push and the calendar events |
