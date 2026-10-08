"""Legato practice, the public-domain passage library, and pronunciation's
library mode. Dry-run like the rest of the suite (no recording, upload,
calendar or network); one real-ffmpeg check is skipped without ffmpeg."""
from __future__ import annotations

import datetime as dt
import json
import os
import plistlib
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

from fdecoach import audio, legato as L, library  # noqa: E402
from fdecoach.config import Paths, load_config  # noqa: E402

from test_coach import Home  # noqa: E402  (same dry-run harness)

SKILL = SCRIPTS.parent


def _lib() -> list:
    return library.builtin()


# --------------------------------------------------------------------------- library integrity

class TestPassageLibrary(unittest.TestCase):
    def test_builtin_shape_and_provenance(self):
        ps = _lib()
        self.assertGreaterEqual(len(ps), 50)
        self.assertEqual(len({p["id"] for p in ps}), len(ps), "duplicate ids")
        for p in ps:
            self.assertTrue(library.MIN_WORDS <= len(p["text"].split()) <= library.MAX_WORDS, p["id"])
            self.assertEqual(p["words"], len(p["text"].split()), p["id"])
            self.assertIn(p["level"], (1, 2, 3))
            self.assertTrue(p["author"] and p["work"], p["id"])
            self.assertLess(int(p["year"]), 1929, f"{p['id']}: only pre-1929 works (US public domain)")
            src = p["source"]
            self.assertRegex(src["url"], r"^https://(standardebooks\.org/ebooks/|www\.gutenberg\.org/ebooks/\d+$)")
            self.assertIn("ublic domain", src["license"])
            self.assertRegex(p["text"], r"[.!?;”’\"']$", f"{p['id']} must end on a sentence")
            self.assertNotRegex(p["text"], r"⁠|_[a-z]|--|\s{2}", f"{p['id']}: leftover markup")

    def test_spec_and_asset_agree(self):
        spec = json.loads((SKILL / "assets" / "passage_sources.json").read_text(encoding="utf-8"))
        self.assertEqual([x["id"] for x in spec["passages"]], [p["id"] for p in _lib()])

    def test_pronunciation_notes(self):
        seen = {}
        for p in _lib():
            words = p["pronunciation"]["target_words"]
            self.assertEqual(len(words), 5, p["id"])
            for t in words:
                w = t["word"]
                self.assertRegex(p["text"].lower(), r"\b" + re.escape(w) + r"\b", f"{w!r} not in {p['id']}")
                self.assertNotIn(w, seen, f"{w!r} is a target in {seen.get(w)} and {p['id']}")
                seen[w] = p["id"]
                self.assertLessEqual(len(t["tip"]), 80, w)
                self.assertLessEqual(len(w), 14, w)
                self.assertRegex(t["stress"], r"[A-Z]{2,}", f"{w}: stressed syllable in caps")

    def test_level_and_normalize(self):
        self.assertEqual(library.level_of("Short one. Another short one. And a third."), 1)
        self.assertEqual(library.normalize("MAN'S mind is _very_ like--a =garden=.", gutenberg=True),
                         "Man's mind is very like—a garden.")
        self.assertEqual(library.normalize("a⁠—b  c"), "a—b c")

    def test_choose_fresh_first_then_least_recent(self):
        ps = _lib()[:6]
        d = dt.date(2026, 10, 1)
        used = [p["id"] for p in ps[:5]]
        self.assertEqual(library.choose(ps, used, d, "t")["id"], ps[5]["id"])
        everything = [p["id"] for p in ps]
        again = library.choose(ps, everything, d, "t")
        self.assertIn(again["id"], everything[:2], "after a full cycle the least recently read come back")

    def test_import_gutenberg_offline(self):
        para = ("It was a quiet morning in the valley, and the river ran slowly under the old stone bridge. "
                "The farmers walked out early, talking of rain and of the price of grain at the market. "
                "Nobody hurried; there was time enough for every task, and every task was done with care. "
                "By noon the fields were warm, and the children carried bread and water to the workers.")
        other = ("When the letter finally arrived, my grandmother read it twice at the kitchen table before "
                 "she said a single word. Then she folded it carefully, put on her best coat, and walked to the "
                 "station without telling anyone where she was going. We learned the reason only in the spring, "
                 "when a stranger with her eyes knocked at our door and asked for her by name.")
        raw = ("Title: A Test Book\nAuthor: Jane Writer\n\n*** START OF THE PROJECT GUTENBERG EBOOK TEST ***\n\n"
               "CHAPTER I\n\n" + para.replace(". ", ".\n") + "\n\n\"Yes!\" \"No!\" \"Maybe!\" \"Why?\" \"Because!\"\n\n"
               "[Illustration: a bridge]\n\n" + other +
               "\n\n*** END OF THE PROJECT GUTENBERG EBOOK TEST ***\n")
        tmp = Path(tempfile.mkdtemp())
        try:
            paths = Paths(tmp)
            paths.ensure()
            res = library.import_gutenberg(paths, 99999, raw=raw)
            self.assertEqual((res["title"], res["author"], res["added"]), ("A Test Book", "Jane Writer", 2))
            mine = library.user_passages(paths)
            self.assertEqual([p["id"] for p in mine], ["pg99999-001", "pg99999-002"])
            self.assertEqual(mine[0]["source"]["url"], "https://www.gutenberg.org/ebooks/99999")
            self.assertEqual(library.import_gutenberg(paths, 99999, raw=raw)["added"], 0, "re-import skips dupes")
            self.assertTrue(library.remove_user(paths, "pg99999-001"))
            self.assertEqual(len(library.user_passages(paths)), 1)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


