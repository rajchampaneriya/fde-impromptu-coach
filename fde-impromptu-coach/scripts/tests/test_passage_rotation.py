"""Evals for passage rotation, passage feedback and the legato / pronunciation banks.

The scenarios live in tests/features/passage_rotation.feature. Each has exactly one test in
PassageRotationFeature, named after it and written Given / When / Then;
test_every_scenario_has_one_test_and_back fails if the two drift apart. The checkers and the
in-process driver live in passage_evals.py.

Two kinds of test, so the evals measure the intent rather than one implementation:

* **PassageRotationFeature** runs the real skill: practice.ensure_today (the CLI's path) in-process
  for the long simulations, the CLI itself for replace, capture, cross-process state and migration.
  Tests marked @pending(step) are red until that fix step lands: a failing assertion is reported
  as a skip naming the step and the first failure, a pass fails the run until the marker is
  removed, and any other exception is an error (a bug in the eval). FDE_EVALS_STRICT=1 runs them
  as plain tests.
* **TestEvalHarness** proves each checker before it is trusted: it must flag the learner's real
  logs and known-bad selectors, and pass a reference selector built to the fix plan. That is how we
  know a green eval means "fixed" and not "the eval can't see the bug".

No audio is read or produced: inputs are state JSON, passage text, config and source code.
Run from the skill folder:

    python3 -m unittest discover -s scripts/tests -p "test_passage_rotation.py" -v

Re-record the regression baseline only for an intended change:

    python3 scripts/tests/test_passage_rotation.py record-baseline
"""
from __future__ import annotations

import collections
import datetime as dt
import functools
import hashlib
import json
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from test_coach import Home  # noqa: E402  (also puts scripts/ on sys.path)

import passage_evals as E  # noqa: E402
from fdecoach import audio, legato, library, practice  # noqa: E402

TESTS = Path(__file__).resolve().parent
FEATURE = TESTS / "features" / "passage_rotation.feature"
FIXTURES = TESTS / "fixtures"
BACKUP = FIXTURES / "backup_state"
BASELINE = FIXTURES / "regression" / "baseline.json"
SKILL_DIR = TESTS.parents[1]
ASSETS = SKILL_DIR / "assets"
PROMPTS = ASSETS / "legato_prompts.json"
BUILD_TOOL = SKILL_DIR / "scripts" / "tools" / "build_passage_library.py"
SOURCES_CACHE = os.environ.get("FDE_PASSAGE_SOURCES_CACHE", "")
STRICT = os.environ.get("FDE_EVALS_STRICT") == "1"

DAY = dt.date(2026, 12, 1)
INDIA_CFG = {"legato": {"themes": ["india"]}, "pronunciation": {"themes": ["india"]}}
PINNED = {"legato": ["dickens-best-of-times", "aps-take-time", "woolf-flowers"],
          "pronunciation": ["douglass-twelve", "carroll-rabbit", "muir-sierra-day"]}


def scenarios() -> list:
    return re.findall(r"^\s*Scenario: (.+?)\s*$", FEATURE.read_text(encoding="utf-8"), re.MULTILINE)


def scenario_test_name(scenario: str) -> str:
    slug = re.sub(r"['’]", "", scenario.lower())
    return "test_" + re.sub(r"[^a-z0-9]+", "_", slug).strip("_")


def pending(step: str):
    """Red until fix step `step` lands (see the docstring at the top)."""
    def deco(fn):
        if STRICT:
            return fn

        @functools.wraps(fn)
        def wrapper(self):
            try:
                fn(self)
            except AssertionError as exc:
                first = (str(exc).strip().splitlines() or ["assertion failed"])[0][:240]
                raise unittest.SkipTest(f"RED until fix step {step}: {first}")
            self.fail(f"pending eval now passes: remove @pending({step!r}) from {fn.__name__}")
        wrapper.pending_step = step
        return wrapper
    return deco


def india() -> list:
    return [p["id"] for p in library.by_theme(library.builtin(), ["india"])]


def days(start: dt.date, n: int) -> list:
    return [start + dt.timedelta(days=i) for i in range(n)]


def summary(violations: list) -> str:
    kinds = collections.Counter(v.kind for v in violations)
    return f"{dict(kinds)}; first: {violations[0]}" if violations else "none"


def spread_text(s: dict) -> str:
    return (f"{s['passages']} passages, mean {s['mean']:.2f}, counts {s['min']}-{s['max']}, "
            f"worst {s['max_dev']:.2f} from the mean, {s['within_1']:.0%} within 1")


class CoachCase(unittest.TestCase):
    def coach(self, config=None, state_from=None) -> E.Coach:
        tmp = Path(tempfile.mkdtemp(prefix="fdecoach-eval-"))
        c = E.Coach(tmp, config=config, state_from=state_from)
        self.addCleanup(shutil.rmtree, tmp, True)
        self.addCleanup(c.close)
        return c

    def home(self, claude: bool = True) -> Home:
        h = Home(claude=claude)
        self.addCleanup(h.cleanup)
        return h


def home_state(h: Home, key: str) -> dict:
    f = h.dir / "home" / "state" / E.STATE_FILES[key]
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {"sessions": {}}


# =========================================================================== the scenarios

