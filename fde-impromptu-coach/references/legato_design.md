# Legato practice — design

Third daily practice (06:00, its own streak, reminders and calendar alerts),
built on the same engine as the pronunciation practice (`fdecoach/practice.py`):
a timed deck runs while ffmpeg records the voice, then a slides-plus-voice
MP4 is uploaded privately to YouTube.

## What it trains

*Legato* (music: "tied together") is speech whose words flow into one
another instead of arriving one by one (*staccato*). Choppy delivery is what
listeners hear as hesitant or nervous; joined, breath-paced phrases sound calm
and sure. Three habits make legato speech:

1. **Breath at phrase boundaries only.** One breath carries a whole phrase;
   the voice does not stop inside it.
2. **Linking.** A word ending in a consonant sound hands that sound to the next
   word when it begins with a vowel sound: *turn it off* → *tur-ni-toff*,
   *an hour* → *a-nour*. No glottal stop, no gap.
3. **Steady tone.** Intoning (chanting on one note) makes any gap audible,
   which is why it is the middle read.

## Session (defaults, all configurable under `legato`)

| # | Slide | Seconds | What the learner does |
|---|---|---|---|
| 1 | Intro | 10 | Day, streak, flow level, today's passage credit |
| 2 | Breath & hum | 30 | Exhale, low breath, hum 8 counts, open to "mah", glide *may-mee-my-moh-moo*, twice |
| 3 | Linking drill | 45 | 4–6 joins taken from today's passage, each twice: slowly, then at speed |
| 4 | Read 1 · phrase map | 60 | Passage with `/` breath marks, `//` at sentence ends, joins underlined |
| 5 | Read 2 · intone | 60 | Same marks; chant on one note, no gaps |
| 6 | Read 3 · speak it | 60 | Clean text; natural voice, keep the thread |
| 7 | Respond | 45 | Impromptu: one rotating prompt about the passage (agree/disagree, retell, apply at work…), "Wrap up" at 0:35 |
| 8 | Closing | – | Full credit: author, work, year, section, translator, source link |

Total 310 s; `min_audio_seconds` 180 with the same Keep / Try-again loop.
After recording: "How did the flow feel?" → **Choppy / Mostly smooth / Smooth**.

## Reading marks (computed, never generated)

All marks come from `fdecoach/legato.py`, working on the verbatim text:

* **Breath groups**: a breath after `;` `:` `—` once the group has 3+ words,
  after `,` once it has 5+ words, and `//` at every sentence end. Groups over
  14 words split at the conjunction or preposition nearest the middle (*and,
  but, that, which, when, because, of, to, with…*).
* **Links**: inside a breath group, word A links to word B when A ends in a
  consonant sound (silent final *e* counts: *make, there*; *-gh* does not:
  *though*) and B starts with a vowel sound (silent *h* counts: *hour, honest*;
  *one, use, uni-, eu-* do not). Never across punctuation.
* **Linking drill**: runs of linked words, scored by length and content
  (trivial pairs like *is a* are skipped), up to 6, in text order.
* **Flow respelling** (*tur-ni-toff*): only when every join is a simple
  consonant (b d f k l m n p r t v z, doubled letters, *ck*) and the shortened
  words stay readable (≤ 5 letters, no silent *gh*). Otherwise the slide says
  "say it as one word". These are spelling-based coaching cues, not phonetics.

A test rebuilds every library passage from its marked tokens and requires it
to match the original text exactly: marks never change the words.

## Choosing the passage and the flow level

* Passages never read before come first; after a full cycle, the least
  recently read third returns (re-reading is good practice).
* **Flow level** 1–3 = average sentence length of the passage (< 17 words,
  ≤ 26, longer). The learner starts at `start_level` 1 and moves up one level
  every `sessions_per_level` 7 recorded sessions; *Choppy* / *Smooth* adjust it
  (bounded ±2). The nearest level wins among fresh passages.
* `legato.themes` narrows the pool (`speaking`, `story`, `reflection`,
  `india`, `nature`, or a theme given to imported books). An unknown theme
  never empties the pool.
* `legato generate --replace --passage ID` picks one by hand (before recording).

## Settings (`fde-coach config --set legato.KEY=VALUE`)

`enabled`, `daily_time` (06:00), `prompt_after_pronunciation`, `audio_device`
(empty = pronunciation's), `themes`, `include_user_passages`, `start_level`,
`sessions_per_level`, the seven `*_seconds`, `min_audio_seconds`,
`audio_clean_preset`; `youtube.legato_playlist_id`.

## Files

`legato.py` (content + marks), `legato_deck.py` (deck + 1920×1080 frames),
`legato_session.py` (spec, feedback, YouTube description), state in
`~/FDE-Impromptu/state/legato.json`, audio and video in
`~/Movies/FDE-Impromptu/legato/`, launchd agent `com.fdecoach.legato`,
calendar event ids `fdelegatoYYYYMMDD`.
