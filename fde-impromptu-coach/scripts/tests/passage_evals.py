"""Eval kit for passage rotation in Legato and Pronunciation.

Everything here is text: state JSON, passage text, config and source code. No audio file is
read, written or analysed, so the evals hold to the "no audio treatment" constraint themselves.

Two halves:

* **Checkers** are pure functions over reads, sessions and passages. Each returns the list of
  violations (empty = pass) or the numbers a threshold is applied to. test_passage_rotation.py
  proves every checker on known-bad and known-good inputs before trusting it on the skill.
* **Coach** drives the real skill in-process through ``practice.ensure_today`` (the path the CLI
  uses), with deck rendering stubbed out, so a year of sessions runs in seconds and every pick is
  made by the production selection code.

The contract the fix must meet (from the fix plan, section c):

* A session in legato.json / pronunciation.json keeps ``passage_id`` and may add
  ``replaced`` (ids replaced that day, which count as served), ``selection`` ({"tier": "T0".."T4"}),
  ``passage_feedback`` (a list of FEEDBACK_LABELS) and, for legato, ``response_prompt_id``.
* ``config.passages`` holds ``cooldown_days`` (30), ``recent_sessions`` (60) and
  ``exclude_days`` ({"repeated": 120, "unhelpful": 365}).
* passages.json entries may carry ``practices``; pronunciation notes may carry ``level`` and
  ``intonation``. assets/legato_prompts.json holds the response prompts.
"""
from __future__ import annotations

import ast
import collections
import dataclasses
import datetime as dt
import json
import os
import re
import shutil
import statistics
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple
from unittest import mock

from fdecoach import legato, library, practice
from fdecoach.config import Paths, load_config
from fdecoach.questions import is_duplicate
from fdecoach.state import History

PRACTICES = ("legato", "pronunciation")
# Same-day order: the morning chain runs pronunciation (05:45) before legato (06:00).
PRACTICE_ORDER = {"pronunciation": 0, "legato": 1}
STATE_FILES = {"legato": "legato.json", "pronunciation": "pronunciation.json"}

# Thresholds, one place. The fix plan's section (e) explains each.
RECENT_SESSIONS = 60          # no repeat within this many sessions of one practice
COOLDOWN_DAYS = 30            # no repeat across practices within this many days
EXCLUDE_DAYS = {"repeated": 120, "unhelpful": 365}
FEEDBACK_LABELS = ("too_easy", "too_hard", "repeated", "unhelpful")
# The after-session dialog "Anything about today's passage? (optional)": button -> stored label.
DIALOG_LABELS = {"Too easy": "too_easy", "Too hard": "too_hard", "Read it recently": "repeated",
                 "Not useful": "unhelpful"}
# `fde-coach <legato|pronounce> passage --flag <value>` -> stored label.
FLAG_VALUES = {"too-easy": "too_easy", "too-hard": "too_hard", "repeated": "repeated", "unhelpful": "unhelpful"}
MIN_ELIGIBLE = 120            # passages per practice
MIN_UNIQUE = 150              # passages in the library
MIN_LEVEL_SHARE = 0.20        # of a practice's pool at each level 1, 2, 3
PROMPT_WINDOW = 14            # legato response prompt: no repeat within this many sessions
PROMPT_TYPES = ("restate", "respond", "apply", "exec", "story", "challenge", "teach")

