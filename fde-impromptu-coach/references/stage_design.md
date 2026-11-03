# Weekend Stage — design

A weekly practice (Saturday 08:00, Sunday 08:00 as the catch-up, its own streak in
weeks), on camera, built on the shared practice engine (`fdecoach/practice.py`)
with `media="video"` and `cadence="weekly"`: QuickTime records the camera while a
timed deck runs, and the recording uploads privately as it is.

## What it trains

Reciting a whole talk trains memory, not delivery. What carries over to exec
meetings and interviews is **stealing one delivery move a week** and using it on
your own material. So each weekend:

1. **Study, off camera (about 25 minutes).** One 2–4 minute segment of a famous
   TED talk, watched three times: normal (structure, beats), muted (body: stance,
   hands, eye line), eyes closed (voice: pace, pauses, pitch, stress). Then a
   beat sheet (5–7 keywords, `/` pause, CAPS stress) and two passes of shadowing
   with headphones.
2. **Three takes, on camera (about 10 minutes).** Take A mirrors the segment;
   Take B uses the same move on the learner's own FDE material, for the listener
   on the slide; Take C adds a twist that stays hidden until its slide.
3. **Review (about 15 minutes, off the tool for now).** Watch Take A beside the
   original in two windows, pick one fix for next weekend.

## The curriculum (`assets/talks.json`)

Ten talks, ten subjects, easiest to hardest, in four phases: find your voice
(weeks 1–3: Cutts, Okamoto, Treasure), structure and persuasion (4–6: Sinek,
Pink, Rosling), story and connection (7–9: Robinson, Brown, Adichie), gravitas
(10: Stevenson). After week 10 the cycle starts again.

Each talk holds: title, speaker, event, year, length, subject, the ted.com page,
TED's embed URL (`https://embed.ted.com/talks/lang/en/<slug>`), an optional TED
YouTube link, the **move to steal**, three **watch-for** notes, the **segment**
(a label; start and end where known), Take A's length, **Take B** (listener,
what they care about, prompt, seconds) and **Take C** (twist, seconds).

`stage.validate_catalogue()` (run by `test_stage.py`) refuses a transcript field,
a non-TED link, a missing segment, Take B or Take C, and coach notes longer than
60 words.

## Licence (TED's usage policy)

TED talks are CC BY-NC-ND 4.0: shareable unchanged, with credit, non-commercially.
TED asks for its embeddable player and does not allow scraping; transcripts may
be used only alongside the video under the same licence. So:

* **Links, never copies.** The catalogue keeps links, times and delivery notes
  in our own words. No transcript, no downloaded audio or video, ever.
* **The prep page embeds TED's player** and links the transcript on ted.com.
* **Nothing from TED reaches an upload.** The upload is the camera recording;
  shadowing happens on headphones so TED audio stays out of the microphone; the
  description credits the talk (`© TED Conferences, LLC, licensed CC BY-NC-ND
  4.0. Original: <url>`) and says the video contains no TED audio or video.
* **Take A stays private** (a performance of the speaker's words); Take B is
  entirely the learner's own content.

## Session (deck, all lengths per talk except intro and resets)

| # | Slide | Seconds | What the learner does |
|---|---|---|---|
| 1 | Intro | 15 | Week, phase, talk, the move to steal, week streak |
| 2 | Take A · Mirror | talk's `take_a_seconds` (120–240) | The segment from the beat sheet; "Wrap up" 20 s before the end |
| 3 | Reset | 20 | Breathe out; next: Take B |
| 4 | Take B · Make it yours | `take_b.seconds` (150; 300 for the capstone) | `TO <listener> · cares about …`, the prompt, the same move |
| 5 | Reset | 20 | Next: Take C (unseen) |
| 6 | Take C · Pressure | `take_c.seconds` (45–120) | The twist |
| 7 | Closing | – | Review cue and the TED credit |

YouTube chapters: Intro, Take A, Take B, Take C (each reset rides at the end of
the take before it). `stage.min_video_seconds` (240) is the shortest take kept
without asking.

## Weekly cadence

Sessions are filed under the Saturday of their Monday-to-Sunday week
(`state.period_start`), so a Sunday catch-up, or a midweek take, lands on the same
weekend. `weekly_streaks` counts consecutive weekends; the streak stays alive
until Sunday night. The calendar alert for an unrecorded weekend sits on its
Sunday at `google_calendar.event_time`.

## Segments

Week 1's segment is the whole talk (0:00–3:10). The others carry a label; the
learner finds the times on the first watch and saves them with
`fde-coach stage segment --start M:SS --end M:SS`. They are stored per talk in
`state/stage.json` (`segments`), and an unrecorded deck for that talk is rebuilt
so Take A shows them.

## Settings (`fde-coach config --set stage.KEY=VALUE`)

`enabled`, `days` (`["Sat","Sun"]`), `time` (08:00; `days` and `time` reinstall
the schedule), `intro_seconds`, `reset_seconds`, `wrap_up_cue_seconds`,
`min_video_seconds`, `open_prep_when_ready`; `youtube.stage_playlist_id`.

## Files

`assets/talks.json` (curriculum), `stage.py` (catalogue, week, segments, credit),
`stage_deck.py` (deck), `stage_prep.py` (prep page), `stage_session.py` (spec,
YouTube description, public API), state in `~/FDE-Impromptu/state/stage.json`,
prep pages in `~/FDE-Impromptu/stage/`, videos in `~/Movies/FDE-Impromptu/stage/`,
launchd agent `com.fdecoach.stage`, calendar event ids `fdestageYYYYMMDD` (the
weekend's Saturday).

## Next slices

* **The challenge:** the ladder (notes on screen 7 → 5 → 3 → 0 keywords; first
  take counts from week 7), the six-line rubric with the one-fix carry-over onto
  next weekend's intro, three hard words a week into the pronunciation pool.
* **The feedback:** local transcription of the learner's own takes (words per
  minute, fillers, pauses) against their week-1 baseline, a trend page, and a
  weekday echo of the week's move in one impromptu slot.