# --------------------------------------------------------------------------- legato analysis

class TestLegatoAnalysis(unittest.TestCase):
    def test_sounds(self):
        for w in ("turn", "make", "much", "there", "back", "Daisy’s"):
            self.assertTrue(L.ends_in_consonant_sound(w), w)
        for w in ("the", "free", "through", "day", "now"):
            self.assertFalse(L.ends_in_consonant_sound(w), w)
        for w in ("it", "hour", "honest", "apple", "“and"):
            self.assertTrue(L.starts_with_vowel_sound(w), w)
        for w in ("one", "use", "university", "house", "yes"):
            self.assertFalse(L.starts_with_vowel_sound(w), w)

    def test_flow_respelling(self):
        self.assertEqual(L.flow_respelling(["turn", "it", "off"]), "tur-ni-toff")
        self.assertEqual(L.flow_respelling(["an", "hour"]), "a-nour")
        self.assertEqual(L.flow_respelling(["will", "always"]), "wi-lalways")
        self.assertEqual(L.flow_respelling(["back", "up"]), "ba-kup")
        self.assertEqual(L.flow_respelling(["make", "it"]), "", "silent e: no misleading respelling")
        self.assertEqual(L.flow_respelling(["thought", "is"]), "", "silent gh")
        self.assertEqual(L.flow_respelling(["vexed", "at"]), "", "-ed can sound /t/")

    def test_marks_keep_the_text_verbatim(self):
        for p in _lib():
            toks = L.marked_tokens(p["text"])
            rebuilt = "".join(t["text"] + (" " if t["space"] else "") for t in toks).strip()
            self.assertEqual(rebuilt, p["text"], p["id"])
            self.assertEqual(toks[-1]["mark"], "//", p["id"])

    def test_breath_groups_and_links(self):
        for p in _lib():
            toks = L.tokens(p["text"])
            groups = L.breath_groups(p["text"])
            self.assertEqual(groups[0][0], 0)
            self.assertEqual(groups[-1][1], len(toks))
            for (a, b, _), (c, _, _) in zip(groups, groups[1:]):
                self.assertEqual(b, c, f"{p['id']}: groups must tile the passage")
            ends = {b for _, b, _ in groups}
            for i in L.links(p["text"]):
                self.assertNotIn(i + 1, ends, f"{p['id']}: a link never crosses a breath")
                self.assertNotRegex(toks[i], r"[,;:.!?—]$", f"{p['id']}: no link across punctuation")
            self.assertTrue(L.drill_chains(p["text"]), f"{p['id']}: every passage gives a linking drill")

    def test_semicolons_are_breaths(self):
        text = ("Where the mind is without fear; Where knowledge is free; Where words come out from the "
                "depth of truth.")
        self.assertEqual([m for _, _, m in L.breath_groups(text)], ["/", "/", "//"])


# --------------------------------------------------------------------------- legato end-to-end

