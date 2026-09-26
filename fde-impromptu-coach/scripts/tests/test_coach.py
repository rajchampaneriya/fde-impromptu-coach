"""Tests for FDE Impromptu Coach. Run from the skill folder:

    python3 -m unittest discover -s scripts/tests -v

Everything macOS-specific is simulated (FDE_COACH_DRYRUN=1), so the suite runs
on any machine and never touches your real data, calendar, camera or YouTube.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
ENTRY = SCRIPTS / "fde_coach.py"
FAKE_CLAUDE = Path(__file__).resolve().parent / "fake_claude.py"

from fdecoach import questions as Q  # noqa: E402
from fdecoach.config import Paths, load_config  # noqa: E402
from fdecoach.state import History, Runtime, difficulty_curve, level_for, streaks  # noqa: E402


class Home:
    """An isolated data folder + dry-run environment for one test."""

    def __init__(self, claude: bool = True):
        self.dir = Path(tempfile.mkdtemp(prefix="fdecoach-test-"))
        self.env = dict(os.environ)
        self.env.update({
            "FDE_COACH_HOME": str(self.dir / "home"),
            "FDE_COACH_DRYRUN": "1",
            "FDE_COACH_AGENTS_DIR": str(self.dir / "agents"),
            "FDE_COACH_RECORDINGS": str(self.dir / "movies"),
            "FDE_COACH_SKIP_NETWORK_WAIT": "1",
            "FDE_COACH_NO_CLAUDE_DISCOVERY": "1",
            "PATH": "/usr/bin:/bin",  # make sure a real `claude` is never picked up
        })
        self.env.pop("FDE_COACH_TODAY", None)
        self.run("setup", "--no-warmup", now="2026-09-01T09:00:00")
        claude_path = str(FAKE_CLAUDE) if claude else "/nonexistent/claude"
        self.run("config", "--set", f"claude_path={claude_path}", now="2026-09-01T09:00:00")

    def run(self, *args: str, now: str, answers: str = "", extra=None, check: bool = True) -> subprocess.CompletedProcess:
        env = dict(self.env, FDE_COACH_NOW=now, FDE_COACH_DRYRUN_ANSWERS=answers)
        env.update(extra or {})
        proc = subprocess.run([sys.executable, str(ENTRY)] + list(args), env=env, capture_output=True, text=True,
                              timeout=120)
        if check and proc.returncode != 0:
            raise AssertionError(f"{args} failed ({proc.returncode}):\n{proc.stdout}\n{proc.stderr}")
        return proc

    def history(self) -> dict:
        path = self.dir / "home" / "state" / "history.json"
        return json.loads(path.read_text()) if path.exists() else {"sessions": {}}

    def cleanup(self) -> None:
        shutil.rmtree(self.dir, ignore_errors=True)


# --------------------------------------------------------------------------- pure logic

class TestNovelty(unittest.TestCase):
    def test_rewording_is_detected(self):
        a = "Renewal is in three weeks, usage is down 40%, and your executive sponsor has gone quiet. What do you say?"
        b = "Your renewal is in three weeks, usage is down 40% and the executive sponsor went quiet. What do you say?"
        self.assertIsNotNone(Q.is_duplicate(b, [a]))

    def test_different_question_passes(self):
        a = "Explain what an API is to a hospital administrator who has never written code."
        b = "The CISO wants every prompt logged for seven years. Legal wants nothing kept. Mediate in the meeting."
        self.assertIsNone(Q.is_duplicate(b, [a]))

    def test_bank_has_no_internal_duplicates(self):
        texts = [q["text"] for q in Q.bank()["questions"]]
        for i, t in enumerate(texts):
            self.assertIsNone(Q.is_duplicate(t, texts[:i]), t)

    def test_bank_shape(self):
        b = Q.bank()
        self.assertEqual(len(b["categories"]), 12)
        self.assertGreaterEqual(len(b["questions"]), 120)
        for q in b["questions"]:
            self.assertIn(q["category"], b["categories"])
            self.assertIn(q["format"], b["frameworks"])
            self.assertTrue(1 <= q["difficulty"] <= 5)
            self.assertTrue(40 <= len(q["text"]) <= 300, q["id"])
            self.assertNotIn("<", q["text"])


class TestStreakAndLevel(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.paths = Paths(self.tmp)
        self.paths.ensure()
        self.history = History(self.paths)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _rec(self, *days):
        for d in days:
            self.history.put({"date": d.isoformat(), "recorded": True, "questions": []})

    def test_streak_alive_until_midnight(self):
        today = dt.date(2026, 10, 10)
        self._rec(today - dt.timedelta(days=2), today - dt.timedelta(days=1))
        s = streaks(self.history, today)
        self.assertEqual(s["current"], 2)
        self.assertFalse(s["recorded_today"])
        self._rec(today)
        self.assertEqual(streaks(self.history, today)["current"], 3)

    def test_streak_broken_and_best(self):
        today = dt.date(2026, 10, 10)
        self._rec(*(dt.date(2026, 10, d) for d in (1, 2, 3, 4, 7)))
        s = streaks(self.history, today)
        self.assertEqual((s["current"], s["best"], s["total"], s["broken"]), (0, 4, 5, True))

    def test_level_progression_and_adjust(self):
        cfg = load_config(self.paths)
        rt = Runtime(self.paths)
        today = dt.date(2026, 10, 30)
        self.assertEqual(level_for(self.history, cfg, rt, today), 2)
        self._rec(*(today - dt.timedelta(days=i) for i in range(1, 13)))
        self.assertEqual(level_for(self.history, cfg, rt, today), 4)
        rt.data["level_adjust"] = 2
        self.assertEqual(level_for(self.history, cfg, rt, today), 5)  # capped at 5
        rt.data["level_adjust"] = -9
        self.assertEqual(level_for(self.history, cfg, rt, today), 1)  # floor at 1

    def test_daily_ramp(self):
        self.assertEqual(difficulty_curve(2, 5), [2, 2, 3, 3, 4])
        self.assertEqual(difficulty_curve(5, 5), [5, 5, 5, 5, 5])

    def test_bank_never_repeats_for_weeks(self):
        cfg = load_config(self.paths)
        rt = Runtime(self.paths)
        seen = set()
        start = dt.date(2026, 1, 1)
        for i in range(24):  # 24 days x 5 = 120 questions from a 132-question bank
            d = start + dt.timedelta(days=i)
            qs, label, lvl, _ = Q.generate_questions(self.history, rt, cfg, self.paths, d, source="bank")
            self.assertEqual(len(qs), 5)
            self.assertEqual(len({q["category"] for q in qs}), 5, "five different competencies per day")
            for q in qs:
                self.assertNotIn(q["text"], seen)
                seen.add(q["text"])
            self.history.put({"date": d.isoformat(), "recorded": True, "questions": qs})
        self.assertGreaterEqual(lvl, 4)
        constrained = [q for s in self.history.sessions.values() for q in s["questions"] if q.get("constraint")]
        self.assertTrue(constrained, "constraints appear once the learner reaches level 3+")


class TestClaudeParsing(unittest.TestCase):
    def test_envelope(self):
        env = json.dumps({"type": "result", "is_error": False, "result": json.dumps({"questions": [{"slot": 1}]})})
        self.assertEqual(Q.parse_claude_output(env), [{"slot": 1}])

    def test_fenced(self):
        body = "Sure!\n```json\n" + json.dumps({"questions": [{"slot": 2}]}) + "\n```"
        env = json.dumps({"type": "result", "is_error": False, "result": body})
        self.assertEqual(Q.parse_claude_output(env), [{"slot": 2}])

    def test_raw(self):
        self.assertEqual(Q.parse_claude_output(json.dumps({"questions": []})), [])

    def test_error_envelope(self):
        with self.assertRaises(ValueError):
            Q.parse_claude_output(json.dumps({"type": "result", "is_error": True, "result": "usage limit"}))

    def test_garbage(self):
        with self.assertRaises(ValueError):
            Q.parse_claude_output("I can't do that")


# --------------------------------------------------------------------------- end-to-end (dry run)

class TestEndToEnd(unittest.TestCase):
    def setUp(self):
        self.h = Home()

    def tearDown(self):
        self.h.cleanup()

    def test_daily_record_upload_and_streak(self):
        self.h.run("daily", now="2026-10-01T05:30:00", answers="Start now,About right")
        s = self.h.history()["sessions"]["2026-10-01"]
        self.assertTrue(s["recorded"])
        self.assertEqual(s["source"], "claude")
        self.assertEqual(s["youtube"]["status"], "uploaded")
        self.assertTrue(s["youtube"]["url"].startswith("https://youtu.be/"))
        self.assertTrue(Path(s["video_path"]).exists())
        self.assertEqual(s["feedback"], "About right")
        out = self.h.run("status", "--json", now="2026-10-01T08:00:00").stdout
        st = json.loads(out)
        self.assertEqual(st["streak"]["current"], 1)
        self.assertTrue(all(st["agents"].values()))

    def test_session_without_camera_exits_gracefully(self):
        from fdecoach import macos, recorder
        orig_cam, orig_mic = macos.has_camera, macos.has_microphone
        macos.has_camera = lambda: False
        macos.has_microphone = lambda: False
        try:
            self.h.run("generate", now="2026-10-01T05:30:00")
            s = self.h.history()["sessions"]["2026-10-01"]
            res = recorder.record(s, {"recording": {"mode": "auto"}}, Paths(self.h.dir / "home"))
            self.assertFalse(res["ok"])
            self.assertIn("no camera/microphone", res["error"])
            self.assertIn("complete --no-video", res["error"])
        finally:
            macos.has_camera, macos.has_microphone = orig_cam, orig_mic

    def test_deck_structure_and_timings(self):
        self.h.run("generate", now="2026-10-01T05:30:00")
        s = self.h.history()["sessions"]["2026-10-01"]
        from pptx import Presentation
        prs = Presentation(s["deck_path"])
        self.assertEqual(len(prs.slides), 7)  # intro + 5 questions + review
        with zipfile.ZipFile(s["deck_path"]) as z:
            q1 = z.read("ppt/slides/slide2.xml").decode()
            self.assertIn('advTm="60000"', q1)
            self.assertIn('dur="60000"', q1)          # 60 s timer bar
            self.assertIn('delay="45000"', q1)        # wrap-up cue
            self.assertIn('advTm="10000"', z.read("ppt/slides/slide1.xml").decode())
            self.assertNotIn("advTm", z.read("ppt/slides/slide7.xml").decode())
            self.assertIn('useTimings="1"', z.read("ppt/presProps.xml").decode())
            self.assertIn('vertBarState="minimized"', z.read("ppt/viewProps.xml").decode())
            # Keynote refuses the file without this (python-pptx template omits it)
            pres = z.read("ppt/presentation.xml").decode()
            self.assertIn("notesMasterIdLst", pres)
            rels = z.read("ppt/_rels/presentation.xml.rels").decode()
            rid = pres.split("notesMasterId r:id=\"")[1].split('"')[0]
            self.assertIn(f'Id="{rid}" Type=', rels)
            fonts = set()
            for name in z.namelist():
                if name.startswith("ppt/slides/slide") and name.endswith(".xml"):
                    xml = z.read(name).decode()
                    fonts.update(part.split('"')[0] for part in xml.split('typeface="')[1:])
            self.assertEqual(fonts, {"Calibri"})
        with zipfile.ZipFile(s["show_path"]) as z:
            self.assertIn("slideshow.main+xml", z.read("[Content_Types].xml").decode())

    def test_questions_hidden_before_recording(self):
        self.h.run("generate", now="2026-10-01T05:30:00")
        out = self.h.run("history", "--json", now="2026-10-01T06:00:00").stdout
        self.assertEqual(json.loads(out)[0]["questions"], ["(hidden until you record today)"])
        out = self.h.run("generate", now="2026-10-01T06:00:00").stdout
        self.assertIn("hidden", json.loads(out)["questions"])

    def test_missed_0530_is_caught_up_by_reminder(self):
        out = self.h.run("remind", now="2026-10-02T08:10:00", answers="Later").stdout
        self.assertIn("catch-up", out)
        self.assertIn("2026-10-02", self.h.history()["sessions"])
        # next tick within 30 minutes does not nag again
        out = self.h.run("remind", now="2026-10-02T08:25:00").stdout
        self.assertIn("recently-prompted", out)

    def test_reminder_escalation_snooze_and_quiet_hours(self):
        self.h.run("daily", now="2026-10-03T05:30:00")  # nobody there: dialog times out
        self.assertIn("nothing-due", self.h.run("remind", now="2026-10-03T06:10:00").stdout)
        self.assertIn("Snooze", self.h.run("remind", now="2026-10-03T06:31:00", answers="Snooze 20 min").stdout)
        self.assertIn("snoozed", self.h.run("remind", now="2026-10-03T06:45:00").stdout)
        self.assertIn("prompted", self.h.run("remind", now="2026-10-03T06:52:00", answers="Later").stdout)
        self.assertIn("nothing-due", self.h.run("remind", now="2026-10-03T07:05:00").stdout)
        last = self.h.run("remind", now="2026-10-03T22:05:00", answers="Later")
        self.assertIn("Last call", last.stderr)
        self.assertIn("quiet-hours", self.h.run("remind", now="2026-10-03T22:50:00").stdout)

    def test_claude_failures_fall_back_to_bank(self):
        for mode, expected in (("error", "bank"), ("garbage", "bank"), ("dupes", "bank"), ("partial", "mixed"),
                               ("fenced", "claude")):
            h = Home()
            try:
                h.run("generate", now="2026-10-04T05:30:00", extra={"FAKE_CLAUDE_MODE": mode})
                s = h.history()["sessions"]["2026-10-04"]
                self.assertEqual(len(s["questions"]), 5, mode)
                self.assertEqual(s["source"], expected, mode)
                self.assertTrue(Path(s["deck_path"]).exists())
            finally:
                h.cleanup()

    def test_no_claude_installed(self):
        h = Home(claude=False)
        try:
            h.run("generate", now="2026-10-04T05:30:00")
            self.assertEqual(h.history()["sessions"]["2026-10-04"]["source"], "bank")
        finally:
            h.cleanup()

    def test_replace_only_before_recording(self):
        self.h.run("generate", now="2026-10-05T05:30:00")
        first = [q["text"] for q in self.h.history()["sessions"]["2026-10-05"]["questions"]]
        self.h.run("generate", "--replace", "--brief", "healthcare customer", now="2026-10-05T05:40:00",
                   extra={"FAKE_CLAUDE_SALT": "x"})
        second = [q["text"] for q in self.h.history()["sessions"]["2026-10-05"]["questions"]]
        self.assertNotEqual(first, second)
        self.h.run("session", now="2026-10-05T06:00:00", answers="About right")
        proc = self.h.run("generate", "--replace", now="2026-10-05T06:10:00", check=False)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("already recorded", proc.stderr)

    def test_questions_never_repeat_across_days(self):
        seen = set()
        for day in range(1, 8):
            date = f"2026-11-{day:02d}"
            self.h.run("session", now=f"{date}T06:00:00", answers="About right")
            for q in self.h.history()["sessions"][date]["questions"]:
                self.assertIsNone(Q.is_duplicate(q["text"], list(seen)))
                seen.add(q["text"])
        st = json.loads(self.h.run("status", "--json", now="2026-11-07T08:00:00").stdout)
        self.assertEqual(st["streak"]["current"], 7)

    def test_authoring_plan_and_build_from_file(self):
        plan = json.loads(self.h.run("plan", now="2026-10-06T05:00:00").stdout)
        self.assertEqual(len(plan["slots"]), 5)
        scenes = [
            "A junior analyst on the customer's team keeps rebuilding your pipeline overnight without telling anyone.",
            "The customer's CFO asks you, in the elevator, why the pilot costs more than the quote said.",
            "Legal wants every model output reviewed by a person, which would triple the workflow time.",
            "Your product team shipped a breaking API change the morning of the customer's quarterly demo.",
            "A regional director asks you to quietly share another client's results to win over her boss.",
        ]
        items = [{"slot": s["slot"], "category": s["category"], "difficulty": s["difficulty"], "format": "roleplay",
                  "text": scenes[i] + " Respond.", "constraint": "", "coach_note": "Lead, then land it."}
                 for i, s in enumerate(plan["slots"])]
        Path(plan["write_json_to"]).write_text(json.dumps({"questions": items}))
        out = json.loads(self.h.run("build", "--questions", plan["write_json_to"], "--replace",
                                    now="2026-10-06T05:05:00").stdout)
        self.assertEqual(out["source"], "claude-interactive", out)
        texts = [q["text"] for q in self.h.history()["sessions"]["2026-10-06"]["questions"]]
        self.assertEqual(texts, [x["text"] for x in items])

    def test_manual_completion_keeps_streak(self):
        self.h.run("generate", now="2026-10-07T05:30:00")
        movies = self.h.dir / "movies"
        movies.mkdir(exist_ok=True)
        video = movies / "phone-take.mov"
        video.write_bytes(b"\0" * 2_000_000)
        self.h.run("complete", "--video", str(video), now="2026-10-07T20:00:00")
        s = self.h.history()["sessions"]["2026-10-07"]
        self.assertTrue(s["recorded"])
        self.assertEqual(s["youtube"]["status"], "uploaded")
        self.h.run("complete", "--no-video", now="2026-10-08T20:00:00")
        st = json.loads(self.h.run("status", "--json", now="2026-10-08T21:00:00").stdout)
        self.assertEqual(st["streak"]["current"], 2)

    def test_launchd_plists(self):
        import plistlib
        agents = self.h.dir / "agents"
        daily = plistlib.loads((agents / "com.fdecoach.daily.plist").read_bytes())
        self.assertEqual(daily["StartCalendarInterval"], {"Hour": 5, "Minute": 30})
        self.assertEqual(daily["ProgramArguments"][-1], "daily")
        remind = plistlib.loads((agents / "com.fdecoach.reminder.plist").read_bytes())
        self.assertEqual(remind["StartInterval"], 900)
        self.assertTrue(remind["RunAtLoad"])
        self.h.run("config", "--set", "daily_time=06:15", now="2026-10-09T09:00:00")
        daily = plistlib.loads((agents / "com.fdecoach.daily.plist").read_bytes())
        self.assertEqual(daily["StartCalendarInterval"], {"Hour": 6, "Minute": 15})

    def test_youtube_metadata(self):
        from fdecoach import youtube
        from fdecoach.deck import chapters
        cfg = load_config(Paths(self.h.dir / "unused"))
        session = {"date": "2026-10-10", "day_number": 12, "level": 3, "questions": [
            {"text": f"Question {i} text with enough length to be realistic here.", "category_label": "Crisis",
             "difficulty": 3, "constraint": "Use one analogy." if i == 2 else ""} for i in range(1, 6)]}
        marks = chapters(session, cfg, offset=3.2)
        self.assertEqual(marks[0], (0, "Intro"))
        self.assertEqual(marks[1][0], 13)
        meta = youtube.build_metadata(session, cfg, marks, streak=12)
        self.assertEqual(meta["status"]["privacyStatus"], "private")
        self.assertIn("0:13 Q1", meta["snippet"]["description"])
        self.assertIn("Constraint: Use one analogy.", meta["snippet"]["description"])
        self.assertLessEqual(len(meta["snippet"]["title"]), 100)


class TestYouTubeUploadRequest(unittest.TestCase):
    """Real googleapiclient request building (offline): private status, resumable media, retry on 503."""

    def test_upload_builds_private_resumable_request(self):
        try:
            from google.auth.credentials import AnonymousCredentials
            from googleapiclient import http as gahttp
            from googleapiclient.errors import HttpError
        except ImportError:
            self.skipTest("Google client libraries not installed")
        from unittest import mock
        from fdecoach import youtube

        tmp = Path(tempfile.mkdtemp())
        try:
            video = tmp / "v.mov"
            video.write_bytes(b"\0" * 1024)
            seen = {}
            calls = {"n": 0}

            def fake_next_chunk(self, http=None, num_retries=0):
                calls["n"] += 1
                seen["body"] = json.loads(self.body) if isinstance(self.body, (str, bytes)) else self.body
                seen["uri"] = self.uri
                if calls["n"] == 1:
                    raise HttpError(mock.Mock(status=503), b"backend error")
                return None, {"id": "abc123"}

            meta = youtube.build_metadata({"date": "2026-10-10", "day_number": 3, "level": 2, "questions": []},
                                          load_config(Paths(tmp)), None, 3)
            env = {k: v for k, v in os.environ.items() if k != "FDE_COACH_DRYRUN"}
            with mock.patch.dict(os.environ, env, clear=True), \
                    mock.patch.object(youtube, "_credentials", return_value=AnonymousCredentials()), \
                    mock.patch.object(gahttp.HttpRequest, "next_chunk", fake_next_chunk), \
                    mock.patch.object(youtube.time, "sleep"):
                vid = youtube.upload(Paths(tmp), video, meta)
            self.assertEqual(vid, "abc123")
            self.assertEqual(calls["n"], 2, "retried once after a 503")
            self.assertEqual(seen["body"]["status"]["privacyStatus"], "private")
            self.assertIn("uploadType=resumable", seen["uri"])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class TestGoogleCalendarAlerts(unittest.TestCase):
    """Missed-practice alerts: an event per unrecorded day; recording deletes it (dry run)."""

    def setUp(self):
        self.h = Home()

    def tearDown(self):
        self.h.cleanup()

    def store(self) -> dict:
        path = self.h.dir / "home" / "state" / "dryrun_calendar.json"
        return json.loads(path.read_text()) if path.exists() else {}

    def test_alert_lifecycle(self):
        self.h.run("daily", now="2026-10-01T05:30:00")  # not recorded yet
        st = self.store()
        for day in ("20261001", "20261002", "20261003"):
            self.assertEqual(st[f"fdecoach{day}"]["status"], "confirmed", day)
        body = st["fdecoach20261001"]["body"]
        self.assertIn("T21:30:00", body["start"]["dateTime"])
        self.assertEqual(body["reminders"]["overrides"], [
            {"method": "popup", "minutes": 840}, {"method": "popup", "minutes": 540},
            {"method": "popup", "minutes": 210}, {"method": "popup", "minutes": 0},
            {"method": "email", "minutes": 540}])
        self.assertFalse(body["reminders"]["useDefault"])
        self.assertEqual(body["transparency"], "transparent")

        # recording deletes today's alert so it never fires
        self.h.run("session", now="2026-10-01T06:00:00", answers="About right")
        self.assertEqual(self.store()["fdecoach20261001"]["status"], "cancelled")
        self.assertEqual(self.store()["fdecoach20261002"]["status"], "confirmed")

        # a missed day keeps its alert, and the window rolls forward
        self.h.run("remind", now="2026-10-02T23:00:00")
        st = self.store()
        self.assertEqual(st["fdecoach20261002"]["status"], "confirmed")
        self.assertEqual(st["fdecoach20261004"]["status"], "confirmed")
        (self.h.dir / "home" / "secrets" / "calendar_token.json").write_text("{}")  # "connected" for status
        status = self.h.run("status", now="2026-10-02T23:05:00").stdout
        self.assertIn("Google Calendar alert today: armed", status)

    def test_no_new_alert_after_the_event_time(self):
        self.h.run("calendar-sync", now="2026-10-05T22:00:00")
        st = self.store()
        self.assertNotIn("fdecoach20261005", st)
        self.assertIn("fdecoach20261006", st)

    def test_disable_and_clear_remove_upcoming_alerts(self):
        self.h.run("calendar-sync", now="2026-10-05T08:00:00")
        self.assertEqual(self.store()["fdecoach20261006"]["status"], "confirmed")
        self.h.run("calendar-sync", "--clear", now="2026-10-05T08:05:00")
        self.assertTrue(all(v["status"] == "cancelled" for v in self.store().values()))
        self.h.run("calendar-sync", now="2026-10-05T08:10:00")  # re-arms after a clear
        self.assertEqual(self.store()["fdecoach20261006"]["status"], "confirmed")
        self.h.run("config", "--set", "google_calendar.enabled=false", now="2026-10-05T08:15:00")
        self.h.run("calendar-sync", now="2026-10-05T08:20:00")
        self.assertTrue(all(v["status"] == "cancelled" for v in self.store().values()))

    def test_calendar_api_requests_offline(self):
        """Real googleapiclient requests: insert with our id and alerts; 409 restores via update."""
        try:
            from google.auth.credentials import AnonymousCredentials
            from googleapiclient import http as gahttp
            from googleapiclient.errors import HttpError
        except ImportError:
            self.skipTest("Google client libraries not installed")
        from unittest import mock
        from fdecoach import gcal

        cfg = load_config(Paths(self.h.dir / "unused"))
        body = gcal.build_event(dt.date(2026, 10, 7), cfg, streak=9)
        calls = []

        def fake_execute(req, http=None, num_retries=0):
            calls.append((req.method, req.uri, json.loads(req.body) if req.body else None))
            if req.method == "POST":
                raise HttpError(mock.Mock(status=409), b"duplicate")
            return {}

        env = {k: v for k, v in os.environ.items() if k != "FDE_COACH_DRYRUN"}
        with mock.patch.dict(os.environ, env, clear=True), \
                mock.patch.object(gcal, "_credentials", return_value=AnonymousCredentials()), \
                mock.patch.object(gahttp.HttpRequest, "execute", fake_execute):
            result = gcal.ensure_event(Paths(self.h.dir / "unused"), "primary", body)
            gone = gcal.delete_event(Paths(self.h.dir / "unused"), "primary", body["id"])
        self.assertEqual(result, "updated")
        self.assertEqual(gone, "deleted")
        post, put, delete = calls
        self.assertIn("/calendars/primary/events", post[1])
        self.assertEqual(post[2]["id"], "fdecoach20261007")
        self.assertEqual(len(post[2]["reminders"]["overrides"]), 5)
        self.assertEqual(put[0], "PUT")
        self.assertEqual(put[2]["status"], "confirmed")
        self.assertEqual(delete[0], "DELETE")


if __name__ == "__main__":
    unittest.main()