# Pronunciation focus labels that name a sound contrast or a stress pattern (the existing
# vocabulary in passage_annotations.json, minus labels that are neither, such as silent letters).
CONTRAST_OR_STRESS = {
    "th", "voiced th", "voiced vs voiceless th", "th clusters", "th + s", "v", "v / w", "s vs z endings",
    "z", "z spellings", "z and sh", "zh", "sh spellings", "-ed endings", "ng", "kw", "x sounds", "st as ch",
    "d as j", "soft g", "c as s", "ch as k", "schwa", "consonant clusters", "str", "str clusters",
    "sp / sk clusters", "kyuh / yuh", "yoo starts", "-teen numbers", "stress shift", "long-word stress",
    "first-syllable stress", "second-syllable stress", "noun/verb stress", "noun/adjective stress",
    "-tion", "-tion stress", "-ate endings", "-ately", "-edness", "dropped syllables",
}
INTONATION = {"question", "list", "contrast", "conditional", "parenthesis"}
ABBREVIATION_BREATH = re.compile(r"\b(?:Mr|Mrs|Ms|Dr|St|Mt)\. ↘//")
# t/d dropped or merged before a consonant across a word boundary: "next day", "most pleasing".
ELISION = re.compile(r"\b[a-z']*(?:st|nd|ct|pt|ft|ld|nt|sk)\s+(?!h)[bcdfgjklmnpqrstvwz][a-z']*", re.I)
AUDIO_LIBRARIES = {"librosa", "pydub", "whisper", "soundfile", "torchaudio", "speech_recognition",
                   "pyaudio", "sounddevice", "wave", "audioop", "fdecoach.audio"}


# --------------------------------------------------------------------------- reads

@dataclasses.dataclass(frozen=True)
class Read:
    """One passage put in front of the learner."""
    date: dt.date
    practice: str
    pid: str
    recorded: bool = True
    feedback: Tuple[str, ...] = ()
    replaced: bool = False        # served, then swapped out the same day


def reads_from_sessions(sessions_by_practice: Dict[str, Dict[str, Dict[str, Any]]]) -> List[Read]:
    """Every served passage, oldest first. A replaced passage counts as served on its day."""
    out: List[Read] = []
    for prac, sessions in sessions_by_practice.items():
        for key, s in sessions.items():
            day = dt.date.fromisoformat(s.get("date", key))
            for pid in s.get("replaced") or []:
                out.append(Read(day, prac, pid, False, (), True))
            if s.get("passage_id"):
                out.append(Read(day, prac, s["passage_id"], bool(s.get("recorded")),
                                tuple(s.get("passage_feedback") or ()), False))
    return sorted(out, key=order)


def order(r: "Read") -> Tuple[dt.date, int, bool]:
    """Chronological: by day, then the morning chain, a replaced passage before its replacement."""
    return (r.date, PRACTICE_ORDER.get(r.practice, 9), not r.replaced)


def reads_from_state_dir(state_dir: Path) -> List[Read]:
    data = {}
    for prac, name in STATE_FILES.items():
        f = Path(state_dir) / name
        data[prac] = json.loads(f.read_text(encoding="utf-8"))["sessions"] if f.exists() else {}
    return reads_from_sessions(data)


# --------------------------------------------------------------------------- E1 near-term repeats

@dataclasses.dataclass(frozen=True)
class Violation:
    kind: str
    pid: str
    date: dt.date
    practice: str
    earlier: dt.date
    earlier_practice: str
    gap: int                       # sessions for "within", days otherwise

    def __str__(self) -> str:
        unit = "sessions" if self.kind == "within" else "days"
        return (f"{self.kind}: {self.pid} in {self.practice} on {self.date} after {self.earlier_practice} "
                f"on {self.earlier} ({self.gap} {unit})")


