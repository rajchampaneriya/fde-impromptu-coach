"""Pronunciation practice content: flashcard word scheduling and the daily
paragraph.

Default (`pronunciation.paragraph_source = "library"`): the paragraph is a
verbatim passage from a public-domain book (fdecoach.library), chosen to
contain the learner's due words where possible. Its hard words come with
hand-written coach notes; Claude is asked only to mark up words that have no
notes yet (respelling + one tip) and never writes the text itself.

Legacy (`"claude"`): headless claude -p writes a work-context paragraph, with
the curated AI-written bank as the fallback."""
from __future__ import annotations

import datetime as dt
import json
import logging
import re
from typing import Any, Dict, List, Optional, Sequence, Tuple

from . import library
from .config import ASSETS_DIR, REFERENCES_DIR, Paths
from .questions import call_claude, is_duplicate
from .state import History

log = logging.getLogger("fdecoach")

_PRON_BANK: Optional[Dict[str, Any]] = None  # cache for assets/pronunciation_bank.json (questions.py has its own _BANK)
MIN_WORDS = 90
MAX_WORDS = 140
MIN_USES = 2
GAP_STEPS = (1, 2, 4, 8)
MAX_SESSION_WORDS = 6
MAX_DUE_IN_LIBRARY = 3
FALLBACK_TIP = "Slowly, syllable by syllable, then at normal speed."
RETIRE_AFTER = 4


def bank() -> Dict[str, Any]:
    global _PRON_BANK
    if _PRON_BANK is None:
        _PRON_BANK = json.loads((ASSETS_DIR / "pronunciation_bank.json").read_text(encoding="utf-8"))
    return _PRON_BANK


# --------------------------------------------------------------------------- word scheduling

def word_state(history: History) -> Dict[str, Dict[str, Any]]:
    return history.data.setdefault("words", {})


def _sync_pool(history: History, cfg: Dict[str, Any]) -> None:
    """Words added via the CLI enter the schedule the first time they are seen."""
    state = word_state(history)
    for w in cfg.get("pronunciation", {}).get("words") or []:
        if w and w not in state:
            state[w] = {"easy_streak": 0, "gap_index": 0, "next_due": "", "added": ""}


def due_words(history: History, cfg: Dict[str, Any], date: dt.date) -> List[str]:
    _sync_pool(history, cfg)
    state = word_state(history)
    due = [w for w, st in state.items() if not st.get("retired") and (not st.get("next_due")
                                                                     or st["next_due"] <= date.isoformat())]
    return sorted(due, key=lambda w: state[w].get("next_due") or "")


def update_after_session(history: History, cfg: Dict[str, Any], date: dt.date,
                         session_words: List[str], hard_words: List[str]) -> None:
    """Flashcard spacing: hard words come back tomorrow; each easy answer doubles
    the gap (1, 2, 4, 8 days); four easy answers in a row retire a word."""
    _sync_pool(history, cfg)
    state = word_state(history)
    hard = {w.lower() for w in hard_words}
    for w in session_words:
        st = state.setdefault(w, {"easy_streak": 0, "gap_index": 0, "next_due": "", "added": date.isoformat()})
        if w.lower() in hard:
            st["easy_streak"] = 0
            st["gap_index"] = 0
            st["next_due"] = (date + dt.timedelta(days=1)).isoformat()
            st.pop("retired", None)
        else:
            st["easy_streak"] = int(st.get("easy_streak", 0)) + 1
            st["gap_index"] = min(int(st["easy_streak"]) - 1, len(GAP_STEPS) - 1)
            if st["easy_streak"] >= RETIRE_AFTER:
                st["retired"] = True
                st["next_due"] = ""
            else:
                st["next_due"] = (date + dt.timedelta(days=GAP_STEPS[st["gap_index"]])).isoformat()


# --------------------------------------------------------------------------- validation

def _uses(text: str, word: str) -> int:
    return len(re.findall(r"\b" + re.escape(word.lower()) + r"\b", text.lower()))


