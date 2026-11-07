"""Behaviour tests for Weekend Stage (one famous TED talk a weekend, three takes on camera).

The scenarios live in tests/features/stage.feature. Each scenario has exactly one test
here, named after it and written Given / When / Then; test_every_scenario_has_one_test_and_back
fails if the two drift apart. Dry-run like the rest of the suite: no camera, upload,
calendar or network. Run from the skill folder:

    python3 -m unittest discover -s scripts/tests -v
"""
from __future__ import annotations

import json
import plistlib
import re
import unittest
import zipfile
from pathlib import Path

from test_coach import Home  # noqa: E402  (also puts scripts/ on sys.path)

from fdecoach import stage  # noqa: E402
from fdecoach.config import CLAUDE_SKILLS, Paths, load_config  # noqa: E402

TESTS = Path(__file__).resolve().parent
FEATURE = TESTS / "features" / "stage.feature"
SKILL_DIR = TESTS.parents[1]          # fde-impromptu-coach/
REPO = SKILL_DIR.parent               # the clone's root
IN_CLONE = (REPO / "AGENTS.md").is_file() and (SKILL_DIR / "link_skills.sh").is_file()

SATURDAYS = ("2026-10-17", "2026-10-24", "2026-10-31", "2026-11-07")


def scenarios() -> list:
    return re.findall(r"^\s*Scenario: (.+?)\s*$", FEATURE.read_text(encoding="utf-8"), re.MULTILINE)


def scenario_test_name(scenario: str) -> str:
    slug = re.sub(r"['’]", "", scenario.lower())
    return "test_" + re.sub(r"[^a-z0-9]+", "_", slug).strip("_")


def slide_xml(deck_path: str) -> list:
    with zipfile.ZipFile(deck_path) as z:
        names = sorted((n for n in z.namelist() if re.match(r"ppt/slides/slide\d+\.xml$", n)),
                       key=lambda n: int(re.search(r"(\d+)", n).group(1)))
        return [z.read(n).decode() for n in names]


