"""Legato practice content: today's passage (a verbatim paragraph from a free,
public-domain book) and the reading marks derived from it.

Legato speech keeps the voice moving through a phrase: words join, and the
breath is taken only at phrase boundaries. Everything here is computed from
the human-written text itself; nothing is generated:

* breath groups: where to breathe ("/" short, "//" sentence end), built from
  punctuation, merging very short groups and splitting long ones at a
  conjunction or preposition near the middle;
* links: a word that ends in a consonant sound followed by one that starts
  with a vowel sound, inside a breath group ("turn it off" -> "tur-ni-toff");
* chains for the linking drill: runs of linked words, longest first.

The rules are spelling-based heuristics (silent h, "one", "use", silent final
e and so on are handled); they are coaching cues, not phonetics.
"""
from __future__ import annotations

import datetime as dt
import random
import re
from typing import Any, Dict, List, Optional, Sequence, Tuple

from . import library
from .config import Paths
from .state import History

MIN_GROUP = 5          # words before a comma counts as a breath point
MAX_GROUP = 14         # longer groups are split at a natural joint
MAX_CHAINS = 6
SILENT_H = ("hour", "honest", "honour", "honor", "heir", "herb")
CONSONANT_SOUND_START = re.compile(r"^(one\b|once\b|uni|use|usu|ura|uri|uro|ure|ute|uti|uto|eu|ewe|ubiq)")
VOWEL_E_WORDS = {"the", "be", "he", "she", "we", "me", "ye"}
SIMPLE_FINALS = set("bdfklmnprtvz")
JOINTS = {"and", "but", "or", "nor", "that", "which", "who", "whom", "whose", "when", "where", "while",
          "because", "if", "as", "though", "although", "until", "unless", "so", "than", "before", "after",
          "since", "for", "with", "without", "into", "from", "to", "in", "of", "on", "by", "like"}
END_PUNCT = re.compile(r"[.!?]+[”’\"')\]]*$")
STRONG_PUNCT = re.compile(r"[;:—–]+[”’\"']*$")
BREAK_PUNCT = re.compile(r"[,;:—–)\]]+[”’\"']*$|[.!?]+[”’\"')\]]*$")
OPEN_PUNCT = re.compile(r"^[“‘\"'(\[—]")

RESPONSE_PROMPTS = [
    "In your own words: what is the author asking of the reader?",
    "Agree or disagree with the author. One reason, one example.",
    "Retell the passage to a colleague who has not read it.",
    "Where would this idea help you at work this week?",
    "What would you say back to the author?",
    "Describe a moment from your own life this passage reminds you of.",
    "Give the passage's message in three sentences, then one question it raises.",
]


# --------------------------------------------------------------------------- word sounds

def _bare(token: str) -> str:
    return re.sub(r"[^a-z']", "", token.lower().replace("’", "'")).strip("'")


def ends_in_consonant_sound(token: str) -> bool:
    w = _bare(token).replace("'", "")
    if not w or w in VOWEL_E_WORDS:
        return False
    if w.endswith("e"):
        return len(w) >= 3 and w[-2] not in "aeiouy"      # silent e: make, time, there
    if w.endswith("gh"):
        return False                                     # though, through, high
    if w.endswith(("ch", "sh", "th", "ph", "ck", "ng")):
        return True
    return w[-1] in "bcdfgjklmnpqrstvxz"


def starts_with_vowel_sound(token: str) -> bool:
    w = _bare(token)
    if not w:
        return False
    if w.startswith(SILENT_H):
        return True
    return w[0] in "aeiou" and not CONSONANT_SOUND_START.match(w)


def _simple_final(word: str) -> Optional[str]:
    """The consonant letter that moves to the next word in a flow respelling,
    or None when the spelling would mislead (s/z, c, g, x, digraphs, silent e)."""
    w = _bare(word).replace("'", "")
    if w.endswith("ck"):
        return "k"
    if len(w) >= 2 and w[-1] == w[-2] and w[-1] in SIMPLE_FINALS:
        return w[-1]
    if w and w[-1] in SIMPLE_FINALS and not w.endswith(("th", "ng")):
        return w[-1]
    return None


