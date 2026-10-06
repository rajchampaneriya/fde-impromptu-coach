# Pronunciation Practice (pen method) — Implementation Plan

Second daily practice alongside the FDE impromptu session. Same architecture,
same CLI, same install. The FDE flow (05:30) is untouched except for one
optional prompt after it finishes.

## Goal

Every day at 05:45: build a 7-slide auto-advancing deck that trains the words
the learner struggles to pronounce, record **audio only** with QuickTime while
the slides run, keep the .m4a always, assemble a slides+voice MP4 with ffmpeg
and upload it to YouTube as a private video.

## Session flow (all durations configurable)

1. Intro 10 s — "Pronunciation practice, Day N" + pen-method instructions
2. Warm-up words 45 s — 5–6 target words with respelling, stressed syllable in
   caps, one-line tip; say each twice
3. Round 1, 60 s — the paragraph, target words bold blue (no pen)
4. Round 2, 75 s — same paragraph, cue "Pen between teeth. Over-articulate."
5. Round 3, 60 s — same paragraph, cue "Pen out. Slow and clear."
6. Words again 30 s — each word slowly, then at normal speed
7. Closing slide, no auto-advance

Total 280 s; `min_audio_seconds` default 180 with the same Keep / Try-again
loop as the FDE recorder. Paragraph text 28–32 pt.

## New modules

| File | Responsibility |
|---|---|
| `fdecoach/pronounce.py` | Word pool + flashcard scheduling (hard → due tomorrow; each easy answer doubles the gap 1/2/4/8; retired after 4 easy in a row), content generation via headless `claude -p` with `references/pronunciation_design.md` as rubric, paragraph validation (90–140 words, every target word ≥ 2×, never repeat a past paragraph, FDE/work context), retry once, fallback to `assets/pronunciation_bank.json` (~50 curated paragraphs, one sound pattern and scenario each, no target word reused) |
| `fdecoach/pronounce_deck.py` | The 7-slide deck (reuses deck.py primitives: `_text`, `_rect`, `_timer`, `set_transition`, `set_auto_animations`, notes-master fix, .ppsx play copy) and 1920×1080 Pillow PNG rendering of each slide for the video (same blue/Calibri look) |
| `fdecoach/pronounce_session.py` | Session flow: ensure deck → QuickTime **audio** recording (`new audio recording`) → run slideshow under the shared `session` lock → stop + save `.m4a` (reuse the macOS 26 sidecar recovery) → min-length check → "which words felt hard?" multi-select dialog → scheduling update → mark recorded → audio clean-up → ffmpeg video → YouTube upload (+optional playlist) → calendar alert cleanup |
| `fdecoach/audio.py` | ffmpeg audio clean-up, presets `light` (denoise + loudnorm) / `none`; ffmpeg probe |

## Reused with small extensions

- `config.py`: `pronunciation` defaults (times, durations, `words`, `focus_sounds`,
  `min_audio_seconds`, `audio_clean_preset`), `youtube.pronunciation_playlist_id`;
  `Paths.pron_state`
- `state.py`: `History` gets an optional file argument (pronunciation keeps its
  own `state/pronunciation.json`; streaks logic reused unchanged)
- `macos.py`: `quicktime_start_audio_recording`, `quicktime_stop_audio_save`
  (sidecar helpers parametrised for `Audio Recording.m4a`), `choose_from_list`
  (multi-select dialog), `quicktime_audio_check` (doctor)
- `scheduler.py`: third agent `com.fdecoach.pronounce` at
  `pronunciation.daily_time` (default 05:45) running `pronounce daily`;
  installed/uninstalled with the others
- `gcal.py`: `event_id`/`build_event` take a prefix + title so pronunciation
  events use ids like `fdepron20260929` (a–v, 0–9 only); separate runtime
  bookkeeping key
- `youtube.py`: `add_to_playlist` helper (scopes already granted)
- `app.py`: after the FDE session is marked recorded → optional
  "Pronunciation practice next? (5 min)" prompt (spawns `pronounce session`);
  `status()` reports both streaks; the 05:45 agent only prompts when the
  session lock is free
- `fde_coach.py`: `pronounce session|generate|status|history|daily|words
  --add/--remove/--list`; doctor checks QuickTime audio recording + ffmpeg

## Video assembly

Pillow renders each slide as PNG; ffmpeg concat demuxer with per-slide
durations shifted by the recorded audio-vs-show offset; audio from audio.py
clean-up; `libx264 -tune stillimage -pix_fmt yuv420p`, AAC 192 k, `-shortest`.
Output length equals the audio length. If ffmpeg is missing: keep the .m4a,
skip the upload, notify once with the fix (`brew install ffmpeg`).

## YouTube

Title "Pronunciation · Day N · DATE"; description = paragraph + target words
with respellings + chapters (Warm-up, Round 1, Round 2 with pen, Round 3,
Words again); privacy private; optional playlist from
`youtube.pronunciation_playlist_id`.

## Failure policy

A failure in any step never breaks either streak and the .m4a is always kept:
the day is marked recorded as soon as the audio exists; video/upload failures
are logged, retried by `pronounce upload`, and the raw audio stays on disk.

## Tests (all existing tests must still pass, unchanged)

- Unit: paragraph validation (length, ≥2 uses, novelty), word scheduling
  (1/2/4/8 doubling, retire after 4, hard reset), event id format `[a-v0-9]+`
- Dry-run end-to-end: generate → session (fake .m4a + fake mp4) → marked
  recorded → upload queued/uploaded (dry-run YouTube)
- Real ffmpeg test (skipped when ffmpeg is absent): synthetic audio + slides,
  output duration matches the audio
- `fake_claude.py` answers pronunciation prompts when the rubric asks for one

## Docs

SKILL.md (new row "pronunciation practice" / "pen method" / "add a hard word"),
README section, troubleshooting entries (no ffmpeg, audio save sidecar, agent
not loaded).
