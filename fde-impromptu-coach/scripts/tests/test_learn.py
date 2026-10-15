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
                title = "".join(nb["cells"][0]["source"]).splitlines()[0]
                self.assertEqual(title, f"# Day {t['day']} · {t['title']}", t["id"])
            tm = t["time"]
            self.assertEqual(tm["total"], tm["learn"] + tm["build"] + tm["explain"], t["id"])
            self.assertTrue(1 <= tm["mornings"] <= 3, t["id"])
        # every project ends with an article on the learner's site, and only there
        for p in data["projects"]:
            ts = [t for t in topics if t["project"] == p["n"]]
            self.assertEqual(ts[-1]["artifact"], "article", f"project {p['n']} must end with an article")
            self.assertEqual(sum(t["artifact"] == "article" for t in ts), 1)
            self.assertEqual(ts[-1]["starter"], ["article.md"])
            self.assertGreaterEqual(ts[-1]["min_words"], 300)
            self.assertEqual([t["step"] for t in ts], list(range(1, len(ts) + 1)))
        pace = data["pace"]
        self.assertEqual(pace["minutes_per_morning"] * pace["mornings_per_week"], pace["hours_per_week"] * 60)

    def test_curriculum_page_and_estimates_are_current(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("build_curriculum", SKILL / "scripts" / "tools" / "build_curriculum.py")
        tool = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(tool)
        self.assertEqual(tool.main(["--check"]), 0, "run scripts/tools/build_curriculum.py")
        s = tool.summary(json.loads((ASSETS / "learning_path.json").read_text()))
        # the realistic range the plan promises: about 4-5 months at 8 hours a week
        self.assertTrue(3.5 <= s["months_fast"] <= s["months_schedule"] <= 6, s)


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
        return json.loads((self.track / ".learn" / "progress.json").read_text())

    def youtube(self):
        path = self.h.dir / "home" / "state" / "dryrun_youtube.json"
        return json.loads(path.read_text()) if path.exists() else {}

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
        data = json.loads((ASSETS / "learning_path.json").read_text())
        mornings = {t["id"]: t["time"]["mornings"] for t in data["topics"]}
        self.assertEqual((mornings["p1-01"], mornings["p1-02"]), (2, 2),
                         "curriculum timing changed: update the dates in this test")
        out = self.learn("init", "--repo", str(self.repo), now="2026-10-13T10:00:00").stdout
        self.assertIn("first topic drops tomorrow", out)
        self.assertTrue((self.track / ".learn" / "progress.json").exists())
        self.assertIn("learn: start", git(self.remote, "log", "--oneline", "main"))

        # Wednesday 05:55: day 1 drops with two mornings (Wed, Thu): due Friday 05:50
        res = json.loads(self.learn("drop", now="2026-10-14T05:55:00").stdout)
        self.assertEqual((res["topic"], res["mornings"], res["deadline"]), ("p1-01", 2, "2026-10-16T05:50"))
        folder = self.track / "1-measure-before-you-believe" / "01-an-llm-call-is-http"
        self.assertTrue((folder / "notebook.ipynb").exists() and (folder / "README.md").exists())
        today = (self.track / ".learn" / "TODAY.md").read_text()
        self.assertIn("Day 1 of", today)
        self.assertIn("morning 1 of 2", today)
        self.assertIn("**Time:** about", today)
        self.assertIn("drop Day 1", git(self.remote, "log", "--oneline", "main"))
        cal = self.calendar()
        self.assertEqual(cal["fdelearn20261014t"]["status"], "confirmed")
        self.assertIn("Day 1/", cal["fdelearn20261014t"]["body"]["summary"])
        self.assertIn("morning 1 of 2", cal["fdelearn20261014t"]["body"]["summary"])
        self.assertNotIn("fdelearn20261014n", cal)          # no "not shipped" nudge before the last morning
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
        readme = (folder / "README.md").read_text()
        self.assertIn("[![Watch the video](video/thumbnail.png)](https://youtu.be/abcdEFGH123)", readme)
        self.assertIn("YouTube title, description and thumbnail set", out)
        from PIL import Image
        with Image.open(folder / "video" / "thumbnail.png") as img:
            self.assertEqual(img.size, (1280, 720))
        self.assertIn("video/thumbnail.png", git(self.remote, "show", "--stat", "--format=", "main"))
        yt = self.youtube()["abcdEFGH123"]
        self.assertEqual(yt["snippet"]["title"], "Day 1 · One model call: tokens, time and randomness | FDE First Principles")
        desc = yt["snippet"]["description"]
        self.assertTrue(desc.startswith("What does one model call really cost"), desc[:80])
        self.assertIn("▸ For a beginner: In my own words, simply.", desc)
        self.assertIn("https://github.com/rajchampaneriya/fde-impromptu-coach", desc)
        self.assertIn("01-an-llm-call-is-http", desc)                 # the notebook on GitHub
        self.assertIn("https://docs.ollama.com/api/chat", desc)        # the free resources
        self.assertEqual((yt["thumbnail"], yt["snippet"]["categoryId"]), ("thumbnail.png", "27"))
        self.assertIn(yt["snippet"]["title"], (folder / "video" / "youtube.md").read_text())
        self.assertIn("shipped Day 1", git(self.remote, "log", "--oneline", "main"))
        cal = self.calendar()
        self.assertEqual(cal["fdelearn20261015t"]["status"], "confirmed")      # finished early: day 2 drops Thursday
        self.assertIn("| 1 |", (self.track / "README.md").read_text())

        # Thursday: day 2 drops (Thu, Fri). Friday is its second morning: nothing is missed, the nudge appears
        self.assertEqual(json.loads(self.learn("drop", now="2026-10-15T06:00:00").stdout)["topic"], "p1-02")
        res = json.loads(self.learn("drop", now="2026-10-16T06:00:00").stdout)
        self.assertTrue(res["continuing"])
        self.assertEqual((res["topic"], res["morning"], res["mornings"]), ("p1-02", 2, 2))
        self.assertNotIn("missed", json.dumps(self.progress()["log"]))
        self.assertIn("morning 2 of 2", (self.track / ".learn" / "TODAY.md").read_text())
        self.assertIn("(morning 2 of 2)", git(self.remote, "log", "--oneline", "main"))
        cal = self.calendar()
        self.assertIn("morning 2 of 2", cal["fdelearn20261016t"]["body"]["summary"])
        self.assertEqual(cal["fdelearn20261016n"]["status"], "confirmed")
        self.assertTrue(json.loads(self.learn("drop", now="2026-10-16T09:00:00").stdout)["already"])

        # Saturday: past its deadline, so it comes back at minimum scope with half the mornings (1)
        res = json.loads(self.learn("drop", now="2026-10-17T06:00:00").stdout)
        self.assertEqual((res["topic"], res["attempt"], res["mornings"]), ("p1-02", 2, 1))
        self.assertEqual(self.progress()["log"][-1]["status"], "missed")
        self.assertIn("minimum scope", (self.track / ".learn" / "TODAY.md").read_text())

        # shipping partial work still counts, labelled partial
        (self.track / "1-measure-before-you-believe" / "02-workflow-or-agent" / "diagram.excalidraw.svg").write_text("<svg/>")
        out = self.learn("done", "--partial", "--video", "https://www.youtube.com/watch?v=abcdEFGH123",
                         now="2026-10-17T23:00:00").stdout
        self.assertIn("partial", out)
        self.assertIn("Previous: Day 1 · One model call", self.youtube()["abcdEFGH123"]["snippet"]["description"])

        # Sunday is a rest day: nothing new drops
        self.assertTrue(json.loads(self.learn("drop", now="2026-10-18T06:00:00").stdout).get("rest_day"))
        status = json.loads(self.learn("status", "--json", now="2026-10-18T12:00:00").stdout)
        self.assertEqual(status["shipped"], 2)
        self.assertEqual(json.loads(self.learn("drop", now="2026-10-19T06:00:00").stdout)["topic"], "p1-03")
        # existing work in the repo is never touched
        self.assertEqual((self.repo / "dsa" / "notes.md").read_text(), "existing work\n")

    def jump_to(self, topic_id, now):
        """Pretend everything before `topic_id` shipped yesterday, then drop it."""
        data = json.loads((ASSETS / "learning_path.json").read_text())
        ids = [t["id"] for t in data["topics"]]
        prev = ids[ids.index(topic_id) - 1]
        p = self.progress()
        p["current"] = {"topic_id": prev, "folder": "x", "dropped_on": "2026-10-13", "seen_on": "2026-10-13",
                        "deadline": "2026-10-14T05:50", "attempt": 1, "mornings": 1,
                        "shipped_at": "2026-10-13T20:00", "status": "shipped"}
        (self.track / ".learn" / "progress.json").write_text(json.dumps(p))
        git(self.repo, "commit", "-qam", "test: jump")
        return json.loads(self.learn("drop", now=now).stdout)

    def test_legacy_track_root_files_migrate_into_learn_dir(self):
        self.learn("init", "--repo", str(self.repo), now="2026-10-13T10:00:00")
        state = self.track / ".learn"
        for name in ("progress.json", "TODAY.md", "later.md"):
            (state / name).replace(self.track / name)          # back to the old track-root layout
        self.learn("drop", now="2026-10-14T05:55:00")           # touches progress.json + TODAY.md
        self.learn("init", "--repo", str(self.repo), now="2026-10-14T12:00:00")  # touches later.md
        for name in ("progress.json", "TODAY.md", "later.md"):
            self.assertTrue((state / name).exists(), name)
            self.assertFalse((self.track / name).exists(), name)

    def test_article_is_the_project_finish_line(self):
        self.learn("init", "--repo", str(self.repo), now="2026-10-13T10:00:00")
        res = self.jump_to("p1-12", "2026-10-14T06:00:00")
        self.assertEqual((res["topic"], res["mornings"], res["deadline"]), ("p1-12", 3, "2026-10-17T05:50"))
        folder = self.track / "1-measure-before-you-believe" / "12-article"
        readme = (folder / "README.md").read_text()
        self.assertIn("## Without notes", readme)
        self.assertIn("<!-- learn:article -->", readme)
        self.assertIn("draft: true", (folder / "article.md").read_text())
        self.assertIn("--article https://rajc.work/blog/", (self.track / ".learn" / "TODAY.md").read_text())
        self.assertIn("--article", self.calendar()["fdelearn20261014t"]["body"]["description"])

        refused = self.learn("done", now="2026-10-14T20:00:00", check=False)
        self.assertIn("Without notes", refused.stderr)
        self.assertIn("live article link", refused.stderr)
        self.assertNotIn("In my words", refused.stderr)
        partial = self.learn("done", "--partial", now="2026-10-14T20:00:00", check=False)
        self.assertIn("can't ship partial", partial.stderr)

        words = " ".join(["measure"] * 260)
        (folder / "README.md").write_text(readme.replace("## Without notes", "## Without notes\n" + words, 1))
        article = (folder / "article.md").read_text()
        (folder / "article.md").write_text(article + "\n" + " ".join(["evidence"] * 300))
        short = self.learn("done", "--article", "https://rajc.work/blog/2026/10/measure/", now="2026-10-15T20:00:00",
                           check=False)
        self.assertIn("the minimum is 500", short.stderr)
        (folder / "article.md").write_text(article + "\n" + " ".join(["evidence"] * 650))
        elsewhere = self.learn("done", "--article", "https://medium.com/@me/measure", now="2026-10-15T20:00:00",
                               check=False)
        self.assertIn("is not on rajc.work", elsewhere.stderr)
        out = self.learn("done", "--article", "https://rajc.work/blog/2026/10/measure/", now="2026-10-15T20:00:00").stdout
        self.assertIn("project finished", out)
        self.assertEqual(self.progress()["log"][-1]["article"], "https://rajc.work/blog/2026/10/measure/")
        self.assertIn("📝 **Published:**", (folder / "README.md").read_text())
        self.assertIn("[📝](https://rajc.work/blog/2026/10/measure/)", (self.track / "README.md").read_text())
        self.assertEqual(json.loads(self.learn("status", "--json", now="2026-10-15T21:00:00").stdout)["projects_done"], 1)

    def test_video_details_before_and_after_shipping(self):
        self.learn("init", "--repo", str(self.repo), now="2026-10-13T10:00:00")
        self.learn("drop", now="2026-10-14T05:55:00")
        folder = self.track / "1-measure-before-you-believe" / "01-an-llm-call-is-http"
        out = self.learn("video", now="2026-10-14T07:00:00").stdout
        self.assertIn("Day 1 · One model call: tokens, time and randomness | FDE First Principles", out)
        self.assertIn("'In my words' is not filled in yet", out)
        self.assertTrue((folder / "video" / "thumbnail.png").exists() and (folder / "video" / "youtube.md").exists())
        self.assertEqual(self.youtube(), {})                            # nothing is sent before you ship
        self.finish_topic(folder)
        self.learn("done", "--video", "https://youtu.be/abcdEFGH123", now="2026-10-14T20:00:00")
        readme = folder / "README.md"
        readme.write_text(readme.read_text().replace("**For a customer:** In my own words, simply.",
                                                     "**For a customer:** Same prompt, different answers: plan for it."))
        res = json.loads(self.learn("video", "--json", now="2026-10-14T21:00:00").stdout)
        self.assertTrue(res["shipped"])
        self.assertIn("Same prompt, different answers", self.youtube()["abcdEFGH123"]["snippet"]["description"])
        self.assertIn("video details Day 1", git(self.remote, "log", "--oneline", "main"))

    def test_youtube_update_can_be_switched_off(self):
        self.h.run("config", "--set", "learn.youtube_update=false", now="2026-10-13T09:00:00")
        self.learn("init", "--repo", str(self.repo), now="2026-10-13T10:00:00")
        self.learn("drop", now="2026-10-14T05:55:00")
        folder = self.track / "1-measure-before-you-believe" / "01-an-llm-call-is-http"
        self.finish_topic(folder)
        out = self.learn("done", "--video", "https://youtu.be/abcdEFGH123", now="2026-10-14T20:00:00").stdout
        self.assertNotIn("YouTube title", out)
        self.assertEqual(self.youtube(), {})
        self.assertTrue((folder / "video" / "youtube.md").exists())    # still ready to paste by hand

    def test_learn_next_pulls_the_next_topic_forward(self):
        self.learn("init", "--repo", str(self.repo), now="2026-10-13T10:00:00")
        self.learn("drop", now="2026-10-14T05:55:00")
        self.assertIn("still open", self.learn("next", now="2026-10-14T07:00:00", check=False).stderr)
        self.finish_topic(self.track / "1-measure-before-you-believe" / "01-an-llm-call-is-http")
        self.learn("done", "--video", "https://youtu.be/abcdEFGH123", now="2026-10-14T07:30:00")
        self.h.run("remind", now="2026-10-14T07:45:00")              # the 15-minute tick waits for tomorrow
        self.assertEqual(self.progress()["current"]["topic_id"], "p1-01")
        out = self.learn("next", now="2026-10-14T07:50:00").stdout
        self.assertIn("Day 2", out)
        cur = self.progress()["current"]
        self.assertEqual((cur["topic_id"], cur["dropped_on"]), ("p1-02", "2026-10-14"))
        self.assertTrue(json.loads(self.learn("drop", now="2026-10-14T09:00:00").stdout)["already"])

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
        # a 2-morning topic dropped on Saturday covers Saturday and Monday: due Tuesday 05:50
        self.assertEqual(learn.deadline_for(dt.date(2026, 10, 17), cfg, 2), dt.datetime(2026, 10, 20, 5, 50))
        self.assertEqual(learn.deadline_for(dt.date(2026, 10, 14), cfg), dt.datetime(2026, 10, 15, 5, 50))

    def test_streak_counts_every_morning_of_a_shipped_topic(self):
        import sys
        sys.path.insert(0, str(SKILL / "scripts"))
        from fdecoach import learn
        cfg = {"learn": {"drop_time": "05:50", "rest_days": ["Sun"]}}
        progress = {"log": [
            {"topic_id": "p1-01", "dropped_on": "2026-10-14", "mornings": 2, "status": "shipped",
             "shipped_at": "2026-10-15T20:00"},
            {"topic_id": "p1-02", "dropped_on": "2026-10-16", "mornings": 2, "status": "late",
             "shipped_at": "2026-10-17T22:00"},
        ], "current": {"topic_id": "p1-03", "dropped_on": "2026-10-19", "mornings": 2}}
        # Tue 20: the open topic's mornings (Mon, Tue) and Sunday are skipped; Sat, Fri, Thu, Wed count
        self.assertEqual(learn.streak(progress, cfg, dt.date(2026, 10, 20)), 4)
        progress["log"][1]["status"] = "missed"
        self.assertEqual(learn.streak(progress, cfg, dt.date(2026, 10, 20)), 0)

    def test_video_description_is_built_from_the_video(self):
        import sys
        sys.path.insert(0, str(SKILL / "scripts"))
        from fdecoach import learn_video as lv
        data = json.loads((ASSETS / "learning_path.json").read_text())
        t = next(x for x in data["topics"] if x["id"] == "p1-07")
        readme = ("## In my words\n<!-- note -->\n**For a beginner:** A small test can fool you.\nLike one coin toss.\n\n"
                  "**For an engineer:** n = 30 gives about ± 15 points.\n\n**For a customer:** …\n\n"
                  "## What surprised me\nHow wide the range is.\n\n## How I used AI\n…\n")
        parts = lv.readme_parts(readme)
        self.assertEqual(parts["beginner"], "A small test can fool you.\nLike one coin toss.")
        self.assertNotIn("customer", parts)                           # a placeholder is not an answer
        self.assertEqual(parts["surprised"], "How wide the range is.")
        meta = lv.metadata(t, {"youtube": {"category_id": "27"}}, readme, n_topics=66, project=data["projects"][0],
                           n_projects=6, folder_link="https://github.com/me/cl/tree/main/x", track_link="",
                           previous={"day": 6, "title": "Version B", "url": "https://youtu.be/prev"})
        self.assertEqual(meta["title"], "Day 7 · Why 30 test cases can lie: error bars | FDE First Principles")
        d = meta["description"]
        self.assertEqual(d.splitlines()[0], t["question"])
        for piece in ("Day 7 of 66 in FDE First Principles · Project 1 of 6", "▸ For an engineer: n = 30",
                      "What surprised me\nHow wide the range is.", "Maths in this topic: Standard error",
                      "Previous: Day 6 · Version B: https://youtu.be/prev", lv.COACH_REPO, "#FirstPrinciples"):
            self.assertIn(piece, d)
        self.assertNotIn("For a customer", d)
        self.assertNotIn("<", d)
        self.assertLessEqual(len(d), 4900)

    def test_article_checks(self):
        import sys
        sys.path.insert(0, str(SKILL / "scripts"))
        from fdecoach import learn
        cfg = {"learn": {"article_site": "rajc.work"}}
        self.assertEqual(learn.article_url_problem("https://rajc.work/blog/2026/10/x/", cfg), "")
        self.assertEqual(learn.article_url_problem("https://www.rajc.work/blog/x/", cfg), "")
        self.assertIn("https", learn.article_url_problem("http://rajc.work/blog/x/", cfg))
        self.assertIn("home page", learn.article_url_problem("https://rajc.work/", cfg))
        self.assertIn("not on rajc.work", learn.article_url_problem("https://notrajc.work/x", cfg))
        body = "---\ntitle: \"Hello world\"\ntags: [a, b]\n---\n\n**The setup:** …\n<!-- hidden note -->\nOne [link](https://x.y/z) here."
        self.assertEqual(learn.count_words(learn.article_body(body)), 5)    # The setup One link here


if __name__ == "__main__":
    unittest.main()
