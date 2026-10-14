"""YouTube details for the learning track's videos: title, description and thumbnail.

You upload each topic's video yourself (the coach's own uploads are locked to private), so the coach
prepares the details and, when you ship with the link, sets them on your video:

* **title**: "Day 7 · Why 30 test cases can lie: error bars | FDE First Principles";
* **description**: built from what the video says (your three "In my words" answers are its outline),
  plus what surprised you, the maths, the free resources, your notebook on GitHub, the previous video,
  and the open-source coach that runs the series;
* **thumbnail**: the impromptu title card's minimalist blue look (white, navy, one blue accent, a
  streak card) with the topic title and a track progress bar.

The files land in the topic folder's `video/` (thumbnail.png and youtube.md, ready to paste) and are
committed with the topic, so the GitHub journal shows the same card.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional

COACH_REPO = "https://github.com/rajchampaneriya/fde-impromptu-coach"
SERIES = "FDE First Principles"
VIDEO_DIR = "video"
THUMBNAIL = "thumbnail.png"
DETAILS = "youtube.md"
TITLE_TEMPLATE = "Day {day} · {title} | FDE First Principles"
ABOUT = ("A public learning log: a software architect learning AI from first principles for the Forward Deployed "
         "Engineer role. One topic at a time, built from scratch and explained in plain words.")
TAGS = ["FDE First Principles", "first principles", "AI engineering", "forward deployed engineer",
        "machine learning", "LLM", "learning in public"]
HASHTAGS = "#FirstPrinciples #AIEngineering #ForwardDeployedEngineer"
PLACEHOLDER = "…"

NAVY, BLUE, GRAY, GRAY_L = "#0B2545", "#1F5FBF", "#5B6B7F", "#8A98A9"
BLUE_SOFT, BLUE_TINT = "#DCE7F7", "#F1F6FD"


def _section(cfg: Dict[str, Any]) -> Dict[str, Any]:
    return cfg.get("learn", {})


def _clean(text: str, limit: int) -> str:
    """YouTube refuses < and > in titles and descriptions; keep within the length limit."""
    text = (text or "").replace("<", "").replace(">", "")
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def display_title(t: Dict[str, Any]) -> str:
    """The topic title without the 'Article: ' prefix, first letter capitalised."""
    title = re.sub(r"^Article:\s*", "", t["title"])
    return title[:1].upper() + title[1:]


# --------------------------------------------------------------------------- what the video says

def _strip(text: str) -> str:
    text = re.sub(r"<!--.*?-->", "", text or "", flags=re.S).replace(PLACEHOLDER, " ")
    return re.sub(r"[ \t]+", " ", "\n".join(ln.strip() for ln in text.strip().splitlines())).strip()


def readme_parts(readme_text: str) -> Dict[str, str]:
    """The learner's own words from a topic README: the three explanations and 'What surprised me'."""
    parts: Dict[str, str] = {}
    words = readme_text.split("## In my words", 1)[1].split("\n## ", 1)[0] if "## In my words" in readme_text else ""
    words = re.sub(r"<!--.*?-->", "", words, flags=re.S)
    for m in re.finditer(r"^\*\*For (an? )?(\w+):\*\*(.*?)(?=^\*\*For |\Z)", words, flags=re.S | re.M):
        text = _strip(m.group(3))
        if text:
            parts[m.group(2).lower()] = text
    m = re.search(r"^## What surprised me\s*\n(.*?)(?=^## |\Z)", readme_text, flags=re.S | re.M)
    if m and _strip(m.group(1)):
        parts["surprised"] = _strip(m.group(1))
    return parts


def video_title(t: Dict[str, Any], cfg: Dict[str, Any]) -> str:
    template = _section(cfg).get("video_title_template") or TITLE_TEMPLATE
    return _clean(template.format(day=t["day"], title=display_title(t), series=SERIES), 100)


