"""Passage library: verbatim paragraphs from free, public-domain books, used as
the reading material for the legato and pronunciation practices instead of
AI-written text.

* Built-in passages ship in assets/passages.json. They are cut verbatim from
  Standard Ebooks / Project Gutenberg editions by
  scripts/tools/build_passage_library.py, which can also re-verify them.
* Learners add more from any free book: `fde-coach library import-gutenberg ID`
  (downloads the plain text from gutenberg.org on this Mac) or
  `fde-coach library import-file PATH` for any text they have the right to use.
  These live in ~/FDE-Impromptu/library/passages.json.

Only typographic normalisation is applied (line wrapping, invisible joiners,
_italic_ markers, "--" dashes, drop-cap capitals). Nothing is rewritten.
"""
from __future__ import annotations

import datetime as dt
import json
import logging
import random
import re
import urllib.request
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple

from .config import ASSETS_DIR, Paths

log = logging.getLogger("fdecoach")

MIN_WORDS, MAX_WORDS = 50, 130
_BUILTIN: Optional[List[Dict[str, Any]]] = None
GUTENBERG_TEXT_URLS = (
    "https://www.gutenberg.org/cache/epub/{id}/pg{id}.txt",
    "https://www.gutenberg.org/files/{id}/{id}-0.txt",
    "https://www.gutenberg.org/files/{id}/{id}.txt",
)


# --------------------------------------------------------------------------- text helpers

def normalize(text: str, gutenberg: bool = False) -> str:
    """Typographic clean-up only; the words stay exactly as written."""
    text = text.replace("⁠", "").replace("­", "").replace("﻿", "")
    if gutenberg:
        text = re.sub(r"_([^_]+)_", r"\1", text)
        text = re.sub(r"=([^=\s][^=]*)=", r"\1", text)
        text = text.replace("--", "—")
        m = re.match(r"^([A-Z][A-Z']+)(\s+[a-z])", text)  # drop cap: "MAN'S mind" -> "Man's mind"
        if m:
            text = m.group(1).capitalize() + text[len(m.group(1)):]
    return re.sub(r"\s+", " ", text).strip()


def sentences(text: str) -> List[str]:
    parts = re.split(r"(?<=[.!?])[”’\"']?\s+(?=[“‘\"'(]?[A-Z])", text)
    return [p for p in parts if p.strip()]


def level_of(text: str) -> int:
    """Average sentence length: 1 = short sentences (< 17 words), 2 = medium,
    3 = long, winding sentences (> 26 words) that need more breath control."""
    avg = len(text.split()) / max(1, len(sentences(text)))
    if avg < 17:
        return 1
    if avg <= 26:
        return 2
    return 3


def credit_line(p: Dict[str, Any], short: bool = False) -> str:
    """'Mark Twain, The Adventures of Tom Sawyer (1876)' (+ section, translator)."""
    head = f"{p.get('author', '')}, {p.get('work', '')}".strip(", ")
    if p.get("year"):
        head += f" ({p['year']})"
    if short:
        return head
    if p.get("section"):
        head += f" · {p['section']}"
    if p.get("translator"):
        head += f" · tr. {p['translator']}"
    return head


# --------------------------------------------------------------------------- loading

def builtin() -> List[Dict[str, Any]]:
    global _BUILTIN
    if _BUILTIN is None:
        data = json.loads((ASSETS_DIR / "passages.json").read_text(encoding="utf-8"))
        _BUILTIN = [dict(p, origin="builtin") for p in data["passages"]]
    return [dict(p) for p in _BUILTIN]


def user_file(paths: Paths) -> Path:
    return paths.library / "passages.json"


def user_passages(paths: Paths) -> List[Dict[str, Any]]:
    path = user_file(paths)
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        log.error("library file unreadable (%s); ignoring it", exc)
        return []
    return [dict(p, origin="user") for p in data.get("passages", [])]


def _save_user(paths: Paths, entries: List[Dict[str, Any]]) -> None:
    path = user_file(paths)
    path.parent.mkdir(parents=True, exist_ok=True)
    clean = [{k: v for k, v in e.items() if k != "origin"} for e in entries]
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps({"version": 1, "passages": clean}, ensure_ascii=False, indent=1) + "\n",
                   encoding="utf-8")
    tmp.replace(path)


