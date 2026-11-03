"""Weekend Stage: the Practice spec for the shared engine (practice.py), on camera and
weekly, plus its prep page, saved segment times and YouTube description.

One session per weekend, filed under that weekend's Saturday. The scheduled run fires on
Saturday and again on Sunday (a catch-up that reopens the same week, never a new one).
The upload is the camera recording as QuickTime saved it: no TED audio or video is ever
mixed in, and the description credits the talk under TED's CC BY-NC-ND 4.0 licence.
"""
from __future__ import annotations

import datetime as dt
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from . import macos, practice, stage, stage_prep, youtube
from .config import Paths
from .stage_deck import build_deck, chapters, default_durations, render_slide_pngs, slide_durations
from .state import History, file_lock, streaks, today

log = logging.getLogger("fdecoach")

GCAL_PREFIX = "fdestage"  # event ids: a-v and 0-9 only


def _describe(s: Dict[str, Any]) -> Dict[str, Any]:
    """What status and history show. Take C's twist is left out until the week is recorded."""
    talk = s.get("talk") or {}
    out = {"week": s.get("week") or s.get("day_number"), "talk_id": s.get("talk_id"),
           "talk": stage.short_credit(talk) if talk else "", "segment": stage.segment_text(s.get("segment") or {}),
           "phase": s.get("phase", "")}
    if s.get("recorded"):
        out["twist"] = s.get("twist", "")
    return out


def _on_ready(ctx, session: Dict[str, Any]) -> None:
    """The scheduled run opens the prep page with the deck: the weekend starts with study."""
    if ctx.cfg.get("stage", {}).get("open_prep_when_ready", True):
        macos.open_path(stage_prep.write(ctx.paths, session))


def build_metadata(session: Dict[str, Any], cfg: Dict[str, Any], marks: Optional[List[Tuple[int, str]]],
                   streak: int) -> Dict[str, Any]:
    yt = cfg.get("youtube", {})
    talk = session["talk"]
    tb = talk["take_b"]
    title = "Weekend Stage · Week {week} · {speaker}".format(week=session.get("day_number", "?"), speaker=talk["speaker"])
    lines = ["Weekend speaking practice — Forward Deployed Engineer.",
             f"Streak {streak} week{'s' if streak != 1 else ''} · move: {talk['move']}", ""]
    if marks:
        lines += [f"{m // 60}:{m % 60:02d} {label}" for m, label in marks]
        lines.append("")
    lines += ["Takes",
              f"A · Mirror: {stage.segment_text(session.get('segment') or {})}",
              f"B · Make it yours, to {tb['listener']}: {tb['prompt']}",
              f"C · Pressure: {session.get('twist', '')}", "",
              "This is my own camera recording. It contains no TED audio or video.",
              f"Practising a segment of {stage.credit(talk)}"]
    return {
        "snippet": {
            "title": youtube._clean(title, 100),
            "description": youtube._clean("\n".join(lines), 4900),
            "tags": ["weekend stage", "public speaking", "speech delivery", "forward deployed engineer"],
            "categoryId": str(yt.get("category_id", "27")),
        },
        "status": {"privacyStatus": yt.get("privacy_status", "private"), "selfDeclaredMadeForKids": False},
    }


SPEC = practice.Practice(
    key="stage", title="Weekend Stage", cli="stage", state_attr="stage_state", file_stem="Stage",
    gcal_prefix=GCAL_PREFIX, gcal_runtime_key="gcal_stage_events", reminder_tag="[stage]",
    event_summary="Weekend Stage not recorded yet — one TED talk, three takes on camera",
    ready_body="This weekend's talk is ready: study it, then three takes on camera.",
    prompt_body="Study first: the prep page just opened (about 25 minutes). Then about 10 minutes on camera: "
                "Take A mirrors the speaker, Take B makes it yours, Take C brings a twist.",
    generate=stage.generate_content, session_fields=stage.session_fields, build_deck=build_deck,
    render_pngs=render_slide_pngs, durations=default_durations, chapters=chapters, metadata=build_metadata,
    describe=_describe, media="video", cadence="weekly", timeline=slide_durations, on_ready=_on_ready,
)


