"""Daily first-principles learning track ("fde-coach learn").

A topic drops in the morning (default 05:50) into your public learning repo
(for example github.com/<you>/continuous-learning) and gets as many mornings as
its time estimate needs (one to three). You learn, build and record it, then ship
it with `fde-coach learn done --video <YouTube link>` before its deadline. Each
project ends with an article on your site, shipped with `--article <link>`.
The repo itself is the memory: progress.json, TODAY.md, one folder per topic with
your notebook / diagram / article and a journal README, all committed and pushed.

Google Calendar gets a 06:00 event with the whole task every morning, plus a
"not shipped yet" event on the topic's last evening that is deleted as soon as you
ship. Rules: one topic, no menus; a missed topic comes back at minimum scope (you
never skip ahead); partial work can ship, labelled partial (an article cannot:
it is the project's finish line). Finished early? `fde-coach learn next`.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import logging
import math
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from . import gcal, macos
from .config import ASSETS_DIR, parse_hhmm
from .state import file_lock, now

log = logging.getLogger("fdecoach")

PATH_FILE = ASSETS_DIR / "learning_path.json"
STARTERS = ASSETS_DIR / "learn_starters"
SHIPPED = ("shipped", "late", "partial")
ICON = {"shipped": "✅", "late": "🕒", "partial": "🟡", "missed": "❌", "open": "⏳"}
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
YOUTUBE = re.compile(r"^https://(www\.|m\.)?(youtube\.com/(watch\?v=|shorts/|live/)|youtu\.be/)([\w-]{6,})")
SECRETS = [
    re.compile(r"sk-(ant-)?[A-Za-z0-9_\-]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"gh[pousr]_[A-Za-z0-9]{30,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{40,}"),
    re.compile(r"AIza[0-9A-Za-z\-_]{35}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"(?i)(api[_-]?key|secret|token|password)[\"']?\s*[:=]\s*[\"'][^\"'\s]{16,}[\"']"),
]
MAX_FILE_MB = 25
WORDS_HEADING = "## In my words"
NO_NOTES_HEADING = "## Without notes"
NO_NOTES_MIN_WORDS = 200
PLACEHOLDER = "…"
WORD = re.compile(r"[^\W_]+(?:['’-][^\W_]+)*")


class LearnError(RuntimeError):
    pass


# --------------------------------------------------------------------------- curriculum

_PATH: Dict[str, Any] = {}


def curriculum() -> Dict[str, Any]:
    if not _PATH:
        _PATH.update(json.loads(PATH_FILE.read_text(encoding="utf-8")))
    return _PATH


def topics() -> List[Dict[str, Any]]:
    return curriculum()["topics"]


def topic(topic_id: str) -> Dict[str, Any]:
    for t in topics():
        if t["id"] == topic_id:
            return t
    raise LearnError(f"Unknown topic {topic_id!r}")


def next_topic(topic_id: Optional[str]) -> Optional[Dict[str, Any]]:
    if topic_id is None:
        return topics()[0]
    ids = [t["id"] for t in topics()]
    i = ids.index(topic_id) + 1
    return topics()[i] if i < len(ids) else None


def project(n: int) -> Dict[str, Any]:
    return next(p for p in curriculum()["projects"] if p["n"] == n)


def is_article(t: Dict[str, Any]) -> bool:
    """The last topic of each project: an article on your site, the project's finish line."""
    return t.get("artifact") == "article"


def topic_mornings(t: Dict[str, Any], attempt: int = 1) -> int:
    """Mornings a topic gets: its estimate on the first attempt, half of it (rounded up) at minimum scope."""
    m = max(1, int((t.get("time") or {}).get("mornings", 1)))
    return m if attempt <= 1 else max(1, math.ceil(m / 2))


def minutes(t: Dict[str, Any], part: str, default: int) -> int:
    return int((t.get("time") or {}).get(part, default))


# --------------------------------------------------------------------------- settings and time

def section(cfg: Dict[str, Any]) -> Dict[str, Any]:
    return cfg.get("learn", {})


def repo_path(cfg: Dict[str, Any]) -> Optional[Path]:
    raw = section(cfg).get("repo_path") or ""
    return Path(raw).expanduser() if raw else None


def track_dir(cfg: Dict[str, Any]) -> Path:
    repo = repo_path(cfg)
    if repo is None:
        raise LearnError("Learning repo not set up yet. Run: fde-coach learn init --repo ~/Code/continuous-learning")
    return repo / section(cfg).get("track_dir", "fde-first-principles")


def initialized(cfg: Dict[str, Any]) -> bool:
    try:
        return (track_dir(cfg) / "progress.json").exists()
    except LearnError:
        return False


def _at(date: dt.date, hhmm: str) -> dt.datetime:
    h, m = parse_hhmm(hhmm)
    return dt.datetime.combine(date, dt.time(h, m))


def drop_time(cfg: Dict[str, Any]) -> str:
    return section(cfg).get("drop_time", "05:50")


def learning_date(t: dt.datetime, cfg: Dict[str, Any]) -> dt.date:
    """The learning day a moment belongs to: a day runs from one drop to the next."""
    h, m = parse_hhmm(drop_time(cfg))
    return (t - dt.timedelta(hours=h, minutes=m)).date()


def is_rest_day(date: dt.date, cfg: Dict[str, Any]) -> bool:
    return DAYS[date.weekday()] in (section(cfg).get("rest_days") or [])


def next_learning_day(date: dt.date, cfg: Dict[str, Any]) -> dt.date:
    d = date + dt.timedelta(days=1)
    for _ in range(7):
        if not is_rest_day(d, cfg):
            return d
        d += dt.timedelta(days=1)
    return d


def learning_days(start: dt.date, mornings: int, cfg: Dict[str, Any]) -> List[dt.date]:
    """The learning days a topic dropped on `start` covers (rest days are skipped)."""
    days = [start]
    for _ in range(max(1, mornings) - 1):
        days.append(next_learning_day(days[-1], cfg))
    return days


def deadline_for(date: dt.date, cfg: Dict[str, Any], mornings: int = 1) -> dt.datetime:
    """The drop after the topic's last morning."""
    return _at(learning_days(date, mornings, cfg)[-1] + dt.timedelta(days=1), drop_time(cfg))


def morning_of(cur: Dict[str, Any], date: dt.date, cfg: Dict[str, Any]) -> Tuple[int, int]:
    """(k, n): `date` is morning k of the n mornings the open topic has (k is capped at n)."""
    n = max(1, int(cur.get("mornings", 1)))
    if not cur.get("dropped_on"):
        return 1, n
    days = learning_days(dt.date.fromisoformat(cur["dropped_on"]), n, cfg)
    return min(n, sum(1 for d in days if d <= date) or 1), n


def _morning_label(k: int, n: int) -> str:
    return f"morning {k} of {n}" if n > 1 else ""


def _fmt(t: dt.datetime) -> str:
    return f"{DAYS[t.weekday()]} {t.day} {t.strftime('%b')}, {t.strftime('%H:%M')}"


# --------------------------------------------------------------------------- progress (lives in the repo)