class TestLegatoEndToEnd(unittest.TestCase):
    def setUp(self):
        self.h = Home()

    def tearDown(self):
        self.h.cleanup()

    def leg(self) -> dict:
        path = self.h.dir / "home" / "state" / "legato.json"
        return json.loads(path.read_text()) if path.exists() else {"sessions": {}}

    def test_daily_session_feedback_and_upload(self):
        self.h.run("legato", "daily", now="2026-10-01T06:00:00", answers="Start now,Smooth")
        data = self.leg()
        s = data["sessions"]["2026-10-01"]
        self.assertTrue(s["recorded"])
        self.assertTrue(Path(s["audio_path"]).exists())
        self.assertEqual(s["youtube"]["status"], "uploaded")
        self.assertEqual(s["feedback"], "Smooth")
        self.assertEqual(data["flow_adjust"], 1)
        self.assertEqual(s["flow_level"], 1, "the first day starts at flow level 1")
        self.assertTrue(list((self.h.dir / "movies" / "legato").glob("*.mp4")))
        st = json.loads(self.h.run("status", "--json", now="2026-10-01T08:00:00").stdout)
        self.assertEqual(st["legato"]["streak"]["current"], 1)
        self.assertEqual(st["streak"]["current"], 0, "FDE streak untouched")
        self.assertEqual(st["pronunciation"]["streak"]["current"], 0, "pronunciation streak untouched")

    def test_deck_structure(self):
        self.h.run("legato", "generate", "--passage", "dickens-best-of-times", now="2026-10-01T05:59:00")
        s = self.leg()["sessions"]["2026-10-01"]
        from pptx import Presentation
        self.assertEqual(len(Presentation(s["deck_path"]).slides), 8)
        with zipfile.ZipFile(s["deck_path"]) as z:
            for i, adv in enumerate(("10000", "30000", "45000", "60000", "60000", "60000", "45000"), 1):
                self.assertIn(f'advTm="{adv}"', z.read(f"ppt/slides/slide{i}.xml").decode(), f"slide{i}")
            self.assertNotIn("advTm", z.read("ppt/slides/slide8.xml").decode())
            read1 = z.read("ppt/slides/slide4.xml").decode()
            self.assertIn('u="sng"', read1, "joins are underlined on the phrase map")
            self.assertNotIn('u="sng"', z.read("ppt/slides/slide6.xml").decode(), "Read 3 is clean text")
            self.assertIn("standardebooks.org/ebooks/charles-dickens/a-tale-of-two-cities",
                          z.read("ppt/slides/slide8.xml").decode())
            fonts = set()
            for name in z.namelist():
                if name.startswith("ppt/slides/slide") and name.endswith(".xml"):
                    xml = z.read(name).decode()
                    fonts.update(part.split('"')[0] for part in xml.split('typeface="')[1:])
            self.assertEqual(fonts, {"Calibri"})

    def test_cold_read_hidden_until_recorded(self):
        out = json.loads(self.h.run("legato", "generate", now="2026-10-01T05:59:00").stdout)
        self.assertIn("hidden", out["paragraph"])
        rows = json.loads(self.h.run("legato", "history", "--json", now="2026-10-01T06:00:00").stdout)
        self.assertIn("hidden", rows[0]["paragraph"])
        rows = json.loads(self.h.run("legato", "history", "--json", "--reveal", now="2026-10-01T06:00:00").stdout)
        self.assertNotIn("hidden", rows[0]["paragraph"])

    def test_passages_do_not_repeat_and_flow_adapts(self):
        seen = []
        for day in range(1, 9):
            now = f"2026-10-{day:02d}T06:00:00"
            answer = "Choppy" if day <= 3 else "Smooth"
            self.h.run("legato", "session", now=now, answers=answer)
            seen.append(self.leg()["sessions"][f"2026-10-{day:02d}"]["passage_id"])
        self.assertEqual(len(seen), len(set(seen)), "no passage twice in a cycle")
        self.assertEqual(self.leg()["flow_adjust"], 2, "bounded calibration: -2 after Choppy, +4 Smooth -> +2")

    def test_disabled_and_launchd(self):
        plist = plistlib.loads((self.h.dir / "agents" / "com.fdecoach.legato.plist").read_bytes())
        self.assertEqual(plist["StartCalendarInterval"], {"Hour": 6, "Minute": 0})
        self.assertEqual(plist["ProgramArguments"][-2:], ["legato", "daily"])
        self.h.run("config", "--set", "legato.daily_time=06:20", now="2026-10-01T05:00:00")
        plist = plistlib.loads((self.h.dir / "agents" / "com.fdecoach.legato.plist").read_bytes())
        self.assertEqual(plist["StartCalendarInterval"], {"Hour": 6, "Minute": 20})
        self.h.run("config", "--set", "legato.enabled=false", now="2026-10-01T05:01:00")
        out = json.loads(self.h.run("legato", "daily", now="2026-10-01T06:20:00").stdout)
        self.assertTrue(out.get("disabled"))
        self.assertEqual(self.leg()["sessions"], {})

    def test_calendar_alerts_and_clear_cover_every_practice(self):
        self.h.run("calendar-sync", now="2026-10-05T08:00:00")
        store = json.loads((self.h.dir / "home" / "state" / "dryrun_calendar.json").read_text())
        for prefix in ("fdecoach", "fdepron", "fdelegato"):
            self.assertEqual(store[f"{prefix}20261006"]["status"], "confirmed", prefix)
        self.h.run("calendar-sync", "--clear", now="2026-10-05T08:05:00")
        store = json.loads((self.h.dir / "home" / "state" / "dryrun_calendar.json").read_text())
        self.assertTrue(all(v["status"] == "cancelled" for v in store.values()))

    def test_fde_offers_pronunciation_then_legato(self):
        """The follow-up prompt used to be checked while the session lock was still
        held, so it never appeared. Now: FDE -> pronunciation -> legato."""
        self.h.run("daily", now="2026-10-02T05:30:00", answers="Start now,About right,Start now,none,Start now,Smooth")
        st = json.loads(self.h.run("status", "--json", now="2026-10-02T07:00:00").stdout)
        self.assertEqual(st["streak"]["current"], 1)
        self.assertEqual(st["pronunciation"]["streak"]["current"], 1)
        self.assertEqual(st["legato"]["streak"]["current"], 1)

    def test_metadata(self):
        from fdecoach import legato_session as LS
        cfg = load_config(Paths(self.h.dir / "unused"))
        p = next(x for x in _lib() if x["id"] == "walden-drummer")
        session = {"date": "2026-10-10", "day_number": 3, "paragraph": p["text"], "flow_level": 2,
                   "passage": {k: p[k] for k in ("id", "author", "work", "year", "section", "source")},
                   "chains": L.drill_chains(p["text"]), "response_prompt": "What would you say back to the author?"}
        marks = LS.chapters(session, cfg, offset=1.0)
        self.assertEqual([m[1] for m in marks][:3], ["Intro", "Breath & hum", "Linking drill"])
        self.assertEqual(marks[1][0], 11)
        meta = LS.build_metadata(session, cfg, marks, streak=3)
        desc = meta["snippet"]["description"]
        self.assertEqual(meta["status"]["privacyStatus"], "private")
        self.assertIn("Henry David Thoreau, Walden (1854)", desc)
        self.assertIn("https://standardebooks.org/ebooks/henry-david-thoreau/walden", desc)
        self.assertIn("//", desc)

    def test_uninstall_script_covers_every_agent(self):
        text = (SKILL / "uninstall.sh").read_text()
        for label in ("com.fdecoach.daily", "com.fdecoach.reminder", "com.fdecoach.pronounce", "com.fdecoach.legato"):
            self.assertIn(label, text)