def near_term_repeats(reads: Sequence[Read], recent_sessions: int = RECENT_SESSIONS,
                      cooldown_days: int = COOLDOWN_DAYS, since: Optional[dt.date] = None) -> List[Violation]:
    """Repeats too soon: within `recent_sessions` sessions of one practice, within `cooldown_days`
    across practices, or the same passage in both practices on one day. Only reads on or after
    `since` are judged; earlier ones are history."""
    reads = sorted(reads, key=order)
    session_no: Dict[Tuple[str, dt.date], int] = {}
    for prac in PRACTICES:
        days = sorted({r.date for r in reads if r.practice == prac})
        session_no.update({(prac, d): i for i, d in enumerate(days)})
    last_here: Dict[Tuple[str, str], Read] = {}
    last_any: Dict[str, Read] = {}
    out: List[Violation] = []
    for r in reads:
        judged = since is None or r.date >= since
        prev = last_here.get((r.practice, r.pid))
        if judged and prev is not None:
            gap = session_no[(r.practice, r.date)] - session_no[(r.practice, prev.date)]
            if gap < recent_sessions:
                out.append(Violation("within", r.pid, r.date, r.practice, prev.date, prev.practice, gap))
        other = last_any.get(r.pid)
        if judged and other is not None and other.practice != r.practice:
            days = (r.date - other.date).days
            if days == 0:
                out.append(Violation("same-day", r.pid, r.date, r.practice, other.date, other.practice, 0))
            elif days < cooldown_days:
                out.append(Violation("cross", r.pid, r.date, r.practice, other.date, other.practice, days))
        last_here[(r.practice, r.pid)] = r
        last_any[r.pid] = r
    return out


def served_before_pool_exhausted(reads: Sequence[Read], pool: Iterable[str]) -> List[Read]:
    """Reads that repeat a passage while some pool passage has not been read since the cycle began.
    Both practices share the cycle: the pool is exhausted when every passage was read in either."""
    pool = set(pool)
    seen: set = set()
    out: List[Read] = []
    for r in sorted(reads, key=order):
        if r.pid not in pool:
            continue
        if r.pid in seen:
            if len(seen) < len(pool):
                out.append(r)
            else:
                seen = set()
        seen.add(r.pid)
    return out


# --------------------------------------------------------------------------- E2 fair rotation

def rotation_spread(reads: Sequence[Read], practice_key: str, eligible: Iterable[str],
                    since: Optional[dt.date] = None) -> Dict[str, float]:
    """Serve counts per eligible passage in one practice: mean, worst deviation, share within ±1."""
    eligible = list(eligible)
    counts = collections.Counter(r.pid for r in reads
                                 if r.practice == practice_key and not r.replaced
                                 and (since is None or r.date >= since))
    values = [counts[p] for p in eligible]
    mean = statistics.mean(values) if values else 0.0
    devs = [abs(v - mean) for v in values]
    return {"passages": len(values), "mean": mean, "min": min(values, default=0), "max": max(values, default=0),
            "max_dev": max(devs, default=0.0),
            "within_1": (sum(d <= 1 for d in devs) / len(devs)) if devs else 1.0}


# --------------------------------------------------------------------------- E3 feedback

def flags(reads: Sequence[Read], label: str) -> List[Read]:
    return [r for r in reads if label in r.feedback]


def excluded_but_served(reads: Sequence[Read], exclude_days: Dict[str, int] = None) -> List[Tuple[Read, Read]]:
    """(flag, later read) pairs where a passage flagged repeated or unhelpful came back, in either
    practice, inside its exclusion window."""
    exclude_days = exclude_days or EXCLUDE_DAYS
    out = []
    for label, days in exclude_days.items():
        for f in flags(reads, label):
            for r in reads:
                if r.pid == f.pid and f.date < r.date < f.date + dt.timedelta(days=days):
                    out.append((f, r))
    return out


def too_easy_not_deprioritised(reads: Sequence[Read], pool: Iterable[str]) -> List[Tuple[Read, Read]]:
    """A passage flagged too easy goes to the back of its practice's queue: when it is served
    again there, every unflagged pool passage must already have been served there more often than
    it. (Served first in the next cycle = not deprioritised.)"""
    pool = set(pool)
    out = []
    for f in flags(reads, "too_easy"):
        flagged = {g.pid for g in flags(reads, "too_easy") if g.practice == f.practice}
        others = pool - flagged
        counts: collections.Counter = collections.Counter()
        for r in sorted(reads, key=order):
            if r.practice != f.practice or r.replaced:
                continue
            if r.date > f.date and r.pid == f.pid and any(counts[p] <= counts[f.pid] for p in others):
                out.append((f, r))
                break
            counts[r.pid] += 1
    return out