def load_progress(cfg: Dict[str, Any]) -> Dict[str, Any]:
    path = track_dir(cfg) / "progress.json"
    if not path.exists():
        raise LearnError("Track not initialised. Run: fde-coach learn init --repo PATH")
    return json.loads(path.read_text(encoding="utf-8"))


def save_progress(cfg: Dict[str, Any], progress: Dict[str, Any]) -> Path:
    path = track_dir(cfg) / "progress.json"
    path.write_text(json.dumps(progress, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def streak(progress: Dict[str, Any], cfg: Dict[str, Any], on: dt.date) -> int:
    """Consecutive learning days (rest days skipped) covered by a shipped topic. A topic covers the mornings
    it was given up to the day it shipped; the mornings of the topic still open do not break the streak."""
    covered = set()
    for e in progress.get("log", []):
        if e.get("status") not in SHIPPED or not e.get("dropped_on"):
            continue
        last = learning_date(dt.datetime.fromisoformat(e["shipped_at"]), cfg) if e.get("shipped_at") else None
        for d in learning_days(dt.date.fromisoformat(e["dropped_on"]), int(e.get("mornings", 1)), cfg):
            if last is None or d <= last:
                covered.add(d)
        if last is not None:
            covered.add(max(last, dt.date.fromisoformat(e["dropped_on"])))
    cur = progress.get("current") or {}
    still_open = set()
    if cur.get("dropped_on") and not cur.get("shipped_at"):
        still_open = set(learning_days(dt.date.fromisoformat(cur["dropped_on"]), int(cur.get("mornings", 1)), cfg))
    d, count = on, 0
    for _ in range(800):
        if is_rest_day(d, cfg) or (d not in covered and (d == on or d in still_open)):
            d -= dt.timedelta(days=1)
            continue
        if d not in covered:
            break
        count += 1
        d -= dt.timedelta(days=1)
    return count


# --------------------------------------------------------------------------- git

def _git(repo: Path, *args: str, timeout: int = 60) -> Tuple[int, str]:
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0", GIT_SSH_COMMAND="ssh -o BatchMode=yes")
    try:
        proc = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, timeout=timeout, env=env)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 1, str(exc)
    return proc.returncode, (proc.stdout + proc.stderr).strip()


def commit(cfg: Dict[str, Any], paths: List[Path], message: str) -> bool:
    """Commit exactly these paths (never anything else you have staged). Returns True if a commit was made."""
    repo = repo_path(cfg)
    rel = sorted({str(p.relative_to(repo)) for p in paths})
    code, out = _git(repo, "add", "-A", "--", *rel)
    if code != 0:
        raise LearnError(f"git add failed: {out}")
    code, out = _git(repo, "diff", "--cached", "--quiet", "--", *rel)
    if code == 0:
        return False
    code, out = _git(repo, "commit", "-q", "-m", message, "--", *rel)
    if code != 0:
        raise LearnError(f"git commit failed: {out}")
    return True


def push(ctx) -> str:
    """Best effort: pull fast-forward first, then push. A failure is remembered and retried later."""
    cfg = ctx.cfg
    repo = repo_path(cfg)
    if not section(cfg).get("push", True):
        return "push disabled"
    _git(repo, "pull", "--ff-only", "-q", timeout=90)
    code, out = _git(repo, "push", "-q", "origin", "HEAD", timeout=120)
    from .app import update_runtime
    update_runtime(ctx, lambda r: r.data.update(learn_push_pending=code != 0, learn_push_error=out[-300:] if code else ""))
    if code != 0:
        log.warning("learn: git push failed: %s", out)
        return f"push failed (will retry): {out[-200:]}"
    return "pushed"


def repo_url(cfg: Dict[str, Any]) -> str:
    url = section(cfg).get("repo_url") or ""
    if url:
        return url.rstrip("/")
    repo = repo_path(cfg)
    if repo is None:
        return ""
    code, out = _git(repo, "remote", "get-url", "origin")
    if code != 0:
        return ""
    out = out.strip()
    m = re.match(r"git@([^:]+):(.+?)(\.git)?$", out)
    if m:
        return f"https://{m.group(1)}/{m.group(2)}"
    return re.sub(r"\.git$", "", re.sub(r"https://[^@]+@", "https://", out))


def branch(cfg: Dict[str, Any]) -> str:
    code, out = _git(repo_path(cfg), "rev-parse", "--abbrev-ref", "HEAD")
    return out.strip() if code == 0 else "main"


def web_link(cfg: Dict[str, Any], rel: str) -> str:
    base = repo_url(cfg)
    track = section(cfg).get("track_dir", "fde-first-principles")
    return f"{base}/tree/{branch(cfg)}/{track}/{rel}" if base else ""


# --------------------------------------------------------------------------- texts

def time_line(t: Dict[str, Any], attempt: int = 1) -> str:
    n = topic_mornings(t, attempt)
    total = minutes(t, "total", 70)
    if attempt > 1:
        return f"**Time:** minimum scope, {n} morning{'s' if n > 1 else ''} (about {total} minutes for the full topic)"
    return f"**Time:** about {total} minutes, over {n} morning{'s' if n > 1 else ''}"


def article_site(cfg: Optional[Dict[str, Any]] = None) -> str:
    return str(section(cfg or {}).get("article_site") or "rajc.work").strip().lower()


def ship_command(t: Dict[str, Any], cfg: Optional[Dict[str, Any]] = None) -> str:
    if is_article(t):
        return f"fde-coach learn done --article https://{article_site(cfg)}/blog/…"
    return "fde-coach learn done --video https://youtu.be/…"


def task_markdown(t: Dict[str, Any], attempt: int = 1) -> str:
    p = project(t["project"])
    lines = [f"> **First-principles question:** {t['question']}", "", f"**Why it matters for an FDE:** {t['why']}", "",
             time_line(t, attempt), ""]
    if attempt > 1:
        lines += [f"**Attempt {attempt}: minimum scope.** Ship at least this: {t['minimum']}", ""]
    if t.get("setup"):
        lines += ["### Set up", *[f"- {s}" for s in t["setup"]], ""]
    lines += [f"### 1 · Learn (about {minutes(t, 'learn', 20)} minutes)"]
    lines += [f"- [{x['title']}]({x['url']}) · {x['minutes']} min. {x['how']}" for x in t["learn"]]
    if t.get("math"):
        lines += ["", f"**Maths you need today: {t['math']['idea']}.** {t['math']['plain']}"]
    build = "Write and publish" if is_article(t) else "Build"
    lines += ["", f"### 2 · {build} (about {minutes(t, 'build', 40)} minutes)",
              *[f"{i}. {s}" for i, s in enumerate(t["build"], 1)]]
    if "notebook.ipynb" in t.get("starter", []):
        lines += ["", "Your starter notebook is `notebook.ipynb` in this folder: fill in the **TODO** cells and run the "
                      "✅ self-check at the end."]
    if is_article(t):
        lines += ["", "Your starter is `article.md` in this folder: Hugo front matter plus a skeleton. Copy it into "
                      "your site when it is ready."]
    record = "3 · Record (optional for an article)" if is_article(t) else "3 · Record (5 minutes or less)"
    lines += ["", "### Done when", *[f"- [ ] {s}" for s in t["done_when"]],
              "", f"### {record}", *[f"- {s}" for s in t["record"]],
              "", f"_Tempted to do more? Park it in `later.md`: {t['parking']}_",
              "", f"<sub>Project {p['n']} · {p['title']}: {p['goal']}</sub>"]
    return "\n".join(lines)


def topic_readme(t: Dict[str, Any], dropped_on: dt.date, deadline: dt.datetime, attempt: int) -> str:
    if is_article(t):
        return article_readme(t, dropped_on, deadline, attempt)
    return f"""# Day {t['day']} · {t['title']}

<!-- learn:status -->
{status_block(t, 'open', attempt, dropped_on, deadline)}
<!-- /learn:status -->

{task_markdown(t, attempt)}

{WORDS_HEADING}
<!-- Fill these in before you ship (plain, simple English is perfect). Claude can help you turn what you said
     in your video into text, but keep your own words. -->
**For a beginner:** {PLACEHOLDER}

**For an engineer:** {PLACEHOLDER}

**For a customer:** {PLACEHOLDER}

## What surprised me
{PLACEHOLDER}

## How I used AI
{PLACEHOLDER}

## Video
<!-- learn:video -->
_Added when you ship._
<!-- /learn:video -->
"""


def article_readme(t: Dict[str, Any], dropped_on: dt.date, deadline: dt.datetime, attempt: int) -> str:
    return f"""# Day {t['day']} · {t['title']}

<!-- learn:status -->
{status_block(t, 'open', attempt, dropped_on, deadline)}
<!-- /learn:status -->

{task_markdown(t, attempt)}

{NO_NOTES_HEADING}
<!-- Step 1, before you open any notebook: about 300 words from memory. What you built, what you measured,
     what surprised you. No notes, no AI. Whatever you can't write is what to revisit. -->
{PLACEHOLDER}

## How I used AI
{PLACEHOLDER}

## The article
<!-- learn:article -->
_Added when you ship._
<!-- /learn:article -->

## Video
<!-- learn:video -->
_Optional for an article._
<!-- /learn:video -->
"""


def status_block(t: Dict[str, Any], status: str, attempt: int, dropped_on: dt.date, deadline: dt.datetime,
                 shipped_at: str = "", morning: Tuple[int, int] = (1, 1)) -> str:
    head = f"**Status:** {ICON.get(status, '')} {status}"
    if status == "open" and morning[1] > 1:
        head += f" · {_morning_label(*morning)}"
    if attempt > 1:
        head += f" · attempt {attempt}"
    head += f" · dropped {dropped_on.isoformat()} · ship by {_fmt(deadline)}"
    if shipped_at:
        head += f" · shipped {shipped_at[:16].replace('T', ' ')}"
    return head + f" · project {t['project']}, step {t['step']}"


def _replace_block(text: str, name: str, body: str) -> str:
    pattern = re.compile(rf"(<!-- learn:{name} -->).*?(<!-- /learn:{name} -->)", re.S)
    return pattern.sub(lambda m: m.group(1) + "\n" + body + "\n" + m.group(2), text, count=1)


def video_id(url: str) -> str:
    m = YOUTUBE.match(url or "")
    return m.group(4) if m else ""


def video_block(url: str) -> str:
    vid = video_id(url)
    if vid:
        return f"[![Watch the video](https://img.youtube.com/vi/{vid}/hqdefault.jpg)]({url})"
    return f"[Watch the video]({url})" if url else "_No video for this one._"


def article_block(url: str) -> str:
    return f"📝 **Published:** [{url}]({url})" if url else "_Not published yet._"


def article_url_problem(url: str, cfg: Dict[str, Any]) -> str:
    """'' if the link is a page on your site, otherwise what is wrong with it."""
    site = article_site(cfg)
    parsed = urlparse(url or "")
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or not host:
        return f"{url} is not an https link"
    if host != site and not host.endswith("." + site):
        return f"{url} is not on {site} (the article must be published on your site)"
    if parsed.path.strip("/") == "":
        return f"{url} is the home page: give the article's own link"
    return ""


def count_words(text: str) -> int:
    return len(WORD.findall(text or ""))


def article_body(text: str) -> str:
    """The article without front matter, comments, placeholders and markdown links' targets."""
    text = text or ""
    m = re.match(r"^(---|\+\+\+)\s*\n.*?\n\1\s*\n", text, re.S)
    if m:
        text = text[m.end():]
    text = re.sub(r"<!--.*?-->", " ", text, flags=re.S)
    text = re.sub(r"\]\([^)]*\)", "]", text)          # keep link text, drop URLs
    return text.replace(PLACEHOLDER, " ")


def section_text(readme_text: str, heading: str) -> str:
    part = readme_text.split(heading, 1)[1] if heading in readme_text else ""
    part = part.split("\n## ", 1)[0]
    return re.sub(r"<!--.*?-->", "", part, flags=re.S).replace(PLACEHOLDER, " ")


# --------------------------------------------------------------------------- track files

TRACK_README = """# FDE First Principles

A public learning log. A topic drops in the morning at 06:00 (IST) and gets one to three mornings, depending on
its size. I learn it, build it (a notebook, code or an Excalidraw diagram) and explain it on video. Each project
ends with an article on my site. The goal: understand AI systems from first principles, the way a Forward
Deployed Engineer needs to: measure before believing, know what is inside the model, and recommend the simplest
design the evidence supports.

Six projects, {n} topics: {projects}.

Maths shows up only on the day a project needs it. Almost everything runs on my own Mac (Ollama) for free; one
final evaluation uses a stronger model under a hard spending cap. The drops, deadlines and this table are managed
by [fde-coach learn](https://github.com/rajchampaneriya/fde-impromptu-coach).

## Progress
<!-- learn:progress -->
<!-- /learn:progress -->
"""

GITIGNORE = """.venv/
__pycache__/
.ipynb_checkpoints/
data/cache/
data/downloads/
*.executed.ipynb
*.mov
*.mp4
*.m4a
.env
.DS_Store
"""

PYPROJECT = """[project]
name = "fde-first-principles"
version = "0.1.0"
description = "Daily first-principles AI learning notebooks"
requires-python = ">=3.10"
dependencies = [
    "numpy",
    "pandas",
    "matplotlib",
    "requests",
    "ipykernel",
    "jupyterlab",
]
"""

LATER = """# Later

Ideas that are good, but not for today. Parking them here keeps each day small and shippable.
Revisit this list at the end of each project.

"""


def ensure_track_files(cfg: Dict[str, Any]) -> List[Path]:
    track = track_dir(cfg)
    track.mkdir(parents=True, exist_ok=True)
    projects = ", ".join(f"{p['n']}. {p['title']}" for p in curriculum()["projects"])
    files = {
        "README.md": TRACK_README.format(n=len(topics()), projects=projects),
        ".gitignore": GITIGNORE,
        "pyproject.toml": PYPROJECT,
        "later.md": LATER,
    }
    written = []
    for name, text in files.items():
        path = track / name
        if not path.exists():
            path.write_text(text, encoding="utf-8")
            written.append(path)
    return written


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else ""


def prepare_topic(cfg: Dict[str, Any], t: Dict[str, Any], dropped_on: dt.date, deadline: dt.datetime,
                  attempt: int, mornings: int = 1) -> Tuple[List[Path], Dict[str, str]]:
    """Create the topic folder (README + starter files). Never overwrites your work."""
    track = track_dir(cfg)
    folder = track / t["folder"]
    folder.mkdir(parents=True, exist_ok=True)
    written: List[Path] = []
    hashes: Dict[str, str] = {}
    for rel in t.get("starter", []):
        src = STARTERS / t["id"] / rel
        if rel.startswith("_track/"):
            dst, key = track / rel[len("_track/"):], "/" + rel[len("_track/"):]
        else:
            dst, key = folder / rel, rel
        if not dst.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dst)
            written.append(dst)
        hashes[key] = _hash(src)
    readme = folder / "README.md"
    morning = (1, max(1, mornings))
    if not readme.exists():
        readme.write_text(topic_readme(t, dropped_on, deadline, attempt), encoding="utf-8")
    text = readme.read_text(encoding="utf-8")
    readme.write_text(_replace_block(text, "status", status_block(t, "open", attempt, dropped_on, deadline,
                                                                   morning=morning)), encoding="utf-8")
    written.append(readme)
    return written, hashes


