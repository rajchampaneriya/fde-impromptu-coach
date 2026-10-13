# FDE Learn

A daily, project-based path from software architect to first-principles AI engineer, for the Forward Deployed
Engineer role. **One topic every morning. Learn it, build it, explain it on video, ship it within 24 hours.**

```
05:50  topic drops into your public repo  ──►  06:00 Google Calendar event with the whole task
       learn ~20 min → build ~40 min (notebook / code / Excalidraw) → record ≤ 5 min (2 takes)
       fde-coach learn done --video <YouTube link>  ──►  journal + video + progress table pushed to GitHub
next 05:50  deadline: shipped / late / partial; a missed topic comes back at minimum scope
```

## The track: 59 topics in 6 projects

| # | Project | What you build | Maths you meet |
|---|---|---|---|
| 1 | Measure before you believe | A support assistant for a fictional broadband company, three ways (rules, one call, an agent loop from scratch), measured with error bars | fractions, error bars, percentiles |
| 2 | Meaning as numbers | Semantic search in NumPy, recall@k, chunking, a vector DB comparison, RAG measured | vectors, dot product, cosine |
| 3 | Learn a formula from data | Your hosting-cost formula and a yes/no classifier by gradient descent | slopes, loss, derivatives, sigmoid |
| 4 | Backprop by hand | micrograd: an autograd engine and a tiny neural-net library | the chain rule |
| 5 | Tiny GPT | From counting letters to a Transformer, plus tokens and cost in Indian languages | probability, log, softmax, attention |
| 6 | Back to the customer | Root causes, tool calls, context, prompt injection, human-in-the-loop, the final recommendation | none new |

The full map with every resource: [references/curriculum.md](references/curriculum.md). Resources are free and
chosen for clear English and visuals: 3Blue1Brown (lessons have text versions), Andrej Karpathy's lectures
(split into ~20-minute chapters), Google's ML Crash Course, Anthropic's engineering posts, Hamel Husain on evals.
Models run locally with Ollama, so the whole track costs nothing.

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
| `fde-coach learn status` | Topics shipped, streak, current topic, push/calendar state |
| `fde-coach learn pause --until DATE` · `resume` | Travel or illness: nothing counts as missed |
| `fde-coach learn drop` | Drop today's topic now (the 05:50 agent runs this) |
| `fde-coach learn sync` | Retry a failed push and the calendar events |
