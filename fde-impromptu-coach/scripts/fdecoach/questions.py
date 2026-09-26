"""Question selection: plan slots, generate with Claude Code, validate novelty,
fall back to the curated bank so a deck is always produced."""
from __future__ import annotations

import datetime as dt
import json
import logging
import os
import random
import re
import shutil
import socket
import subprocess
import time
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .config import ASSETS_DIR, REFERENCES_DIR, Paths
from .state import History, Runtime, difficulty_curve, level_for

log = logging.getLogger("fdecoach")

_BANK: Optional[Dict[str, Any]] = None

STOPWORDS = set(
    "a an the to of and or in on for with your you is are be that this it as at by from their they them "
    "our we i me my he she his her its was were has have had do does did not but so if what how why when "
    "who which about into than then there just one out up".split()
)
JACCARD_DUP = 0.6
RATIO_DUP = 0.82


def bank() -> Dict[str, Any]:
    global _BANK
    if _BANK is None:
        _BANK = json.loads((ASSETS_DIR / "question_bank.json").read_text(encoding="utf-8"))
    return _BANK


def categories() -> Dict[str, Dict[str, str]]:
    return bank()["categories"]


def frameworks() -> Dict[str, str]:
    return bank()["frameworks"]


# --------------------------------------------------------------------------- novelty

def _tokens(text: str) -> List[str]:
    return [w for w in re.findall(r"[a-z0-9%']+", text.lower().replace("\u2019", "'")) if w not in STOPWORDS]


def similarity(a: str, b: str) -> Tuple[float, float]:
    ta, tb = _tokens(a), _tokens(b)
    sa, sb = set(ta), set(tb)
    jac = len(sa & sb) / len(sa | sb) if (sa | sb) else 0.0
    ra, rb = " ".join(ta), " ".join(tb)
    sm = SequenceMatcher(None, ra, rb)
    ratio = sm.ratio() if sm.real_quick_ratio() >= RATIO_DUP else 0.0
    return jac, ratio


def is_duplicate(text: str, others: Sequence[str]) -> Optional[str]:
    for other in others:
        jac, ratio = similarity(text, other)
        if jac >= JACCARD_DUP or ratio >= RATIO_DUP:
            return other
    return None


# --------------------------------------------------------------------------- planning

def _rng(date: dt.date, salt: str = "") -> random.Random:
    return random.Random(f"{date.isoformat()}:{salt}")


def plan_slots(history: History, runtime: Runtime, cfg: Dict[str, Any], date: dt.date) -> Dict[str, Any]:
    """Pick today's competencies (least practiced first) and the difficulty ramp."""
    n = int(cfg.get("questions_per_day", 5))
    level = level_for(history, cfg, runtime, date)
    counts = history.category_counts(exclude_date=date)
    rng = _rng(date, "slots")
    cats = list(categories())
    rng.shuffle(cats)
    cats.sort(key=lambda c: counts.get(c, 0))
    chosen: List[str] = []
    focus = [c for c in cfg.get("focus_categories") or [] if c in categories()]
    if focus:
        focus.sort(key=lambda c: counts.get(c, 0))
        chosen.append(focus[0])
    for c in cats:
        if len(chosen) >= n:
            break
        if c not in chosen:
            chosen.append(c)
    rng.shuffle(chosen)
    curve = difficulty_curve(level, n)
    slots = [{"slot": i + 1, "category": c, "difficulty": d} for i, (c, d) in enumerate(zip(chosen, curve))]
    return {"level": level, "slots": slots}


def _constraint_for(fmt: str, difficulty: int, level: int, rng: random.Random, force: bool = False,
                    avoid: Sequence[str] = ()) -> str:
    if not force:
        if level < 3 or difficulty < 3:
            return ""
        chance = {3: 0.5, 4: 0.8, 5: 1.0}.get(difficulty, 0.0)
        if rng.random() > chance:
            return ""
    options = [c["text"] for c in bank()["constraints"] if fmt in c["formats"] and c["text"] not in avoid]
    return rng.choice(options) if options else ""


def _finish(q: Dict[str, Any], source: str) -> Dict[str, Any]:
    cat = categories().get(q["category"], {})
    q.setdefault("constraint", "")
    q["coach_note"] = (q.get("coach_note") or cat.get("great", "")).strip()
    q["framework"] = frameworks().get(q.get("format", "roleplay"), frameworks()["roleplay"])
    q["category_label"] = cat.get("label", q["category"])
    q["source"] = source
    return q