def next_drop_day(cur: Dict[str, Any], cfg: Dict[str, Any]) -> dt.date:
    """When the topic after a shipped one drops: the learning day after the day it shipped."""
    shipped = learning_date(dt.datetime.fromisoformat(cur["shipped_at"]), cfg) if cur.get("shipped_at") else None
    return next_learning_day(shipped or dt.date.fromisoformat(cur["dropped_on"]), cfg)


def write_today(cfg: Dict[str, Any], progress: Dict[str, Any], note: str = "") -> Path:
    track = track_dir(cfg)
    cur = progress.get("current")
    path = track / "TODAY.md"
    if note:
        body = note
    elif not cur:
        body = "# Today\n\nNothing has dropped yet. The first topic drops at the next morning drop."
    else:
        t = topic(cur["topic_id"])
        deadline = dt.datetime.fromisoformat(cur["deadline"])
        if cur.get("shipped_at"):
            nxt = next_topic(t["id"])
            nxt_day = next_drop_day(cur, cfg)
            body = (f"# Today: shipped {ICON[cur.get('status', 'shipped')]}\n\nDay {t['day']} · "
                    f"[{t['title']}]({t['folder']}/README.md) is {cur.get('status', 'shipped')}.\n\n"
                    + (f"Next: **Day {nxt['day']} · {nxt['title']}** drops {DAYS[nxt_day.weekday()]} "
                       f"{nxt_day.isoformat()} at {drop_time(cfg)}. Time left today? `fde-coach learn next` "
                       f"starts it now." if nxt else "That was the last topic. 🎉"))
        else:
            today = learning_date(now(), cfg)
            k, n = morning_of(cur, max(today, dt.date.fromisoformat(cur["dropped_on"])), cfg)
            label = f" · **{_morning_label(k, n)}**" if n > 1 else ""
            partial = ("An article ships only when it is live (it is the project's finish line)." if is_article(t)
                       else "Partial work can ship too (`--partial`).")
            body = (f"# Today · Day {t['day']} of {len(topics())}: {t['title']}\n\n"
                    f"**Ship by {_fmt(deadline)}**{label} · folder: [{t['folder']}]({t['folder']}/README.md)\n\n"
                    + task_markdown(t, int(cur.get("attempt", 1))) +
                    f"\n\n### Ship it\n```\n{ship_command(t, cfg)}\n```\n"
                    f"or tell Claude Code: *ship today's topic*. {partial}")
    path.write_text(body + "\n", encoding="utf-8")
    return path