def flow_respelling(chain: Sequence[str]) -> str:
    """'turn it off' -> 'tur-ni-toff'. Only when every join is a simple
    consonant and the shortened words stay readable (five letters or fewer,
    no silent -gh-), otherwise '' and the slide shows the joined phrase alone."""
    words = [_bare(w).replace("'", "") for w in chain]
    if any(len(w) > 5 or "gh" in w or w.endswith("ed") for w in words[:-1]):
        return ""  # -ed may sound /t/ (vexed at -> vex-tat), so no spelling-based hint
    pieces: List[str] = []
    carry = ""
    for i, w in enumerate(words):
        if carry and w.startswith(SILENT_H):
            w = w[1:]                                   # an hour -> a-nour
        piece = carry + w
        if i < len(words) - 1:
            move = _simple_final(chain[i])
            if move is None:
                return ""
            strip = 2 if (w.endswith("ck") or (len(w) >= 2 and w[-1] == w[-2])) else 1
            piece = carry + w[:-strip]
            carry = move
        if not piece:
            return ""
        pieces.append(piece)
    return "-".join(pieces)


# --------------------------------------------------------------------------- analysis

def _tokenize(text: str) -> List[Tuple[str, bool]]:
    """(token, space_after). Em dashes written without spaces ("subject—to")
    split into two tokens so the dash can be a breath point; display keeps the
    original spacing."""
    out: List[Tuple[str, bool]] = []
    for raw in text.split():
        parts = re.split("(?<=—)(?=[A-Za-z“‘\"'])", raw)
        for k, part in enumerate(parts):
            out.append((part, k == len(parts) - 1))
    return out


def tokens(text: str) -> List[str]:
    return [t for t, _ in _tokenize(text)]


def breath_groups(text: str) -> List[Tuple[int, int, str]]:
    """[(start_token, end_token_exclusive, mark)] covering the text; mark is
    '/' (breath) or '//' (sentence end)."""
    toks = tokens(text)
    groups: List[Tuple[int, int, str]] = []
    start = 0
    for i, tok in enumerate(toks):
        n = i + 1 - start
        last = i == len(toks) - 1
        if END_PUNCT.search(tok) or last:
            groups.append((start, i + 1, "//"))
            start = i + 1
        elif (STRONG_PUNCT.search(tok) and n >= 3) or (BREAK_PUNCT.search(tok) and n >= MIN_GROUP):
            groups.append((start, i + 1, "/"))
            start = i + 1
    out: List[Tuple[int, int, str]] = []
    for g in groups:
        out.extend(_split_long(toks, g))
    return out


def _split_long(toks: List[str], group: Tuple[int, int, str]) -> List[Tuple[int, int, str]]:
    a, b, mark = group
    if b - a <= MAX_GROUP:
        return [group]
    mid = (a + b) / 2
    joints = [j for j in range(a + 4, b - 3) if _bare(toks[j]) in JOINTS and not OPEN_PUNCT.match(toks[j])]
    if not joints:
        return [group]
    j = min(joints, key=lambda x: abs(x - mid))
    return _split_long(toks, (a, j, "/")) + _split_long(toks, (j, b, mark))


def links(text: str) -> List[int]:
    """Token indexes i where token i links into token i+1 (same breath group)."""
    toks = tokens(text)
    ends = {b for _, b, _ in breath_groups(text)}
    out = []
    for i in range(len(toks) - 1):
        if i + 1 in ends:
            continue
        a, b = toks[i], toks[i + 1]
        if BREAK_PUNCT.search(a) or re.search(r"[”’\"'?!]$", a) or OPEN_PUNCT.match(b):
            continue
        if ends_in_consonant_sound(a) and starts_with_vowel_sound(b):
            out.append(i)
    return out


def chains(text: str) -> List[List[int]]:
    """Runs of linked tokens, e.g. [[4, 5, 6], [10, 11]] for 'turn it off' ..."""
    toks = tokens(text)
    found: List[List[int]] = []
    current: List[int] = []
    for i in links(text):
        if current and current[-1] == i:
            current.append(i + 1)
        else:
            if current:
                found.append(current)
            current = [i, i + 1]
    if current:
        found.append(current)
    return [c for c in found if len(c) <= len(toks)]


