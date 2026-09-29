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

## Target words

- Use every word from the "words due today" list, unless there are more than
  six, in which case take the first six in order.
- If fewer than five words are due, add related words that share the same
  difficult sounds (from the focus sounds list when given).
- 5–6 target words total.
- For each word give:
  - `word`: lowercase, the exact form used in the paragraph;
  - `respelling`: how to say it with hyphens, e.g. `ar-TIC-yoo-late`;
  - `stress`: the respelling with the stressed syllable in CAPS;
  - `tip`: ONE line, max ~12 words, a concrete mouth instruction.

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