# --------------------------------------------------------------------------- public API

def stage_history(paths: Paths) -> History:
    return practice.history(paths, SPEC)


def ensure_week(ctx, replace: bool = False, talk_id: Optional[str] = None) -> Tuple[Dict[str, Any], bool]:
    return practice.ensure_today(ctx, SPEC, replace=replace, talk_id=talk_id)


def daily(ctx, from_prompt: bool = False) -> Dict[str, Any]:
    return practice.daily(ctx, SPEC, from_prompt=from_prompt)


def run_session(ctx, force: bool = False, max_tries: int = 2) -> Dict[str, Any]:
    return practice.run_session(ctx, SPEC, force=force, max_tries=max_tries)


def upload_pending(ctx, interactive: bool = False) -> List[str]:
    return practice.upload_pending(ctx, SPEC, interactive=interactive)


def calendar_sync(ctx, clear: bool = False) -> List[str]:
    return practice.calendar_sync(ctx, SPEC, clear=clear)


def status(ctx) -> Dict[str, Any]:
    st = practice.status(ctx, SPEC)
    weekend = dt.date.fromisoformat(st["period"])
    st["due"] = (weekend + dt.timedelta(days=1)).isoformat()   # the Sunday that closes this week
    nxt = stage_history(ctx.paths).completed_before(weekend) + 1
    talk = stage.talk_for_week(nxt)
    st["next_talk"] = stage.short_credit(talk) if not (st["today"] or {}).get("talk") else st["today"]["talk"]
    return st


def history_rows(ctx, limit: int = 14) -> List[Dict[str, Any]]:
    rows = practice.history_rows(ctx, SPEC, limit=limit)
    for r in rows:
        r.pop("paragraph", None)   # stage has no reading text
    return rows


def prep(ctx, open_page: bool = True) -> Dict[str, Any]:
    """Build (or reuse) this weekend's session and write its prep page."""
    session, created = ensure_week(ctx)
    page = stage_prep.write(ctx.paths, session)
    if open_page:
        macos.open_path(page)
    return {"week": session["day_number"], "weekend": session["date"], "created": created,
            "talk": stage.short_credit(session["talk"]), "segment": stage.segment_text(session["segment"]),
            "page": str(page), "recorded": bool(session.get("recorded"))}


def save_segment(ctx, start: str, end: str, talk_id: Optional[str] = None) -> Dict[str, Any]:
    """Save the segment times for this weekend's talk (or another, by id). An unrecorded
    deck for that talk is rebuilt so Take A shows them; the prep page is rewritten."""
    with file_lock(ctx.paths, "history", blocking=True):
        hist = stage_history(ctx.paths)
        current = hist.get(practice.period(SPEC))
        tid = talk_id or (current or {}).get("talk_id") or stage.talk_for_week(
            hist.completed_before(practice.period(SPEC)) + 1)["id"]
        saved = stage.save_segment(hist, tid, start, end)
        rebuilt = False
        if current and current.get("talk_id") == tid and not current.get("recorded"):
            current["segment"] = stage.segment_for(hist, stage.talk_by_id(tid))
            pptx, ppsx = build_deck(current, streaks(hist, today()), ctx.cfg, ctx.paths.decks)
            current["deck_path"], current["show_path"] = str(pptx), str(ppsx)
            hist.put(current)
            rebuilt = True
        hist.save()
    page = stage_prep.write(ctx.paths, current) if rebuilt else None
    return {"talk_id": tid, "start": saved["start"], "end": saved["end"], "deck_rebuilt": rebuilt,
            "page": str(page) if page else None}


def prep_page(paths: Paths, session: Dict[str, Any]) -> Path:
    return stage_prep.prep_path(paths, session)
