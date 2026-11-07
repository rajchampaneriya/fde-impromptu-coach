# Regression baseline

`baseline.json` was recorded on commit 798feed, before any passage-rotation fix, by:

    python3 scripts/tests/test_passage_rotation.py record-baseline

It holds 7 days of impromptu questions (all 12 categories, bank fallback, no Claude), legato and
pronunciation content for 3 pinned passages each, and a digest of skill evals 1 to 8. The E9 scenarios
compare against it. Re-record only when a change to those outputs is intended, and say so in CHANGELOG.md.