def description(t: Dict[str, Any], cfg: Dict[str, Any], readme_text: str, *, n_topics: int,
                project: Dict[str, Any], n_projects: int, folder_link: str = "", track_link: str = "",
                article: str = "", previous: Optional[Dict[str, str]] = None) -> str:
    """The YouTube description: a hook, what the video says (in the learner's words), how to learn it,
    where the work is, and the series links."""
    sec = _section(cfg)
    site = str(sec.get("article_site") or "rajc.work").strip()
    parts = readme_parts(readme_text)
    lines = [t["question"], "",
             f"Day {t['day']} of {n_topics} in {SERIES} · Project {project['n']} of {n_projects}: {project['title']}",
             str(sec.get("video_about") or ABOUT), ""]
    if article:
        lines += [f"Read the article: {article}", ""]
    said = [(label, parts.get(key)) for key, label in
            (("beginner", "For a beginner"), ("engineer", "For an engineer"), ("customer", "For a customer"))]
    if any(text for _, text in said):
        lines.append("In this video")
        lines += [f"▸ {label}: {text}" for label, text in said if text]
        lines.append("")
    else:
        lines += [f"Why it matters for an FDE: {t['why']}", ""]
    if parts.get("surprised"):
        lines += ["What surprised me", parts["surprised"], ""]
    if t.get("math"):
        lines += [f"Maths in this topic: {t['math']['idea']}. {t['math']['plain']}", ""]
    lines.append("Learn it yourself (free)")
    lines += [f"• {x['title']}: {x['url']}" for x in t.get("learn", [])]
    lines.append("")
    if folder_link:
        work = {"notebook": "notebook", "code": "code", "diagram": "diagram", "doc": "write-up",
                "article": "draft"}.get(t.get("artifact", ""), "work")
        lines += [f"My {work} and journal for this topic", folder_link]
        if track_link:
            lines.append(f"The whole learning log: {track_link}")
        lines.append("")
    if previous and previous.get("url"):
        lines += [f"Previous: Day {previous['day']} · {previous['title']}: {previous['url']}", ""]
    lines += ["How this series runs",
              "Every topic drops on a schedule with a deadline, a calendar event and this video as its finish line; "
              "each project ends with an article. The coach that runs it is open source: FDE Impromptu Coach, "
              f"{COACH_REPO}",
              f"Articles: https://{site}", "", HASHTAGS]
    return _clean("\n".join(lines), 4900)


def metadata(t: Dict[str, Any], cfg: Dict[str, Any], readme_text: str, **links: Any) -> Dict[str, Any]:
    """title, description, tags and categoryId for YouTube's snippet."""
    tags = list(_section(cfg).get("video_tags") or TAGS)[:15]
    return {"title": video_title(t, cfg), "description": description(t, cfg, readme_text, **links),
            "tags": tags, "categoryId": str(cfg.get("youtube", {}).get("category_id", "27"))}


# --------------------------------------------------------------------------- thumbnail

def _wrap(draw, text: str, font, max_w: int) -> List[str]:
    lines: List[str] = []
    for word in text.split():
        trial = f"{lines[-1]} {word}" if lines else word
        if lines and draw.textlength(trial, font=font) <= max_w:
            lines[-1] = trial
        else:
            lines.append(word)
    return lines