# --------------------------------------------------------------------------- pronunciation, library mode

class TestPronunciationLibraryMode(unittest.TestCase):
    def setUp(self):
        self.h = Home()

    def tearDown(self):
        self.h.cleanup()

    def pron(self) -> dict:
        path = self.h.dir / "home" / "state" / "pronunciation.json"
        return json.loads(path.read_text()) if path.exists() else {"sessions": {}}

    def test_default_uses_a_book_passage_and_its_notes(self):
        self.h.run("pronounce", "generate", now="2026-10-01T05:45:00")
        s = self.pron()["sessions"]["2026-10-01"]
        self.assertEqual(s["source"], "library")
        p = library.get(Paths(self.h.dir / "home"), s["passage_id"])
        self.assertEqual(s["paragraph"], p["text"], "verbatim passage, never rewritten")
        self.assertEqual(s["words"], [t["word"] for t in p["pronunciation"]["target_words"]])

    def test_due_words_first_and_marked_up_by_claude_only(self):
        self.h.run("config", "--set", 'pronunciation.words=["entrepreneur","hierarchy","diaphragm","rhythm"]',
                   now="2026-10-01T05:00:00")
        self.h.run("pronounce", "generate", now="2026-10-01T05:45:00")
        s = self.pron()["sessions"]["2026-10-01"]
        self.assertEqual(len(s["words"]), 6)
        due_first = s["words"][:3]
        self.assertEqual(set(due_first) <= {"entrepreneur", "hierarchy", "diaphragm", "rhythm"}, True)
        self.assertIn("diaphragm", due_first, "a due word that appears in a passage pulls that passage in")
        self.assertIn("diaphragm", s["paragraph"])
        notes = {t["word"]: t for t in s["target_words"]}
        self.assertEqual(notes["diaphragm"]["stress"], "DY-uh-fram", "hand-written note reused")
        others = [w for w in due_first if w != "diaphragm"]
        self.assertTrue(all(notes[w]["stress"] == w.upper() for w in others), "fake Claude marked these up")

    def test_works_without_claude(self):
        self.h.run("config", "--set", "claude_path=/nonexistent/claude",
                   "--set", 'pronunciation.words=["entrepreneur"]', now="2026-10-01T05:00:00")
        self.h.run("pronounce", "daily", now="2026-10-01T05:45:00", answers="Start now,")
        s = self.pron()["sessions"]["2026-10-01"]
        self.assertTrue(s["recorded"])
        self.assertEqual(s["words"][0], "entrepreneur")
        self.assertEqual(s["target_words"][0]["stress"], "")

    def test_imported_passage_gets_claude_notes(self):
        home = Paths(self.h.dir / "home")
        text = ("The lighthouse keeper climbed the spiral stairs each evening, polishing the enormous lens "
                "until it gleamed. Ships passed safely through the treacherous channel because of his "
                "patience, and the fishermen remembered him in their prayers long after the light was "
                "automated and the little cottage stood empty beside the sea.")
        library.add_user(home, library.make_entries([text], "Test Author", "Test Work", 1900,
                                                    {"name": "Test", "url": "", "license": "Public domain"},
                                                    "story", "user-test"))
        self.h.run("pronounce", "generate", "--passage", "user-test-001", now="2026-10-01T05:45:00")
        s = self.pron()["sessions"]["2026-10-01"]
        self.assertEqual(s["source"], "library-user")
        self.assertEqual(len(s["words"]), 5)
        self.assertTrue(all(w in s["paragraph"].lower() for w in s["words"]))
        cached = library.get(home, "user-test-001")["pronunciation"]["target_words"]
        self.assertEqual([t["word"] for t in cached], s["words"], "notes cached in the user library")

    def test_youtube_credit(self):
        from fdecoach import pronounce_session as PS
        cfg = load_config(Paths(self.h.dir / "unused"))
        p = next(x for x in _lib() if x["id"] == "aps-breath")
        session = {"date": "2026-10-10", "day_number": 2, "paragraph": p["text"],
                   "passage": {k: p[k] for k in ("id", "author", "work", "year", "section", "source")},
                   "target_words": p["pronunciation"]["target_words"], "words": []}
        desc = PS.build_metadata(session, cfg, None, streak=1)["snippet"]["description"]
        self.assertIn("The Art of Public Speaking (1915)", desc)
        self.assertIn("https://www.gutenberg.org/ebooks/16317", desc)