def drill_chains(text: str, limit: int = MAX_CHAINS) -> List[Dict[str, Any]]:
    """The linking-drill items: longest and most contentful chains, in text order."""
    toks = tokens(text)
    items = []
    for c in chains(text):
        words = [re.sub(r"^[^\w]+|[^\w']+$", "", toks[i].replace("’", "'")) for i in c]
        if all(len(w) <= 2 for w in words):
            continue  # "is a", "at a": too slight to drill
        flow = flow_respelling(words)
        score = 2 * len(words) + 0.5 * sum(max(0, len(w) - 3) for w in words) + (2 if flow else 0)
        items.append({"tokens": c, "words": words, "phrase": " ".join(words), "flow": flow, "score": score})
    best = sorted(items, key=lambda x: -x["score"])[:limit]
    seen, out = set(), []
    for it in sorted(best, key=lambda x: x["tokens"][0]):
        if it["phrase"].lower() not in seen:
            seen.add(it["phrase"].lower())
            out.append({k: it[k] for k in ("tokens", "phrase", "flow")})
    return out


def marked_tokens(text: str) -> List[Dict[str, Any]]:
    """Per token: text, linked (into the next token), chain (part of any link),
    mark ('/', '//' or '') after it. Used by the deck and the video frames."""
    toks = _tokenize(text)
    linked = set(links(text))
    in_chain = linked | {i + 1 for i in linked}
    marks = {b - 1: m for _, b, m in breath_groups(text)}
    return [{"text": t, "space": sp, "linked": i in linked, "chain": i in in_chain, "mark": marks.get(i, "")}
            for i, (t, sp) in enumerate(toks)]


def phrase_map(text: str) -> str:
    """Plain-text version for the YouTube description: '‿' joins, '/' breaths."""
    out = []
    for t in marked_tokens(text):
        if t["mark"]:
            out.append(t["text"] + f" {t['mark']} ")
        elif t["linked"]:
            out.append(t["text"] + "‿")
        else:
            out.append(t["text"] + (" " if t["space"] else ""))
    return "".join(out).strip()


# --------------------------------------------------------------------------- level + choice

def flow_level(history: History, cfg: Dict[str, Any], date: dt.date) -> int:
    leg = cfg.get("legato", {})
    done = history.completed_before(date)
    base = int(leg.get("start_level", 1)) + done // max(1, int(leg.get("sessions_per_level", 7)))
    adjust = int(history.data.get("flow_adjust", 0))
    return max(1, min(3, base + adjust))


def apply_feedback(history: History, answer: str) -> None:
    """'Choppy' eases tomorrow's passage, 'Smooth' raises it (bounded ±2)."""
    delta = {"Choppy": -1, "Smooth": 1}.get(answer, 0)
    history.data["flow_adjust"] = max(-2, min(2, int(history.data.get("flow_adjust", 0)) + delta))


def used_passages(history: History) -> List[str]:
    return [s["passage_id"] for _, s in sorted(history.sessions.items()) if s.get("passage_id")]


def response_prompt(date: dt.date, passage_id: str) -> str:
    rng = random.Random(f"{date.isoformat()}:{passage_id}:respond")
    return RESPONSE_PROMPTS[(date.toordinal() + rng.randrange(len(RESPONSE_PROMPTS))) % len(RESPONSE_PROMPTS)]


def generate_content(history: History, cfg: Dict[str, Any], paths: Paths, date: dt.date,
                     passage_id: Optional[str] = None, **_: Any) -> Tuple[Dict[str, Any], List[str]]:
    leg = cfg.get("legato", {})
    notes: List[str] = []
    level = flow_level(history, cfg, date)
    if passage_id:
        chosen = library.get(paths, passage_id)
        if chosen is None:
            raise ValueError(f"no passage with id {passage_id!r} (see: fde-coach library list)")
    else:
        pool = library.by_theme(library.all_passages(paths, bool(leg.get("include_user_passages", True))),
                                leg.get("themes") or [])
        chosen = library.choose(pool, used_passages(history), date, "legato", target_level=level)
    text = chosen["text"]
    meta = {k: chosen.get(k) for k in ("id", "author", "work", "year", "section", "translator", "source", "level")
            if chosen.get(k) is not None}
    content = {
        "paragraph": text,
        "passage": meta,
        "flow_level": level,
        "chains": drill_chains(text),
        "response_prompt": response_prompt(date, chosen["id"]),
        "source": "library" if chosen.get("origin") != "user" else "library-user",
    }
    if not content["chains"]:
        notes.append("no linking chains found in this passage; the drill shows its first phrases instead")
    return content, notes
