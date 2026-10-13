"""Tests for the daily learning track (fde-coach learn). Dry-run: a temporary git repo with a
local bare remote stands in for GitHub; Google Calendar calls go to the dry-run store."""
from __future__ import annotations

import datetime as dt
import json
import plistlib
import subprocess
import unittest
from pathlib import Path

from test_coach import Home

SKILL = Path(__file__).resolve().parents[2]
ASSETS = SKILL / "assets"


def git(cwd, *args):
    return subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True, check=True).stdout


class TestCurriculum(unittest.TestCase):
    def test_learning_path_integrity(self):
        data = json.loads((ASSETS / "learning_path.json").read_text())
        topics = data["topics"]
        self.assertGreaterEqual(len(topics), 50)
        self.assertEqual([t["day"] for t in topics], list(range(1, len(topics) + 1)))
        self.assertEqual(len({t["id"] for t in topics}), len(topics))
        for t in topics:
            for key in ("title", "question", "why", "learn", "build", "done_when", "minimum", "record", "expect"):
                self.assertTrue(t[key], f"{t['id']} has no {key}")
            for item in t["learn"]:
                self.assertTrue(item["url"].startswith("https://"), item["url"])
                self.assertLessEqual(item["minutes"], 30, t["id"])
            for rel in t["starter"]:
                self.assertTrue((ASSETS / "learn_starters" / t["id"] / rel).exists(), f"{t['id']}: {rel}")
            if "notebook.ipynb" in t["starter"]:
                nb = json.loads((ASSETS / "learn_starters" / t["id"] / "notebook.ipynb").read_text())
                self.assertEqual(nb["nbformat"], 4)
                self.assertTrue(any(c.get("id") == "check" for c in nb["cells"]), f"{t['id']} has no self-check")


