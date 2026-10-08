# Changelog

## v3 — Legato practice and human-written passages

**New**

- **Legato practice** (06:00, own streak, about 5 minutes, audio only): breath & hum,
  a linking drill from the day's passage (*turn it off → tur-ni-toff*), three reads
  (phrase map with `/` breath marks and underlined joins, intoned, spoken clean), and a
  45-second impromptu response to the author. Flow level 1–3 adapts to a
  Choppy / Smooth tap. `fde-coach legato session|status|history|generate|upload`.
- **Passage library**: 56 verbatim paragraphs from 34 public-domain works by 29
  writers (Standard Ebooks / Project Gutenberg), each credited with a link on the
  slides and in the video description. `fde-coach library list|show|import-gutenberg|import-file|remove`.
  `scripts/tools/build_passage_library.py verify` re-checks every passage against its source.
- **Pronunciation uses real passages by default**: chosen to contain your due words,
  with hand-written coach notes; Claude only marks up words without notes and never
  writes text. The AI-written paragraph is still available:
  `config --set pronunciation.paragraph_source=claude`.
- One "Start now" can run all three: FDE → pronunciation → legato.

**Fixed**

- The "Pronunciation practice next?" prompt after the FDE session never appeared.
- `uninstall.sh` left the 05:45 pronunciation agent running.
- `calendar-sync --clear` (and turning alerts off) left pronunciation alerts behind.
- Pending pronunciation uploads were never shown or retried automatically.
- YouTube playlist adds always failed (NameError).
- `pronounce history` revealed today's paragraph before recording; `pronounce status` printed an empty date.
- The warm-up slide's instruction overlapped the timer label.

**Internals**

- `fdecoach/practice.py`: one engine for the audio practices (build, record, video,
  upload, calendar, status); `pronounce_session` keeps its public API.
- 84 tests (26 new), passing on Python 3.9 and 3.13.