def pick_from_bank(slots: List[Dict[str, Any]], history: History, level: int, date: dt.date,
                   taken_texts: Sequence[str] = ()) -> List[Dict[str, Any]]:
    """One bank question per slot. Unused first; recycle (with a new twist) only when exhausted."""
    rng = _rng(date, "bank")
    past = history.all_questions(exclude_date=date)
    past_ids = {q.get("id") for q in past}
    past_texts = [q.get("text", "") for q in past]
    used_today: List[str] = list(taken_texts)
    last_seen: Dict[str, str] = {}
    last_constraint: Dict[str, str] = {}
    for q in past:
        if q.get("id"):
            last_seen[q["id"]] = max(last_seen.get(q["id"], ""), q.get("date", ""))
            last_constraint[q["id"]] = q.get("constraint", "")
    all_q = bank()["questions"]
    out: List[Dict[str, Any]] = []
    for slot in slots:
        target = slot["difficulty"]

        def fresh(q: Dict[str, Any]) -> bool:
            return (q["id"] not in past_ids and q["text"] not in used_today
                    and not is_duplicate(q["text"], past_texts + used_today))

        pool = [q for q in all_q if q["category"] == slot["category"] and fresh(q)]
        if not pool:
            today_cats = {o["category"] for o in out}
            pool = [q for q in all_q if q["category"] not in today_cats and fresh(q)]
        recycled = False
        if not pool:
            recycled = True
            pool = [q for q in all_q if q["category"] == slot["category"] and q["text"] not in used_today]
            pool.sort(key=lambda q: last_seen.get(q["id"], ""))
            pool = pool[: max(3, len(pool) // 3)]
        formats_today = [o["format"] for o in out]

        def score(q: Dict[str, Any]) -> int:
            # difficulty match first; repeating a format already used today is a soft penalty
            return abs(q["difficulty"] - target) * 2 + formats_today.count(q["format"])

        best = min(score(q) for q in pool)
        choice = dict(rng.choice([q for q in pool if score(q) == best]))
        choice["difficulty"] = max(choice["difficulty"], target) if recycled else choice["difficulty"]
        choice["constraint"] = _constraint_for(
            choice["format"], choice["difficulty"], level, rng, force=recycled,
            avoid=[last_constraint.get(choice["id"], "")])
        choice["slot"] = slot["slot"]
        out.append(_finish(choice, "recycled" if recycled else "bank"))
        used_today.append(choice["text"])
    return out


# --------------------------------------------------------------------------- validation

def validate_candidates(cands: List[Dict[str, Any]], slots: List[Dict[str, Any]],
                        history: History, date: dt.date) -> Tuple[Dict[int, Dict[str, Any]], List[str]]:
    """Returns accepted questions keyed by slot number, plus human-readable rejections."""
    past_texts = [q.get("text", "") for q in history.all_questions(exclude_date=date)]
    bank_texts = [q["text"] for q in bank()["questions"]]
    accepted: Dict[int, Dict[str, Any]] = {}
    errors: List[str] = []
    slot_by_no = {s["slot"]: s for s in slots}
    for idx, raw in enumerate(cands):
        if not isinstance(raw, dict):
            errors.append(f"item {idx + 1}: not an object")
            continue
        slot_no = raw.get("slot")
        if not isinstance(slot_no, int) or slot_no not in slot_by_no or slot_no in accepted:
            free = [s for s in sorted(slot_by_no) if s not in accepted]
            slot_no = free[0] if free else None
        if slot_no is None:
            errors.append(f"item {idx + 1}: more questions than slots")
            continue
        slot = slot_by_no[slot_no]
        text = re.sub(r"\s+", " ", str(raw.get("text", ""))).strip().replace("<", "").replace(">", "")
        if not 40 <= len(text) <= 300:
            errors.append(f"slot {slot_no}: text must be 40-300 characters (got {len(text)})")
            continue
        dup = is_duplicate(text, past_texts + [a["text"] for a in accepted.values()])
        if dup:
            errors.append(f"slot {slot_no}: too similar to a past question: {dup[:90]!r}")
            continue
        if is_duplicate(text, bank_texts):
            # Bank items are the offline fallback; keep them unspent.
            errors.append(f"slot {slot_no}: too similar to a built-in bank question; write something new")
            continue
        category = raw.get("category") if raw.get("category") in categories() else slot["category"]
        fmt = raw.get("format") if raw.get("format") in frameworks() else "roleplay"
        try:
            difficulty = int(raw.get("difficulty", slot["difficulty"]))
        except (TypeError, ValueError):
            difficulty = slot["difficulty"]
        difficulty = max(1, min(5, difficulty))
        constraint = re.sub(r"\s+", " ", str(raw.get("constraint") or "")).strip()[:120]
        coach = re.sub(r"\s+", " ", str(raw.get("coach_note") or "")).strip()[:320]
        q = {
            "id": f"GEN-{date.strftime('%Y%m%d')}-{slot_no}",
            "slot": slot_no, "category": category, "difficulty": difficulty, "format": fmt,
            "text": text, "constraint": constraint.replace("<", "").replace(">", ""), "coach_note": coach,
        }
        accepted[slot_no] = q
    return accepted, errors


def merge_with_bank(accepted: Dict[int, Dict[str, Any]], slots: List[Dict[str, Any]], history: History,
                    level: int, date: dt.date, source: str) -> Tuple[List[Dict[str, Any]], str]:
    missing = [s for s in slots if s["slot"] not in accepted]
    fill = pick_from_bank(missing, history, level, date, taken_texts=[q["text"] for q in accepted.values()])
    by_slot = {q["slot"]: _finish(q, source) for q in accepted.values()}
    for q in fill:
        by_slot[q["slot"]] = q
    final = [by_slot[s["slot"]] for s in slots]
    label = source if not missing else ("bank" if len(missing) == len(slots) else "mixed")
    return final, label


# --------------------------------------------------------------------------- Claude Code

def resolve_claude(cfg: Dict[str, Any]) -> Optional[str]:
    """Configured path first, then PATH and the usual install locations (launchd has a minimal PATH)."""
    candidates = [cfg.get("claude_path") or ""]
    if os.environ.get("FDE_COACH_NO_CLAUDE_DISCOVERY") != "1":  # tests set this to never hit the real CLI
        home = Path.home()
        candidates.append(shutil.which("claude") or "")
        candidates += [str(p) for p in (
            home / ".local/bin/claude", home / ".claude/local/claude", Path("/opt/homebrew/bin/claude"),
            Path("/usr/local/bin/claude"), home / ".npm-global/bin/claude", home / ".bun/bin/claude")]
    for c in candidates:
        if c and os.path.isfile(c) and os.access(c, os.X_OK):
            return c
    return None


def _wait_for_network(host: str = "api.anthropic.com", timeout: int = 90) -> bool:
    deadline = time.time() + timeout
    while True:
        try:
            socket.getaddrinfo(host, 443)
            return True
        except OSError:
            if time.time() > deadline:
                return False
            time.sleep(5)


def build_claude_prompt(plan: Dict[str, Any], history: History, cfg: Dict[str, Any], date: dt.date,
                        feedback: Sequence[str] = (), brief: str = "") -> str:
    rubric = (REFERENCES_DIR / "question_design.md").read_text(encoding="utf-8")
    recent = history.all_questions(exclude_date=date)[-150:]
    recent_lines = "\n".join(f"- {q.get('text', '')[:160]}" for q in recent) or "- (none yet)"
    slot_lines = "\n".join(
        f"- slot {s['slot']}: category `{s['category']}` ({categories()[s['category']]['label']}), difficulty {s['difficulty']}"
        for s in plan["slots"])
    context = ""
    if str(cfg.get("learner_context") or "").strip():
        context += f"\n\n# About the learner\n\n{str(cfg['learner_context']).strip()[:800]}"
    if brief.strip():
        context += (f"\n\n# Today's brief from the learner\n\n{brief.strip()[:500]}\n\n"
                    "Honour the brief while keeping each slot's category and difficulty.")
    fb = ""
    if feedback:
        fb = "\n\nYour previous attempt was rejected for these reasons; fix them:\n" + "\n".join(f"- {f}" for f in feedback)
    return (
        "You are generating today's impromptu speaking questions for a learner training for the "
        f"{cfg.get('role', 'Forward Deployed Engineer')} role. Do not use any tools. Do not ask questions. "
        "Reply with the JSON object only.\n\n"
        f"# Rubric\n\n{rubric}\n\n"
        f"# Today ({date.isoformat()}) — learner level {plan['level']} of 5\n\n"
        f"Write exactly {len(plan['slots'])} questions, one per slot:\n{slot_lines}{context}\n\n"
        "# Past questions — do not repeat or lightly reword any of these\n\n"
        f"{recent_lines}{fb}\n\n"
        "Return only the JSON object described in the Output schema section."
    )


def parse_claude_output(stdout: str) -> List[Dict[str, Any]]:
    text = stdout.strip()
    try:
        env = json.loads(text)
        if isinstance(env, dict) and "result" in env:
            if env.get("is_error"):
                raise ValueError(f"claude reported an error: {str(env.get('result'))[:200]}")
            text = str(env["result"])
        elif isinstance(env, dict) and "questions" in env:
            return list(env["questions"])
    except ValueError as exc:
        if "claude reported" in str(exc):
            raise
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.MULTILINE)
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("no JSON object in Claude output")
    data = json.loads(text[start:end + 1])
    items = data.get("questions") if isinstance(data, dict) else None
    if not isinstance(items, list):
        raise ValueError("JSON has no 'questions' list")
    return items


def call_claude(prompt: str, cfg: Dict[str, Any], paths: Paths) -> str:
    exe = resolve_claude(cfg)
    if not exe:
        raise FileNotFoundError("Claude Code CLI not found (set claude_path in config.json)")
    cmd = [exe, "-p", prompt, "--output-format", "json"]
    if cfg.get("claude_model"):
        cmd += ["--model", str(cfg["claude_model"])]
    env = dict(os.environ)
    extra = [str(Path(exe).parent), "/opt/homebrew/bin", "/usr/local/bin", str(Path.home() / ".local/bin")]
    env["PATH"] = os.pathsep.join(extra + [env.get("PATH", "/usr/bin:/bin:/usr/sbin:/sbin")])
    paths.incoming.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(paths.incoming), env=env,
                          timeout=int(cfg.get("claude_timeout_seconds", 240)))
    if proc.returncode != 0:
        raise RuntimeError(f"claude exited {proc.returncode}: {(proc.stderr or proc.stdout)[-400:]}")
    return proc.stdout