def all_passages(paths: Paths, include_user: bool = True) -> List[Dict[str, Any]]:
    return builtin() + (user_passages(paths) if include_user else [])


def get(paths: Paths, pid: str) -> Optional[Dict[str, Any]]:
    return next((p for p in all_passages(paths) if p["id"] == pid), None)


def by_theme(passages: Iterable[Dict[str, Any]], themes: Sequence[str]) -> List[Dict[str, Any]]:
    want = {t.strip().lower() for t in themes or [] if t.strip()}
    items = list(passages)
    if not want:
        return items
    picked = [p for p in items if str(p.get("theme", "")).lower() in want]
    return picked or items  # an unknown theme never empties the library


def update_user(paths: Paths, pid: str, fn: Callable[[Dict[str, Any]], None]) -> bool:
    entries = user_passages(paths)
    for e in entries:
        if e["id"] == pid:
            fn(e)
            _save_user(paths, entries)
            return True
    return False


def remove_user(paths: Paths, pid: str) -> bool:
    entries = user_passages(paths)
    keep = [e for e in entries if e["id"] != pid]
    if len(keep) == len(entries):
        return False
    _save_user(paths, keep)
    return True


def add_user(paths: Paths, new: List[Dict[str, Any]]) -> Tuple[int, int]:
    """Adds entries, skipping texts already in the library. Returns (added, skipped)."""
    from .questions import is_duplicate
    entries = user_passages(paths)
    existing = [p["text"] for p in builtin()] + [e["text"] for e in entries]
    ids = {p["id"] for p in builtin()} | {e["id"] for e in entries}
    added = skipped = 0
    for e in new:
        if is_duplicate(e["text"], existing):
            skipped += 1
            continue
        base, n = e["id"], 1
        while e["id"] in ids:  # a second import of the same book keeps ids unique
            n += 1
            e["id"] = f"{base}-{n}"
        ids.add(e["id"])
        entries.append(e)
        existing.append(e["text"])
        added += 1
    _save_user(paths, entries)
    return added, skipped


# --------------------------------------------------------------------------- choosing

