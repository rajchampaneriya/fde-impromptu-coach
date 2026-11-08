# Regression baseline

`baseline.json` was recorded on commit 798feed, before any passage-rotation fix, by:

    python3 scripts/tests/test_passage_rotation.py record-baseline

It holds 7 days of impromptu questions (all 12 categories, bank fallback, no Claude), legato and
pronunciation content for 3 pinned passages each, and a digest of skill evals 1 to 8. The E9 scenarios
compare against it. Re-record only when a change to those outputs is intended, and say so in CHANGELOG.md.

Re-recorded on `feat/question-bank-voice`: the question bank grew from 144 to 240, so the bank fallback
picks different questions for the 7 days. Only `impromptu` changed; `pinned` and the evals digest are
byte-identical to the 798feed recording.