def flow_rises_after_choppy(sessions: Sequence[Dict[str, Any]], window: int = 3) -> List[str]:
    """Legato: a Choppy tap must not be followed by a higher flow level within `window` sessions.
    `sessions` are legato sessions in date order with flow_level and feedback."""
    out = []
    for i, s in enumerate(sessions):
        if s.get("feedback") != "Choppy":
            continue
        for j in range(i + 1, min(i + 1 + window, len(sessions))):
            if sessions[j].get("flow_level", 1) > sessions[j - 1].get("flow_level", 1):
                out.append(f"{sessions[j]['date']}: flow level rose to {sessions[j]['flow_level']} "
                           f"{j - i} session(s) after Choppy on {s['date']}")
    return out


def prompt_repeats(sessions: Sequence[Dict[str, Any]], window: int = PROMPT_WINDOW) -> List[str]:
    """Legato response prompts repeated within `window` sessions (by id, else by text)."""
    out = []
    last: Dict[str, int] = {}
    for i, s in enumerate(sessions):
        key = s.get("response_prompt_id") or s.get("response_prompt") or ""
        if key in last and i - last[key] < window:
            out.append(f"{s['date']}: {key!r} again after {i - last[key]} session(s)")
        last[key] = i
    return out


# --------------------------------------------------------------------------- E5 / E6 content

def practices_of(p: Dict[str, Any]) -> Tuple[str, ...]:
    return tuple(p.get("practices") or PRACTICES)


def eligible(passages: Iterable[Dict[str, Any]], practice_key: str) -> List[Dict[str, Any]]:
    return [p for p in passages if practice_key in practices_of(p)]


def pron_level(p: Dict[str, Any]) -> Optional[int]:
    return (p.get("pronunciation") or {}).get("level")


def bank_problems(passages: Sequence[Dict[str, Any]]) -> List[str]:
    """Duplicate ids, near-duplicate texts and target words used by two passages."""
    out = []
    ids = collections.Counter(p["id"] for p in passages)
    out += [f"duplicate id {i}" for i, n in ids.items() if n > 1]
    texts: List[str] = []
    for p in passages:
        dup = is_duplicate(p["text"], texts)
        if dup:
            out.append(f"{p['id']} near-duplicates another passage: {dup[:60]!r}")
        texts.append(p["text"])
    owner: Dict[str, str] = {}
    for p in passages:
        for t in (p.get("pronunciation") or {}).get("target_words", []):
            if t["word"] in owner and owner[t["word"]] != p["id"]:
                out.append(f"target word {t['word']!r} in {owner[t['word']]} and {p['id']}")
            owner.setdefault(t["word"], p["id"])
    return out


def level_shares(pool: Sequence[Dict[str, Any]], level_of: Callable[[Dict[str, Any]], Optional[int]]) -> Dict[int, float]:
    n = len(pool) or 1
    c = collections.Counter(level_of(p) for p in pool)
    return {lvl: c[lvl] / n for lvl in (1, 2, 3)}


def legato_features(text: str) -> Dict[str, Any]:
    groups = legato.breath_groups(text)
    sizes = [b - a for a, b, _ in groups] or [0]
    return {"links": len(legato.links(text)), "chains": len(legato.drill_chains(text)),
            "elisions": len(ELISION.findall(re.sub(r"[—–]", " — ", text))),
            "avg_group": sum(sizes) / len(sizes),
            "abbreviation_breaths": len(ABBREVIATION_BREATH.findall(legato.phrase_map(text)))}


