"""Weekend Stage deck (same blue/Calibri look as the other practices). QuickTime
records the camera while it plays, so nothing on these slides reaches the video.

Slides: intro · Take A (mirror the speaker) · reset · Take B (the same move on your
own material, for the listener on the slide) · reset · Take C (the twist, unseen
until its slide) · closing (review and the TED credit).
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Any, Dict, List, Tuple

from pptx import Presentation
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches

from .deck import (BAR_Y, BLUE, BLUE_TINT, CONTENT_W, GRAY, GRAY_LIGHT, MARGIN, NAVY, SLIDE_H, SLIDE_W,
                   _background, _ensure_use_timings, _notes, _rect, _register_notes_master, _spoiler_guard, _text,
                   _timer, fit_font_size, make_show_copy, set_auto_animations, set_transition)
from .stage import TAKES, credit, segment_text, short_credit

HEADER = "WEEKEND STAGE"
RESET_LINES = ("Breathe out. Shake out your hands. Find the lens again.",)


def _st(cfg: Dict[str, Any]) -> Dict[str, Any]:
    return cfg.get("stage", {})


def slide_durations(session: Dict[str, Any], cfg: Dict[str, Any]) -> List[int]:
    """intro, Take A, reset, Take B, reset, Take C (the closing slide has no timer)."""
    st = _st(cfg)
    a, b, c = (int(x) for x in session["take_seconds"])
    reset = int(st.get("reset_seconds", 20))
    return [int(st.get("intro_seconds", 15)), a, reset, b, reset, c]


def default_durations(cfg: Dict[str, Any]) -> List[int]:
    """A typical weekend (week 1's lengths), for prompts that run before a deck exists."""
    return slide_durations({"take_seconds": [190, 150, 90]}, cfg)


def chapters(session: Dict[str, Any], cfg: Dict[str, Any], offset: float = 0.0) -> List[Tuple[int, str]]:
    """YouTube chapters: the intro, then one per take (each reset rides at the end of the take before it)."""
    d = slide_durations(session, cfg)
    starts = [d[0], d[0] + d[1] + d[2], d[0] + d[1] + d[2] + d[3] + d[4]]
    return [(0, "Intro")] + [(int(offset + s), name) for s, name in zip(starts, TAKES)]


def _label(s, text: str) -> None:
    _text(s, MARGIN, 0.7, 9.5, 0.35, [(text.upper(), {"size": 14, "bold": True, "color": BLUE, "spacing": 150})])


def _take_timer(s, seconds: int, cfg: Dict[str, Any], label: str) -> None:
    cue = int(_st(cfg).get("wrap_up_cue_seconds", 20))
    effects = _timer(s, seconds, label=label, ticks=False, cue=(max(5, seconds - cue), "Wrap up"))
    set_transition(s, seconds * 1000)
    set_auto_animations(s, effects)


def _mmss(seconds: int) -> str:
    return f"{seconds // 60}:{seconds % 60:02d}"


def _intro_slide(prs, session: Dict[str, Any], stats: Dict[str, Any], cfg: Dict[str, Any]) -> None:
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _background(s)
    talk = session["talk"]
    phase = session.get("phase") or ""
    _label(s, f"{HEADER}  ·  {phase}" if phase else HEADER)
    _text(s, MARGIN, 1.45, 8.0, 1.2, [(f"Week {session['day_number']}", {"size": 66, "color": NAVY})],
          anchor=MSO_ANCHOR.BOTTOM)
    weekend = dt.date.fromisoformat(session["date"])
    _text(s, MARGIN, 2.75, 8.2, 0.5, [(f"Weekend of {weekend.strftime('%d %B %Y')}", {"size": 24, "color": GRAY})])
    _text(s, MARGIN, 3.55, 8.2, 0.9, [(talk["title"], {"size": 26, "bold": True, "color": NAVY}),
                                       (talk["speaker"], {"size": 20, "color": GRAY, "newline": True})])
    _text(s, MARGIN, 4.65, 8.2, 0.9, [("Move to steal:  ", {"size": 17, "bold": True, "color": BLUE}),
                                       (talk["move"], {"size": 17, "color": NAVY})], line_spacing=1.1)
    px, pw = 9.25, SLIDE_W - MARGIN - 9.25
    _rect(s, px, 1.45, pw, 2.2, BLUE_TINT)
    _text(s, px, 1.7, pw, 0.9, [(str(int(stats.get("current", 0))), {"size": 54, "bold": True, "color": BLUE})],
          align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    _text(s, px, 2.6, pw, 0.35, [("week streak", {"size": 14, "color": NAVY})], align=PP_ALIGN.CENTER)
    _text(s, px, 3.1, pw, 0.35, [("3 takes · on camera", {"size": 13, "color": GRAY_LIGHT})], align=PP_ALIGN.CENTER)
    intro = slide_durations(session, cfg)[0]
    effects = _timer(s, intro, label=f"Starting in {intro} seconds — stand tall, eyes on the lens", ticks=False)
    set_transition(s, intro * 1000)
    set_auto_animations(s, effects)
    _notes(s, "The camera is recording. Beat sheet in reach, not in hand. Look at the lens, not the screen.")


def _take_a_slide(prs, session: Dict[str, Any], cfg: Dict[str, Any], seconds: int) -> None:
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _background(s)
    talk = session["talk"]
    _label(s, f"{TAKES[0]}  ·  {_mmss(seconds)}")
    _text(s, MARGIN, 1.35, CONTENT_W, 0.5, [("Perform the segment from your beat sheet, as the speaker would.",
                                             {"size": 22, "color": NAVY})])
    _text(s, MARGIN, 2.05, CONTENT_W, 0.5, [("Segment:  ", {"size": 18, "bold": True, "color": BLUE}),
                                             (segment_text(session["segment"]), {"size": 18, "color": NAVY})],
          name="Segment")
    size = fit_font_size(talk["move"], CONTENT_W, 1.6, sizes=(36, 34, 32, 30, 28))
    _text(s, MARGIN, 2.75, CONTENT_W, 1.6, [(talk["move"], {"size": size, "bold": True, "color": NAVY})],
          anchor=MSO_ANCHOR.MIDDLE, line_spacing=1.05, name="Move")
    _text(s, MARGIN, 4.6, CONTENT_W, 0.45, [("Hit the beats, not the words.", {"size": 20, "color": BLUE})])
    # above the timer row, so it never meets the "Wrap up" cue at the bar's right end
    _text(s, MARGIN, BAR_Y - 0.9, CONTENT_W, 0.3, [("After " + short_credit(talk), {"size": 13, "color": GRAY})],
          name="Credit")
    _take_timer(s, seconds, cfg, TAKES[0])
    _notes(s, "Mirror: copy the speaker's pace, pauses and gestures. If you lose a line, say the beat in your own "
              "words and keep going.")


def _reset_slide(prs, cfg: Dict[str, Any], seconds: int, next_name: str, next_line: str) -> None:
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _background(s)
    _label(s, "Reset")
    _text(s, MARGIN, 1.6, CONTENT_W, 1.0, [(RESET_LINES[0], {"size": 34, "color": NAVY})])
    _text(s, MARGIN, 3.0, CONTENT_W, 1.2, [("Next:  ", {"size": 22, "bold": True, "color": BLUE}),
                                            (next_name, {"size": 22, "bold": True, "color": NAVY}),
                                            (next_line, {"size": 18, "color": GRAY, "newline": True,
                                                         "space_before": 6})])
    effects = _timer(s, seconds, label="Reset", ticks=False)
    set_transition(s, seconds * 1000)
    set_auto_animations(s, effects)
    _notes(s, "Keep recording. One slow breath out before the next take.")


def _take_b_slide(prs, session: Dict[str, Any], cfg: Dict[str, Any], seconds: int) -> None:
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _background(s)
    tb = session["talk"]["take_b"]
    _label(s, f"{TAKES[1]}  ·  {_mmss(seconds)}")
    _text(s, MARGIN, 1.3, CONTENT_W, 0.5, [(f"TO {tb['listener'].upper()}", {"size": 18, "bold": True, "color": BLUE}),
                                            (f"  ·  cares about {tb['cares']}", {"size": 18, "color": GRAY})],
          name="Listener")
    size = fit_font_size(tb["prompt"], CONTENT_W, 2.6, sizes=(38, 36, 34, 32, 30, 28))
    _text(s, MARGIN, 1.95, CONTENT_W, 2.6, [(tb["prompt"], {"size": size, "color": NAVY})], anchor=MSO_ANCHOR.MIDDLE,
          line_spacing=1.05, name="Prompt")
    _text(s, MARGIN, 4.75, CONTENT_W, 0.45, [("Same move as Take A:  ", {"size": 18, "bold": True, "color": BLUE}),
                                              (session["talk"]["move"], {"size": 18, "color": GRAY})])
    _take_timer(s, seconds, cfg, TAKES[1])
    _notes(s, "Your own material, the speaker's move. Speak to the listener on the slide, then stop.")


def _take_c_slide(prs, session: Dict[str, Any], cfg: Dict[str, Any], seconds: int) -> None:
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _background(s)
    _label(s, f"{TAKES[2]}  ·  {_mmss(seconds)}")
    twist = session["twist"]
    size = fit_font_size(twist, CONTENT_W, 3.0, sizes=(40, 38, 36, 34, 32, 30))
    _text(s, MARGIN, 1.5, CONTENT_W, 3.0, [(twist, {"size": size, "color": NAVY})], anchor=MSO_ANCHOR.MIDDLE,
          line_spacing=1.05, name="Twist")
    _take_timer(s, seconds, cfg, TAKES[2])
    _notes(s, "The twist is the point: adapt, don't restart.")


def _closing_slide(prs, session: Dict[str, Any]) -> None:
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _background(s)
    _label(s, "Session complete")
    _text(s, MARGIN, 1.3, CONTENT_W, 0.9, [("That’s this weekend’s stage.", {"size": 44, "color": NAVY})])
    _text(s, MARGIN, 2.3, CONTENT_W, 0.9, [
        ("Recording stops on its own. Review: watch Take A beside the original in two windows, "
         "then pick one fix for next weekend.", {"size": 18, "color": GRAY})], line_spacing=1.1)
    _text(s, MARGIN, 3.5, CONTENT_W, 1.4, [
        ("THIS WEEKEND’S TALK", {"size": 13, "bold": True, "color": BLUE, "spacing": 150}),
        (credit(session["talk"]), {"size": 15, "color": NAVY, "newline": True, "space_before": 6}),
    ], line_spacing=1.1, name="Credit")
    set_transition(s, None)


def build_deck(session: Dict[str, Any], stats: Dict[str, Any], cfg: Dict[str, Any], out_dir: Path) -> Tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    prs = Presentation()
    prs.slide_width = Emu(int(Inches(SLIDE_W)))
    prs.slide_height = Emu(int(Inches(SLIDE_H)))
    d = slide_durations(session, cfg)
    _intro_slide(prs, session, stats, cfg)
    _take_a_slide(prs, session, cfg, d[1])
    _reset_slide(prs, cfg, d[2], TAKES[1], "The same move, your own material, for the listener on the slide.")
    _take_b_slide(prs, session, cfg, d[3])
    _reset_slide(prs, cfg, d[4], TAKES[2], "A twist you haven't seen. Adapt, don't restart.")
    _take_c_slide(prs, session, cfg, d[5])
    _closing_slide(prs, session)
    _register_notes_master(prs)
    _ensure_use_timings(prs)
    _spoiler_guard(prs)
    cp = prs.core_properties
    cp.title = f"Weekend Stage — Week {session['day_number']} ({session['date']})"
    cp.author = "FDE Impromptu Coach"
    stem = f"{session['date']}_Stage"
    pptx_path = out_dir / f"{stem}.pptx"
    tmp = out_dir / f".{stem}.tmp.pptx"
    prs.save(str(tmp))
    tmp.replace(pptx_path)
    ppsx_path = out_dir / f"{stem}.ppsx"
    make_show_copy(pptx_path, ppsx_path)
    return pptx_path, ppsx_path


def render_slide_pngs(session: Dict[str, Any], cfg: Dict[str, Any], out_dir: Path) -> List[Path]:
    """Unused: a video practice uploads its camera recording, not slides."""
    return []
