"""Pronunciation practice deck (same blue/Calibri look as the FDE deck) and
1920x1080 Pillow renders of each slide for the YouTube video."""
from __future__ import annotations

import datetime as dt
import logging
import re
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

log = logging.getLogger("fdecoach")
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches, Pt

from .deck import (BAR_Y, BLUE, BLUE_SOFT, BLUE_TINT, CONTENT_W, FONT, GRAY, GRAY_LIGHT, MARGIN, NAVY,
                   SLIDE_H, SLIDE_W, WHITE, _background, _ensure_use_timings, _notes, _register_notes_master,
                   _rect, _spoiler_guard, _text, _timer, fit_font_size, make_show_copy,
                   set_auto_animations, set_transition)

HEADER = "PRONUNCIATION PRACTICE"


def _pron(cfg: Dict[str, Any]) -> Dict[str, Any]:
    return cfg.get("pronunciation", {})


def slide_durations(cfg: Dict[str, Any]) -> List[int]:
    p = _pron(cfg)
    return [int(p.get("intro_seconds", 10)), int(p.get("warmup_seconds", 45)),
            int(p.get("round1_seconds", 60)), int(p.get("round2_seconds", 75)),
            int(p.get("round3_seconds", 60)), int(p.get("words_seconds", 30))]


def session_seconds(cfg: Dict[str, Any]) -> int:
    return sum(slide_durations(cfg))


def chapters(session: Dict[str, Any], cfg: Dict[str, Any], offset: float = 0.0) -> List[Tuple[int, str]]:
    names = ["Warm-up words", "Round 1", "Round 2 with pen", "Round 3", "Words again"]
    durs = slide_durations(cfg)
    marks: List[Tuple[int, str]] = [(0, "Intro")]
    t = durs[0]
    for name, secs in zip(names, durs[1:]):
        marks.append((int(offset + t), name))
        t += secs
    return marks


# --------------------------------------------------------------------------- runs

def _paragraph_runs(paragraph: str, targets: Sequence[str], size: int) -> List[Tuple[str, Dict[str, Any]]]:
    """Paragraph split into runs; target words bold blue."""
    words = [t["word"].lower() for t in targets]
    pattern = re.compile(r"\b(" + "|".join(re.escape(w) for w in words) + r")\b", re.IGNORECASE)
    runs: List[Tuple[str, Dict[str, Any]]] = []
    pos = 0
    for m in pattern.finditer(paragraph):
        if m.start() > pos:
            runs.append((paragraph[pos:m.start()], {"size": size, "color": NAVY}))
        runs.append((m.group(0), {"size": size, "bold": True, "color": BLUE}))
        pos = m.end()
    if pos < len(paragraph):
        runs.append((paragraph[pos:], {"size": size, "color": NAVY}))
    return runs


# --------------------------------------------------------------------------- slides