def write_track_readme(cfg: Dict[str, Any], progress: Dict[str, Any]) -> Path:
    path = track_dir(cfg) / "README.md"
    if not path.exists():
        ensure_track_files(cfg)
    rows = ["| Day | Date | Topic | Proof | Status |", "|---|---|---|---|---|"]
    entries = list(progress.get("log", []))
    cur = progress.get("current")
    if cur and not cur.get("shipped_at"):
        entries.append(dict(cur, status="open"))
    for e in entries:
        t = topic(e["topic_id"])
        proof = " ".join(([f"[📝]({e['article']})"] if e.get("article") else [])
                         + ([f"[▶]({e['video']})"] if e.get("video") else []))
        attempt = f" (attempt {e['attempt']})" if int(e.get("attempt", 1)) > 1 else ""
        rows.append(f"| {t['day']} | {e['dropped_on']} | [{t['title']}]({t['folder']}/README.md){attempt} | {proof} | "
                    f"{ICON.get(e['status'], '')} {e['status']} |")
    shipped = sum(1 for e in progress.get("log", []) if e.get("status") in SHIPPED)
    rows.append("")
    rows.append(f"**{shipped} of {len(topics())} topics shipped.**")
    text = path.read_text(encoding="utf-8")
    if "<!-- learn:progress -->" not in text:
        text += "\n## Progress\n<!-- learn:progress -->\n<!-- /learn:progress -->\n"
    path.write_text(_replace_block(text, "progress", "\n".join(rows)), encoding="utf-8")
    return path


# --------------------------------------------------------------------------- commands

def init(ctx, repo: Path, start: str = "tomorrow", track: str = "") -> List[str]:
    from .config import save_config
    repo = repo.expanduser().resolve()
    code, out = _git(repo, "rev-parse", "--show-toplevel")
    if code != 0:
        raise LearnError(f"{repo} is not a git repository. Clone yours first, e.g.\n"
                         f"  git clone https://github.com/<you>/continuous-learning ~/Code/continuous-learning")
    protected = [Path.home() / d for d in ("Documents", "Desktop", "Downloads")]
    if any(str(repo).startswith(str(p)) for p in protected):
        raise LearnError("macOS blocks the 05:50 background job from Documents, Desktop and Downloads. Move the "
                         "clone (for example to ~/Code/continuous-learning) and run init again.")
    user = json.loads(ctx.paths.config.read_text(encoding="utf-8")) if ctx.paths.config.exists() else {}
    learn_cfg = user.setdefault("learn", {})
    learn_cfg["repo_path"] = str(repo)
    if track:
        learn_cfg["track_dir"] = track
    save_config(ctx.paths, user)
    from .config import load_config
    ctx.cfg = load_config(ctx.paths)
    out_lines = [f"Learning repo: {repo}", f"Track folder: {track_dir(ctx.cfg)}"]
    written = ensure_track_files(ctx.cfg)
    if not (track_dir(ctx.cfg) / "progress.json").exists():
        progress = {"version": 1, "track": curriculum()["track"], "started": now().date().isoformat(),
                    "current": None, "log": []}
        written.append(save_progress(ctx.cfg, progress))
        written.append(write_today(ctx.cfg, progress))
        written.append(write_track_readme(ctx.cfg, progress))
    if commit(ctx.cfg, written, "learn: start the FDE First Principles track"):
        out_lines.append("Committed the track files. " + push(ctx))
    from . import scheduler
    for line in scheduler.install(ctx.cfg, ctx.paths):
        if "learn" in line:
            out_lines.append("Schedule: " + line)
    if start == "today":
        res = drop(ctx)
        out_lines.append(f"Dropped today's topic: {res.get('title')}")
    else:
        out_lines.append(f"The first topic drops tomorrow at {drop_time(ctx.cfg)} (or now: fde-coach learn drop).")
    return out_lines