class PassageRotationFeature(CoachCase):
    longMessage = False      # a red eval reports its own one-line reason, not a 100-line diff

    # ----------------------------------------------------------------------- E1 near-term repeats

    @pending("2-3 (one seen-log, tiered pick) and 8 (168-passage bank)")
    def test_nothing_repeats_within_60_sessions_or_across_practices_within_30_days(self):
        # Given the learner's backed-up history of 30 legato and 40 pronunciation sessions
        c = self.coach(state_from=BACKUP)
        start = E.first_day_after(BACKUP)
        # When both practices run every day for the next 365 days
        c.run_days(start, 365)
        # Then no passage repeats within 60 sessions, across practices within 30 days, or on one day
        bad = E.near_term_repeats(c.reads(), since=start)
        self.assertEqual(bad, [], f"{len(bad)} near-term repeats in 730 sessions: {summary(bad)}")

    def test_a_small_pool_is_read_in_full_before_anything_repeats(self):
        # Given both practices read only the 6 India-themed passages
        pool = india()
        self.assertEqual(len(pool), 6, "fixture assumption: 6 India-themed passages")
        c = self.coach(INDIA_CFG)
        # When both practices run for 3 days
        c.run_days(DAY, 3)
        served = [r.pid for r in c.reads() if not r.replaced]
        # Then the 6 reads are 6 different passages
        self.assertEqual(E.served_before_pool_exhausted(c.reads(), pool), [], f"served in order: {served}")
        self.assertEqual(sorted(served), sorted(pool))

    # ----------------------------------------------------------------------- E2 fair rotation

    def test_every_passage_gets_its_turn(self):
        # Given a new learner who gives no feedback
        c = self.coach()
        # When both practices run every day for 420 days
        c.run_days(DAY, 420)
        # Then in each practice every eligible passage is served within 1 of the mean
        unfair = []
        for key in E.PRACTICES:
            pool = [p["id"] for p in E.eligible(library.builtin(), key)]
            s = E.rotation_spread(c.reads(), key, pool)
            if s["max_dev"] > 1.0:
                unfair.append(f"{key}: {spread_text(s)}")
        self.assertEqual(unfair, [], "; ".join(unfair))

    def test_fair_rotation_survives_feedback_and_level_changes(self):
        # Given a new learner who taps Choppy, Mostly smooth or Smooth at random
        # And flags 3% of passages read recently, 3% not useful and 10% too easy
        c = self.coach()
        rng = random.Random(20261201)
        # When both practices run every day for 420 days
        for day in days(DAY, 420):
            for key in ("pronunciation", "legato"):
                tap = rng.choice(["Choppy", "Mostly smooth", "Smooth"]) if key == "legato" else None
                c.session(key, day, answers=tap)
                x = rng.random()
                label = "repeated" if x < 0.03 else "unhelpful" if x < 0.06 else "too_easy" if x < 0.16 else ""
                if label:
                    c.flag(key, day, label)
        # Then at least 90% of the passages not flagged away are within 1 of the mean, none more than 2
        reads = c.reads()
        away = {r.pid for r in reads if {"repeated", "unhelpful"} & set(r.feedback)}
        unfair = []
        for key in E.PRACTICES:
            pool = [p["id"] for p in E.eligible(library.builtin(), key) if p["id"] not in away]
            s = E.rotation_spread(reads, key, pool)
            if s["within_1"] < 0.90 or s["max_dev"] > 2.0:
                unfair.append(f"{key}: {spread_text(s)}")
        self.assertEqual(unfair, [], "; ".join(unfair))

    # ----------------------------------------------------------------------- E3 feedback

    def test_read_it_recently_and_not_useful_keep_a_passage_away(self):
        # Given the learner's backed-up history
        c = self.coach(state_from=BACKUP)
        today = E.first_day_after(BACKUP) - dt.timedelta(days=1)
        leg = c.state("legato")["sessions"][today.isoformat()]["passage_id"]
        pron = c.state("pronunciation")["sessions"][today.isoformat()]["passage_id"]
        # And today's legato passage is flagged read it recently and today's pronunciation passage not useful
        c.flag("legato", today, "repeated")
        c.flag("pronunciation", today, "unhelpful")
        # When both practices run every day for the next 365 days
        c.run_days(today + dt.timedelta(days=1), 365)
        # Then the first is served in neither practice for 120 days, the second for 365 days
        bad = E.excluded_but_served(c.reads())
        msg = "; ".join(f"{f.pid} flagged {f.feedback} on {f.date} came back in {r.practice} on {r.date}"
                        for f, r in bad[:3])
        self.assertEqual(bad, [], f"{len(bad)} serves inside an exclusion window ({leg}, {pron}): {msg}")

    def test_a_too_easy_passage_goes_to_the_back_of_the_queue(self):
        # Given pronunciation reads only the 6 India-themed passages and has read all 6 once
        pool = india()
        c = self.coach(INDIA_CFG)
        for day in days(DAY, 6):
            c.session("pronunciation", day)
        first_cycle = [s["passage_id"] for s in c.sessions("pronunciation")]
        self.assertEqual(sorted(first_cycle), sorted(pool), "precondition: one full cycle")
        # And the learner flagged the first of them too easy
        flagged = first_cycle[0]
        c.flag("pronunciation", DAY, "too_easy")
        # When the next 6 pronunciation sessions run
        for day in days(DAY + dt.timedelta(days=6), 6):
            c.session("pronunciation", day)
        second = [s["passage_id"] for s in c.sessions("pronunciation")][6:]
        # Then the flagged passage comes back only after the other 5
        self.assertEqual(E.too_easy_not_deprioritised(c.reads(), pool), [],
                         f"{flagged} was flagged too easy; the next cycle served {second}")
        self.assertEqual(sorted(second[:5]), sorted(set(pool) - {flagged}), f"next cycle: {second}")

    def test_a_replaced_passage_does_not_come_straight_back(self):
        h = self.home()
        day = "2026-10-01"
        # Given today's legato deck is built
        h.run("legato", "generate", now=f"{day}T05:59:00")
        first = home_state(h, "legato")["sessions"][day]["passage_id"]
        # When the learner asks for a different passage twice
        h.run("legato", "generate", "--replace", now=f"{day}T06:00:00")
        second = home_state(h, "legato")["sessions"][day]["passage_id"]
        h.run("legato", "generate", "--replace", now=f"{day}T06:01:00")
        s = home_state(h, "legato")["sessions"][day]
        third = s["passage_id"]
        # Then each new passage differs from every earlier one that day
        self.assertEqual(len({first, second, third}), 3, f"passages after two replaces: {first}, {second}, {third}")
        # And today's session lists the replaced passages, which count as served
        self.assertEqual(s.get("replaced"), [first, second])
        served = {r.pid for r in E.reads_from_sessions({"legato": home_state(h, "legato")["sessions"]})}
        self.assertEqual(served, {first, second, third})

    def test_choppy_flow_never_raises_the_legato_level(self):
        # Given a learner who taps Choppy after every legato session for 25 days
        c = self.coach()
        for day in days(DAY, 25):
            # When each next deck is built
            c.session("legato", day, answers="Choppy")
        # Then the flow level never rises within 3 sessions of a Choppy tap
        ss = c.sessions("legato")
        bad = E.flow_rises_after_choppy(ss)
        self.assertEqual(bad, [], f"{bad[:1]}; levels {[s.get('flow_level') for s in ss]}")

    def test_passage_feedback_is_captured_from_the_dialog_and_the_command_line(self):
        h = self.home()
        # Given a legato session ends with the taps Choppy and Read it recently
        h.run("legato", "session", now="2026-10-01T06:00:00", answers="Choppy,Read it recently")
        # And the learner runs pronounce passage --flag too-easy after today's pronunciation deck is built
        h.run("pronounce", "generate", now="2026-10-01T06:30:00")
        flag = h.run("pronounce", "passage", "--flag", "too-easy", now="2026-10-01T06:31:00", check=False)
        leg = home_state(h, "legato")["sessions"]["2026-10-01"]
        pron = home_state(h, "pronunciation")["sessions"]["2026-10-01"]
        # Then legato stores passage_feedback repeated next to the flow tap
        self.assertEqual((leg.get("feedback"), leg.get("passage_feedback")), ("Choppy", ["repeated"]))
        # And pronunciation stores passage_feedback too_easy
        self.assertEqual(flag.returncode, 0, f"pronounce passage --flag failed: {flag.stderr.strip()[-200:]}")
        self.assertEqual(pron.get("passage_feedback"), ["too_easy"])

    # ----------------------------------------------------------------------- E4 state persists

    def test_one_practice_sees_what_the_other_already_served(self):
        h = self.home()
        h.run("config", "--set", 'legato.themes=["india"]', "--set", 'pronunciation.themes=["india"]',
              now="2026-10-01T05:00:00")
        # Given both practices read only the 6 India-themed passages
        # And pronunciation read 5 of them on 5 days, each in its own process
        for day in days(dt.date(2026, 10, 1), 5):
            h.run("pronounce", "generate", now=f"{day}T05:45:00")
        read = {s["passage_id"] for s in home_state(h, "pronunciation")["sessions"].values()}
        unread = set(india()) - read
        self.assertEqual(len(unread), 1, f"precondition: pronunciation read 5 different passages, got {read}")
        # When a new process builds the next legato deck
        h.run("legato", "generate", now="2026-10-06T06:00:00")
        s = home_state(h, "legato")["sessions"]["2026-10-06"]
        # Then legato serves the one passage neither practice has read
        self.assertEqual(s["passage_id"], unread.pop(), f"legato served {s['passage_id']}, read in pronunciation")
        # And legato.json records the passage id and the selection tier T0
        self.assertEqual((s.get("selection") or {}).get("tier"), "T0")

    def test_migration_keeps_every_existing_session(self):
        h = self.home()
        root = h.dir / "home"
        state = root / "state"
        # Given the learner's backed-up state and settings, including the light audio clean-up
        for name in E.STATE_FILES.values():
            shutil.copy(BACKUP / name, state / name)
        cfg = json.loads((root / "config.json").read_text(encoding="utf-8"))
        cfg = E._merge(cfg, json.loads((BACKUP / "config.json").read_text(encoding="utf-8")))
        (root / "config.json").write_text(json.dumps(cfg, indent=1), encoding="utf-8")
        original = {n: (state / n).read_bytes() for n in E.STATE_FILES.values()}
        # When fde-coach migrate runs twice
        first = h.run("migrate", now="2026-11-08T05:00:00", check=False)
        self.assertEqual(first.returncode, 0, f"fde-coach migrate failed: {first.stderr.strip()[-200:]}")
        after_first = {n: (state / n).read_bytes() for n in E.STATE_FILES.values()}
        h.run("migrate", now="2026-11-08T05:01:00")
        # Then a state.backup folder holds the original files unchanged
        backups = sorted(root.glob("state.backup-*"))
        self.assertEqual(len(backups), 1, f"backups: {[b.name for b in backups]}")
        for name, raw in original.items():
            self.assertEqual((backups[0] / name).read_bytes(), raw, name)
        # And every original session keeps every field and value
        for name, raw in original.items():
            before = json.loads(raw)["sessions"]
            after = json.loads(after_first[name])["sessions"]
            self.assertEqual(sorted(after), sorted(before), f"{name}: sessions added or lost")
            for day, s in before.items():
                kept = {k: after[day].get(k) for k in s}
                self.assertEqual(kept, s, f"{name} {day}: a field changed")
        # And every legato session gains a response_prompt_id that names its prompt
        self.assertTrue(PROMPTS.exists(), "assets/legato_prompts.json is missing")
        prompts = {p["id"]: p["text"] for p in json.loads(PROMPTS.read_text(encoding="utf-8"))["prompts"]}
        for day, s in json.loads(after_first["legato.json"])["sessions"].items():
            self.assertEqual(prompts.get(s.get("response_prompt_id")), s["response_prompt"], day)
        # And the second run changes nothing
        for name, raw in after_first.items():
            self.assertEqual((state / name).read_bytes(), raw, f"{name} changed on the second run")
        # And the next legato deck keeps the learner's flow level
        last = json.loads(original["legato.json"])["sessions"]
        last_level = last[max(last)]["flow_level"]
        h.run("legato", "generate", now="2026-11-08T06:00:00")
        self.assertEqual(home_state(h, "legato")["sessions"]["2026-11-08"]["flow_level"], last_level)
        # And legato and pronunciation audio clean-up is none
        cfg = json.loads((root / "config.json").read_text(encoding="utf-8"))
        self.assertEqual((cfg["legato"]["audio_clean_preset"], cfg["pronunciation"]["audio_clean_preset"]),
                         ("none", "none"))

    # ----------------------------------------------------------------------- E5 bank size and coverage

    @pending("8 (168-passage bank, tagged by practice)")
    def test_the_passage_bank_is_big_enough_and_varied(self):
        # When the passage library is loaded
        lib = library.builtin()
        problems = []
        # Then it has at least 150 passages and each practice at least 120 eligible
        if len(lib) < E.MIN_UNIQUE:
            problems.append(f"{len(lib)} passages (need {E.MIN_UNIQUE})")
        for key in E.PRACTICES:
            pool = E.eligible(lib, key)
            if len(pool) < E.MIN_ELIGIBLE:
                problems.append(f"{len(pool)} {key}-eligible (need {E.MIN_ELIGIBLE})")
            # And each practice has at least 20% of its pool at each level
            shares = E.level_shares(pool, lambda p: p.get("level"))
            thin = {lvl: f"{s:.1%}" for lvl, s in shares.items() if s < E.MIN_LEVEL_SHARE}
            if thin:
                problems.append(f"{key} levels under 20%: {thin}")
        # And no two passages share an id, a near-duplicate text or a target word
        problems += E.bank_problems(lib)
        self.assertEqual(problems, [], "; ".join(problems[:6]))

    def test_the_legato_prompt_bank_is_big_enough_and_rotates(self):
        # When the legato prompt bank is loaded
        self.assertTrue(PROMPTS.exists(), "assets/legato_prompts.json is missing")
        prompts = json.loads(PROMPTS.read_text(encoding="utf-8"))["prompts"]
        texts = [p["text"] for p in prompts]
        # Then it has at least 42 different prompts, 6 of each type and 14 at each level
        problems = []
        if len(prompts) < 42:
            problems.append(f"{len(prompts)} prompts (need 42)")
        if len({p["id"] for p in prompts}) != len(prompts):
            problems.append("duplicate prompt ids")
        problems += [f"near-duplicate prompt: {t!r}" for i, t in enumerate(texts) if E.is_duplicate(t, texts[:i])]
        types = collections.Counter(p.get("type") for p in prompts)
        levels = collections.Counter(p.get("level") for p in prompts)
        problems += [f"type {t}: {types[t]} prompts (need 6)" for t in E.PROMPT_TYPES if types[t] < 6]
        problems += [f"level {lvl}: {levels[lvl]} prompts (need 14)" for lvl in (1, 2, 3) if levels[lvl] < 14]
        # And its first 7 are today's prompts, word for word
        if texts[:7] != list(legato.RESPONSE_PROMPTS):
            problems.append("the first 7 prompts differ from legato.RESPONSE_PROMPTS")
        self.assertEqual(problems, [], "; ".join(problems[:6]))
        # And over 60 legato sessions no prompt comes back within 14 sessions
        c = self.coach()
        for day in days(DAY, 60):
            c.session("legato", day)
        ss = c.sessions("legato")
        ids = {p["id"] for p in prompts}
        self.assertTrue(all(s.get("response_prompt_id") in ids for s in ss), "sessions without a bank prompt id")
        bad = E.prompt_repeats(ss)
        self.assertEqual(bad, [], f"{len(bad)} prompt repeats: {bad[:2]}")

    # ----------------------------------------------------------------------- E6 content quality

    @pending("7-8 (practice tags, abbreviation fix, new passages)")
    def test_legato_passages_carry_connected_speech_features(self):
        # When every legato-eligible passage is analysed as text
        pool = E.eligible(library.builtin(), "legato")
        # Then each has 6 links, 3 drill chains, 2 elision sites, 4-14 word breath groups, no abbreviation mark
        bad = {p["id"]: E.legato_quality_failures(p) for p in pool}
        bad = {k: v for k, v in bad.items() if v}
        example = next(iter(bad.items()), None)
        self.assertEqual(bad, {}, f"{len(bad)} of {len(pool)} legato passages fall short, e.g. {example}")

    @pending("8 (pronunciation level and intonation on every passage)")
    def test_pronunciation_passages_carry_contrasts_and_stress_or_intonation_patterns(self):
        # When every pronunciation-eligible passage is checked
        pool = E.eligible(library.builtin(), "pronunciation")
        # Then it has 5 target words in the text, 2 contrast or stress labels, 1 intonation pattern, a level
        bad = {p["id"]: E.pron_quality_failures(p) for p in pool}
        bad = {k: v for k, v in bad.items() if v}
        example = next(iter(bad.items()), None)
        self.assertEqual(bad, {}, f"{len(bad)} of {len(pool)} pronunciation passages fall short, e.g. {example}")
        # And each pronunciation level holds at least 20% of the pool
        shares = E.level_shares(pool, E.pron_level)
        self.assertTrue(all(s >= E.MIN_LEVEL_SHARE for s in shares.values()), f"level shares {shares}")

    # ----------------------------------------------------------------------- E7 schema validity

    def test_every_passage_passes_the_schema_and_source_checks(self):
        # When the passage library and its source spec are loaded
        lib = library.builtin()
        spec = json.loads((ASSETS / "passage_sources.json").read_text(encoding="utf-8"))
        # Then every passage has the fields and limits the library tests require
        self.assertEqual([x["id"] for x in spec["passages"]], [p["id"] for p in lib], "spec and asset disagree")
        for p in lib:
            self.assertTrue(library.MIN_WORDS <= len(p["text"].split()) <= library.MAX_WORDS, p["id"])
            self.assertEqual(p["words"], len(p["text"].split()), p["id"])
            self.assertIn(p["level"], (1, 2, 3), p["id"])
            self.assertLess(int(p["year"]), 1929, p["id"])
            self.assertRegex(p["source"]["url"], r"^https://(standardebooks\.org/ebooks/|www\.gutenberg\.org/ebooks/\d+$)")
            notes = p.get("pronunciation") or {}
            self.assertEqual(len(notes.get("target_words", [])), 5, p["id"])
            # And the optional practices, level and intonation fields hold allowed values
            if "practices" in p:
                self.assertTrue(p["practices"] and set(p["practices"]) <= set(E.PRACTICES), p["id"])
            if "level" in notes:
                self.assertIn(notes["level"], (1, 2, 3), p["id"])
            if "intonation" in notes:
                self.assertLessEqual(set(notes["intonation"]), E.INTONATION, p["id"])
        by_id = {p["id"]: p for p in lib}
        for x in spec["passages"]:
            if "practices" in x:
                self.assertEqual(by_id[x["id"]].get("practices"), x["practices"], f"{x['id']}: build dropped practices")
        # And with a source cache configured every passage matches its book verbatim
        if SOURCES_CACHE:
            proc = subprocess.run([sys.executable, "-I", str(BUILD_TOOL), "verify", "--cache", SOURCES_CACHE],
                                  capture_output=True, text=True, timeout=1800)
            self.assertEqual(proc.returncode, 0, (proc.stdout + proc.stderr)[-400:])

    # ----------------------------------------------------------------------- E8 no audio treatment

    def test_legato_and_pronunciation_apply_no_audio_filter(self):
        # Given the default settings
        c = self.coach()
        problems = []
        for key in E.PRACTICES:
            src = c.workdir / f"{key}_take.m4a"
            src.write_bytes(b"")                     # a placeholder path; never decoded
            commands = []

            def fake_run(cmd, *a, **k):
                commands.append(list(cmd))
                Path(cmd[-1]).write_bytes(b"\0")
                return subprocess.CompletedProcess(cmd, 0, "", "")
            # When the audio for a legato and a pronunciation video is prepared
            with mock.patch.object(audio, "ffmpeg_path", return_value="/usr/local/bin/ffmpeg"), \
                    mock.patch.object(audio.subprocess, "run", side_effect=fake_run):
                used = practice._audio_for_video({"audio_path": str(src)}, c.ctx.cfg, practice.spec_for(key))
            # Then no ffmpeg command filters the audio
            for cmd in E.audio_filter_commands(commands):
                problems.append(f"{key}: {' '.join(cmd[cmd.index('-af'):cmd.index('-af') + 2]) if '-af' in cmd else cmd}")
            # And the recording goes into the video as it was
            if Path(used) != src:
                problems.append(f"{key}: the video uses {Path(used).name}, not the recording")
        self.assertEqual(problems, [], "; ".join(problems))

    def test_passage_selection_content_and_evals_use_no_audio(self):
        # When the selection, content and eval modules are read
        modules = [SKILL_DIR / "scripts" / "fdecoach" / n for n in ("library.py", "legato.py", "pronounce.py")]
        modules.append(TESTS / "passage_evals.py")
        # Then none imports an audio library or the skill's audio module
        found = {m.name: E.audio_imports(m.read_text(encoding="utf-8")) for m in modules}
        self.assertEqual({k: v for k, v in found.items() if v}, {})
        # And every eval fixture is JSON or Markdown
        others = [str(f.relative_to(FIXTURES)) for f in FIXTURES.rglob("*")
                  if f.is_file() and f.suffix not in (".json", ".md")]
        self.assertEqual(others, [])

    # ----------------------------------------------------------------------- E9 regression

    def test_impromptu_questions_are_chosen_as_before(self):
        # Given a new learner with no Claude / When impromptu decks are built for 7 days
        got = impromptu_snapshot()
        # Then each day's questions match the recorded baseline
        self.assertEqual(got, baseline()["impromptu"])

    def test_a_pinned_passage_is_served_as_before(self):
        # When legato and pronunciation decks are built with --passage for 3 passages each
        got = pinned_snapshot()
        # Then the passage text, drill chains and word notes match the recorded baseline
        self.assertEqual(got, baseline()["pinned"])

    def test_skill_evals_1_to_8_are_unchanged(self):
        # When evals/evals.json is loaded / Then evals 1 to 8 match the recorded baseline
        self.assertEqual(skill_evals_digest(), baseline()["skill_evals_1_8_sha256"])

    def test_every_scenario_has_one_test_and_back(self):
        wanted = {scenario_test_name(s) for s in scenarios()} | {"test_every_scenario_has_one_test_and_back"}
        have = {n for n in dir(self) if n.startswith("test_")}
        self.assertEqual(wanted - have, set(), "scenarios without a test")
        self.assertEqual(have - wanted, set(), "tests without a scenario")


