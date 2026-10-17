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


def audiences() -> Dict[str, Dict[str, Any]]:
    """Listener types: exec, account_leader, technical_peer, business, interviewer."""
    return bank().get("audiences", {})


def exec_shape() -> str:
    return bank().get("exec_shape", "Headline \u2192 So what \u2192 What I need \u2192 Offer detail")


def exec_cfg(cfg: Dict[str, Any]) -> Dict[str, Any]:
    return cfg.get("exec_mode") or {}


def exec_audiences(cfg: Dict[str, Any]) -> List[str]:
    """Listeners that get the exec treatment (headline window + reply), [] when exec mode is off."""
    ec = exec_cfg(cfg)
    if not ec.get("enabled", True):
        return []
    return [a for a in ec.get("audiences", ["exec", "account_leader"]) if a in audiences()]


_EXEC_RE = re.compile(r"\b(CEO|CFO|COO|CIO|CTO|CISO|CRO|CMO|VP|SVP|EVP|board|executive|sponsor|chief|president|"
                      r"steering committee|leadership)\b", re.I)
_ACCOUNT_RE = re.compile(r"\b(account (executive|director|leader|lead|manager|team|owner)|sales (lead|VP|director|"
                         r"leader|team)|your AE)\b", re.I)
_PEER_RE = re.compile(r"\b(engineers?|research (team|lead)|product (team|manager)|security team|architect)\b", re.I)
_INTERVIEW_RE = re.compile(r"^(tell me about|describe a time|what |how do you|how would you|when is it|is it better|"
                           r"take a position|if you were|in five years)", re.I)


def infer_audience(text: str) -> str:
    """Best guess at the listener for questions saved before listeners existed."""
    if _ACCOUNT_RE.search(text):
        return "account_leader"
    if _EXEC_RE.search(text):
        return "exec"
    if _INTERVIEW_RE.search(text.strip()):
        return "interviewer"
    if _PEER_RE.search(text):
        return "technical_peer"
    return "business"


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
    _assign_audiences(slots, history, cfg, date)
    return {"level": level, "slots": slots}


def _assign_audiences(slots: List[Dict[str, Any]], history: History, cfg: Dict[str, Any], date: dt.date) -> None:
    """Exec focus: the first `focus_slots` listeners from `focus_audiences` (cycled) go to random slots,
    preferring slots whose competency still has an unused bank question for that listener, so the
    offline fallback keeps the promise too. Other slots leave the listener to the question writer."""
    ec = exec_cfg(cfg)
    focus = [a for a in (ec.get("focus_audiences") or []) if a in audiences()]
    n = min(int(ec.get("focus_slots", 0) or 0), len(slots))
    if not ec.get("enabled", True) or not focus or n <= 0:
        return
    rng = _rng(date, "audiences")
    past_ids = {q.get("id") for q in history.all_questions(exclude_date=date)}
    order = list(range(len(slots)))
    rng.shuffle(order)

    def stocked(i: int, aud: str) -> bool:
        return any(q["category"] == slots[i]["category"] and q.get("audience") == aud and q["id"] not in past_ids
                   for q in bank()["questions"])

    taken: List[int] = []
    for k in range(n):
        aud = focus[k % len(focus)]
        free = [i for i in order if i not in taken]
        best = [i for i in free if stocked(i, aud)] or free
        slots[best[0]]["audience"] = aud
        taken.append(best[0])


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
    aud = q.get("audience") if q.get("audience") in audiences() else infer_audience(q.get("text", ""))
    info = audiences().get(aud, {})
    q["audience"] = aud
    q["audience_label"] = info.get("label", aud)
    q["listener"] = (q.get("listener") or info.get("label", "")).strip()
    q["cares"] = (q.get("cares") or info.get("cares", "")).strip()
    return q


# Constraints that fight a 25-second headline window (a time limit, a list of points, a long setup).
_EXEC_CLASH = re.compile(r"\b\d+ seconds\b|\bone minute\b|three points|setup", re.I)


