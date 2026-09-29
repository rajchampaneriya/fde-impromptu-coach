"""Pronunciation practice content: flashcard word scheduling and daily
paragraph generation (headless claude -p with a curated bank fallback)."""
from __future__ import annotations

import datetime as dt
import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .config import ASSETS_DIR, REFERENCES_DIR, Paths
from .questions import call_claude, is_duplicate
from .state import History

log = logging.getLogger("fdecoach")

_PRON_BANK: Optional[Dict[str, Any]] = None  # cache for assets/pronunciation_bank.json (questions.py has its own _BANK)
MIN_WORDS = 90
MAX_WORDS = 140
MIN_USES = 2
GAP_STEPS = (1, 2, 4, 8)
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

def build_prompt(cfg: Dict[str, Any], date: dt.date, due: List[str], past_paragraphs: List[str]) -> str:
    rubric = (REFERENCES_DIR / "pronunciation_design.md").read_text(encoding="utf-8")
    pron = cfg.get("pronunciation", {})
    due_line = "\n".join(f"- {w}" for w in due) or "- (none due: pick 5-6 words the learner is likely to " \
        "struggle with, consistent with the focus sounds below)"
    focus = ", ".join(pron.get("focus_sounds") or []) or "your choice of commonly confused sounds"
    past = "\n".join(f"- {p[:140]}" for p in past_paragraphs[-40:]) or "- (none yet)"
    return (
        "You are writing today's pronunciation practice for a Forward Deployed Engineer. "
        "Do not use any tools. Do not ask questions. Reply with the JSON object only.\n\n"
        f"# Rubric\n\n{rubric}\n\n"
        f"# Today ({date.isoformat()})\n\n"
        f"# Words due today (use every one of them, or explain in nothing — they are required)\n\n{due_line}\n\n"
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
    # prefer an entry that shares at least one due word, else rotate by date
    for e in pool:
        if any(_uses(e["paragraph"], w) > 0 for w in due):
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
                     date: dt.date) -> Tuple[Dict[str, Any], List[str]]:
    """Returns (content, notes). Content always produced: Claude first, one retry,
    then the curated bank."""
    due = due_words(history, cfg, date)
    past = past_paragraphs(history)
    notes: List[str] = []
    from .questions import _wait_for_network  # same offline behaviour as the FDE flow
    import os
    if os.environ.get("FDE_COACH_SKIP_NETWORK_WAIT") != "1" and not _wait_for_network():
        return _from_bank(history, date, due), ["network unavailable; using the bank"]
    content: Optional[Dict[str, Any]] = None
    for attempt in (1, 2):
        prompt = build_prompt(cfg, date, due, past)
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