def generate_with_claude(plan: Dict[str, Any], history: History, cfg: Dict[str, Any], paths: Paths,
                         date: dt.date, brief: str = "") -> Tuple[Dict[int, Dict[str, Any]], List[str]]:
    accepted: Dict[int, Dict[str, Any]] = {}
    feedback: List[str] = []
    if os.environ.get("FDE_COACH_SKIP_NETWORK_WAIT") != "1" and not _wait_for_network():
        return accepted, ["network unavailable"]
    for attempt in (1, 2):
        remaining = [s for s in plan["slots"] if s["slot"] not in accepted]
        if not remaining:
            break
        sub_plan = {"level": plan["level"], "slots": remaining}
        prompt = build_claude_prompt(sub_plan, history, cfg, date, feedback, brief)
        try:
            raw = parse_claude_output(call_claude(prompt, cfg, paths))
        except Exception as exc:  # noqa: BLE001 - any failure falls back to the bank
            log.warning("Claude generation attempt %d failed: %s", attempt, exc)
            feedback = [f"attempt {attempt}: {exc}"]
            if isinstance(exc, (FileNotFoundError, subprocess.TimeoutExpired)):
                break
            continue
        got, errors = validate_candidates(raw, remaining, _HistoryPlus(history, accepted), date)
        accepted.update(got)
        feedback = errors
        if errors:
            log.info("Claude attempt %d: %d accepted, rejected: %s", attempt, len(got), "; ".join(errors))
    return accepted, feedback