def apply_exec_mode(questions: List[Dict[str, Any]], cfg: Dict[str, Any], date: dt.date) -> List[Dict[str, Any]]:
    """Mark exec-listener questions and give each one the listener's reply (deterministic per day):
    "that's all I needed" trains stopping; "biggest risk?" and "what do you need?" train one level deeper."""
    ec = exec_cfg(cfg)
    auds = set(exec_audiences(cfg))
    replies = bank().get("exec_replies", {})
    weights = {k: float(v) for k, v in (ec.get("reply_weights") or {}).items() if k in replies and float(v) > 0}
    rng = _rng(date, "replies")
    last = ""
    for q in questions:
        q["exec"] = bool(auds) and q.get("audience") in auds
        if not q["exec"]:
            q.pop("exec_reply", None)
            continue
        q["framework"] = exec_shape()
        if _EXEC_CLASH.search(q.get("constraint") or ""):
            q["constraint"] = ""
        if not (ec.get("replies", True) and weights):
            q.pop("exec_reply", None)
            continue
        kinds = [k for k in weights if k != last] or list(weights)
        kind = rng.choices(kinds, weights=[weights[k] for k in kinds])[0]
        last = kind
        r = replies[kind]
        q["exec_reply"] = {
            "kind": kind,
            "line": r["lines"].get(q["audience"]) or next(iter(r["lines"].values())),
            "seconds": int(r["seconds"]),
            "instruction": r["instruction"],
            "check": r["check"],
        }
    return questions


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
            # the slot's listener first (exec focus), then difficulty; repeating a format is a soft penalty
            wrong_listener = bool(slot.get("audience")) and q.get("audience") != slot["audience"]
            return wrong_listener * 5 + abs(q["difficulty"] - target) * 2 + formats_today.count(q["format"])

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
        need = slot.get("audience")
        audience = raw.get("audience") if raw.get("audience") in audiences() else None
        if need and audience and audience != need:
            errors.append(f"slot {slot_no}: the listener must be audience `{need}` "
                          f"({audiences()[need]['label']}), got `{audience}`")
            continue
        audience = audience or need or infer_audience(text)
        listener = re.sub(r"\s+", " ", str(raw.get("listener") or "")).strip().replace("<", "").replace(">", "")[:48]
        cares = re.sub(r"\s+", " ", str(raw.get("cares") or "")).strip().replace("<", "").replace(">", "")[:80]
        q = {
            "id": f"GEN-{date.strftime('%Y%m%d')}-{slot_no}",
            "slot": slot_no, "category": category, "difficulty": difficulty, "format": fmt,
            "text": text, "constraint": constraint.replace("<", "").replace(">", ""), "coach_note": coach,
            "audience": audience, "listener": listener, "cares": cares,
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
    ec = exec_cfg(cfg)
    focus_on = bool(ec.get("enabled", True) and ec.get("focus_audiences") and int(ec.get("focus_slots", 0) or 0) > 0)

    def listener(s: Dict[str, Any]) -> str:
        aud = s.get("audience")
        if not aud and focus_on:
            # today's exec slots are fixed; keep the rest varied
            return "listener: your choice, but not an executive or account leader"
        if not aud:
            return "listener: your choice"
        return f"listener `{aud}` ({audiences()[aud]['label']}, cares about {audiences()[aud]['cares']})"

    slot_lines = "\n".join(
        f"- slot {s['slot']}: category `{s['category']}` ({categories()[s['category']]['label']}), "
        f"difficulty {s['difficulty']}, {listener(s)}"
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


def extract_json_object(stdout: str) -> Dict[str, Any]:
    """The JSON object in Claude's answer: unwraps the `--output-format json` envelope and code fences."""
    text = stdout.strip()
    try:
        env = json.loads(text)
        if isinstance(env, dict) and "result" in env:
            if env.get("is_error"):
                raise ValueError(f"claude reported an error: {str(env.get('result'))[:200]}")
            text = str(env["result"])
        elif isinstance(env, dict):
            return env
    except ValueError as exc:
        if "claude reported" in str(exc):
            raise
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.MULTILINE)
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("no JSON object in Claude output")
    data = json.loads(text[start:end + 1])
    if not isinstance(data, dict):
        raise ValueError("Claude output is not a JSON object")
    return data


def parse_claude_output(stdout: str) -> List[Dict[str, Any]]:
    items = extract_json_object(stdout).get("questions")
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
    return apply_exec_mode(questions, cfg, date), label, plan["level"], notes


def questions_from_file(path: Path, history: History, runtime: Runtime, cfg: Dict[str, Any],
                        date: dt.date) -> Tuple[List[Dict[str, Any]], str, int, List[str]]:
    """Questions authored interactively (by Claude in a Claude Code session or by the user)."""
    plan = plan_slots(history, runtime, cfg, date)
    raw = parse_claude_output(path.read_text(encoding="utf-8"))
    accepted, errors = validate_candidates(raw, plan["slots"], history, date)
    questions, label = merge_with_bank(accepted, plan["slots"], history, plan["level"], date, "claude")
    return apply_exec_mode(questions, cfg, date), label, plan["level"], errors
