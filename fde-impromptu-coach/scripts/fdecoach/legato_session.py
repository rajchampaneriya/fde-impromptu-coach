"""Legato practice (connected speech): the spec for the shared audio-practice
engine (practice.py), its after-session "how did the flow feel?" calibration
and its YouTube description. Audio only, about 5 minutes, own streak."""
from __future__ import annotations

import datetime as dt
import logging
from typing import Any, Dict, List, Optional, Tuple

from . import macos, practice, youtube
from .config import APP_NAME, Paths
from .legato import apply_feedback, generate_content, phrase_map
from .legato_deck import build_deck, chapters, render_slide_pngs, slide_durations
from .library import credit_line
from .state import History, file_lock

log = logging.getLogger("fdecoach")

GCAL_PREFIX = "fdelegato"  # event ids: a-v and 0-9 only
FEEDBACK = ["Choppy", "Mostly smooth", "Smooth"]


def _session_fields(content: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "paragraph": content["paragraph"],
        "passage": content["passage"],
        "passage_id": content["passage"].get("id"),
        "flow_level": content.get("flow_level", 1),
        "chains": content.get("chains", []),
        "response_prompt": content.get("response_prompt", ""),
    }


def _describe(s: Dict[str, Any]) -> Dict[str, Any]:
    return {"passage": credit_line(s.get("passage") or {}, short=True), "passage_id": s.get("passage_id"),
            "flow_level": s.get("flow_level"), "feedback": s.get("feedback")}


def ask_flow_feedback(ctx, date: dt.date) -> None:
    """One tap tunes tomorrow's passage: Choppy -> shorter sentences, Smooth -> longer."""
    answer = macos.dialog("How did the flow feel today?", APP_NAME, FEEDBACK, "Mostly smooth", timeout_seconds=120)
    if answer not in FEEDBACK:
        return
    with file_lock(ctx.paths, "history", blocking=True):
        hist = legato_history(ctx.paths)
        s = hist.get(date)
        if s is not None:
            s["feedback"] = answer
            hist.put(s)
        apply_feedback(hist, answer)
        hist.save()
    log.info("Legato feedback: %s", answer)


def build_metadata(session: Dict[str, Any], cfg: Dict[str, Any], marks: Optional[List[Tuple[int, str]]],
                   streak: int) -> Dict[str, Any]:
    yt = cfg.get("youtube", {})
    title = "Legato · Day {day} · {date}".format(day=session.get("day_number", "?"), date=session["date"])
    lines = ["Daily legato practice (smooth, connected speech) — Forward Deployed Engineer.",
             f"Streak {streak} day{'s' if streak != 1 else ''} · flow level {session.get('flow_level', 1)} of 3", ""]
    if marks:
        lines += [f"{m // 60}:{m % 60:02d} {label}" for m, label in marks]
        lines.append("")
    lines += ["Passage", session.get("paragraph", ""), "— " + practice.passage_credit(session.get("passage")), "",
              "Phrase map (‿ join, / breathe)", phrase_map(session.get("paragraph", "")), ""]
    if session.get("chains"):
        lines.append("Linking drill")
        lines += [f"- {c['phrase']}" + (f" → {c['flow']}" if c.get("flow") else "") for c in session["chains"]]
        lines.append("")
    lines += ["Respond", session.get("response_prompt", "")]
    return {
        "snippet": {
            "title": youtube._clean(title, 100),
            "description": youtube._clean("\n".join(lines), 4900),
            "tags": ["legato", "connected speech", "public speaking", "forward deployed engineer"],
            "categoryId": str(yt.get("category_id", "27")),
        },
        "status": {"privacyStatus": yt.get("privacy_status", "private"), "selfDeclaredMadeForKids": False},
    }


SPEC = practice.Practice(
    key="legato", title="Legato", cli="legato", state_attr="legato_state", file_stem="Legato",
    gcal_prefix=GCAL_PREFIX, gcal_runtime_key="gcal_legato_events", reminder_tag="[legato]",
    event_summary="Legato practice not recorded yet — 5 minutes of connected speech",
    ready_body="Five minutes of smooth, connected reading keeps the streak alive.",
    prompt_body="Audio only, about 5 minutes: breath, linking, three reads of a real book passage, "
                "then a 45-second response.",
    generate=generate_content, session_fields=_session_fields, build_deck=build_deck,
    render_pngs=render_slide_pngs, durations=slide_durations, chapters=chapters, metadata=build_metadata,
    feedback=ask_flow_feedback, describe=_describe,
)


# --------------------------------------------------------------------------- public API

def legato_history(paths: Paths) -> History:
    return practice.history(paths, SPEC)


def ensure_today(ctx, replace: bool = False, passage_id: Optional[str] = None) -> Tuple[Dict[str, Any], bool]:
    return practice.ensure_today(ctx, SPEC, replace=replace, passage_id=passage_id)


def daily(ctx, from_prompt: bool = False) -> Dict[str, Any]:
    return practice.daily(ctx, SPEC, from_prompt=from_prompt)


def run_session(ctx, force: bool = False, max_tries: int = 2) -> Dict[str, Any]:
    return practice.run_session(ctx, SPEC, force=force, max_tries=max_tries)


def upload_pending(ctx, interactive: bool = False) -> List[str]:
    return practice.upload_pending(ctx, SPEC, interactive=interactive)


def calendar_sync(ctx, clear: bool = False) -> List[str]:
    return practice.calendar_sync(ctx, SPEC, clear=clear)


def status(ctx) -> Dict[str, Any]:
    from .legato import flow_level
    from .state import today
    st = practice.status(ctx, SPEC)
    st["next_flow_level"] = flow_level(legato_history(ctx.paths), ctx.cfg, today())
    return st


def history_rows(ctx, limit: int = 14, reveal_today: bool = False) -> List[Dict[str, Any]]:
    return practice.history_rows(ctx, SPEC, limit=limit, reveal_today=reveal_today)
