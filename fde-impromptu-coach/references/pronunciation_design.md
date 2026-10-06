# Pronunciation paragraph — rubric and JSON schema

You write ONE paragraph per day for a "pen method" pronunciation practice:
the learner reads it three times (once normally, once with a pen held
horizontally between the teeth, once without the pen, slowly), after warming
up on the individual target words.

## Paragraph requirements

- 90–140 words, English, professional but natural.
- Realistic Forward Deployed Engineer / work context: a customer update, an
  incident review, a trade-off, a rollout plan. No fairy tales.
- Every target word must appear in the paragraph **at least twice** (inflected
  forms do not count — the exact word must repeat).
- Never repeat or lightly reword a paragraph from the "past paragraphs" list.
- Short sentences help the reader breathe; keep most under 18 words.

## Variety — the learner reads one of these every day

- Pick a setting the past paragraphs have not used. Rotate both the moment
  (kickoff call, incident review, design review, renewal negotiation, exec
  readout, workshop, hiring debrief, mentoring 1:1, on-site visit, handover,
  conference talk, vendor escalation, cost review) and the customer (hospital,
  bank, law firm, city government, retailer, logistics, factory, startup).
- Let the second use of a word arrive naturally in a different sentence,
  ideally in a different role: noun then verb (`record`), adjective then verb
  (`estimate`, `separate`), singular then plural (`criterion` / `criteria`).
- Do not lean on doubling crutches such as "We test X, and we test X again" or
  "…, and that X …", and do not close with a sentence that strings the target
  words together as a summary.
- Vary the shape: include a number, a question or a short quote; open with
  something other than "Here is".

## Target words

- Use every word from the "words due today" list, unless there are more than
  six, in which case take the first six in order.
- If fewer than five words are due, add related words that share the same
  difficult sounds (from the focus sounds list when given). Never add a word
  from the "already practiced" list; choose a new one.
- 5–6 target words total, ideally sharing one sound pattern so the paragraph
  drills one thing.
- Choose words a Forward Deployed Engineer actually says: technical (`cache`,
  `schema`, `idempotent`, `kubernetes`), business (`procurement`, `fiduciary`,
  `revenue`) or meeting language (`caveat`, `segue`, `nuance`). Avoid exotic
  words nobody uses at work.
- Choose words that are genuinely hard for a fluent speaker: stress that moves
  in a word family (`analyst` / `analysis` / `analytical`), noun/verb stress
  (`record`, `present`), `-ate` endings (`estimate`), silent letters (`subtle`,
  `foreign`), consonant clusters (`prompts`, `twelfth`), `th`, `v`/`w`, `r`/`l`,
  `zh` (`usually`), `-teen`/`-ty` numbers, vowel pairs (`live`/`leave`,
  `walk`/`work`).
- For each word give:
  - `word`: lowercase, the exact form used in the paragraph;
  - `respelling`: how to say it with hyphens, e.g. `ar-TIC-yoo-late`;
  - `stress`: the respelling with the stressed syllable in CAPS;
  - `tip`: ONE line, max ~12 words (under 80 characters), a concrete mouth instruction.

## Output schema (JSON only, no prose)

```json
{
  "paragraph": "…90–140 words…",
  "target_words": [
    {"word": "articulate", "respelling": "ar-TIK-yoo-late", "stress": "ar-TIK-yoo-late",
     "tip": "Stress TIK; the end is -late, not -lit."}
  ],
  "focus_sounds": ["th", "l/r"]
}
```

A validator checks the paragraph length, that every target word really occurs
twice, and novelty against all past paragraphs. Get it right the first time;
there is exactly one retry before a curated fallback paragraph is used.
