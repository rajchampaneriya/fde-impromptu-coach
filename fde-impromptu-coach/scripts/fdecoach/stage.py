"""Weekend Stage content: the ten-talk curriculum (assets/talks.json), which talk a
weekend gets, the segment times the learner saves, and the TED credit line.

TED talks are licensed CC BY-NC-ND 4.0. The catalogue therefore keeps only
links, times and our own delivery notes: never a transcript, never TED audio or
video. Nothing here downloads anything; the prep page embeds TED's own player.
"""
from __future__ import annotations

import datetime as dt
import json
import re
from typing import Any, Dict, List, Optional, Tuple

from .config import ASSETS_DIR, Paths
from .state import History

TALKS_FILE = ASSETS_DIR / "talks.json"
TAKES = ("Take A · Mirror", "Take B · Make it yours", "Take C · Pressure")
MAX_NOTE_WORDS = 60  # coach notes describe delivery; they never grow into a summary of the talk
_TIME = re.compile(r"^(\d{1,2}):([0-5]\d)$")


def catalogue() -> Dict[str, Any]:
    return json.loads(TALKS_FILE.read_text(encoding="utf-8"))


def talks() -> List[Dict[str, Any]]:
    return sorted(catalogue()["talks"], key=lambda t: t["week"])


def talk_by_id(talk_id: str) -> Dict[str, Any]:
    for t in talks():
        if t["id"] == talk_id:
            return t
    raise KeyError(f"no talk {talk_id!r}; see assets/talks.json (fde-coach stage generate --talk ID)")


def talk_for_week(week: int) -> Dict[str, Any]:
    """Week 1 is the first talk; after week 10 the cycle starts again."""
    ts = talks()
    return ts[(max(1, week) - 1) % len(ts)]


def phase_for(week: int) -> str:
    w = (max(1, week) - 1) % len(talks()) + 1
    for p in catalogue().get("phases", []):
        lo, hi = p["weeks"]
        if lo <= w <= hi:
            return p["name"]
    return ""


def parse_time(value: str) -> int:
    """'2:05' -> 125 seconds. Minutes and seconds only: a segment never runs an hour."""
    m = _TIME.match(str(value).strip())
    if not m:
        raise ValueError(f"time {value!r} must look like M:SS, for example 2:05")
    return int(m.group(1)) * 60 + int(m.group(2))


def segment_text(segment: Dict[str, Any]) -> str:
    """'The opening · 2:05–5:10', or the label with a nudge to find it on the first watch."""
    if segment.get("start") and segment.get("end"):
        return f"{segment['label']} · {segment['start']}–{segment['end']}"
    return f"{segment['label']} · find it on your first watch"


def segment_for(hist: History, talk: Dict[str, Any]) -> Dict[str, Any]:
    """The catalogue's segment, with the start and end the learner saved for this talk on top."""
    seg = dict(talk.get("segment") or {})
    saved = (hist.data.get("segments") or {}).get(talk["id"]) or {}
    if saved.get("start") and saved.get("end"):
        seg.update(start=saved["start"], end=saved["end"])
    return seg


def save_segment(hist: History, talk_id: str, start: str, end: str) -> Dict[str, Any]:
    """Store the times the learner found; they apply to every deck and prep page for that talk."""
    talk_by_id(talk_id)
    a, b = parse_time(start), parse_time(end)
    if b <= a:
        raise ValueError(f"the end ({end}) must come after the start ({start})")
    fmt = lambda s: f"{s // 60}:{s % 60:02d}"  # noqa: E731
    hist.data.setdefault("segments", {})[talk_id] = {"start": fmt(a), "end": fmt(b)}
    return hist.data["segments"][talk_id]


def credit(talk: Dict[str, Any]) -> str:
    lic = catalogue().get("license") or {}
    return (f"“{talk['title']}” by {talk['speaker']} ({talk['event']}). © {lic.get('holder', 'TED Conferences, LLC')}, "
            f"licensed {lic.get('name', 'CC BY-NC-ND 4.0')}. Original: {talk['ted_url']}")


def short_credit(talk: Dict[str, Any]) -> str:
    return f"{talk['speaker']} · {talk['title']} ({talk['event']}, {talk['length']})"


def public_talk(talk: Dict[str, Any]) -> Dict[str, Any]:
    """The fields a session keeps: everything in the catalogue except Take C's twist,
    which lives under the session's own `twist` key and stays off the prep page."""
    return {k: v for k, v in talk.items() if k != "take_c"}


# --------------------------------------------------------------------------- the Practice hooks

def generate_content(hist: History, cfg: Dict[str, Any], paths: Paths, date: dt.date,
                     talk_id: Optional[str] = None, **_: Any) -> Tuple[Dict[str, Any], List[str]]:
    """This weekend's talk: the next one in the curriculum, or the one named with --talk."""
    week = hist.completed_before(date) + 1
    talk = talk_by_id(talk_id) if talk_id else talk_for_week(week)
    notes = [f"week {week}: {talk['speaker']} ({talk['id']})" + (" chosen by hand" if talk_id else "")]
    seg = segment_for(hist, talk)
    content = {
        "source": "catalogue",
        "talk": public_talk(talk),
        "week": week,
        "phase": phase_for(talk["week"]),
        "segment": seg,
        "take_seconds": [int(talk["take_a_seconds"]), int(talk["take_b"]["seconds"]), int(talk["take_c"]["seconds"])],
        "twist": talk["take_c"]["twist"],
    }
    return content, notes


def session_fields(content: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "talk_id": content["talk"]["id"],
        "talk": content["talk"],
        "week": content["week"],
        "phase": content.get("phase", ""),
        "segment": content["segment"],
        "take_seconds": content["take_seconds"],
        "twist": content["twist"],
    }


def validate_catalogue(data: Optional[Dict[str, Any]] = None) -> List[str]:
    """Problems with the catalogue, empty when it is fit to ship (the tests run this)."""
    data = data or catalogue()
    problems: List[str] = []
    ts = data.get("talks") or []
    for t in ts:
        tid = t.get("id", "?")
        if "transcript" in json.dumps(t).lower():
            problems.append(f"{tid}: no transcript, or any field about one, belongs in the catalogue")
        if not str(t.get("ted_url", "")).startswith("https://www.ted.com/talks/"):
            problems.append(f"{tid}: ted_url must be a ted.com talk page")
        if not str(t.get("embed_url", "")).startswith("https://embed.ted.com/talks/"):
            problems.append(f"{tid}: embed_url must be TED's embed player")
        if not (t.get("segment") or {}).get("label"):
            problems.append(f"{tid}: segment needs a label")
        for k in ("take_b", "take_c"):
            if not t.get(k) or not int(t[k].get("seconds", 0)):
                problems.append(f"{tid}: {k} needs seconds")
        if not (t.get("take_b") or {}).get("prompt") or not (t.get("take_c") or {}).get("twist"):
            problems.append(f"{tid}: Take B needs a prompt and Take C a twist")
        notes = " ".join(t.get("watch_for") or []) + " " + t.get("move", "")
        if len(notes.split()) > MAX_NOTE_WORDS:
            problems.append(f"{tid}: coach notes run {len(notes.split())} words (max {MAX_NOTE_WORDS})")
    if "CC BY-NC-ND" not in (data.get("license") or {}).get("name", ""):
        problems.append("license: the catalogue must name TED's CC BY-NC-ND licence")
    return problems