def validate_paragraph(raw: Any, past_paragraphs: List[str]) -> Tuple[Optional[Dict[str, Any]], str]:
    """Returns (content, "") or (None, reason). Checks: paragraph 90-140 words,
    every target word used at least twice, no repeat of a past paragraph."""
    if not isinstance(raw, dict):
        return None, "not an object"
    paragraph = re.sub(r"\s+", " ", str(raw.get("paragraph", ""))).strip()
    words = paragraph.split()
    if not MIN_WORDS <= len(words) <= MAX_WORDS:
        return None, f"paragraph must be {MIN_WORDS}-{MAX_WORDS} words (got {len(words)})"
    targets_raw = raw.get("target_words")
    if not isinstance(targets_raw, list) or not 3 <= len(targets_raw) <= 8:
        return None, "target_words must be a list of 3-8 items"
    targets: List[Dict[str, Any]] = []
    for t in targets_raw:
        if not isinstance(t, dict) or not t.get("word"):
            return None, "target_words items need a word"
        word = str(t["word"]).strip().lower()
        n = _uses(paragraph, word)
        if n < MIN_USES:
            return None, f"target word {word!r} used {n}x, needs {MIN_USES}"
        targets.append({
            "word": word,
            "respelling": str(t.get("respelling", "")).strip()[:60],
            "stress": str(t.get("stress", "")).strip()[:60],
            "tip": str(t.get("tip", "")).strip()[:160],
        })
    if is_duplicate(paragraph, past_paragraphs):
        return None, "too similar to a past paragraph"
    return {
        "paragraph": paragraph,
        "target_words": targets,
        "focus_sounds": [str(s) for s in raw.get("focus_sounds") or []][:6],
    }, ""


# --------------------------------------------------------------------------- generation

def build_prompt(cfg: Dict[str, Any], date: dt.date, due: List[str], past_paragraphs: List[str],
                 practiced: Optional[List[str]] = None) -> str:
    rubric = (REFERENCES_DIR / "pronunciation_design.md").read_text(encoding="utf-8")
    pron = cfg.get("pronunciation", {})
    due_line = "\n".join(f"- {w}" for w in due) or "- (none due: pick 5-6 words the learner is likely to " \
        "struggle with, consistent with the focus sounds below)"
    focus = ", ".join(pron.get("focus_sounds") or []) or "your choice of commonly confused sounds"
    past = "\n".join(f"- {p[:140]}" for p in past_paragraphs[-40:]) or "- (none yet)"
    # one comma-separated line, not a "- word" list: only due words are listed one per line
    seen = ", ".join((practiced or [])[-200:]) or "(none yet)"
    return (
        "You are writing today's pronunciation practice for a Forward Deployed Engineer. "
        "Do not use any tools. Do not ask questions. Reply with the JSON object only.\n\n"
        f"# Rubric\n\n{rubric}\n\n"
        f"# Today ({date.isoformat()})\n\n"
        f"# Words due today (use every one of them, or explain in nothing — they are required)\n\n{due_line}\n\n"
        "# Already practiced — never pick one of these as an extra word yourself\n\n"
        f"{seen}\n\n"
        f"# Focus sounds\n\n{focus}\n\n"
        "# Past paragraphs — do not repeat or lightly reword any of these\n\n"
        f"{past}\n\n"
        "Return only the JSON object described in the Output schema section."
    )


def parse_paragraph_output(stdout: str) -> Any:
    text = stdout.strip()
    try:
        env = json.loads(text)
        if isinstance(env, dict) and "result" in env:
            if env.get("is_error"):
                raise ValueError(f"claude reported an error: {str(env.get('result'))[:200]}")
            text = str(env["result"])
    except ValueError:
        pass
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.MULTILINE)
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("no JSON object in Claude output")
    return json.loads(text[start:end + 1])


def _from_bank(history: History, date: dt.date, due: List[str]) -> Dict[str, Any]:
    past = past_paragraphs(history)
    entries = bank()["paragraphs"]
    fresh = [e for e in entries if not is_duplicate(e["paragraph"], past)]
    pool = fresh or entries
    # prefer an entry that drills a due word as a target, else rotate by date
    due_set = set(due)
    for e in pool:
        if any(t["word"] in due_set for t in e["target_words"]):
            choice = e
            break
    else:
        choice = pool[date.toordinal() % len(pool)]
    out = json.loads(json.dumps(choice))
    out["source"] = "bank"
    return out


def past_paragraphs(history: History) -> List[str]:
    out = []
    for key in sorted(history.sessions):
        p = history.sessions[key].get("paragraph")
        if p:
            out.append(p if isinstance(p, str) else str(p.get("paragraph", "")))
    return out