class TestLegatoVideo(unittest.TestCase):
    def test_video_duration_matches_audio(self):
        if not audio.has_ffmpeg():
            self.skipTest("ffmpeg not installed")
        from unittest import mock
        from fdecoach import legato_session as LS, practice
        tmp = Path(tempfile.mkdtemp())
        try:
            exe = audio.ffmpeg_path()
            m4a = tmp / "voice.m4a"
            subprocess.run([exe, "-y", "-f", "lavfi", "-i", "sine=frequency=330:duration=7", "-c:a", "aac", str(m4a)],
                           capture_output=True, check=True, timeout=60)
            cfg = load_config(Paths(tmp / "unused"))
            cfg["legato"]["audio_clean_preset"] = "none"
            p = _lib()[0]
            session = {"date": "2026-10-10", "day_number": 1, "audio_path": str(m4a), "chapter_offset": 1.0,
                       "paragraph": p["text"], "passage": {k: p[k] for k in ("id", "author", "work", "year", "source")},
                       "chains": L.drill_chains(p["text"]), "response_prompt": "Retell it."}
            paths = Paths(tmp / "home")
            paths.ensure()
            env = {k: v for k, v in os.environ.items() if k not in ("FDE_COACH_DRYRUN", "FDE_COACH_RECORDINGS")}
            env["FDE_COACH_RECORDINGS"] = str(tmp / "movies")
            with mock.patch.dict(os.environ, env, clear=True):
                video = practice.assemble_video(session, cfg, paths, LS.SPEC)
            self.assertIsNotNone(video)
            self.assertAlmostEqual(audio.audio_duration_seconds(m4a), audio.audio_duration_seconds(Path(video)),
                                   delta=0.6)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
