"""Pronunciation practice tests: validation, word scheduling, event ids,
dry-run end-to-end, and a real ffmpeg assembly check (skipped without ffmpeg)."""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
ENTRY = SCRIPTS / "fde_coach.py"

from fdecoach import audio, gcal, pronounce as P  # noqa: E402
from fdecoach.config import Paths, load_config  # noqa: E402
from fdecoach.state import History, streaks  # noqa: E402

from test_coach import Home  # noqa: E402  (same dry-run harness)


def _history(tmp: Path) -> History:
    paths = Paths(tmp)
    paths.ensure()
    return History(paths, file=paths.pron_state)


FILLER = ("The quarterly review covered latency, budgets and the migration checklist in plain language "
          "for every stakeholder in the room. Plain numbers beat confident guesses. ")


class TestParagraphValidation(unittest.TestCase):
    def _raw(self, paragraph: str, words: list) -> dict:
        return {"paragraph": paragraph,
                "target_words": [{"word": w, "respelling": w.upper(), "stress": w.upper(), "tip": "t"}
                                 for w in words]}

    def test_valid(self):
        raw = self._raw("The hierarchy " + FILLER * 3 + " hierarchy again and hierarchy once more. "
                        "The thesis thesis holds, and the final verdict verdict lands cleanly.",
                        ["hierarchy", "thesis", "verdict"])
        out, err = P.validate_paragraph(raw, [])
        self.assertEqual(err, "")
        self.assertEqual(out["target_words"][0]["word"], "hierarchy")

    def test_too_short(self):
        raw = self._raw("too short hierarchy hierarchy thesis thesis verdict verdict",
                        ["hierarchy", "thesis", "verdict"])
        out, err = P.validate_paragraph(raw, [])
        self.assertIsNone(out)
        self.assertIn("words", err)

    def test_word_not_used_twice(self):
        raw = self._raw("hierarchy occurs once here " + FILLER * 4 + " thesis thesis verdict verdict",
                        ["hierarchy", "thesis", "verdict"])
        out, err = P.validate_paragraph(raw, [])
        self.assertIsNone(out)
        self.assertIn("needs 2", err)

    def test_duplicate_of_past(self):
        paragraph = ("The hierarchy is flat and the hierarchy holds. " + FILLER * 4 +
                     "thesis thesis verdict verdict.")
        raw = self._raw(paragraph, ["hierarchy", "thesis", "verdict"])
        out, err = P.validate_paragraph(raw, [paragraph])
        self.assertIsNone(out)
        self.assertIn("similar", err)

    def test_bank_shape(self):
        entries = P.bank()["paragraphs"]
        self.assertGreaterEqual(len(entries), 28)
        past: list = []
        for e in entries:
            out, err = P.validate_paragraph(e, past)
            self.assertEqual(err, "", f"bank entry rejected: {err}")
            past.append(e["paragraph"])

    def test_bank_variety(self):
        seen: dict = {}
        for i, e in enumerate(P.bank()["paragraphs"]):
            self.assertTrue(5 <= len(e["target_words"]) <= 6, f"entry {i}")
            for t in e["target_words"]:
                self.assertNotIn(t["word"], seen, f"{t['word']!r} is a target in entries {seen.get(t['word'])} and {i}")
                seen[t["word"]] = i
                self.assertLessEqual(len(t["tip"]), 80, f"{t['word']}: the warm-up slide cuts tips at 80 chars")
                self.assertLessEqual(len(t["word"]), 14, f"{t['word']}: too wide for the warm-up slide")