class _HistoryPlus(History):
    """History view that also treats already-accepted questions as 'past' for novelty checks."""

    def __init__(self, base: History, extra: Dict[int, Dict[str, Any]]):  # noqa: D401
        self.paths = base.paths
        self.data = {"version": 1, "sessions": dict(base.sessions)}
        if extra:
            self.data["sessions"]["_accepted"] = {"questions": list(extra.values())}


def generate_questions(history: History, runtime: Runtime, cfg: Dict[str, Any], paths: Paths,
                       date: dt.date, source: str = "auto", brief: str = "") -> Tuple[List[Dict[str, Any]], str, int, List[str]]:
    """Returns (questions, source_label, level, notes)."""
    plan = plan_slots(history, runtime, cfg, date)
    notes: List[str] = []
    accepted: Dict[int, Dict[str, Any]] = {}
    if source in ("auto", "claude"):
        accepted, errs = generate_with_claude(plan, history, cfg, paths, date, brief)
        notes += errs
        if not accepted:
            notes.append("Claude unavailable; using the built-in question bank")
    questions, label = merge_with_bank(accepted, plan["slots"], history, plan["level"], date,
                                       "claude" if accepted else "bank")
    return questions, label, plan["level"], notes


def questions_from_file(path: Path, history: History, runtime: Runtime, cfg: Dict[str, Any],
                        date: dt.date) -> Tuple[List[Dict[str, Any]], str, int, List[str]]:
    """Questions authored interactively (by Claude in a Claude Code session or by the user)."""
    plan = plan_slots(history, runtime, cfg, date)
    raw = parse_claude_output(path.read_text(encoding="utf-8"))
    accepted, errors = validate_candidates(raw, plan["slots"], history, date)
    questions, label = merge_with_bank(accepted, plan["slots"], history, plan["level"], date, "claude")
    return questions, label, plan["level"], errors