def generate_content(history: History, cfg: Dict[str, Any], paths: Paths,
                     date: dt.date, **options: Any) -> Tuple[Dict[str, Any], List[str]]:
    """Returns (content, notes). Content is always produced."""
    if str(cfg.get("pronunciation", {}).get("paragraph_source", "library")) == "claude":
        return claude_content(history, cfg, paths, date)
    return library_content(history, cfg, paths, date, passage_id=options.get("passage_id"))


def claude_content(history: History, cfg: Dict[str, Any], paths: Paths,
                   date: dt.date) -> Tuple[Dict[str, Any], List[str]]:
    """Legacy mode: Claude writes the paragraph, one retry, then the curated bank."""
    due = due_words(history, cfg, date)
    past = past_paragraphs(history)
    notes: List[str] = []
    from .questions import _wait_for_network  # same offline behaviour as the FDE flow
    import os
    if os.environ.get("FDE_COACH_SKIP_NETWORK_WAIT") != "1" and not _wait_for_network():
        return _from_bank(history, date, due), ["network unavailable; using the bank"]
    practiced = [w for w in word_state(history) if w not in due]
    content: Optional[Dict[str, Any]] = None
    for attempt in (1, 2):
        prompt = build_prompt(cfg, date, due, past, practiced)
        try:
            raw = parse_paragraph_output(call_claude(prompt, cfg, paths))
        except Exception as exc:  # noqa: BLE001 - any failure falls back to the bank
            log.warning("Pronunciation Claude attempt %d failed: %s", attempt, exc)
            notes.append(f"attempt {attempt}: {exc}")
            continue
        content, err = validate_paragraph(raw, past)
        if content:
            content["source"] = "claude"
            return content, notes
        notes.append(f"attempt {attempt}: {err}")
        log.info("Pronunciation attempt %d rejected: %s", attempt, err)
    return _from_bank(history, date, due), notes


# --------------------------------------------------------------------------- library mode

def used_passages(history: History) -> List[str]:
    return [s["passage_id"] for _, s in sorted(history.sessions.items()) if s.get("passage_id")]


def _known_annotation(word: str, history: History) -> Optional[Dict[str, Any]]:
    """A word's coach note from the learner's own word log or any library passage."""
    cached = history.data.get("annotations", {}).get(word)
    if cached:
        return dict(cached, word=word)
    for p in library.builtin():
        for t in (p.get("pronunciation") or {}).get("target_words", []):
            if t["word"] == word:
                return dict(t)
    return None


def build_annotation_prompt(text: str = "", words: Sequence[str] = (), count: int = 5) -> str:
    """Claude only marks up words; it never writes or edits the passage."""
    rubric = (REFERENCES_DIR / "pronunciation_annotation.md").read_text(encoding="utf-8")
    if text:
        task = (f"Pick exactly {count} words from the passage below that a fluent professional is most likely to "
                "mispronounce, copying each word exactly as it appears (lowercase). Do not change the passage.\n\n"
                f"# Passage (copy words exactly from here)\n\n{text}")
    else:
        task = "Annotate exactly these words:\n\n# Words to annotate\n\n" + "\n".join(f"- {w}" for w in words)
    return ("You are writing coach notes for a pronunciation annotation task (pen method practice). "
            "Do not use any tools. Do not ask questions. Reply with the JSON object only.\n\n"
            f"# Rubric\n\n{rubric}\n\n# Task\n\n{task}\n\n"
            "Return only the JSON object described in the Output schema section.")