def _still_open(cur: Optional[Dict[str, Any]], t_now: dt.datetime) -> bool:
    """An unshipped topic whose deadline has not passed yet (it has more mornings to go)."""
    return bool(cur and cur.get("dropped_on") and not cur.get("shipped_at") and cur.get("deadline")
                and t_now < dt.datetime.fromisoformat(cur["deadline"]))


def _shipped_on(cur: Optional[Dict[str, Any]], cfg: Dict[str, Any]) -> Optional[dt.date]:
    if cur and cur.get("shipped_at"):
        return learning_date(dt.datetime.fromisoformat(cur["shipped_at"]), cfg)
    return None


def drop(ctx, scheduled: bool = False, early: bool = False) -> Dict[str, Any]:
    """The morning drop. Safe to run any number of times: it only acts once per learning day.

    A topic with more than one morning stays open until its deadline; on its later mornings the drop only
    refreshes TODAY.md, the README status and the calendar. With `early=True` (`fde-coach learn next`) the
    next topic drops straight away once the current one has shipped, instead of at the next morning drop."""
    cfg = ctx.cfg
    if not section(cfg).get("enabled", True):
        return {"ok": True, "skipped": "learn.enabled is false"}
    if not initialized(cfg):
        return {"ok": True, "skipped": "not initialised (fde-coach learn init --repo PATH)"}
    with file_lock(ctx.paths, "learn", blocking=True):
        t_now = now()
        today = learning_date(t_now, cfg)
        progress = load_progress(cfg)
        cur = progress.get("current")
        if early:
            if cur and not cur.get("shipped_at"):
                t = topic(cur["topic_id"])
                raise LearnError(f"Day {t['day']} · {t['title']} is still open. Ship it first: {ship_command(t, cfg)}")
        elif cur and (cur["dropped_on"] == today.isoformat() or _shipped_on(cur, cfg) == today
                      or (_still_open(cur, t_now) and cur.get("seen_on") == today.isoformat())):
            return {"ok": True, "already": True, "topic": cur["topic_id"]}
        if progress.get("paused_until") and today.isoformat() < progress["paused_until"]:
            return {"ok": True, "skipped": f"paused until {progress['paused_until']}"}
        _git(repo_path(cfg), "pull", "--ff-only", "-q", timeout=90)
        progress = load_progress(cfg)
        cur = progress.get("current")
        if progress.get("paused_until"):
            progress.pop("paused_until")
            if progress.get("resume_topic") and not cur:
                cur = {"topic_id": progress.pop("resume_topic"), "dropped_on": "", "attempt": 0, "resume": True}
        if is_rest_day(today, cfg) and not early:
            note = "# Today: rest day 🌿\n\nNo new topic today."
            if cur and not cur.get("shipped_at") and not cur.get("resume"):
                t = topic(cur["topic_id"])
                if _still_open(cur, t_now):
                    note += (f" Your open topic, Day {t['day']} · {t['title']}, is due "
                             f"{_fmt(dt.datetime.fromisoformat(cur['deadline']))}: no rush today.")
                else:
                    note += (f" Your open topic, Day {t['day']} · {t['title']}, is past its deadline: ship it today "
                             f"if you like (`fde-coach learn done`), otherwise it returns tomorrow at minimum scope.")
            paths = [write_today(cfg, progress, note)]
            commit(cfg, paths, f"learn: rest day {today.isoformat()}")
            push(ctx)
            return {"ok": True, "rest_day": True}
        if _still_open(cur, t_now) and not cur.get("resume"):
            # a later morning of a multi-morning topic: nothing is missed, nothing new drops
            t = topic(cur["topic_id"])
            cur["seen_on"] = today.isoformat()
            progress["current"] = cur
            k, n = morning_of(cur, today, cfg)
            deadline = dt.datetime.fromisoformat(cur["deadline"])
            attempt = int(cur.get("attempt", 1))
            paths = [save_progress(cfg, progress), write_today(cfg, progress), write_track_readme(cfg, progress)]
            readme = track_dir(cfg) / t["folder"] / "README.md"
            if readme.exists():
                readme.write_text(_replace_block(readme.read_text(encoding="utf-8"), "status", status_block(
                    t, "open", attempt, dt.date.fromisoformat(cur["dropped_on"]), deadline, morning=(k, n))),
                    encoding="utf-8")
                paths.append(readme)
            label = f"Day {t['day']} · {t['title']} ({_morning_label(k, n)})"
            commit(cfg, paths, f"learn: {label}")
            pushed = push(ctx)
            result = {"ok": True, "continuing": True, "topic": t["id"], "title": t["title"], "day": t["day"],
                      "attempt": attempt, "morning": k, "mornings": n,
                      "deadline": cur["deadline"], "folder": str(track_dir(cfg) / t["folder"]), "push": pushed}
            nxt = t
        else:
            if cur is None:
                nxt, attempt = next_topic(None), 1
            elif cur.get("resume"):
                nxt, attempt = topic(cur["topic_id"]), 1
            elif cur.get("shipped_at"):
                nxt, attempt = next_topic(cur["topic_id"]), 1
            else:
                progress.setdefault("log", []).append({"topic_id": cur["topic_id"], "dropped_on": cur["dropped_on"],
                                                       "attempt": cur.get("attempt", 1),
                                                       "mornings": cur.get("mornings", 1), "status": "missed"})
                nxt, attempt = topic(cur["topic_id"]), int(cur.get("attempt", 1)) + 1
            if nxt is None:
                progress["current"] = cur
                note = "# Track complete 🎉\n\nAll topics are shipped. Start your next track whenever you are ready."
                paths = [save_progress(cfg, progress), write_today(cfg, progress, note),
                         write_track_readme(cfg, progress)]
                commit(cfg, paths, "learn: track complete")
                push(ctx)
                return {"ok": True, "complete": True}
            mornings = topic_mornings(nxt, attempt)
            deadline = deadline_for(today, cfg, mornings)
            files, hashes = prepare_topic(cfg, nxt, today, deadline, attempt, mornings)
            progress["current"] = {"topic_id": nxt["id"], "folder": nxt["folder"], "dropped_on": today.isoformat(),
                                   "seen_on": today.isoformat(), "deadline": deadline.isoformat(timespec="minutes"),
                                   "attempt": attempt, "mornings": mornings, "starter_hashes": hashes}
            written = files + [save_progress(cfg, progress), write_today(cfg, progress),
                               write_track_readme(cfg, progress)]
            label = f"Day {nxt['day']} · {nxt['title']}" + (f" (attempt {attempt})" if attempt > 1 else "")
            commit(cfg, written, f"learn: drop {label}")
            pushed = push(ctx)
            result = {"ok": True, "topic": nxt["id"], "title": nxt["title"], "day": nxt["day"], "attempt": attempt,
                      "mornings": mornings, "deadline": deadline.isoformat(timespec="minutes"),
                      "folder": str(track_dir(cfg) / nxt["folder"]), "push": pushed}
    calendar_sync_safe(ctx)
    when = f"Ship by {_fmt(deadline)}" + (f" ({result['mornings']} mornings)" if result["mornings"] > 1 else "")
    macos.notify(f"📘 {label}", f"{when}. Ask Claude: what's today's topic?", subtitle=nxt["question"][:90])
    log.info("learn: %s %s (%s)", "continuing" if result.get("continuing") else "dropped", nxt["id"], pushed)
    return result