def legato_quality_failures(p: Dict[str, Any]) -> List[str]:
    f = legato_features(p["text"])
    out = []
    if f["links"] < 6:
        out.append(f"{f['links']} links (need 6)")
    if f["chains"] < 3:
        out.append(f"{f['chains']} drill chains (need 3)")
    if f["elisions"] < 2:
        out.append(f"{f['elisions']} elision sites (need 2)")
    if not 4 <= f["avg_group"] <= 14:
        out.append(f"breath groups average {f['avg_group']:.1f} words (need 4-14)")
    if f["abbreviation_breaths"]:
        out.append("breath mark after an abbreviation")
    return out


def pron_quality_failures(p: Dict[str, Any]) -> List[str]:
    pr = p.get("pronunciation") or {}
    out = []
    words = [t.get("word", "") for t in pr.get("target_words", [])]
    if len(words) != 5:
        out.append(f"{len(words)} target words (need 5)")
    missing = [w for w in words if not re.search(rf"\b{re.escape(w)}\b", p["text"], re.I)]
    if missing:
        out.append(f"target words not in the text: {missing}")
    contrasts = set(pr.get("focus_sounds", [])) & CONTRAST_OR_STRESS
    if len(contrasts) < 2:
        out.append(f"{len(contrasts)} contrast or stress focus labels (need 2)")
    if not set(pr.get("intonation", [])) & INTONATION:
        out.append("no intonation pattern")
    if pr.get("level") not in (1, 2, 3):
        out.append(f"pronunciation level {pr.get('level')!r} (need 1, 2 or 3)")
    return out


# --------------------------------------------------------------------------- E8 audio

def audio_imports(source: str) -> List[str]:
    """Imports of audio libraries (or the skill's own audio module) in a Python source."""
    out = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            out += [a.name for a in node.names if a.name.split(".")[0] in AUDIO_LIBRARIES or a.name in AUDIO_LIBRARIES]
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if mod.split(".")[0] in AUDIO_LIBRARIES or mod in AUDIO_LIBRARIES:
                out.append(mod)
            if mod in ("", "fdecoach") and any(a.name == "audio" for a in node.names):
                out.append(f"{'.' * node.level}{mod}.audio".replace("..", "."))
    return out


def audio_filter_commands(commands: Sequence[Sequence[str]]) -> List[List[str]]:
    """ffmpeg command lines that filter audio (noise reduction, loudness, any -af)."""
    flags_ = {"-af", "-filter:a", "-filter_complex", "-lavfi"}
    return [list(c) for c in commands if any(str(a) in flags_ for a in c)]


# --------------------------------------------------------------------------- driving the real skill