class TestBankFallbackAndPrompt(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.history = _history(self.tmp)
        self.date = dt.date(2026, 10, 1)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_bank_prefers_entry_targeting_a_due_word(self):
        entries = P.bank()["paragraphs"]
        word = entries[-1]["target_words"][0]["word"]
        out = P._from_bank(self.history, self.date, [word])
        self.assertIn(word, [t["word"] for t in out["target_words"]])
        self.assertEqual(out["source"], "bank")

    def test_prompt_lists_practiced_words_on_one_line(self):
        cfg = {"pronunciation": {}}
        prompt = P.build_prompt(cfg, self.date, ["thesis"], [], practiced=["hierarchy", "rhythm"])
        self.assertIn("hierarchy, rhythm", prompt)
        # only due words appear as "- word" lines (fake_claude and the rubric rely on that)
        self.assertEqual(re.findall(r"^- ([a-z']+)$", prompt, re.MULTILINE), ["thesis"])


class TestWordScheduling(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.history = _history(self.tmp)
        self.cfg = {"pronunciation": {"words": ["thesis", "rhythm", "verdict"]}}
        self.date = dt.date(2026, 10, 1)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_pool_syncs_from_config(self):
        self.assertEqual(P.due_words(self.history, self.cfg, self.date), ["thesis", "rhythm", "verdict"])

    def test_easy_doubles_gap_and_hard_resets(self):
        words = ["thesis", "rhythm"]
        P.update_after_session(self.history, self.cfg, self.date, words, hard_words=["thesis"])
        state = P.word_state(self.history)
        self.assertEqual(state["thesis"]["next_due"], "2026-10-02")
        self.assertEqual(state["rhythm"]["next_due"], "2026-10-02")  # first easy answer: gap 1
        d2 = self.date + dt.timedelta(days=1)
        P.update_after_session(self.history, self.cfg, d2, words, hard_words=[])
        self.assertEqual(P.word_state(self.history)["rhythm"]["next_due"], "2026-10-04")  # gap 2
        d4 = d2 + dt.timedelta(days=2)
        P.update_after_session(self.history, self.cfg, d4, words, hard_words=[])
        self.assertEqual(P.word_state(self.history)["rhythm"]["next_due"], "2026-10-08")  # gap 4

    def test_retire_after_four_easy(self):
        words = ["verdict"]
        d = self.date
        for _ in range(4):
            P.update_after_session(self.history, self.cfg, d, words, hard_words=[])
            d += dt.timedelta(days=1)
        state = P.word_state(self.history)
        self.assertTrue(state["verdict"]["retired"])
        self.assertEqual(P.due_words(self.history, self.cfg, d), ["thesis", "rhythm"])

    def test_hard_word_returns_from_retirement(self):
        words = ["verdict"]
        d = self.date
        for _ in range(4):
            P.update_after_session(self.history, self.cfg, d, words, hard_words=[])
            d += dt.timedelta(days=1)
        P.update_after_session(self.history, self.cfg, d, words, hard_words=["verdict"])
        self.assertFalse(P.word_state(self.history)["verdict"].get("retired"))


class TestEventIds(unittest.TestCase):
    def test_format_lowercase_alnum(self):
        for prefix in ("fdecoach", "fdepron"):
            for day in (dt.date(2026, 1, 1), dt.date(2026, 12, 31)):
                self.assertRegex(gcal.event_id(day, prefix), r"^[a-v0-9]+$")
                self.assertTrue(gcal.event_id(day, prefix).startswith(prefix))

    def test_pron_prefix_constant(self):
        from fdecoach import pronounce_session
        self.assertEqual(pronounce_session.GCAL_PREFIX, "fdepron")


class TestPronunciationEndToEnd(unittest.TestCase):
    def setUp(self):
        self.h = Home()
        self.h.run("config", "--set", "pronunciation.words=[\"thesis\",\"rhythm\",\"verdict\",\"paradigm\",\"suite\"]",
                   now="2026-10-01T05:00:00")

    def tearDown(self):
        self.h.cleanup()

    def pron(self) -> dict:
        path = self.h.dir / "home" / "state" / "pronunciation.json"
        return json.loads(path.read_text()) if path.exists() else {"sessions": {}}

    def test_daily_session_words_and_upload(self):
        # daily prompt -> Start now; word dialog -> thesis+verdict felt hard
        self.h.run("pronounce", "daily", now="2026-10-01T05:45:00",
                   answers="Start now,thesis+verdict")
        s = self.pron()["sessions"]["2026-10-01"]
        self.assertTrue(s["recorded"])
        self.assertTrue(Path(s["audio_path"]).exists())
        self.assertEqual(s["youtube"]["status"], "uploaded")
        self.assertTrue(s["youtube"]["url"].startswith("https://youtu.be/"))
        words = self.pron().get("words", {})
        self.assertEqual(words["thesis"]["next_due"], "2026-10-02")
        self.assertEqual(words["rhythm"]["next_due"], "2026-10-02")
        # dry-run: a fake mp4 must have been assembled for the upload
        videos = list((self.h.dir / "movies" / "pronunciation").glob("*.mp4"))
        self.assertTrue(videos, "no video assembled in dry-run")

    def test_fde_streak_untouched(self):
        self.h.run("pronounce", "daily", now="2026-10-01T05:45:00", answers="Start now,")
        fde = self.h.history()["sessions"]
        self.assertNotIn("2026-10-01", fde)
        st = json.loads(self.h.run("status", "--json", now="2026-10-01T08:00:00").stdout)
        self.assertEqual(st["streak"]["current"], 0)
        self.assertEqual(st["pronunciation"]["streak"]["current"], 1)

    def test_status_and_history(self):
        self.h.run("pronounce", "generate", now="2026-10-01T05:40:00")
        out = self.h.run("pronounce", "status", "--json", now="2026-10-01T05:41:00").stdout
        st = json.loads(out)
        self.assertFalse(st["today"]["recorded"])
        self.assertGreaterEqual(len(st["due_words"]), 5)
        self.h.run("pronounce", "session", now="2026-10-01T06:00:00", answers="thesis")
        rows = json.loads(self.h.run("pronounce", "history", "--json", now="2026-10-01T07:00:00").stdout)
        self.assertTrue(rows[0]["recorded"])
        self.assertEqual(len(rows[0]["words"]), 5)

    def test_word_add_remove(self):
        self.h.run("pronounce", "words", "--add", "entrepreneur", "--add", "hierarchy",
                   now="2026-10-01T05:00:00")
        cfg = json.loads((self.h.dir / "home" / "config.json").read_text())
        self.assertIn("hierarchy", cfg["pronunciation"]["words"])
        self.h.run("pronounce", "words", "--remove", "hierarchy", now="2026-10-01T05:01:00")
        cfg = json.loads((self.h.dir / "home" / "config.json").read_text())
        self.assertNotIn("hierarchy", cfg["pronunciation"]["words"])

    def test_claude_failure_falls_back_to_bank(self):
        self.h.run("pronounce", "generate", now="2026-10-01T05:40:00",
                   extra={"FAKE_CLAUDE_MODE": "garbage"})
        s = self.pron()["sessions"]["2026-10-01"]
        self.assertEqual(s["source"], "bank")
        self.assertGreaterEqual(len(s["words"]), 3)

    def test_deck_structure(self):
        self.h.run("pronounce", "generate", now="2026-10-01T05:40:00")
        s = self.pron()["sessions"]["2026-10-01"]
        import zipfile
        from pptx import Presentation
        self.assertEqual(len(Presentation(s["deck_path"]).slides), 7)
        with zipfile.ZipFile(s["deck_path"]) as z:
            for name, adv in (("slide1", "10000"), ("slide2", "45000"), ("slide3", "60000"),
                              ("slide4", "75000"), ("slide6", "30000")):
                self.assertIn(f'advTm="{adv}"', z.read(f"ppt/slides/{name}.xml").decode(), name)
            self.assertNotIn("advTm", z.read("ppt/slides/slide7.xml").decode())
            self.assertIn("notesMasterIdLst", z.read("ppt/presentation.xml").decode())

    def test_launchd_pronounce_agent(self):
        import plistlib
        agents = self.h.dir / "agents"
        plist = plistlib.loads((agents / "com.fdecoach.pronounce.plist").read_bytes())
        self.assertEqual(plist["StartCalendarInterval"], {"Hour": 5, "Minute": 45})
        self.assertEqual(plist["ProgramArguments"][-2:], ["pronounce", "daily"])
        self.h.run("config", "--set", "pronunciation.daily_time=06:00", now="2026-10-01T09:00:00")
        plist = plistlib.loads((agents / "com.fdecoach.pronounce.plist").read_bytes())
        self.assertEqual(plist["StartCalendarInterval"], {"Hour": 6, "Minute": 0})

    def test_metadata_chapters_and_words(self):
        from fdecoach import pronounce_session as PS
        cfg = load_config(Paths(self.h.dir / "unused"))
        session = {"date": "2026-10-10", "day_number": 4,
                   "paragraph": "The hierarchy held. " + "Plain words fill the paragraph nicely here. " * 8,
                   "target_words": [{"word": "hierarchy", "respelling": "HY-er-ar-kee", "stress": "HY-er-ar-kee",
                                     "tip": "stress the first"}],
                   "words": ["hierarchy"]}
        marks = PS.chapters(session, cfg, offset=2.0)
        self.assertEqual(marks[0], (0, "Intro"))
        self.assertEqual(marks[1], (12, "Warm-up words"))
        meta = PS.build_metadata(session, cfg, marks, streak=3)
        self.assertEqual(meta["status"]["privacyStatus"], "private")
        desc = meta["snippet"]["description"]
        self.assertIn("0:12 Warm-up words", desc)
        self.assertIn("hierarchy (HY-er-ar-kee)", desc)


class TestFfmpegAssembly(unittest.TestCase):
    """Real ffmpeg: slides + synthetic audio; the video must match the audio length."""

    def test_video_duration_matches_audio(self):
        if not audio.has_ffmpeg():
            self.skipTest("ffmpeg not installed")
        from unittest import mock
        from fdecoach import pronounce_session as PS
        tmp = Path(tempfile.mkdtemp())
        try:
            exe = audio.ffmpeg_path()
            wav = tmp / "voice.wav"
            subprocess.run([exe, "-y", "-f", "lavfi", "-i", "sine=frequency=440:duration=6",
                            "-c:a", "pcm_s16le", str(wav)], capture_output=True, check=True, timeout=60)
            m4a = tmp / "voice.m4a"
            subprocess.run([exe, "-y", "-i", str(wav), "-c:a", "aac", "-b:a", "128k", str(m4a)],
                           capture_output=True, check=True, timeout=60)
            cfg = load_config(Paths(tmp / "unused"))
            cfg["pronunciation"]["audio_clean_preset"] = "none"
            session = {"date": "2026-10-10", "day_number": 1, "audio_path": str(m4a), "chapter_offset": 1.5,
                       "paragraph": "The hierarchy held because everyone trusted the hierarchy to hold. "
                                    + "Plain filler sentences keep the paragraph long enough for two lines. " * 4,
                       "target_words": [{"word": "hierarchy", "respelling": "HY", "stress": "HY", "tip": "t"}],
                       "words": ["hierarchy"]}
            paths = Paths(tmp / "home")
            paths.ensure()
            env = {k: v for k, v in os.environ.items()
                   if k not in ("FDE_COACH_DRYRUN", "FDE_COACH_RECORDINGS")}
            env["FDE_COACH_RECORDINGS"] = str(tmp / "movies")
            with mock.patch.dict(os.environ, env, clear=True):
                video = PS.assemble_video(session, cfg, paths)
            self.assertIsNotNone(video)
            self.assertTrue(video.exists())
            want = audio.audio_duration_seconds(m4a)
            got = audio.audio_duration_seconds(Path(video))
            self.assertIsNotNone(want)
            self.assertIsNotNone(got)
            self.assertAlmostEqual(want, got, delta=0.6)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
