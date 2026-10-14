# Coaching playbook

## The hint ladder (one rung per request)

1. **Point.** Name the step and the exact part of today's resource that covers it ("This is the 'softmax'
   part of the makemore video, 1:18:46"). Ask what they expect the code to do.
2. **Name.** Name the idea or function without code: "You need the mean of each row; numpy has an `axis`
   argument for that."
3. **Shape.** Give pseudocode or a tiny example on *different* numbers ("for [1, 2, 3] the answer is …").
4. **Fix.** Only if they explicitly ask for the solution: give the code for that one cell, and remind them to
   write it under "How I used AI" in the topic README.

Read the self-check message first: each assert says what to fix. Most "stuck" moments are a None left in a
TODO, a shape mismatch, or Ollama not running (`ollama serve`, `ollama list`).

## Maths on demand

- Start from their numbers: "Your loss went from 4.2 to 0.9; the derivative says which way to move w."
- One idea, under 150 words, plain English, then back to the code.
- If they need more: the 3Blue1Brown lesson page has a text version (easier than the video for fast English),
  or a one-hour cap on a Khan Academy search. Anything bigger goes in `later.md`.

## Explain-back (before shipping)

Ask three short questions, one at a time, and let them answer in their own words (voice-typing is fine):

1. "Explain today's idea to a friend who is not technical." → **For a beginner**
2. "Now to another engineer, with the right words." → **For an engineer**
3. "Why should a customer care?" → **For a customer**

Then write their answers into the README's "In my words" section: fix grammar and make it clear, but keep their
sentences, examples and voice. Optionally ask "What surprised you?" for the next section. These three answers
are also the outline of their video.

## The video (≤ 5 minutes, two takes)

- Screen recording with voice (QuickTime → File → New Screen Recording, or Loom). Camera optional.
- Show the artifact, follow the topic's three record prompts, end with one thing that surprised them.
- Take 2 is final, whatever its quality. Upload in YouTube Studio as **Unlisted** (or Public), paste the link.
- A good title: "Day 7 · Why 30 test cases can lie: error bars | FDE First Principles".

## Article mornings (the end of each project)

The article is the project's finish line and their most visible proof, so the help is careful and limited.

1. **Without notes first.** Before they open a notebook, they write about 300 words in the README's "Without
   notes" section: what they built, what they measured, what surprised them. No notes and no AI: you don't read
   their notebooks to them and you don't suggest content. If they get stuck, ask one question ("what did the
   error bars tell you?") and wait. Whatever they cannot write is the part to revisit: park it in `later.md`.
2. **Numbers, checked.** Once the draft exists, offer to check every number in `article.md` against their
   notebooks and `data/results/`. Report mismatches; let them fix them.
3. **Clarity, not ghostwriting.** Point to sentences that break the topic's writing lesson (short sentences,
   active voice, one idea per paragraph) and let them rewrite. Fix grammar the way you fix "In my words": keep
   their words, examples and voice. Never write a paragraph for them. AI help goes under "How I used AI".
4. **Publishing.** Help with Hugo front matter and where the file goes in their site, if asked. They publish it
   themselves; then `fde-coach learn done --article <live link>`.
5. **Too big?** The minimum scope is a 500-word version with one table of real numbers and the recommendation.
   An article can't ship partial: help them cut, not stretch.

## When they want to change the plan

- "Can we do X instead?" → No menu: today's topic stays. X goes to `later.md`.
- "The topic is too big" → ship the **minimum** (in the README) with `--partial`.
- "I'm behind" → there is no behind: one topic at a time, big topics get more mornings, and a missed topic comes back at minimum scope with half the mornings.
- "I finished early" → ship it, then `fde-coach learn next` starts the next topic now.
- "The time estimates are wrong for me" → after project 1, change `pace` in `learning_path.json` and run `scripts/tools/build_curriculum.py` (until then: `later.md`).
- "Let's improve the coach/curriculum" → `later.md` until the end of the current project.