def words_filled(readme_text: str) -> bool:
    part = readme_text.split(WORDS_HEADING, 1)[-1].split("\n## ", 1)[0]
    part = re.sub(r"<!--.*?-->", "", part, flags=re.S)
    lines = [ln for ln in part.splitlines() if ln.startswith("**For ")]
    return bool(lines) and all(ln.split(":**", 1)[-1].strip() not in ("", PLACEHOLDER) for ln in lines)


def missing_items(cfg: Dict[str, Any], cur: Dict[str, Any], video: str, article: str = "") -> List[str]:
    t = topic(cur["topic_id"])
    track = track_dir(cfg)
    folder = track / t["folder"]
    missing = []
    for pattern in t.get("expect", []):
        base = track if pattern.startswith("/") else folder
        options = [p.lstrip("/") for p in pattern.split("|")]
        found = [m for opt in options for m in base.glob(opt)]
        if not found:
            missing.append(f"{pattern.split('|')[0]} is missing in {base.relative_to(track) if base != track else '.'}")
            continue
        key = pattern if pattern.startswith("/") else pattern
        starter_hash = (cur.get("starter_hashes") or {}).get(key)
        if starter_hash and all(_hash(m) == starter_hash for m in found):
            missing.append(f"{pattern} is still the untouched starter: do the TODOs first")
    readme = folder / "README.md"
    readme_text = readme.read_text(encoding="utf-8") if readme.exists() else ""
    if is_article(t):
        notes = count_words(section_text(readme_text, NO_NOTES_HEADING))
        if notes < NO_NOTES_MIN_WORDS:
            missing.append(f"README.md → 'Without notes': about 300 words from memory ({notes} so far, "
                           f"{NO_NOTES_MIN_WORDS} at least)")
        draft = folder / "article.md"
        if draft.exists():
            words, floor = count_words(article_body(draft.read_text(encoding="utf-8"))), int(t.get("min_words", 500))
            if words < floor:
                missing.append(f"article.md has {words} words: the minimum is {floor}")
        if not article:
            missing.append(f"the live article link (--article https://{article_site(cfg)}/blog/…)")
        else:
            problem = article_url_problem(article, cfg)
            if problem:
                missing.append(problem)
        if video and not video_id(video):
            missing.append(f"{video} does not look like a YouTube link")
        return missing
    if not words_filled(readme_text):
        missing.append("README.md → 'In my words': fill in the three explanations")
    if not video:
        missing.append("a video link (--video https://youtu.be/…)")
    elif not video_id(video):
        missing.append(f"{video} does not look like a YouTube link")
    return missing


def scan_secrets(paths: List[Path]) -> List[str]:
    hits = []
    for p in paths:
        if not p.is_file():
            continue
        if p.stat().st_size > MAX_FILE_MB * 1024 * 1024:
            hits.append(f"{p.name} is {p.stat().st_size // (1024 * 1024)} MB: videos belong on YouTube, not in git")
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for rx in SECRETS:
            m = rx.search(text)
            if m:
                line = text[:m.start()].count("\n") + 1
                hits.append(f"{p.name}:{line} looks like a secret ({m.group(0)[:12]}…). Remove it before shipping.")
                break
    return hits


def changed_files(cfg: Dict[str, Any]) -> List[Path]:
    repo, track = repo_path(cfg), track_dir(cfg)
    code, out = _git(repo, "status", "--porcelain", "-uall", "--", str(track.relative_to(repo)))
    files = []
    for line in out.splitlines() if code == 0 else []:
        rel = line[3:].split(" -> ")[-1].strip().strip('"')
        files.append(repo / rel)
    return files


def ship(ctx, video: str = "", partial: bool = False, note: str = "", article: str = "",
         no_video: bool = False) -> Dict[str, Any]:
    """Ship the open topic. An article topic needs its live link (`article`) and cannot ship partial: it is the
    project's finish line. `no_video` ships any other topic without a video, labelled partial."""
    cfg = ctx.cfg
    with file_lock(ctx.paths, "learn", blocking=True):
        progress = load_progress(cfg)
        cur = progress.get("current")
        if not cur:
            raise LearnError("Nothing to ship: no topic has dropped yet (fde-coach learn drop).")
        if cur.get("shipped_at"):
            raise LearnError("This topic is already shipped. The next one drops at the next morning drop "
                             "(or now: fde-coach learn next).")
        t = topic(cur["topic_id"])
        video, article = (video or "").strip(), (article or "").strip()
        if is_article(t):
            if partial:
                raise LearnError("An article can't ship partial: it is the project's finish line. Publish the "
                                 f"minimum instead ({t['minimum']}), then: {ship_command(t, cfg)}")
        else:
            partial = partial or no_video
        missing = missing_items(cfg, cur, video, article)
        if missing and not partial:
            hint = ("Finish these, then ship." if is_article(t) else "Finish these, or ship what you have with --partial.")
            raise LearnError("Not ready to ship yet:\n  - " + "\n  - ".join(missing) + "\n" + hint)
        if partial and not video and len(missing) >= 3:
            raise LearnError("Nothing to ship yet: add a video link, your explanation or your work first.")
        secrets = scan_secrets(changed_files(cfg))
        if secrets:
            raise LearnError("Stopped before publishing:\n  - " + "\n  - ".join(secrets))
        t_now = now()
        deadline = dt.datetime.fromisoformat(cur["deadline"])
        status = "partial" if partial else ("shipped" if t_now <= deadline else "late")
        folder = track_dir(cfg) / t["folder"]
        readme = folder / "README.md"
        text = readme.read_text(encoding="utf-8")
        shipped_at = t_now.isoformat(timespec="minutes")
        text = _replace_block(text, "status", status_block(t, status, int(cur.get("attempt", 1)),
                                                           dt.date.fromisoformat(cur["dropped_on"]), deadline,
                                                           shipped_at))
        text = _replace_block(text, "video", video_block(video) if video or not is_article(t)
                              else "_No video for this one._")
        if is_article(t):
            text = _replace_block(text, "article", article_block(article))
        readme.write_text(text, encoding="utf-8")
        cur.update(shipped_at=shipped_at, status=status, video=video)
        entry = {"topic_id": t["id"], "dropped_on": cur["dropped_on"], "attempt": cur.get("attempt", 1),
                 "mornings": cur.get("mornings", 1), "status": status, "shipped_at": shipped_at, "video": video}
        if article:
            cur["article"] = entry["article"] = article
        if note:
            entry["note"] = note
        if partial and missing:
            entry["missing"] = missing
        progress.setdefault("log", []).append(entry)
        save_progress(cfg, progress)
        write_today(cfg, progress)
        write_track_readme(cfg, progress)
        commit(cfg, [track_dir(cfg)], f"learn: {status} Day {t['day']} · {t['title']}")
        pushed = push(ctx)
    calendar_sync_safe(ctx)
    n = streak(progress, cfg, learning_date(t_now, cfg))
    nxt = next_topic(t["id"])
    after = ("Project finished. 🎉 " if is_article(t) else "") + (
        "Next topic at the next drop, or now: fde-coach learn next." if nxt else "Track complete.")
    macos.notify(f"{ICON[status]} Day {t['day']} {status}", f"{n}-day learning streak. {after}", sound="Hero")
    return {"ok": True, "status": status, "day": t["day"], "title": t["title"], "streak": n, "push": pushed,
            "missing": missing if partial else [], "link": web_link(cfg, t["folder"]), "article": article,
            "project_done": is_article(t)}


