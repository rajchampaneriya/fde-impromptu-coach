"""Pronunciation practice (pen method): the spec for the shared audio-practice
engine (practice.py) plus the pieces only this practice has: the "which words
felt hard?" feedback that drives the flashcard schedule, and its YouTube
description. The public functions below keep their original signatures."""
from __future__ import annotations

import datetime as dt
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from . import macos, practice, youtube
from .config import Paths
from .pronounce import due_words, generate_content, update_after_session, word_state
from .pronounce_deck import build_deck, chapters, render_slide_pngs, slide_durations
from .state import History, file_lock, today

log = logging.getLogger("fdecoach")

GCAL_PREFIX = "fdepron"  # event ids: a-v and 0-9 only


def _session_fields(content: Dict[str, Any]) -> Dict[str, Any]:
    fields = {
        "paragraph": content["paragraph"],
        "target_words": content["target_words"],
        "focus_sounds": content.get("focus_sounds", []),
        "words": [t["word"] for t in content["target_words"]],
    }
    if content.get("passage"):
        fields["passage"] = content["passage"]
        fields["passage_id"] = content["passage"].get("id")
    return fields


def _describe(s: Dict[str, Any]) -> Dict[str, Any]:
    from .library import credit_line
    return {"words": s.get("words", []),
            "passage": credit_line(s["passage"], short=True) if s.get("passage") else ""}


def ask_words_feedback(ctx, date: dt.date) -> None:
    """Multi-select: hard words come back tomorrow, easy ones space out."""
    history = pron_history(ctx.paths)
    session = history.get(date)
    if not session or not session.get("words"):
        return
    picked = macos.choose_from_list("Which words still felt hard? (unselected ones get easier)",
                                    "Pronunciation practice", session["words"])
    with file_lock(ctx.paths, "history", blocking=True):
        history = pron_history(ctx.paths)
        update_after_session(history, ctx.cfg, date, session["words"], picked)
        history.save()
    if picked:
        log.info("Hard words (back tomorrow): %s", ", ".join(picked))


def build_metadata(session: Dict[str, Any], cfg: Dict[str, Any], marks: Optional[List[Tuple[int, str]]],
                   streak: int) -> Dict[str, Any]:
    yt = cfg.get("youtube", {})
    title = "Pronunciation · Day {day} · {date}".format(day=session.get("day_number", "?"), date=session["date"])
    lines = [
        "Daily pronunciation practice (pen method) — Forward Deployed Engineer.",
        f"Streak {streak} day{'s' if streak != 1 else ''} · {len(session.get('target_words', []))} target words",
        "",
    ]
    if marks:
        lines += [f"{m // 60}:{m % 60:02d} {label}" for m, label in marks]
        lines.append("")
    lines.append("Paragraph")
    lines.append(session.get("paragraph", ""))
    if session.get("passage"):
        lines.append("— " + practice.passage_credit(session["passage"]))
    lines += ["", "Target words"]
    for t in session.get("target_words", []):
        lines.append(f"- {t['word']} ({t.get('stress') or t.get('respelling', '')}) — {t.get('tip', '')}")
    return {
        "snippet": {
            "title": youtube._clean(title, 100),
            "description": youtube._clean("\n".join(lines), 4900),
            "tags": ["pronunciation", "pen method", "forward deployed engineer"],
            "categoryId": str(yt.get("category_id", "27")),
        },
        "status": {"privacyStatus": yt.get("privacy_status", "private"), "selfDeclaredMadeForKids": False},
    }


SPEC = practice.Practice(
    key="pronunciation", title="Pronunciation", cli="pronounce", state_attr="pron_state",
    file_stem="Pronunciation", gcal_prefix=GCAL_PREFIX, gcal_runtime_key="gcal_pron_events",
    reminder_tag="[pronunciation]",
    event_summary="Pronunciation practice not recorded yet — 5 minutes with the pen",
    ready_body="Five minutes with the pen method keeps the streak alive.",
    prompt_body="Audio only, about 5 minutes. Pen ready for Round 2.",
    generate=generate_content, session_fields=_session_fields, build_deck=build_deck,
    render_pngs=render_slide_pngs, durations=slide_durations, chapters=chapters, metadata=build_metadata,
    feedback=ask_words_feedback, describe=_describe, next_key="legato",
)


# --------------------------------------------------------------------------- public API (unchanged names)

def pron_history(paths: Paths) -> History:
    return practice.history(paths, SPEC)


def reminder_title(date: dt.date) -> str:
    return practice.reminder_title(SPEC, date)


def pron_event_summary() -> str:
    return SPEC.event_summary


def ensure_today(ctx, replace: bool = False, **options: Any) -> Tuple[Dict[str, Any], bool]:
    return practice.ensure_today(ctx, SPEC, replace=replace, **options)


def daily(ctx, from_prompt: bool = False) -> Dict[str, Any]:
    return practice.daily(ctx, SPEC, from_prompt=from_prompt)


def run_session(ctx, force: bool = False, max_tries: int = 2) -> Dict[str, Any]:
    return practice.run_session(ctx, SPEC, force=force, max_tries=max_tries)


def mark_recorded(ctx, date: dt.date, result: Dict[str, Any]) -> None:
    practice.mark_recorded(ctx, SPEC, date, result)


def assemble_video(session: Dict[str, Any], cfg: Dict[str, Any], paths: Paths) -> Optional[Path]:
    return practice.assemble_video(session, cfg, paths, SPEC)


def upload_pending(ctx, interactive: bool = False) -> List[str]:
    return practice.upload_pending(ctx, SPEC, interactive=interactive)


def calendar_sync(ctx, clear: bool = False) -> List[str]:
    return practice.calendar_sync(ctx, SPEC, clear=clear)


def calendar_sync_safe(ctx) -> None:
    practice.calendar_sync_safe(ctx, SPEC)


def status(ctx) -> Dict[str, Any]:
    st = practice.status(ctx, SPEC)
    history = pron_history(ctx.paths)
    st["due_words"] = due_words(history, ctx.cfg, today())
    st["all_words"] = sorted(word_state(history))
    st["paragraph_source"] = ctx.cfg.get("pronunciation", {}).get("paragraph_source", "library")
    return st


def history_rows(ctx, limit: int = 14, reveal_today: bool = False) -> List[Dict[str, Any]]:
    return practice.history_rows(ctx, SPEC, limit=limit, reveal_today=reveal_today)