# =========================================================================== regression baseline

def baseline() -> dict:
    return json.loads(BASELINE.read_text(encoding="utf-8"))


def impromptu_snapshot() -> dict:
    h = Home(claude=False)
    try:
        out = {}
        for day in days(dt.date(2026, 10, 1), 7):
            h.run("generate", now=f"{day}T05:00:00")
            s = h.history()["sessions"][day.isoformat()]
            out[day.isoformat()] = [{k: q.get(k) for k in ("id", "category", "format", "difficulty", "audience",
                                                              "constraint", "text")} for q in s["questions"]]
        return out
    finally:
        h.cleanup()


def pinned_snapshot() -> dict:
    tmp = Path(tempfile.mkdtemp(prefix="fdecoach-eval-"))
    c = E.Coach(tmp)
    try:
        out = {"legato": {}, "pronunciation": {}}
        for i, pid in enumerate(PINNED["legato"]):
            s = c.generate("legato", DAY + dt.timedelta(days=i), passage_id=pid)
            out["legato"][pid] = {"paragraph": s["paragraph"], "chains": s["chains"],
                                  "level": s["passage"].get("level")}
        for i, pid in enumerate(PINNED["pronunciation"]):
            s = c.generate("pronunciation", DAY + dt.timedelta(days=i), passage_id=pid)
            out["pronunciation"][pid] = {"paragraph": s["paragraph"], "words": s.get("words"),
                                         "target_words": s.get("target_words"), "focus_sounds": s.get("focus_sounds")}
        return out
    finally:
        c.close()
        shutil.rmtree(tmp, ignore_errors=True)