def today_info(ctx) -> Dict[str, Any]:
    cfg = ctx.cfg
    progress = load_progress(cfg)
    cur = progress.get("current")
    t_now = now()
    info: Dict[str, Any] = {"learning_date": learning_date(t_now, cfg).isoformat(),
                            "track_dir": str(track_dir(cfg)), "today_md": str(track_dir(cfg) / "TODAY.md")}
    if not cur:
        info["state"] = "nothing dropped yet"
        return info
    t = topic(cur["topic_id"])
    deadline = dt.datetime.fromisoformat(cur["deadline"])
    left = deadline - t_now
    k, n = morning_of(cur, learning_date(t_now, cfg), cfg)
    info.update(state="shipped" if cur.get("shipped_at") else ("overdue" if left.total_seconds() < 0 else "open"),
                topic=t, attempt=cur.get("attempt", 1), deadline=cur["deadline"],
                hours_left=round(left.total_seconds() / 3600, 1), folder=str(track_dir(cfg) / t["folder"]),
                status=cur.get("status", "open"), video=cur.get("video", ""), article=cur.get("article", ""),
                morning=k, mornings=n, minutes=minutes(t, "total", 70), is_article=is_article(t),
                ship_command=ship_command(t, cfg))
    if not cur.get("shipped_at"):
        info["missing_to_ship"] = missing_items(cfg, cur, "")
    return info


def status(ctx) -> Dict[str, Any]:
    cfg = ctx.cfg
    out: Dict[str, Any] = {"initialized": initialized(cfg), "enabled": section(cfg).get("enabled", True)}
    if not out["initialized"]:
        return out
    progress = load_progress(cfg)
    rt = ctx.runtime().data
    out.update(
        repo=str(repo_path(cfg)), track=str(track_dir(cfg)), drop_time=drop_time(cfg),
        shipped=sum(1 for e in progress.get("log", []) if e.get("status") in SHIPPED),
        missed=sum(1 for e in progress.get("log", []) if e.get("status") == "missed"),
        total=len(topics()), streak=streak(progress, cfg, learning_date(now(), cfg)),
        push_pending=bool(rt.get("learn_push_pending")), push_error=rt.get("learn_push_error", ""),
        calendar=gcal.is_configured(ctx.paths), paused_until=progress.get("paused_until"),
    )
    cur = progress.get("current")
    if cur:
        t = topic(cur["topic_id"])
        k, n = morning_of(cur, learning_date(now(), cfg), cfg)
        out["current"] = {"day": t["day"], "title": t["title"], "dropped_on": cur["dropped_on"],
                          "deadline": cur["deadline"], "status": cur.get("status", "open"),
                          "attempt": cur.get("attempt", 1), "morning": k, "mornings": n}
    out["projects_done"] = sum(1 for e in progress.get("log", [])
                               if e.get("status") in SHIPPED and is_article(topic(e["topic_id"])))
    return out


def pause(ctx, until: dt.date) -> str:
    cfg = ctx.cfg
    with file_lock(ctx.paths, "learn", blocking=True):
        progress = load_progress(cfg)
        progress["paused_until"] = until.isoformat()
        cur = progress.get("current")
        if cur and not cur.get("shipped_at"):
            # the open topic is not counted as missed: it drops again (same attempt) when the pause ends
            progress["current"] = None
            progress["resume_topic"] = cur["topic_id"]
        note = f"# Paused until {until.isoformat()}\n\nNo topics drop during a pause. Nothing counts as missed."
        paths = [save_progress(cfg, progress), write_today(cfg, progress, note)]
        commit(cfg, paths, f"learn: pause until {until.isoformat()}")
        push(ctx)
    calendar_sync_safe(ctx)
    return f"Paused until {until.isoformat()}. The next topic drops that morning."


def resume(ctx) -> str:
    cfg = ctx.cfg
    with file_lock(ctx.paths, "learn", blocking=True):
        progress = load_progress(cfg)
        progress.pop("paused_until", None)
        save_progress(cfg, progress)
    return "Resumed. The next topic drops at the next morning drop (or now: fde-coach learn drop)."


# --------------------------------------------------------------------------- Google Calendar

def _event_id(date: dt.date, kind: str) -> str:
    return f"fdelearn{date.strftime('%Y%m%d')}{kind}"