def _clean_note(t: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    word = str(t.get("word", "")).strip().lower()
    if not word or " " in word:
        return None
    stress = str(t.get("stress") or t.get("respelling") or "").strip()[:60]
    return {"word": word, "respelling": str(t.get("respelling") or stress).strip()[:60], "stress": stress,
            "tip": str(t.get("tip", "")).strip()[:80]}


def annotate_with_claude(cfg: Dict[str, Any], paths: Paths, text: str = "", words: Sequence[str] = (),
                         count: int = 5) -> Dict[str, Any]:
    """{"target_words": [...], "focus_sounds": [...]} or raises. Words picked
    from a passage must really occur in it."""
    raw = parse_paragraph_output(call_claude(build_annotation_prompt(text, words, count), cfg, paths))
    if not isinstance(raw, dict) or not isinstance(raw.get("target_words"), list):
        raise ValueError("annotation is not a JSON object with target_words")
    notes = [n for n in (_clean_note(t) for t in raw["target_words"] if isinstance(t, dict)) if n]
    if text:
        notes = [n for n in notes if _uses(text, n["word"]) >= 1][:count]
        if len(notes) < 3:
            raise ValueError("annotation picked words that are not in the passage")
    else:
        want = {w.lower() for w in words}
        notes = [n for n in notes if n["word"] in want]
    return {"target_words": notes, "focus_sounds": [str(s) for s in raw.get("focus_sounds") or []][:4]}


def _passage_notes(p: Dict[str, Any], cfg: Dict[str, Any], paths: Paths, notes: List[str]) -> Optional[Dict[str, Any]]:
    ann = p.get("pronunciation")
    if ann and ann.get("target_words"):
        return ann
    if p.get("origin") != "user" or not library_claude_ok(cfg):
        return None
    try:
        ann = annotate_with_claude(cfg, paths, text=p["text"])
    except Exception as exc:  # noqa: BLE001 - fall back to an annotated passage
        notes.append(f"could not mark up {p['id']}: {exc}")
        return None
    library.update_user(paths, p["id"], lambda e: e.update(pronunciation=ann))
    return ann


def library_claude_ok(cfg: Dict[str, Any]) -> bool:
    from .questions import resolve_claude
    return bool(resolve_claude(cfg))


def library_content(history: History, cfg: Dict[str, Any], paths: Paths, date: dt.date,
                    passage_id: Optional[str] = None) -> Tuple[Dict[str, Any], List[str]]:
    pron = cfg.get("pronunciation", {})
    notes: List[str] = []
    due = due_words(history, cfg, date)
    passages = library.by_theme(library.all_passages(paths, bool(pron.get("include_user_passages", True))),
                                pron.get("themes") or [])
    annotated = [p for p in passages if (p.get("pronunciation") or {}).get("target_words")]
    if passage_id:
        chosen = library.get(paths, passage_id)
        if chosen is None:
            raise ValueError(f"no passage with id {passage_id!r} (see: fde-coach library list)")
    else:
        def score(p: Dict[str, Any]) -> float:
            return sum(1.0 for w in due if _uses(p["text"], w)) + (0.5 if p in annotated else 0.0)
        chosen = library.choose(passages, used_passages(history), date, "pronunciation", score=score)
    ann = _passage_notes(chosen, cfg, paths, notes)
    if ann is None:
        chosen = library.choose(annotated or library.builtin(), used_passages(history), date, "pronunciation")
        ann = chosen.get("pronunciation") or {"target_words": [], "focus_sounds": []}
    text = chosen["text"]

    # Due words first (those in the passage before the others), then the passage's own hard words.
    due_sorted = sorted(due, key=lambda w: 0 if _uses(text, w) else 1)[:MAX_DUE_IN_LIBRARY]
    missing = [w for w in due_sorted if _known_annotation(w, history) is None]
    fresh: Dict[str, Dict[str, Any]] = {}
    if missing and library_claude_ok(cfg):
        try:
            got = annotate_with_claude(cfg, paths, words=missing)
            fresh = {t["word"]: t for t in got["target_words"]}
        except Exception as exc:  # noqa: BLE001 - plain words still work on the slide
            notes.append(f"word mark-up unavailable: {exc}")
    targets: List[Dict[str, Any]] = []
    for w in due_sorted:
        note = _known_annotation(w, history) or fresh.get(w) or {"word": w, "respelling": "", "stress": "",
                                                                    "tip": FALLBACK_TIP}
        targets.append(dict(note, word=w))
    for t in ann.get("target_words", []):
        if len(targets) >= MAX_SESSION_WORDS:
            break
        if t["word"] not in {x["word"] for x in targets}:
            targets.append(dict(t))
    known = history.data.setdefault("annotations", {})
    for t in targets:  # remember every coach note so a word keeps it when it comes back
        if t.get("stress"):
            known[t["word"]] = {k: t[k] for k in ("respelling", "stress", "tip") if k in t}
        t["in_text"] = _uses(text, t["word"]) > 0
    meta = {k: chosen.get(k) for k in ("id", "author", "work", "year", "section", "translator", "source", "level")
            if chosen.get(k) is not None}
    return {"paragraph": text, "target_words": targets, "focus_sounds": list(ann.get("focus_sounds") or []),
            "passage": meta, "source": "library" if chosen.get("origin") != "user" else "library-user"}, notes
