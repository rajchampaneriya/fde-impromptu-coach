# Passage library — sources, policy and verification

The pronunciation and legato practices read **human-written paragraphs from
free, public-domain books**, never AI-written text.

## Policy for built-in passages

* Works first published **before 1929** (public domain in the USA), whose
  authors and translators all **died before 1956** (so also public domain in
  countries with life + 70 years, and India's life + 60). Laws differ in a few
  countries; the source link on every passage lets you check.
* Taken **verbatim** from a free edition anyone can open:
  [Standard Ebooks](https://standardebooks.org) (carefully proofread; their own
  edits are CC0) or [Project Gutenberg](https://www.gutenberg.org).
* Only typographic normalisation: line wrapping, invisible word joiners,
  Gutenberg `_italic_` / `=bold=` markers, `--` → `—`, drop-cap capitals
  (`MAN'S mind` → `Man's mind`). No word is added, removed or changed.
* Excerpts start and end on sentence boundaries, 50–130 words (about a
  minute aloud), and are chosen for reading aloud: prose with rhythm, speeches,
  and passages about speaking itself.
* Nothing offensive to read aloud every morning was knowingly included (the
  opening of *Kim* was left out for its colonial framing).

## What is in it (56 passages, 34 works, 29 authors)

| Theme | Examples |
|---|---|
| speaking (21) | *The Art of Public Speaking* (Carnegie & Esenwein, 1915) on pause, breath, fluency, stage fright; Booker T. Washington on public speaking and the 1895 Atlanta address; Franklin on improving his style and on modest phrasing; Douglass on the speeches that "gave tongue" to his thoughts; Gibran's *On Talking*; Bacon's *Of Studies* |
| reflection (10) | Marcus Aurelius, Thoreau (*Walden*), Emerson (*Self-Reliance*), Arnold Bennett, James Allen, Gibran's *On Work* |
| story (17) | Twain, Dickens, Austen, Fitzgerald, Woolf, Melville, London, Stevenson, Doyle, Baum, Carroll, Jerome, Chekhov (tr. Garnett), Chesterton |
| india (6) | Tagore (*Gitanjali* 13 and 35, *The Cabuliwallah*, *The Home and the World*), Kipling's *Jungle Book*, *The Tiger, the Brahman, and the Jackal* |
| nature (2) | John Muir, Thoreau's *Walking* |

`fde-coach library list` shows them all; `library show ID` prints one with
its credit and link.

## Pronunciation notes

`assets/passage_annotations.json` holds five hand-written coach notes per
passage (word as it appears, respelling with the stressed syllable in caps, a
one-line tip): 280 different words, no word used twice. They are coaching
notes, not part of the text.

## Rebuilding and verifying

```bash
cd ~/.claude/skills/fde-impromptu-coach
python3 scripts/tools/build_passage_library.py verify   # downloads the editions, checks every passage verbatim
python3 scripts/tools/build_passage_library.py build    # regenerates assets/passages.json
python3 scripts/tools/build_passage_library.py review   # prints every passage with word count and level
```

Inputs: `assets/passage_sources.json` (books, paragraph locations, start/end
anchors, metadata) and `assets/passage_annotations.json`. Sources download
from the Standard Ebooks and GITenberg (Project Gutenberg) repositories on
GitHub into `~/.cache/fde-coach-sources`.

## Adding your own books

```bash
fde-coach library import-gutenberg 1342 --theme story --year 1813   # gutenberg.org/ebooks/1342
fde-coach library import-file ~/Downloads/speech.txt --author "Swami Vivekananda" \
    --title "Address at the World's Parliament of Religions" --year 1893 --url https://en.wikisource.org/...
fde-coach library list --mine
fde-coach library remove pg1342-007
```

The importer keeps paragraphs of 50–130 words that read as prose (complete
sentences; no headings, footnotes, illustrations, tables of contents or walls
of dialogue), spread evenly through the book, and skips anything already in the
library. Imported passages join the legato rotation at once; for pronunciation,
Claude marks up five hard words the first time one is chosen (it never edits the
text), and without Claude the built-in passages are used. Only import text you
have the right to use; the download happens on your Mac and nothing is shared.