class StageFeature(unittest.TestCase):
    def setUp(self):
        self.h = Home()

    def tearDown(self):
        self.h.cleanup()

    def stage_state(self) -> dict:
        path = self.h.dir / "home" / "state" / "stage.json"
        return json.loads(path.read_text()) if path.exists() else {"sessions": {}}

    def record(self, *days: str) -> None:
        for day in days:
            self.h.run("stage", "session", now=f"{day}T08:30:00")

    def test_the_weekend_talk_follows_the_curriculum(self):
        # Given weeks 1 to 3 are recorded
        self.record(*SATURDAYS[:3])
        self.assertEqual([s["talk_id"] for s in self.stage_state()["sessions"].values()],
                         ["cutts-30-days", "okamoto-introduce-yourself", "treasure-speak-listen"])
        # When the next weekend's deck is built
        self.h.run("stage", "generate", now="2026-11-07T08:00:00")
        s = self.stage_state()["sessions"]["2026-11-07"]
        # Then it uses talk 4, Simon Sinek, and its Take A segment
        self.assertEqual((s["day_number"], s["talk_id"], s["talk"]["speaker"]), (4, "sinek-inspire-action", "Simon Sinek"))
        self.assertEqual(s["segment"]["label"], "The core model explanation")
        xml = slide_xml(s["deck_path"])
        self.assertIn("The core model explanation", xml[1])
        # And the deck runs Take A, Take B and Take C with a reset between each
        labels = ["TAKE A · MIRROR", "RESET", "TAKE B · MAKE IT YOURS", "RESET", "TAKE C · PRESSURE"]
        for slide, label in zip(xml[1:6], labels):
            self.assertIn(label, slide)
        for i, adv in enumerate(("15000", "180000", "20000", "150000", "20000", "120000")):
            self.assertIn(f'advTm="{adv}"', xml[i], f"slide {i + 1}")
        self.assertEqual(len(xml), 7)
        self.assertNotIn("advTm", xml[6], "the closing slide waits")

    def test_the_weekly_streak_survives_the_weekdays(self):
        # Given stage was recorded on each of the last 3 weekends, one of them on a Sunday
        self.record("2026-10-17", "2026-10-25", "2026-10-31")
        self.assertEqual(sorted(self.stage_state()["sessions"]), ["2026-10-17", "2026-10-24", "2026-10-31"])
        # When stage status runs on a Wednesday
        st = json.loads(self.h.run("stage", "status", "--json", now="2026-11-04T09:00:00").stdout)
        # Then the current streak is 3 weeks
        self.assertEqual((st["streak"]["current"], st["streak"]["unit"]), (3, "week"))
        # And this weekend is due by Sunday, with nothing broken
        self.assertEqual((st["period"], st["due"]), ("2026-11-07", "2026-11-08"))
        self.assertFalse(st["streak"]["broken"])
        self.assertIsNone(st["today"])
        top = json.loads(self.h.run("status", "--json", now="2026-11-04T09:00:00").stdout)
        self.assertEqual(top["stage"]["streak"]["current"], 3)
        self.assertEqual(top["streak"]["current"], 0, "the daily FDE streak is untouched")

    def test_a_missed_saturday_rolls_to_sunday(self):
        # Given the launchd agent runs on Saturday and Sunday mornings
        plist = plistlib.loads((self.h.dir / "agents" / "com.fdecoach.stage.plist").read_bytes())
        self.assertEqual(plist["StartCalendarInterval"], [{"Weekday": 6, "Hour": 8, "Minute": 0},
                                                          {"Weekday": 0, "Hour": 8, "Minute": 0}])
        self.assertEqual(plist["ProgramArguments"][-2:], ["stage", "daily"])
        # And Saturday ended without a recording
        sat = json.loads(self.h.run("stage", "daily", now="2026-11-07T08:00:00", answers="Later").stdout)
        self.assertTrue(sat["created"])
        # When the Sunday run fires
        sun = json.loads(self.h.run("stage", "daily", now="2026-11-08T08:00:00", answers="Later").stdout)
        # Then the same week's deck opens again instead of a new one
        self.assertFalse(sun["created"])
        self.assertEqual(sun["deck"], sat["deck"])
        sessions = self.stage_state()["sessions"]
        self.assertEqual(list(sessions), ["2026-11-07"])
        self.assertFalse(sessions["2026-11-07"]["recorded"])
        # And a calendar alert waits for Sunday evening
        store = json.loads((self.h.dir / "home" / "state" / "dryrun_calendar.json").read_text())
        alert = store["fdestage20261107"]
        self.assertEqual(alert["status"], "confirmed")
        self.assertTrue(alert["body"]["start"]["dateTime"].startswith("2026-11-08T21:30"), alert["body"]["start"])

    def test_the_prep_page_embeds_teds_player_and_never_the_words(self):
        # Given this weekend's talk
        talk = stage.talk_for_week(1)
        # When stage prep runs
        out = json.loads(self.h.run("stage", "prep", "--no-open", "--json", now="2026-11-07T07:30:00").stdout)
        page = Path(out["page"]).read_text(encoding="utf-8")
        # Then a local page shows TED's embedded player, the segment and three watch passes
        self.assertIn(f'<iframe src="{talk["embed_url"]}"', page)
        self.assertTrue(talk["embed_url"].startswith("https://embed.ted.com/talks/"))
        self.assertIn("The whole talk · 0:00–3:10", page)
        for name in ("Normal.", "Muted.", "Eyes closed."):
            self.assertIn(f"<b>{name}</b>", page)
        # And it shows Take B's prompt but not Take C's twist
        self.assertIn(talk["take_b"]["prompt"].replace("'", "&#x27;"), page)
        self.assertNotIn(talk["take_c"]["twist"].replace("'", "&#x27;"), page)
        self.assertNotIn("twist", json.dumps(self.stage_state()["sessions"]["2026-11-07"]["talk"]))
        # And the transcript is a link to ted.com, never copied
        link = f'<a href="{talk["ted_url"]}/transcript">Read the transcript on ted.com</a>'
        self.assertEqual(page.count(link), 1)
        self.assertNotIn("transcript", page.replace(link, "").lower())

    def test_a_segment_found_on_the_first_watch_is_saved(self):
        # Given week 4's segment has no times yet
        self.h.run("stage", "generate", "--talk", "sinek-inspire-action", now="2026-11-07T08:00:00")
        s = self.stage_state()["sessions"]["2026-11-07"]
        self.assertIsNone(s["segment"]["start"])
        self.assertIn("find it on your first watch", slide_xml(s["deck_path"])[1])
        # When the learner saves its start and end
        out = json.loads(self.h.run("stage", "segment", "--start", "2:05", "--end", "5:10",
                                    now="2026-11-07T08:20:00").stdout)
        self.assertTrue(out["deck_rebuilt"])
        # Then the prep page and the Take A slide show those times
        s = self.stage_state()["sessions"]["2026-11-07"]
        self.assertIn("The core model explanation · 2:05–5:10", slide_xml(s["deck_path"])[1])
        self.assertIn("The core model explanation · 2:05–5:10", Path(out["page"]).read_text(encoding="utf-8"))
        self.assertEqual(self.stage_state()["segments"]["sinek-inspire-action"], {"start": "2:05", "end": "5:10"})
        bad = self.h.run("stage", "segment", "--start", "5:10", "--end", "2:05", now="2026-11-07T08:21:00", check=False)
        self.assertEqual(bad.returncode, 2)

    def test_talks_are_links_never_text(self):
        # Given the talk catalogue
        data = stage.catalogue()
        # When it is validated
        self.assertEqual(stage.validate_catalogue(data), [])
        # Then it holds 10 talks on 10 subjects, one per week
        ts = stage.talks()
        self.assertEqual([t["week"] for t in ts], list(range(1, 11)))
        self.assertEqual(len({t["subject"] for t in ts}), 10)
        self.assertEqual(len({t["id"] for t in ts}), 10)
        # And every talk has a ted.com link, a segment, its licence, a Take B and a Take C
        self.assertEqual(data["license"]["name"], "CC BY-NC-ND 4.0")
        for t in ts:
            slug = t["ted_url"].rsplit("/", 1)[-1]
            self.assertEqual(t["embed_url"], f"https://embed.ted.com/talks/lang/en/{slug}", t["id"])
            self.assertTrue(t["segment"]["label"] and t["take_b"]["prompt"] and t["take_c"]["twist"], t["id"])
            self.assertTrue(30 <= t["take_a_seconds"] <= 300, t["id"])
        # And no talk has a transcript field and no coach note runs past 60 words
        for t in ts:
            self.assertNotIn("transcript", t)
            self.assertLessEqual(len((" ".join(t["watch_for"]) + " " + t["move"]).split()), stage.MAX_NOTE_WORDS)
        leaky = dict(data, talks=[dict(ts[0], transcript="...")] + ts[1:])
        self.assertTrue(stage.validate_catalogue(leaky), "a transcript field is refused")

    def test_video_practices_record_with_the_camera(self):
        # Given the stage practice records video
        from fdecoach import stage_session
        self.assertEqual((stage_session.SPEC.media, stage_session.SPEC.cadence), ("video", "weekly"))
        # When a session runs
        proc = self.h.run("stage", "session", now="2026-11-07T08:30:00")
        s = self.stage_state()["sessions"]["2026-11-07"]
        # Then QuickTime records the camera into the stage recordings folder
        self.assertIn("QuickTime: new movie recording", proc.stderr)
        video = Path(s["video_path"])
        self.assertEqual((video.parent, video.name), (self.h.dir / "movies" / "stage", "2026-11-07_Stage_Week1.mov"))
        self.assertTrue(video.exists())
        # And no slides-plus-audio video is assembled
        self.assertEqual(list(video.parent.glob("*.mp4")), [])
        self.assertNotIn("audio_path", s)
        # And the week is marked recorded
        self.assertTrue(s["recorded"])
        st = json.loads(self.h.run("stage", "status", "--json", now="2026-11-08T10:00:00").stdout)
        self.assertTrue(st["today"]["recorded"])
        self.assertEqual(st["today"]["twist"], s["twist"], "the twist shows once the week is recorded")

    def test_nothing_from_ted_reaches_youtube(self):
        # Given a recorded stage session
        proc = self.h.run("stage", "session", now="2026-11-07T08:30:00")
        s = self.stage_state()["sessions"]["2026-11-07"]
        # When its upload is prepared
        self.assertEqual(s["youtube"]["status"], "uploaded")
        uploaded = re.findall(r"\[dry-run\] YouTube upload (\S+):", proc.stderr)
        # Then the uploaded file is the camera recording
        self.assertEqual(uploaded, [Path(s["video_path"]).name])
        # And the description credits TED under CC BY-NC-ND 4.0 with the talk's link
        from fdecoach import stage_session
        cfg = load_config(Paths(self.h.dir / "unused"))
        meta = stage_session.build_metadata(s, cfg, stage_session.chapters(s, cfg, 1.0), streak=1)
        desc = meta["snippet"]["description"]
        self.assertIn("CC BY-NC-ND 4.0", desc)
        self.assertIn(s["talk"]["ted_url"], desc)
        self.assertIn("contains no TED audio or video", desc)
        self.assertEqual(meta["snippet"]["title"], "Weekend Stage · Week 1 · Matt Cutts")
        self.assertIn("0:16 Take A · Mirror", desc)
        # And the video is private
        self.assertEqual(meta["status"]["privacyStatus"], "private")

    @unittest.skipUnless(IN_CLONE, "needs a clone of the repo (the deployed copy has no skills/ or AGENTS.md)")
    def test_stage_is_a_real_skill(self):
        # Given the skills in this repo
        skill = REPO / "skills" / "stage" / "SKILL.md"
        self.assertTrue(skill.is_file())
        # When link_skills.sh, CLAUDE_SKILLS and AGENTS.md are compared
        linker = (SKILL_DIR / "link_skills.sh").read_text(encoding="utf-8")
        agents = (REPO / "AGENTS.md").read_text(encoding="utf-8")
        # Then each of them names stage
        self.assertIn("stage:skills/stage", linker)
        self.assertIn("stage", CLAUDE_SKILLS)
        self.assertIn("| `stage` | `/stage [", agents)
        # And /stage with no arguments starts a detached session
        row = next(line for line in skill.read_text(encoding="utf-8").splitlines() if line.startswith("| empty"))
        self.assertIn("`fde-coach stage session --detach`", row)

    def test_every_scenario_has_one_test_and_back(self):
        wanted = {scenario_test_name(s) for s in scenarios()} | {"test_every_scenario_has_one_test_and_back"}
        have = {n for n in dir(self) if n.startswith("test_")}
        self.assertEqual(wanted - have, set(), "scenarios without a test")
        self.assertEqual(have - wanted, set(), "tests without a scenario")


class TestWeeklyStreakLogic(unittest.TestCase):
    """The weekly streak in isolation (state.weekly_streaks), without the CLI."""

    def test_weekends_count_and_a_missed_one_breaks_it(self):
        import datetime as dt
        import shutil
        import tempfile
        from fdecoach.state import History, period_start, streaks
        tmp = Path(tempfile.mkdtemp())
        try:
            hist = History(Paths(tmp), file=tmp / "stage.json", cadence="weekly")
            for d in ("2026-10-03", "2026-10-17", "2026-10-24"):
                hist.put({"date": d, "recorded": True})
            self.assertEqual(period_start(dt.date(2026, 10, 25), "weekly"), dt.date(2026, 10, 24), "Sunday")
            self.assertEqual(period_start(dt.date(2026, 10, 19), "weekly"), dt.date(2026, 10, 24), "Monday")
            st = streaks(hist, dt.date(2026, 10, 28))
            self.assertEqual((st["current"], st["best"], st["total"]), (2, 2, 3))
            self.assertFalse(st["recorded_this_week"])
            gone = streaks(hist, dt.date(2026, 11, 9))
            self.assertEqual(gone["current"], 0)
            self.assertTrue(gone["broken"])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