def skill_evals_digest() -> str:
    evals = json.loads((SKILL_DIR / "evals" / "evals.json").read_text(encoding="utf-8"))["evals"]
    first8 = [e for e in evals if int(e["id"]) <= 8]
    return hashlib.sha256(json.dumps(first8, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def record_baseline() -> None:
    BASELINE.parent.mkdir(parents=True, exist_ok=True)
    data = {"recorded_on_commit": os.environ.get("BASELINE_COMMIT", ""),
            "impromptu": impromptu_snapshot(), "pinned": pinned_snapshot(),
            "skill_evals_1_8_sha256": skill_evals_digest()}
    BASELINE.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {BASELINE}")


# =========================================================================== proving the checkers

def synthetic_pool(n_both: int, n_legato: int = 0, n_pron: int = 0) -> list:
    pool = [{"id": f"p{i:03d}", "practices": ("legato", "pronunciation")} for i in range(n_both)]
    pool += [{"id": f"l{i:03d}", "practices": ("legato",)} for i in range(n_legato)]
    pool += [{"id": f"r{i:03d}", "practices": ("pronunciation",)} for i in range(n_pron)]
    return pool


def simulate(select, pool: list, n_days: int, start: dt.date = DAY, flag=None) -> list:
    reads: list = []
    for day in days(start, n_days):
        for key in ("pronunciation", "legato"):
            pid = select(pool, reads, key, day)
            reads.append(E.Read(day, key, pid, True, tuple(flag(key, day, pid) if flag else ())))
    return reads


def per_practice_fresh_first(pool, reads, key, day):
    """Today's bug: each practice remembers only its own reads."""
    mine = [r for r in reads if r.practice == key]
    last = {r.pid: i for i, r in enumerate(mine)}
    elig = [p["id"] for p in pool if key in p["practices"]]
    return min(elig, key=lambda p: (p in last, last.get(p, -1), p))


def stateless_pick(pool, reads, key, day):
    return random.Random(f"{day}:{key}").choice([p["id"] for p in pool if key in p["practices"]])


def lowest_id_cooled(pool, reads, key, day):
    """Never too soon, but always the lowest id it can: unfair."""
    last_any = {r.pid: r.date for r in reads}
    elig = [p["id"] for p in pool if key in p["practices"]]
    cooled = [p for p in elig if p not in last_any or (day - last_any[p]).days >= E.COOLDOWN_DAYS]
    return min(cooled or elig)


def reference_pick(pool, reads, key, day):
    """The fix plan's selection in a dozen lines: one seen-log, tiers, exclusions, fairness, penalty."""
    elig = [p["id"] for p in pool if key in p["practices"]]
    blocked = {r.pid for r in reads for lab, d in E.EXCLUDE_DAYS.items()
               if lab in r.feedback and (day - r.date).days < d}
    elig = [p for p in elig if p not in blocked] or elig
    last_any = {r.pid: r.date for r in reads}
    mine_days = sorted({r.date for r in reads if r.practice == key})
    idx = {d: i for i, d in enumerate(mine_days)}
    last_here = {r.pid: idx[r.date] for r in reads if r.practice == key}
    count = collections.Counter(r.pid for r in reads if r.practice == key)
    easy = {r.pid for r in reads if r.practice == key and "too_easy" in r.feedback}
    cooled = lambda p: p not in last_any or (day - last_any[p]).days >= E.COOLDOWN_DAYS  # noqa: E731
    far = lambda p: p not in last_here or len(mine_days) - last_here[p] >= E.RECENT_SESSIONS  # noqa: E731
    tiers = [[p for p in elig if p not in last_any], [p for p in elig if p not in last_here and cooled(p)],
             [p for p in elig if cooled(p) and far(p)], [p for p in elig if cooled(p)], elig]
    cand = next(t for t in tiers if t)
    low = min(count[p] for p in cand)
    cand = [p for p in cand if count[p] == low]
    return min(cand, key=lambda p: (p in easy, last_here.get(p, -1), last_any.get(p, dt.date.min), p))


class TestEvalHarness(unittest.TestCase):
    """Each checker must flag what it is meant to catch and pass what it is meant to allow."""

    def fixture_reads(self) -> list:
        return E.reads_from_state_dir(BACKUP)

    # E1
    def test_repeat_checker_finds_the_learners_12_cross_practice_repeats(self):
        bad = E.near_term_repeats(self.fixture_reads())
        self.assertEqual(collections.Counter(v.kind for v in bad), {"cross": 12})
        self.assertEqual(sorted((str(v.date), v.pid) for v in bad), sorted([
            ("2026-10-11", "douglass-twelve"), ("2026-10-21", "washington-idea-per-word"),
            ("2026-10-23", "twain-saturday"), ("2026-10-25", "aps-take-time"), ("2026-10-26", "woolf-flowers"),
            ("2026-10-31", "aps-deep-breath"), ("2026-11-02", "franklin-spectator"), ("2026-11-04", "aps-plunge"),
            ("2026-11-04", "muir-sierra-day"), ("2026-11-05", "washington-twenty-minutes"),
            ("2026-11-05", "jacobs-tiger"), ("2026-11-07", "carroll-rabbit")]))

    def test_repeat_checker_catches_per_practice_histories(self):
        bad = E.near_term_repeats(simulate(per_practice_fresh_first, synthetic_pool(112, 28, 28), 365))
        self.assertGreater(sum(v.kind == "cross" for v in bad), 0)

    def test_repeat_checker_catches_a_stateless_pick(self):
        bad = E.near_term_repeats(simulate(stateless_pick, synthetic_pool(112, 28, 28), 365))
        self.assertGreater(sum(v.kind == "within" for v in bad), 0)

    def test_repeat_checker_counts_a_replaced_passage_as_served(self):
        reads = E.reads_from_sessions({"legato": {"2026-12-01": {"date": "2026-12-01", "passage_id": "a",
                                                                 "replaced": ["a"], "recorded": True}}})
        self.assertEqual([(r.pid, r.replaced) for r in reads], [("a", True), ("a", False)])
        self.assertEqual([v.kind for v in E.near_term_repeats(reads)], ["within"])

    def test_reference_pick_meets_every_threshold_with_168_passages(self):
        pool = synthetic_pool(112, 28, 28)
        reads = simulate(reference_pick, pool, 420)
        self.assertEqual(E.near_term_repeats(reads), [])
        for key in E.PRACTICES:
            s = E.rotation_spread(reads, key, [p["id"] for p in pool if key in p["practices"]])
            self.assertLessEqual(s["max_dev"], 1.0, f"{key}: {spread_text(s)}")

    def test_no_pick_can_meet_the_repeat_rules_with_56_passages(self):
        bad = E.near_term_repeats(simulate(reference_pick, synthetic_pool(56), 365))
        self.assertGreater(len(bad), 0, "56 passages at two reads a day cannot hold a 30-day cooldown")

    def test_pool_exhaustion_checker(self):
        r = lambda d, k, p: E.Read(DAY + dt.timedelta(days=d), k, p)  # noqa: E731
        early = [r(0, "pronunciation", "a"), r(0, "legato", "a"), r(1, "pronunciation", "b"), r(1, "legato", "c")]
        self.assertEqual([x.pid for x in E.served_before_pool_exhausted(early, "abc")], ["a"])
        cycle = [r(0, "pronunciation", "a"), r(0, "legato", "b"), r(1, "pronunciation", "c"), r(1, "legato", "a")]
        self.assertEqual(E.served_before_pool_exhausted(cycle, "abc"), [])

    # E2
    def test_fairness_checker_catches_a_biased_pick(self):
        pool = synthetic_pool(112, 28, 28)
        reads = simulate(lowest_id_cooled, pool, 420)
        s = E.rotation_spread(reads, "legato", [p["id"] for p in pool if "legato" in p["practices"]])
        self.assertGreater(s["max_dev"], 1.0, spread_text(s))

    # E3
    def test_exclusion_checker(self):
        flag = E.Read(DAY, "legato", "a", True, ("repeated",))
        soon = E.Read(DAY + dt.timedelta(days=50), "pronunciation", "a")
        late = E.Read(DAY + dt.timedelta(days=130), "legato", "a")
        self.assertEqual(E.excluded_but_served([flag, soon, late]), [(flag, soon)])
        gone = E.Read(DAY, "pronunciation", "b", True, ("unhelpful",))
        back = E.Read(DAY + dt.timedelta(days=300), "legato", "b")
        self.assertEqual(E.excluded_but_served([gone, back]), [(gone, back)])

    def test_reference_pick_honours_exclusion_flags(self):
        rng = random.Random(3)

        def flag(key, day, pid):
            x = rng.random()
            return ("repeated",) if x < 0.03 else ("unhelpful",) if x < 0.06 else ()
        reads = simulate(reference_pick, synthetic_pool(112, 28, 28), 420, flag=flag)
        self.assertGreater(len(E.flags(reads, "repeated")) + len(E.flags(reads, "unhelpful")), 10)
        self.assertEqual(E.excluded_but_served(reads), [])

    def test_too_easy_checker(self):
        def cycle(order, start):
            return [E.Read(DAY + dt.timedelta(days=start + i), "pronunciation", p,
                           True, ("too_easy",) if (start, p) == (0, "a") else ()) for i, p in enumerate(order)]
        first = cycle("abc", 0)
        self.assertEqual(len(E.too_easy_not_deprioritised(first + cycle("abc", 3), "abc")), 1, "back first")
        self.assertEqual(E.too_easy_not_deprioritised(first + cycle("bca", 3), "abc"), [], "back last")

    def test_flow_checker_flags_the_learners_level_rise(self):
        data = json.loads((BACKUP / "legato.json").read_text(encoding="utf-8"))["sessions"]
        bad = E.flow_rises_after_choppy([data[k] for k in sorted(data)])
        self.assertEqual(len(bad), 1)
        self.assertTrue(bad[0].startswith("2026-10-30"), bad)
        calm = [{"date": f"d{i}", "flow_level": lvl, "feedback": fb}
                for i, (lvl, fb) in enumerate([(2, "Choppy"), (1, "Mostly smooth"), (1, "Smooth"), (1, ""), (2, "")])]
        self.assertEqual(E.flow_rises_after_choppy(calm), [])

    def test_prompt_checker_flags_the_learners_repeated_prompts(self):
        data = json.loads((BACKUP / "legato.json").read_text(encoding="utf-8"))["sessions"]
        bad = E.prompt_repeats([data[k] for k in sorted(data)])
        self.assertTrue(any("after 1 session" in b for b in bad), bad[:3])

    # E5 / E6
    def test_bank_checker_catches_duplicates(self):
        def p(pid, text, word):
            return {"id": pid, "text": text, "pronunciation": {"target_words": [{"word": word}]}}
        a = "The quick brown fox jumps over the lazy dog while the farmer watches from the gate at dawn."
        b = "An entirely different sentence about rivers, bridges, and the slow work of building a town."
        self.assertEqual(E.bank_problems([p("x", a, "fox"), p("y", b, "river")]), [])
        c = "A third passage about lanterns, harbours and the long patience of the people who keep them lit."
        problems = E.bank_problems([p("x", a, "fox"), p("x", b, "river"), p("w", c, "fox"),
                                    p("z", a.replace("dawn", "noon"), "gate")])
        self.assertTrue(any("duplicate id" in m for m in problems), problems)
        self.assertTrue(any("near-duplicates" in m for m in problems), problems)
        self.assertTrue(any("target word 'fox'" in m for m in problems), problems)
        self.assertEqual(E.bank_problems(library.builtin()), [], "today's library is clean")

    def test_legato_checker_separates_flowing_from_choppy_text(self):
        woolf = next(p for p in library.builtin() if p["id"] == "woolf-flowers")
        self.assertIn("breath mark after an abbreviation", E.legato_quality_failures(woolf))
        choppy = {"text": "I sat. He ran. We ate. It rained. They left. She slept. Dogs barked. Cats hid. "
                          "Night fell. Lamps glowed. Doors shut. Birds sang. Wind blew. Trees swayed. "
                          "Clocks ticked. Bells rang. Fires burned. Rain stopped. Sun rose. Day came."}
        self.assertTrue(E.legato_quality_failures(choppy))
        passing = [p["id"] for p in library.builtin() if not E.legato_quality_failures(p)]
        self.assertGreaterEqual(len(passing), 40, "most of today's passages already flow")

    def test_pronunciation_checker_needs_targets_contrasts_and_intonation(self):
        text = ("Speech is simply a modified form of singing; why, then, do we ignore the efficiency of "
                "pitch, the nightingale's considerable range, and the combinations reiterated by every bird?")
        notes = {"target_words": [{"word": w} for w in ("efficiency", "nightingale", "considerable",
                                                          "reiterated", "combinations")],
                 "focus_sounds": ["-tion", "-ed endings"], "intonation": ["question", "list"], "level": 3}
        good = {"text": text, "pronunciation": notes}
        self.assertEqual(E.pron_quality_failures(good), [])
        self.assertIn("no intonation pattern", E.pron_quality_failures(
            {"text": text, "pronunciation": dict(notes, intonation=[])}))
        self.assertTrue(E.pron_quality_failures({"text": text, "pronunciation": dict(
            notes, focus_sounds=["silent letters"])}))
        self.assertTrue(E.pron_quality_failures({"text": text, "pronunciation": dict(
            notes, target_words=[{"word": "elephant"}] * 5)}))

    # E8
    def test_audio_detectors(self):
        self.assertEqual(E.audio_imports("import json\nfrom . import library\n"), [])
        self.assertTrue(E.audio_imports("import librosa\n"))
        self.assertTrue(E.audio_imports("from . import audio\n"))
        self.assertTrue(E.audio_imports("from fdecoach import audio\n"))
        self.assertTrue(E.audio_imports("from pydub import AudioSegment\n"))
        for preset, filtered in (("light", 1), ("none", 0)):
            commands = []

            def fake_run(cmd, *a, **k):
                commands.append(list(cmd))
                Path(cmd[-1]).write_bytes(b"\0")
                return subprocess.CompletedProcess(cmd, 0, "", "")
            tmp = Path(tempfile.mkdtemp())
            try:
                with mock.patch.object(audio, "ffmpeg_path", return_value="/usr/local/bin/ffmpeg"), \
                        mock.patch.object(audio.subprocess, "run", side_effect=fake_run):
                    audio.clean(tmp / "in.m4a", tmp / "out.m4a", preset)
            finally:
                shutil.rmtree(tmp, ignore_errors=True)
            self.assertEqual(len(E.audio_filter_commands(commands)), filtered, preset)


if __name__ == "__main__":
    if sys.argv[1:] == ["record-baseline"]:
        record_baseline()
    else:
        unittest.main()