def _intro_slide(prs, session: Dict[str, Any], stats: Dict[str, Any], cfg: Dict[str, Any]) -> None:
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _background(s)
    date = dt.date.fromisoformat(session["date"])
    _text(s, MARGIN, 0.7, 9.0, 0.35, [(f"{HEADER}  ·  PEN METHOD", {"size": 14, "bold": True,
                                        "color": BLUE, "spacing": 150})])
    _text(s, MARGIN, 1.45, 8.0, 1.2, [(f"Day {session['day_number']}", {"size": 66, "color": NAVY})],
          anchor=MSO_ANCHOR.BOTTOM)
    _text(s, MARGIN, 2.75, 8.0, 0.5, [(date.strftime("%A, %d %B %Y"), {"size": 24, "color": GRAY})])
    _text(s, MARGIN, 3.6, 11.0, 1.6, [
        ("Hold a pen between your teeth for Round 2 only.", {"size": 22, "color": NAVY, "newline": True}),
        ("Read slowly. Exaggerate the consonants.", {"size": 22, "color": NAVY, "newline": True}),
        ("Every target word appears twice — land both.", {"size": 22, "color": NAVY, "newline": True}),
    ], line_spacing=1.3)
    px, pw = 9.25, SLIDE_W - MARGIN - 9.25
    _rect(s, px, 1.45, pw, 1.6, BLUE_TINT)
    _text(s, px, 1.7, pw, 0.9, [(str(int(stats.get("current", 0))), {"size": 54, "bold": True, "color": BLUE})],
          align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    _text(s, px, 2.6, pw, 0.35, [("day streak", {"size": 14, "color": NAVY})], align=PP_ALIGN.CENTER)
    intro = int(_pron(cfg).get("intro_seconds", 10))
    effects = _timer(s, intro, label=f"Starting in {intro} seconds — pen ready, shoulders down", ticks=False)
    set_transition(s, intro * 1000)
    set_auto_animations(s, effects)
    _notes(s, "Audio recording is running. Settle, breathe, keep the pen within reach for Round 2.")


def _words_slide(prs, session: Dict[str, Any], cfg: Dict[str, Any], seconds: int, label: str,
                 again: bool = False) -> None:
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _background(s)
    _text(s, MARGIN, 0.7, 9.0, 0.35, [(label.upper(), {"size": 14, "bold": True, "color": BLUE, "spacing": 150})])
    runs: List[Tuple[str, Dict[str, Any]]] = []
    show_tips = len(session["target_words"]) <= 6
    for i, t in enumerate(session["target_words"], 1):
        runs.append((t["word"], {"size": 26 if show_tips else 24, "bold": True, "color": NAVY, "newline": True,
                                 "space_before": 8 if i > 1 else 0}))
        runs.append((f"   {t.get('stress') or t.get('respelling', '')}", {"size": 17, "bold": True, "color": BLUE}))
        tip = (t.get("tip") or "").strip()
        if tip and show_tips:
            runs.append((tip[:80], {"size": 13, "color": GRAY, "newline": True}))
    _text(s, MARGIN, 1.3, CONTENT_W, 4.75, runs, line_spacing=1.0)
    foot = "Each word slowly, then at normal speed." if again else "Say each word twice, slowly."
    _text(s, MARGIN, 6.05, CONTENT_W, 0.35, [(foot, {"size": 18, "color": GRAY})])
    effects = _timer(s, seconds, label=label, ticks=False)
    set_transition(s, seconds * 1000)
    set_auto_animations(s, effects)


def _round_slide(prs, session: Dict[str, Any], cfg: Dict[str, Any], seconds: int, label: str,
                 cue: str = "") -> None:
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _background(s)
    _text(s, MARGIN, 0.7, 8.0, 0.35, [(label.upper(), {"size": 14, "bold": True, "color": BLUE, "spacing": 150})])
    if cue:
        _text(s, SLIDE_W - MARGIN - 4.2, 0.6, 4.2, 0.5, [(cue, {"size": 20, "bold": True, "color": BLUE})],
              align=PP_ALIGN.RIGHT)
    size = fit_font_size(session["paragraph"], CONTENT_W, 4.55, sizes=(32, 30, 28, 26, 24, 22))
    runs = _paragraph_runs(session["paragraph"], session["target_words"], size)
    _text(s, MARGIN, 1.4, CONTENT_W, 4.55, runs, line_spacing=1.15)
    effects = _timer(s, seconds, label=label, ticks=False)
    set_transition(s, seconds * 1000)
    set_auto_animations(s, effects)
    _notes(s, f"{cue or 'Read naturally.'} Land every bold word twice before the bar runs out.")


def _closing_slide(prs, session: Dict[str, Any]) -> None:
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _background(s)
    _text(s, MARGIN, 0.7, 8.0, 0.35, [("SESSION COMPLETE", {"size": 14, "bold": True, "color": BLUE,
                                        "spacing": 150})])
    _text(s, MARGIN, 1.3, CONTENT_W, 0.9, [("That’s today’s pronunciation.", {"size": 44, "color": NAVY})])
    _text(s, MARGIN, 2.3, CONTENT_W, 0.5, [("Recording stops on its own. Listen back once: find one word to sharpen.",
                                            {"size": 18, "color": GRAY})])
    set_transition(s, None)


def build_deck(session: Dict[str, Any], stats: Dict[str, Any], cfg: Dict[str, Any], out_dir: Path) -> Tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    prs = Presentation()
    prs.slide_width = Emu(int(Inches(SLIDE_W)))
    prs.slide_height = Emu(int(Inches(SLIDE_H)))
    d = slide_durations(cfg)
    _intro_slide(prs, session, stats, cfg)
    _words_slide(prs, session, cfg, d[1], "Warm-up words")
    _round_slide(prs, session, cfg, d[2], "Round 1 · without pen")
    _round_slide(prs, session, cfg, d[3], "Round 2 · pen between teeth", "Pen between teeth. Over-articulate.")
    _round_slide(prs, session, cfg, d[4], "Round 3 · pen out", "Pen out. Slow and clear.")
    _words_slide(prs, session, cfg, d[5], "Words again", again=True)
    _closing_slide(prs, session)
    _register_notes_master(prs)
    _ensure_use_timings(prs)
    _spoiler_guard(prs)
    cp = prs.core_properties
    cp.title = f"Pronunciation Practice — Day {session['day_number']} ({session['date']})"
    cp.author = "FDE Impromptu Coach"
    stem = f"{session['date']}_Pronunciation"
    pptx_path = out_dir / f"{stem}.pptx"
    tmp = out_dir / f".{stem}.tmp.pptx"
    prs.save(str(tmp))
    tmp.replace(pptx_path)
    ppsx_path = out_dir / f"{stem}.ppsx"
    make_show_copy(pptx_path, ppsx_path)
    return pptx_path, ppsx_path


# --------------------------------------------------------------------------- PNG renders (video)

_W, _H = 1920, 1080
_NAVY, _BLUE, _GRAY, _SOFT, _TINT = "#0B2545", "#1F5FBF", "#5B6B7F", "#DCE7F7", "#F1F6FD"


def _fonts():
    from PIL import ImageFont
    cache = {}

    def get(size: int, bold: bool = False):
        key = (size, bold)
        if key not in cache:
            names = ["Arial Bold.ttf", "Arial.ttf"] if bold else ["Arial.ttf", "Helvetica.ttf"]
            for sub in ("Supplemental", ""):
                for name in names:
                    try:
                        cache[key] = ImageFont.truetype(f"/System/Library/Fonts/{sub}/{name}".replace("//", "/"),
                                                         size)
                        break
                    except OSError:
                        continue
                if key in cache:
                    break
            if key not in cache:
                cache[key] = ImageFont.load_default()
        return cache[key]

    return get


def _wrap_words(words: List[Tuple[str, bool]], draw, font_pair, max_w: int) -> List[List[Tuple[str, bool]]]:
    """Greedy wrap of (word, is_target) pairs; returns lines."""
    lines, line, w = [], [], 0
    for word, target in words:
        f = font_pair(target)
        ww = draw.textlength(word + " ", font=f)
        if line and w + ww > max_w:
            lines.append(line)
            line, w = [], 0
        line.append((word, target))
        w += ww
    if line:
        lines.append(line)
    return lines


def _draw_paragraph(draw, paragraph: str, targets: Sequence[str], xy, wh) -> None:
    get = _fonts()
    size = 44
    words = [t["word"].lower() for t in targets]
    import re as _re
    pattern = _re.compile(r"\b(" + "|".join(_re.escape(w) for w in words) + r")\b", _re.IGNORECASE)
    toks: List[Tuple[str, bool]] = []
    for piece in _re.findall(r"\S+\s*|\s+", paragraph):
        toks.append((piece.strip(), bool(pattern.search(piece))))  # search: "word," and "word." count too
    toks = [(w, t) for w, t in toks if w]
    while size >= 26:
        font_pair = lambda target: get(size, True) if target else get(size)  # noqa: E731
        lines = _wrap_words(toks, draw, font_pair, wh[0])
        if len(lines) * size * 1.35 <= wh[1]:
            break
        size -= 2
    x0, y0 = xy
    for line in lines:
        x = x0
        for word, target in line:
            f = get(size, True) if target else get(size)
            draw.text((x, y0), word, font=f, fill=_BLUE if target else _NAVY)
            x += draw.textlength(word + " ", font=f)
        y0 += int(size * 1.35)


def render_slide_pngs(session: Dict[str, Any], cfg: Dict[str, Any], out_dir: Path) -> List[Path]:
    """One 1920x1080 PNG per slide (intro..closing). Returns file paths in order."""
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        log.warning("Pillow not installed; cannot render pronunciation slides")
        return []
    out_dir.mkdir(parents=True, exist_ok=True)
    get = _fonts()
    d = slide_durations(cfg)
    date = dt.date.fromisoformat(session["date"])
    paths: List[Path] = []

    def new_slide() -> Tuple[Any, Any]:
        img = Image.new("RGB", (_W, _H), "white")
        return img, ImageDraw.Draw(img)

    def save(img, idx: int, name: str) -> None:
        p = out_dir / f"slide{idx}_{name}.png"
        img.save(p, "PNG")
        paths.append(p)

    img, dr = new_slide()
    dr.text((128, 90), f"{HEADER}  ·  PEN METHOD", font=get(36, True), fill=_BLUE)
    dr.text((128, 170), f"Day {session['day_number']}", font=get(150, True), fill=_NAVY)
    dr.text((128, 400), date.strftime("%A, %d %B %Y"), font=get(56), fill=_GRAY)
    for i, line in enumerate(["Hold a pen between your teeth for Round 2 only.",
                              "Read slowly. Exaggerate the consonants.",
                              "Every target word appears twice — land both."]):
        dr.text((128, 520 + i * 70), line, font=get(44, True), fill=_NAVY)
    save(img, 1, "intro")

    def words_img(idx: int, name: str, title: str, foot: str) -> None:
        img, dr = new_slide()
        dr.text((128, 80), title.upper(), font=get(34, True), fill=_BLUE)
        y = 190
        for t in session["target_words"]:
            dr.text((128, y), t["word"], font=get(58, True), fill=_NAVY)
            dr.text((560, y + 8), t["stress"], font=get(42, True), fill=_BLUE)
            if t.get("tip"):
                dr.text((560, y + 66), t["tip"], font=get(30), fill=_GRAY)
            y += 128
        dr.text((128, 980), foot, font=get(38), fill=_GRAY)
        save(img, idx, name)

    words_img(2, "warmup", "Warm-up words", "Say each word twice, slowly.")
    words_img(6, "again", "Words again", "Each word slowly, then at normal speed.")

    for idx, (name, title, cue) in enumerate((
            ("round1", "Round 1 · without pen", ""),
            ("round2", "Round 2 · pen between teeth", "Pen between teeth. Over-articulate."),
            ("round3", "Round 3 · pen out", "Pen out. Slow and clear.")), start=3):
        img, dr = new_slide()
        dr.text((128, 80), title.upper(), font=get(34, True), fill=_BLUE)
        if cue:
            w = dr.textlength(cue, font=get(44, True))
            dr.text((_W - 128 - w, 72), cue, font=get(44, True), fill=_BLUE)
        _draw_paragraph(dr, session["paragraph"], session["target_words"], (128, 200), (1664, 780))
        dr.rectangle((128, 1000, _W - 128, 1020), fill=_SOFT)
        save(img, idx, name)

    img, dr = new_slide()
    dr.text((128, 90), "SESSION COMPLETE", font=get(34, True), fill=_BLUE)
    dr.text((128, 200), "That’s today’s pronunciation.", font=get(90, True), fill=_NAVY)
    dr.text((128, 360), "Recording stops on its own. Listen back once: find one word to sharpen.",
            font=get(42), fill=_GRAY)
    save(img, 7, "closing")
    return paths