def choose(passages: List[Dict[str, Any]], used: Sequence[str], date: dt.date, salt: str,
           target_level: Optional[int] = None,
           score: Optional[Callable[[Dict[str, Any]], float]] = None) -> Dict[str, Any]:
    """Fresh passages first (never read before); once all are read, the least
    recently read third comes back. Among candidates: highest score, then the
    level closest to target_level, then a date-seeded shuffle for variety."""
    if not passages:
        raise ValueError("the passage library is empty")
    seen = set(used)
    pool = [p for p in passages if p["id"] not in seen]
    if not pool:
        last_read = {pid: i for i, pid in enumerate(used)}
        pool = sorted(passages, key=lambda p: last_read.get(p["id"], -1))[:max(1, len(passages) // 3)]
    rng = random.Random(f"{date.isoformat()}:{salt}")
    rng.shuffle(pool)

    def key(p: Dict[str, Any]) -> Tuple[float, int]:
        s = score(p) if score else 0.0
        dist = abs(int(p.get("level", 2)) - target_level) if target_level else 0
        return (-s, dist)

    return sorted(pool, key=key)[0]


# --------------------------------------------------------------------------- importing

def _read_url(url: str, timeout: int = 60) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "fde-impromptu-coach (personal reading practice)"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def fetch_gutenberg(book_id: int) -> str:
    last: Exception = RuntimeError("no download attempted")
    for pattern in GUTENBERG_TEXT_URLS:
        try:
            return _read_url(pattern.format(id=book_id)).decode("utf-8", errors="replace")
        except Exception as exc:  # noqa: BLE001 - try the next mirror path
            last = exc
    raise RuntimeError(f"could not download Project Gutenberg book {book_id}: {last}")


def parse_gutenberg(raw: str) -> Tuple[str, str, List[str]]:
    """(title, author, raw paragraphs) from a Project Gutenberg plain-text file."""
    raw = raw.replace("\r\n", "\n")
    head = raw[:5000]
    title = (re.search(r"^Title:\s*(.+)$", head, re.M) or [None, ""])[1].strip()
    author = (re.search(r"^Author:\s*(.+)$", head, re.M) or [None, ""])[1].strip()
    start = re.search(r"\*\*\*\s*START OF.*?\*\*\*", raw)
    end = re.search(r"\*\*\*\s*END OF", raw)
    body = raw[start.end() if start else 0: end.start() if end else len(raw)]
    return title, author, [p for p in re.split(r"\n\s*\n", body) if p.strip()]


def is_readable(text: str, min_words: int = MIN_WORDS, max_words: int = MAX_WORDS) -> bool:
    """A paragraph worth reading aloud: prose of the right length, complete
    sentences, not a heading, footnote, table of contents or wall of dialogue."""
    words = text.split()
    if not min_words <= len(words) <= max_words:
        return False
    if not re.match(r"^[“‘\"'(]?[A-Z]", text) or not re.search(r"[.!?][”’\"')]?$", text):
        return False
    if re.search(r"gutenberg|\[illustration|\[footnote|\bchapter [ivxlc\d]+\b|https?://|www\.", text, re.I):
        return False
    letters = sum(c.isalpha() for c in text)
    if letters < 0.7 * len(text.replace(" ", "")) or sum(c.isupper() for c in text) > 0.2 * max(1, letters):
        return False
    quotes = len(re.findall(r"[“”\"]", text))
    return quotes <= 4


def candidates(paragraphs: Sequence[str], gutenberg: bool, min_words: int = MIN_WORDS,
               max_words: int = MAX_WORDS) -> List[str]:
    out = []
    for p in paragraphs:
        t = normalize(p, gutenberg=gutenberg)
        if is_readable(t, min_words, max_words):
            out.append(t)
    return out


def spread(items: Sequence[str], n: int) -> List[str]:
    """n items evenly spread through the book (not just the first chapter)."""
    if len(items) <= n:
        return list(items)
    step = len(items) / n
    return [items[int(i * step)] for i in range(n)]


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:40] or "book"


def make_entries(texts: Sequence[str], author: str, work: str, year: Optional[int], source: Dict[str, Any],
                 theme: str, id_prefix: str) -> List[Dict[str, Any]]:
    entries = []
    for i, t in enumerate(texts, 1):
        entries.append({
            "id": f"{id_prefix}-{i:03d}", "text": t, "author": author or "Unknown author", "work": work or "Untitled",
            "year": year, "section": "", "theme": theme or "imported", "words": len(t.split()),
            "level": level_of(t), "source": source,
        })
    return entries


def import_gutenberg(paths: Paths, book_id: int, max_n: int = 20, theme: str = "",
                     year: Optional[int] = None, raw: Optional[str] = None) -> Dict[str, Any]:
    raw = raw if raw is not None else fetch_gutenberg(book_id)
    title, author, paras = parse_gutenberg(raw)
    picked = spread(candidates(paras, gutenberg=True), max_n)
    source = {"name": "Project Gutenberg", "url": f"https://www.gutenberg.org/ebooks/{book_id}",
              "gutenberg_id": book_id, "license": "Public domain in the USA (check your country's rules)"}
    entries = make_entries(picked, author, title, year, source, theme, f"pg{book_id}")
    added, skipped = add_user(paths, entries)
    return {"title": title, "author": author, "candidates": len(picked), "added": added, "skipped": skipped,
            "library_file": str(user_file(paths))}


def import_file(paths: Paths, path: Path, author: str, title: str, year: Optional[int] = None, url: str = "",
                theme: str = "", max_n: int = 20) -> Dict[str, Any]:
    raw = path.expanduser().read_text(encoding="utf-8", errors="replace")
    gutenberg = "*** START OF" in raw
    if gutenberg:
        _, _, paras = parse_gutenberg(raw)
    else:
        paras = [p for p in re.split(r"\n\s*\n", raw.replace("\r\n", "\n")) if p.strip()]
    picked = spread(candidates(paras, gutenberg=gutenberg), max_n)
    source = {"name": "Your file" if not url else "Web", "url": url, "license": "Provided by you"}
    entries = make_entries(picked, author, title, year, source, theme, f"user-{_slug(title)}")
    added, skipped = add_user(paths, entries)
    return {"title": title, "author": author, "candidates": len(picked), "added": added, "skipped": skipped,
            "library_file": str(user_file(paths))}