def _event_body(cfg: Dict[str, Any], t: Dict[str, Any], date: dt.date, kind: str, attempt: int = 1,
                deadline: Optional[dt.datetime] = None, morning: Tuple[int, int] = (1, 1)) -> Dict[str, Any]:
    sec = section(cfg)
    deadline = deadline or deadline_for(date, cfg, topic_mornings(t, attempt))
    link = web_link(cfg, t["folder"])
    if kind == "t":
        start = _at(date, sec.get("event_time", "06:00"))
        summary = (f"📘 Day {t['day']}/{len(topics())} · {t['title']}"
                   + (f" ({_morning_label(*morning)})" if morning[1] > 1 else "")
                   + (f" (attempt {attempt})" if attempt > 1 else ""))
        lines = [f"❓ {t['question']}", "", f"WHY: {t['why']}", "",
                 f"TIME: about {minutes(t, 'total', 70)} min over {topic_mornings(t)} morning(s). "
                 + (f"Today is {_morning_label(*morning)}." if morning[1] > 1 else ""), ""]
        if attempt > 1:
            lines += [f"MINIMUM TODAY: {t['minimum']}", ""]
        lines += [f"LEARN (~{minutes(t, 'learn', 20)} min):",
                  *[f"• {x['title']} — {x['url']} ({x['how']})" for x in t["learn"]]]
        if t.get("math"):
            lines += ["", f"MATHS: {t['math']['idea']}. {t['math']['plain']}"]
        build = "WRITE AND PUBLISH" if is_article(t) else "BUILD"
        record = "RECORD (optional)" if is_article(t) else "RECORD (≤ 5 min, 2 takes max)"
        proof = "<live article link>" if is_article(t) else "<YouTube link>"
        flag = "--article" if is_article(t) else "--video"
        lines += ["", f"{build} (~{minutes(t, 'build', 40)} min):", *[f"{i}. {s}" for i, s in enumerate(t["build"], 1)],
                  "", "DONE WHEN:", *[f"☐ {s}" for s in t["done_when"]],
                  "", f"{record}:", *[f"• {s}" for s in t["record"]],
                  "", f"SHIP BY {_fmt(deadline)}: fde-coach learn done {flag} {proof}"]
        if link:
            lines.append(f"Folder: {link}")
        reminders = [{"method": "popup", "minutes": 0}]
        color = str(sec.get("color_id", "9"))
    else:
        start = _at(date, sec.get("nudge_time", "21:00"))
        summary = f"⏳ Not shipped yet: Day {t['day']} · {t['title']}"
        how = (f"Publish the minimum, then: {ship_command(t, cfg)}" if is_article(t)
               else "Partial work counts: fde-coach learn done --partial")
        lines = [f"Ship by {_fmt(deadline)}. {how}", "This event disappears as soon as you ship."]
        reminders = []
        for hhmm in sec.get("nudge_popups", ["18:00", "21:00"])[:4]:
            mins = int((start - _at(date, hhmm)).total_seconds() // 60)
            if 0 <= mins <= 40320:
                reminders.append({"method": "popup", "minutes": mins})
        color = "11"
    end = start + dt.timedelta(minutes=int(sec.get("event_minutes", 15)))
    return {"id": _event_id(date, kind), "summary": summary, "description": "\n".join(lines)[:7900],
            "start": {"dateTime": start.astimezone().isoformat()}, "end": {"dateTime": end.astimezone().isoformat()},
            "reminders": {"useDefault": False, "overrides": reminders}, "colorId": color,
            "transparency": "transparent", "visibility": "private",
            "extendedProperties": {"private": {"fdelearn": t["id"]}}}


def wanted_events(cfg: Dict[str, Any], progress: Dict[str, Any], t_now: dt.datetime) -> Dict[str, Optional[Dict]]:
    """event id -> body (create/update) or None (delete if we created it).

    Every morning of the open topic gets its 06:00 event (created the morning it arrives); the evening
    "not shipped yet" nudge exists only on the topic's last morning."""
    want: Dict[str, Optional[Dict]] = {}
    cur = progress.get("current")
    if not cur or not cur.get("dropped_on"):
        return want
    t = topic(cur["topic_id"])
    attempt = int(cur.get("attempt", 1))
    deadline = dt.datetime.fromisoformat(cur["deadline"])
    day = dt.date.fromisoformat(cur.get("seen_on") or cur["dropped_on"])
    k, n = morning_of(cur, day, cfg)
    want[_event_id(day, "t")] = _event_body(cfg, t, day, "t", attempt, deadline, (k, n))
    nudge_at = _at(day, section(cfg).get("nudge_time", "21:00"))
    if cur.get("shipped_at"):
        want[_event_id(day, "n")] = None
        nxt = next_topic(t["id"])
        nday = next_drop_day(cur, cfg)
        if nxt and not progress.get("paused_until"):
            m = topic_mornings(nxt)
            want[_event_id(nday, "t")] = _event_body(cfg, nxt, nday, "t", 1, deadline_for(nday, cfg, m), (1, m))
    elif k == n and nudge_at > t_now:
        want[_event_id(day, "n")] = _event_body(cfg, t, day, "n", attempt, deadline, (k, n))
    return want


def calendar_sync(ctx, clear: bool = False) -> List[str]:
    cfg = ctx.cfg
    sec = section(cfg)
    if not initialized(cfg):
        return []
    if not gcal.is_configured(ctx.paths) and not macos.dry_run():
        return ["Learning calendar: Google Calendar not connected (run: fde-coach calendar-auth)."]
    from .app import update_runtime
    state: Dict[str, str] = dict(ctx.runtime().data.get("learn_gcal") or {})
    on = sec.get("calendar", True) and cfg.get("google_calendar", {}).get("enabled", True) and not clear
    t_now = now()
    want = wanted_events(cfg, load_progress(cfg), t_now) if on else {}
    if not on:
        today_key = t_now.strftime("%Y%m%d")
        want = {eid: None for eid, st in state.items() if st != "deleted" and eid[8:16] >= today_key}
    cal = str(cfg.get("google_calendar", {}).get("calendar_id", "primary"))
    out = []
    for eid, body in want.items():
        sig = "deleted" if body is None else hashlib.sha1(json.dumps(body, sort_keys=True).encode()).hexdigest()[:12]
        if state.get(eid, "deleted" if body is None else "") == sig:
            continue
        try:
            if body is None:
                result = gcal.delete_event(ctx.paths, cal, eid)
            else:
                result = gcal.ensure_event(ctx.paths, cal, body)
        except (gcal.CalendarAuthExpired, gcal.CalendarNotConfigured) as exc:
            out.append(f"learning calendar: {exc}")
            break
        except Exception as exc:  # noqa: BLE001 - offline: retried by the 15-minute tick
            log.warning("learn calendar %s failed: %s", eid, exc)
            out.append(f"{eid}: failed, will retry")
            continue
        state[eid] = sig
        out.append(f"{eid}: {result}")
    cutoff = (t_now - dt.timedelta(days=21)).strftime("%Y%m%d")
    state = {k: v for k, v in state.items() if k[8:16] >= cutoff}
    update_runtime(ctx, lambda r: r.data.update(learn_gcal=state))
    return out


def calendar_sync_safe(ctx) -> None:
    try:
        calendar_sync(ctx)
    except Exception:  # noqa: BLE001
        log.exception("learn calendar sync failed")


# --------------------------------------------------------------------------- 15-minute tick

def tick(ctx) -> str:
    """Catch up a missed drop (Mac asleep at the drop time), retry a failed push, keep the calendar right."""
    cfg = ctx.cfg
    if not section(cfg).get("enabled", True) or not initialized(cfg):
        return "off"
    progress = load_progress(cfg)
    cur = progress.get("current") or {}
    today = learning_date(now(), cfg)
    paused = progress.get("paused_until") and today.isoformat() < progress["paused_until"]
    rest_done = is_rest_day(today, cfg) and ctx.runtime().data.get("learn_rest_noted") == today.isoformat()
    seen = cur.get("seen_on") or cur.get("dropped_on")
    shipped_today = _shipped_on(cur, cfg) == today
    if seen != today.isoformat() and not shipped_today and not paused and not rest_done:
        result = drop(ctx)
        if result.get("rest_day"):
            from .app import update_runtime
            update_runtime(ctx, lambda r: r.data.update(learn_rest_noted=today.isoformat()))
        if result.get("topic") and not result.get("already"):
            return "continuing" if result.get("continuing") else "dropped"
    if ctx.runtime().data.get("learn_push_pending"):
        push(ctx)
    calendar_sync_safe(ctx)
    return "ok"