def render_thumbnail(t: Dict[str, Any], out_png: Path, *, project: Dict[str, Any], n_topics: int,
                     n_projects: int, streak: int, project_steps: int = 0, boundaries: Optional[List[int]] = None,
                     site: str = "rajc.work") -> Optional[Path]:
    """A 1280x720 PNG in the impromptu title card's look: label, Day N, the topic title, the project,
    a streak card on the right and the track's progress along the bottom."""
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        return None
    from .deck import pil_font as font

    W, H = 1280, 720
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    left, card_x = 80, 960
    left_w = card_x - left - 60

    def fit(text: str, size: int, bold: bool, max_w: int) -> int:
        while size > 14 and d.textlength(text, font=font(size, bold)) > max_w:
            size -= 2
        return size

    kind = "  ·  ARTICLE" if t.get("artifact") == "article" else ""
    label = f"{SERIES.upper()}  ·  PROJECT {project['n']} OF {n_projects}{kind}"
    d.text((left, 70), label, font=font(fit(label, 26, True, left_w), True), fill=BLUE)
    d.text((left, 122), f"Day {t['day']}", font=font(104, True), fill=NAVY)

    # the topic title: as big as fits in at most three lines
    title = display_title(t)
    for size in range(56, 32, -2):
        lines = _wrap(d, title, font(size, True), left_w)
        if len(lines) <= (2 if size >= 44 else 3):
            break
    y = 262
    for line in lines:
        d.text((left, y), line, font=font(size, True), fill=NAVY)
        y += int(size * 1.2)
    y += 18
    sub = f"Project {project['n']}, written up for {site}" if t.get("artifact") == "article" else project["title"]
    d.text((left, y), sub, font=font(fit(sub, 30, False, left_w), False), fill=GRAY)
    if t.get("math"):
        maths = f"Maths: {t['math']['idea']}"
        d.text((left, y + 46), maths, font=font(fit(maths, 24, False, left_w), False), fill=GRAY_L)

    # streak card, as on the impromptu title card
    px, py, pw, ph = card_x, 140, 240, 340
    d.rounded_rectangle((px, py, px + pw, py + ph), radius=24, fill=BLUE_TINT, outline=BLUE_SOFT)
    d.text((px + pw // 2, py + 95), str(int(streak)), font=font(100, True), fill=BLUE, anchor="mm")
    d.text((px + pw // 2, py + 180), "DAY STREAK", font=font(26), fill=GRAY, anchor="mm")
    topic_line = f"Step {t['step']} of {project_steps}" if project_steps else f"Topic {t['day']} of {n_topics}"
    d.text((px + pw // 2, py + 265), topic_line, font=font(fit(topic_line, 22, False, pw - 30)), fill=GRAY_L,
           anchor="mm")

    # track progress, like the deck's timer bar, with a tick at every project boundary
    bx0, bx1, by, bh = left, W - left, 628, 12
    d.text((bx0, by - 40), f"TRACK PROGRESS  ·  TOPIC {t['day']} OF {n_topics}", font=font(18, True), fill=GRAY_L)
    d.rounded_rectangle((bx0, by, bx1, by + bh), radius=bh // 2, fill=BLUE_SOFT)
    done = bx0 + int((bx1 - bx0) * min(1.0, t["day"] / max(1, n_topics)))
    d.rounded_rectangle((bx0, by, max(bx0 + bh, done), by + bh), radius=bh // 2, fill=BLUE)
    for day in boundaries or []:
        x = bx0 + int((bx1 - bx0) * day / max(1, n_topics))
        d.rectangle((x - 1, by - 4, x + 1, by + bh + 4), fill="white")
    out_png.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_png, "PNG", optimize=True)
    return out_png


# --------------------------------------------------------------------------- the files in the topic folder

def details_markdown(t: Dict[str, Any], meta: Dict[str, Any], thumbnail: Optional[Path]) -> str:
    thumb = (f"![Thumbnail]({THUMBNAIL})\n\nUpload `{THUMBNAIL}` as the custom thumbnail (YouTube Studio → "
             "Details → Thumbnail)." if thumbnail else "_No thumbnail: Pillow is not installed._")
    return (f"# YouTube details · Day {t['day']}\n\n"
            "The coach sets these on your video when you ship with `fde-coach learn done --video <link>` "
            "(YouTube connected with `fde-coach youtube-auth`). Not connected? Paste them in YouTube Studio.\n\n"
            f"## Title\n\n```\n{meta['title']}\n```\n\n"
            f"## Description\n\n```\n{meta['description']}\n```\n\n"
            f"## Tags\n\n```\n{', '.join(meta['tags'])}\n```\n\n"
            f"## Thumbnail\n\n{thumb}\n")


def write_files(folder: Path, t: Dict[str, Any], meta: Dict[str, Any], **thumb_args: Any) -> Dict[str, Any]:
    """Write video/thumbnail.png and video/youtube.md. Returns their paths (thumbnail may be None)."""
    out = folder / VIDEO_DIR
    out.mkdir(parents=True, exist_ok=True)
    thumb = render_thumbnail(t, out / THUMBNAIL, **thumb_args)
    details = out / DETAILS
    details.write_text(details_markdown(t, meta, thumb), encoding="utf-8")
    return {"thumbnail": thumb, "details": details}