class Coach:
    """An isolated FDE_COACH_HOME driven in-process through practice.ensure_today, the function the
    CLI's `generate`, `daily` and `session` commands call. Only deck rendering is stubbed."""

    def __init__(self, workdir: Path, config: Optional[Dict[str, Any]] = None,
                 state_from: Optional[Path] = None):
        self.workdir = Path(workdir)
        home = self.workdir / "home"
        self._env = mock.patch.dict(os.environ, {
            "FDE_COACH_HOME": str(home), "FDE_COACH_DRYRUN": "1", "FDE_COACH_SKIP_NETWORK_WAIT": "1",
            "FDE_COACH_NO_CLAUDE_DISCOVERY": "1", "FDE_COACH_AGENTS_DIR": str(self.workdir / "agents"),
            "FDE_COACH_RECORDINGS": str(self.workdir / "movies"), "FDE_COACH_DRYRUN_ANSWERS": ""})
        self._env.start()
        os.environ.pop("FDE_COACH_TODAY", None)
        self.paths = Paths(home)
        self.paths.ensure()
        user = {"claude_path": "/nonexistent/claude", "youtube": {"enabled": False},
                "reminders": {"use_reminders_app": False}, "google_calendar": {"enabled": False}}
        user = _merge(user, config or {})
        self.paths.config.write_text(json.dumps(user, indent=1), encoding="utf-8")
        if state_from:
            for name in STATE_FILES.values():
                src = Path(state_from) / name
                if src.exists():
                    shutil.copy(src, self.paths.state_dir / name)
        self.ctx = SimpleNamespace(paths=self.paths, cfg=load_config(self.paths))
        self._specs = {k: self._fast(practice.spec_for(k)) for k in PRACTICES}

    def close(self) -> None:
        self._env.stop()

    def _fast(self, spec: practice.Practice) -> practice.Practice:
        def build_deck(session, streak, cfg, decks):
            decks.mkdir(parents=True, exist_ok=True)
            pptx = decks / f"{session['date']}_{spec.file_stem}.pptx"
            ppsx = pptx.with_suffix(".ppsx")
            pptx.write_bytes(b"")
            ppsx.write_bytes(b"")
            return pptx, ppsx
        return dataclasses.replace(spec, build_deck=build_deck)

    def _clock(self, date: dt.date, hour: str = "06:00:00"):
        return mock.patch.dict(os.environ, {"FDE_COACH_NOW": f"{date.isoformat()}T{hour}"})

    def generate(self, key: str, date: dt.date, replace: bool = False, **options: Any) -> Dict[str, Any]:
        with self._clock(date):
            session, _ = practice.ensure_today(self.ctx, self._specs[key], replace=replace, **options)
        return session

    def record(self, key: str, date: dt.date) -> None:
        self.update(key, date, lambda s: s.update(recorded=True))

    def feedback(self, key: str, date: dt.date, answers: str) -> None:
        """The after-session dialogs, answered in dry-run order (comma between dialogs, '+' between
        the items picked in one multi-select)."""
        spec = self._specs[key]
        if spec.feedback:
            with self._clock(date, "06:20:00"), mock.patch.dict(os.environ, {"FDE_COACH_DRYRUN_ANSWERS": answers}):
                spec.feedback(self.ctx, date)

    def session(self, key: str, date: dt.date, answers: Optional[str] = None, record: bool = True) -> Dict[str, Any]:
        s = self.generate(key, date)
        if record:
            self.record(key, date)
        if answers is not None:
            self.feedback(key, date, answers)
        return self.state(key)["sessions"][date.isoformat()]

    def flag(self, key: str, date: dt.date, *labels: str) -> None:
        """Passage feedback as the dialog and `passage --flag` store it (the contract)."""
        def add(s):
            s["passage_feedback"] = sorted(set(s.get("passage_feedback") or []) | set(labels))
        self.update(key, date, add)

    def update(self, key: str, date: dt.date, fn: Callable[[Dict[str, Any]], None]) -> None:
        hist = History(self.paths, file=getattr(self.paths, self._specs[key].state_attr))
        s = hist.get(date)
        if s is None:
            raise AssertionError(f"no {key} session on {date}")
        fn(s)
        hist.put(s)
        hist.save()

    def state(self, key: str) -> Dict[str, Any]:
        f = self.paths.state_dir / STATE_FILES[key]
        return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {"sessions": {}}

    def sessions(self, key: str) -> List[Dict[str, Any]]:
        data = self.state(key)["sessions"]
        return [data[k] for k in sorted(data)]

    def reads(self) -> List[Read]:
        return reads_from_state_dir(self.paths.state_dir)

    def run_days(self, start: dt.date, days: int, answers: Optional[Callable[[str, dt.date], Optional[str]]] = None,
                 order: Sequence[str] = ("pronunciation", "legato")) -> None:
        """Both practices every day, as the morning routine runs them (pronunciation, then legato)."""
        for i in range(days):
            date = start + dt.timedelta(days=i)
            for key in order:
                self.session(key, date, answers(key, date) if answers else None)


def _merge(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(a)
    for k, v in b.items():
        out[k] = _merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else v
    return out


def first_day_after(state_dir: Path) -> dt.date:
    days = [r.date for r in reads_from_state_dir(state_dir)]
    return max(days) + dt.timedelta(days=1)