class TestLearnFlow(unittest.TestCase):
    def setUp(self):
        self.h = Home()
        self.remote = self.h.dir / "remote.git"
        subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(self.remote)], check=True)
        self.repo = self.h.dir / "continuous-learning"
        subprocess.run(["git", "clone", "-q", str(self.remote), str(self.repo)], check=True, capture_output=True)
        git(self.repo, "config", "user.email", "test@example.com")
        git(self.repo, "config", "user.name", "Test")
        git(self.repo, "checkout", "-q", "-b", "main")
        (self.repo / "dsa").mkdir()
        (self.repo / "dsa" / "notes.md").write_text("existing work\n")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "existing")
        git(self.repo, "push", "-q", "origin", "main")
        self.track = self.repo / "fde-first-principles"

    def tearDown(self):
        self.h.cleanup()

    def learn(self, *args, now, check=True):
        return self.h.run("learn", *args, now=now, check=check)

    def progress(self):
        return json.loads((self.track / "progress.json").read_text())

    def calendar(self):
        path = self.h.dir / "home" / "state" / "dryrun_calendar.json"
        return json.loads(path.read_text()) if path.exists() else {}

    def finish_topic(self, folder: Path):
        readme = folder / "README.md"
        text = readme.read_text()
        text = text.replace(":** …", ":** In my own words, simply.")
        readme.write_text(text)
        nb = folder / "notebook.ipynb"
        if nb.exists():
            nb.write_text(nb.read_text().replace("data = None", "data = {}"))

    def test_full_cycle(self):
        out = self.learn("init", "--repo", str(self.repo), now="2026-10-13T10:00:00").stdout
        self.assertIn("first topic drops tomorrow", out)
        self.assertTrue((self.track / "progress.json").exists())
        self.assertIn("learn: start", git(self.remote, "log", "--oneline", "main"))

        # Wednesday 05:55: day 1 drops
        res = json.loads(self.learn("drop", now="2026-10-14T05:55:00").stdout)
        self.assertEqual(res["topic"], "p1-01")
        folder = self.track / "1-measure-before-you-believe" / "01-an-llm-call-is-http"
        self.assertTrue((folder / "notebook.ipynb").exists() and (folder / "README.md").exists())
        self.assertIn("Day 1 of", (self.track / "TODAY.md").read_text())
        self.assertIn("drop Day 1", git(self.remote, "log", "--oneline", "main"))
        cal = self.calendar()
        self.assertEqual(cal["fdelearn20261014t"]["status"], "confirmed")
        self.assertIn("Day 1/", cal["fdelearn20261014t"]["body"]["summary"])
        self.assertEqual(cal["fdelearn20261014n"]["status"], "confirmed")
        # running the drop again the same day changes nothing
        self.assertTrue(json.loads(self.learn("drop", now="2026-10-14T09:00:00").stdout)["already"])

        # shipping is refused until the work, the explanation and the video are there
        refused = self.learn("done", now="2026-10-14T20:00:00", check=False)
        self.assertEqual(refused.returncode, 1)
        self.assertIn("In my words", refused.stderr)
        self.finish_topic(folder)
        bad_link = self.learn("done", "--video", "https://example.com/x", now="2026-10-14T20:00:00", check=False)
        self.assertIn("does not look like a YouTube link", bad_link.stderr)
        out = self.learn("done", "--video", "https://youtu.be/abcdEFGH123", now="2026-10-14T21:30:00").stdout
        self.assertIn("shipped", out)
        p = self.progress()
        self.assertEqual(p["log"][-1]["status"], "shipped")
        self.assertIn("img.youtube.com/vi/abcdEFGH123", (folder / "README.md").read_text())
        self.assertIn("shipped Day 1", git(self.remote, "log", "--oneline", "main"))
        cal = self.calendar()
        self.assertEqual(cal["fdelearn20261014n"]["status"], "cancelled")      # nudge removed
        self.assertEqual(cal["fdelearn20261015t"]["status"], "confirmed")      # tomorrow's topic pre-created
        self.assertIn("| 1 |", (self.track / "README.md").read_text())

        # Thursday: day 2 drops, is not shipped; Friday it comes back at minimum scope
        self.assertEqual(json.loads(self.learn("drop", now="2026-10-15T06:00:00").stdout)["topic"], "p1-02")
        res = json.loads(self.learn("drop", now="2026-10-16T06:00:00").stdout)
        self.assertEqual((res["topic"], res["attempt"]), ("p1-02", 2))
        self.assertEqual(self.progress()["log"][-1]["status"], "missed")
        self.assertIn("minimum scope", (self.track / "TODAY.md").read_text())

        # shipping partial work after the deadline still counts, labelled partial
        (self.track / "1-measure-before-you-believe" / "02-workflow-or-agent" / "diagram.excalidraw.svg").write_text("<svg/>")
        out = self.learn("done", "--partial", "--video", "https://www.youtube.com/watch?v=abcdEFGH123",
                         now="2026-10-16T23:00:00").stdout
        self.assertIn("partial", out)

        # Sunday is a rest day: nothing new drops
        self.assertTrue(json.loads(self.learn("drop", now="2026-10-18T06:00:00").stdout).get("rest_day")
                        or self.progress()["current"]["topic_id"] == "p1-03")
        status = self.learn("status", "--json", now="2026-10-18T12:00:00").stdout
        self.assertEqual(json.loads(status)["shipped"], 2)
        # existing work in the repo is never touched
        self.assertEqual((self.repo / "dsa" / "notes.md").read_text(), "existing work\n")

    def test_rest_day_and_secret_scan(self):
        self.learn("init", "--repo", str(self.repo), now="2026-10-17T10:00:00")
        self.assertTrue(json.loads(self.learn("drop", now="2026-10-18T06:00:00").stdout)["rest_day"])   # Sunday
        self.assertEqual(json.loads(self.learn("drop", now="2026-10-19T06:00:00").stdout)["topic"], "p1-01")
        folder = self.track / "1-measure-before-you-believe" / "01-an-llm-call-is-http"
        self.finish_topic(folder)
        (folder / "keys.py").write_text('OPENAI_API_KEY = "sk-abcdefghijklmnopqrstuvwxyz123456"\n')
        res = self.learn("done", "--video", "https://youtu.be/abcdEFGH123", now="2026-10-19T20:00:00", check=False)
        self.assertEqual(res.returncode, 1)
        self.assertIn("looks like a secret", res.stderr)
        self.assertNotIn("sk-abcdef", git(self.remote, "log", "-p", "main"))

    def test_push_failure_is_retried(self):
        self.learn("init", "--repo", str(self.repo), now="2026-10-13T10:00:00")
        git(self.repo, "remote", "set-url", "origin", str(self.h.dir / "missing.git"))
        self.learn("drop", now="2026-10-14T06:00:00")
        self.assertTrue(json.loads(self.learn("status", "--json", now="2026-10-14T07:00:00").stdout)["push_pending"])
        git(self.repo, "remote", "set-url", "origin", str(self.remote))
        self.h.run("remind", now="2026-10-14T07:15:00")
        self.assertFalse(json.loads(self.learn("status", "--json", now="2026-10-14T07:20:00").stdout)["push_pending"])
        self.assertIn("drop Day 1", git(self.remote, "log", "--oneline", "main"))

    def test_reminder_tick_catches_up_a_missed_drop(self):
        self.learn("init", "--repo", str(self.repo), now="2026-10-13T10:00:00")
        self.h.run("remind", now="2026-10-14T08:10:00")          # Mac was asleep at 05:50
        self.assertEqual(self.progress()["current"]["topic_id"], "p1-01")

    def test_launchd_agent(self):
        plist = plistlib.loads((self.h.dir / "agents" / "com.fdecoach.learn.plist").read_bytes())
        self.assertEqual(plist["StartCalendarInterval"], {"Hour": 5, "Minute": 50})
        self.assertEqual(plist["ProgramArguments"][-3:], ["learn", "drop", "--scheduled"])
        self.assertIn("com.fdecoach.learn", (SKILL / "uninstall.sh").read_text())


class TestLearningDate(unittest.TestCase):
    def test_day_runs_from_drop_to_drop(self):
        import sys
        sys.path.insert(0, str(SKILL / "scripts"))
        from fdecoach import learn
        cfg = {"learn": {"drop_time": "05:50", "rest_days": ["Sun"]}}
        self.assertEqual(learn.learning_date(dt.datetime(2026, 10, 15, 5, 49), cfg), dt.date(2026, 10, 14))
        self.assertEqual(learn.learning_date(dt.datetime(2026, 10, 15, 5, 50), cfg), dt.date(2026, 10, 15))
        self.assertEqual(learn.next_learning_day(dt.date(2026, 10, 17), cfg), dt.date(2026, 10, 19))
        self.assertTrue(learn.words_filled("## In my words\n**For a beginner:** a\n\n**For an engineer:** b\n"))
        self.assertFalse(learn.words_filled("## In my words\n**For a beginner:** …\n"))


if __name__ == "__main__":
    unittest.main()
