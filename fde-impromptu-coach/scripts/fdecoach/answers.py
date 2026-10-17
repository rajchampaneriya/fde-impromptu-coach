"""Exec answer key: after the session, a model answer for every question.

Each question gets an *answer ladder*, the shape the learner is training:

1. One breath: the headline the listener must remember.
2. The 25-second exec answer, each sentence tagged with its move
   (Headline -> So what -> What I need -> Offer detail).
3. The detail to hold back and offer if asked.
4. The trap: what a technically strong but wrong-for-this-listener answer does.
5. For exec slides with a reply ("What's the biggest risk?"): the next 20 seconds.

The answers are written by Claude headless after recording (never before: they
would spoil the surprise), validated against the rubric in
references/answer_design.md, and rendered as one self-contained HTML page per
day plus an index of every day's one-breath lines. Offline, the page still
opens with the coach notes and a fill-in exec shape; the 15-minute tick fills in
the model answers once Claude is reachable.
"""
from __future__ import annotations

import datetime as dt
import html
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from . import macos
from .config import REFERENCES_DIR
from .state import LockBusy, _read_json, _write_json, file_lock, now, today

log = logging.getLogger("fdecoach")

MOVES = ("headline", "so_what", "ask", "offer")
MOVE_LABELS = {"headline": "Headline", "so_what": "So what", "ask": "What I need", "offer": "Offer detail"}
REPLY_NEEDS_ANSWER = ("risk", "need")
SEP = " · "
DONE = ("ready", "partial", "pending")  # a page exists


# --------------------------------------------------------------------------- settings / paths

def akcfg(cfg: Dict[str, Any]) -> Dict[str, Any]:
    return cfg.get("answer_key") or {}


def enabled(cfg: Dict[str, Any]) -> bool:
    return bool(akcfg(cfg).get("enabled", True))


def json_path(paths, date: dt.date) -> Path:
    return paths.answers / f"{date.isoformat()}.json"


def html_path(paths, date: dt.date) -> Path:
    return paths.answers / f"{date.isoformat()}_Exec-Answer-Key.html"


def index_path(paths) -> Path:
    return paths.answers / "index.html"


def words(text: str) -> int:
    return len(str(text).split())


def _clean(text: Any, limit: int = 600) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip().replace("<", "").replace(">", "")[:limit]


# --------------------------------------------------------------------------- Claude prompt + validation

def build_prompt(session: Dict[str, Any], cfg: Dict[str, Any], slots: Sequence[int],
                 feedback: Sequence[str] = ()) -> str:
    rubric = (REFERENCES_DIR / "answer_design.md").read_text(encoding="utf-8")
    blocks: List[str] = []
    for i, q in enumerate(session["questions"], 1):
        if i not in slots:
            continue
        lines = [f"- slot {i} · listener: {q.get('listener') or q.get('audience_label') or 'unspecified'}"
                 f" ({q.get('audience_label', '')}; cares about {q.get('cares') or 'the outcome'})"
                 f" · format: {q.get('format', 'roleplay')} · competency: {q.get('category_label', '')}",
                 f"  Question: {q['text']}"]
        if q.get("constraint"):
            lines.append(f"  Constraint: {q['constraint']}")
        if q.get("coach_note"):
            lines.append(f"  What a strong answer does: {q['coach_note']}")
        reply = q.get("exec_reply") or {}
        if reply.get("kind") in REPLY_NEEDS_ANSWER:
            lines.append(f"  Reply after the headline window: “{reply['line']}” → write `reply_answer`.")
        blocks.append("\n".join(lines))
    context = ""
    if str(cfg.get("learner_context") or "").strip():
        context = f"\n\n# About the learner\n\n{str(cfg['learner_context']).strip()[:800]}"
    fb = ""
    if feedback:
        fb = "\n\nYour previous attempt was rejected for these reasons; fix them:\n" + "\n".join(f"- {f}" for f in feedback)
    limits = akcfg(cfg)
    return (
        "You are writing the exec answer key for a learner training for the "
        f"{cfg.get('role', 'Forward Deployed Engineer')} role: model answers they read right after answering "
        "these questions out loud. Do not use any tools. Do not ask questions. Reply with the JSON object only.\n\n"
        f"# Rubric\n\n{rubric}{context}\n\n"
        f"# Answer key slots\n\nThe exec answer must be {int(limits.get('min_words', 20))}–"
        f"{int(limits.get('max_words', 70))} words in total.\n\n" + "\n".join(blocks) + fb +
        "\n\nReturn only the JSON object described in the Output schema section."
    )


def validate(raw_items: Any, session: Dict[str, Any], cfg: Dict[str, Any],
             slots: Sequence[int]) -> Tuple[Dict[int, Dict[str, Any]], List[str]]:
    """Accepted answers keyed by slot, plus human-readable rejections (fed back to Claude)."""
    lo, hi = int(akcfg(cfg).get("min_words", 20)), int(akcfg(cfg).get("max_words", 70))
    accepted: Dict[int, Dict[str, Any]] = {}
    errors: List[str] = []
    if not isinstance(raw_items, list):
        return accepted, ["JSON has no 'answers' list"]
    for idx, raw in enumerate(raw_items):
        if not isinstance(raw, dict):
            errors.append(f"item {idx + 1}: not an object")
            continue
        slot = raw.get("slot")
        if not isinstance(slot, int) or slot not in slots or slot in accepted:
            errors.append(f"item {idx + 1}: slot must be one of {sorted(set(slots) - set(accepted))}")
            continue
        q = session["questions"][slot - 1]
        headline = _clean(raw.get("headline"), 200)
        if not 4 <= words(headline) <= 18:
            errors.append(f"slot {slot}: the one-breath headline must be 4-18 words (got {words(headline)})")
            continue
        moves = raw.get("answer")
        if not isinstance(moves, list) or not 3 <= len(moves) <= 4:
            errors.append(f"slot {slot}: the exec answer must be 3 or 4 tagged sentences")
            continue
        parts = [{"move": str((m or {}).get("move", "")).strip(), "text": _clean((m or {}).get("text"), 400)}
                 for m in moves if isinstance(m, dict)]
        names = [p["move"] for p in parts]
        if (len(parts) != len(moves) or any(n not in MOVES for n in names) or len(set(names)) != len(names)
                or names[0] != "headline" or names[-1] != "offer" or any(not p["text"] for p in parts)):
            errors.append(f"slot {slot}: moves must start with headline, end with offer, use each of "
                          f"{', '.join(MOVES)} at most once (got {names})")
            continue
        total = sum(words(p["text"]) for p in parts)
        if not lo <= total <= hi:
            errors.append(f"slot {slot}: the exec answer must be {lo}-{hi} words to fit the headline window "
                          f"(got {total})")
            continue
        detail = [_clean(d, 220) for d in (raw.get("detail") or []) if _clean(d, 220)]
        if not 2 <= len(detail) <= 4 or any(words(d) > 25 for d in detail):
            errors.append(f"slot {slot}: detail must be 2-4 bullets of at most 20 words")
            continue
        trap = _clean(raw.get("trap"), 300)
        if not 1 <= words(trap) <= 35:
            errors.append(f"slot {slot}: trap must be one sentence of at most 30 words")
            continue
        item = {"slot": slot, "headline": headline, "answer": parts, "detail": detail, "trap": trap,
                "words": total, "question": q["text"]}
        if (q.get("exec_reply") or {}).get("kind") in REPLY_NEEDS_ANSWER:
            reply = _clean(raw.get("reply_answer"), 400)
            if not 4 <= words(reply) <= 50:
                errors.append(f"slot {slot}: reply_answer must answer “{q['exec_reply']['line']}” "
                              "in at most 45 words")
                continue
            item["reply_answer"] = reply
        accepted[slot] = item
    return accepted, errors


def generate(session: Dict[str, Any], cfg: Dict[str, Any], paths, slots: Sequence[int]) -> Tuple[Dict[int, Dict[str, Any]], List[str]]:
    """Up to two Claude calls; the second asks again only for the rejected slots, with the reasons."""
    from .questions import _wait_for_network, call_claude, extract_json_object

    accepted: Dict[int, Dict[str, Any]] = {}
    feedback: List[str] = []
    if not slots:
        return accepted, feedback
    if os.environ.get("FDE_COACH_SKIP_NETWORK_WAIT") != "1" and not _wait_for_network(timeout=60):
        return accepted, ["network unavailable"]
    for attempt in (1, 2):
        remaining = [s for s in slots if s not in accepted]
        if not remaining:
            break
        try:
            data = extract_json_object(call_claude(build_prompt(session, cfg, remaining, feedback), cfg, paths))
        except Exception as exc:  # noqa: BLE001 - offline, usage limit, garbage: the page still opens
            log.warning("answer key attempt %d failed: %s", attempt, exc)
            feedback = [f"attempt {attempt}: {exc}"]
            if isinstance(exc, FileNotFoundError) or "TimeoutExpired" in type(exc).__name__:
                break
            continue
        got, feedback = validate(data.get("answers"), session, cfg, remaining)
        accepted.update(got)
        if feedback:
            log.info("answer key attempt %d: %d accepted, rejected: %s", attempt, len(got), "; ".join(feedback))
    return accepted, feedback


# --------------------------------------------------------------------------- flow

def _update(ctx, date: dt.date, fn) -> Optional[Dict[str, Any]]:
    from .app import update_session
    return update_session(ctx, date, fn)


def _status(session: Dict[str, Any]) -> Dict[str, Any]:
    return session.get("answer_key") or {}


def start(ctx, date: dt.date, open_when_ready: bool = False) -> None:
    """Right after a session is marked recorded: write the answer key in the background."""
    if not enabled(ctx.cfg):
        return

    def mark(s: Dict[str, Any]) -> None:
        ak = s.setdefault("answer_key", {})
        ak.update(status="generating", requested_at=now().isoformat(timespec="seconds"))
        if open_when_ready:
            ak["open_when_ready"] = True

    _update(ctx, date, mark)
    if macos.dry_run():
        prepare(ctx, date)
    else:
        from .app import spawn_detached
        spawn_detached(["answers", "--prepare", "--date", date.isoformat()])


def prepare(ctx, date: dt.date, force: bool = False) -> Dict[str, Any]:
    """Generate the missing model answers, write the page and the index, then open it if the
    learner is already waiting for it."""
    try:
        with file_lock(ctx.paths, "answers"):
            return _prepare_locked(ctx, date, force)
    except LockBusy:
        return {"status": "busy"}


def _prepare_locked(ctx, date: dt.date, force: bool) -> Dict[str, Any]:
    session = ctx.history().get(date)
    if not session:
        return {"status": "no-session"}
    store = _read_json(json_path(ctx.paths, date), {}) if not force else {}
    known = {int(k): v for k, v in (store.get("answers") or {}).items()
             if int(k) <= len(session["questions"]) and v.get("question") == session["questions"][int(k) - 1]["text"]}
    missing = [i for i in range(1, len(session["questions"]) + 1) if i not in known]
    errors: List[str] = []
    if missing:
        got, errors = generate(session, ctx.cfg, ctx.paths, missing)
        known.update(got)
    missing = [i for i in range(1, len(session["questions"]) + 1) if i not in known]
    status = "ready" if not missing else ("partial" if known else "pending")
    _write_json(json_path(ctx.paths, date), {
        "date": date.isoformat(), "updated_at": now().isoformat(timespec="seconds"),
        "answers": {str(k): v for k, v in sorted(known.items())}})
    page = write_page(ctx, session, known)
    write_index(ctx)
    state: Dict[str, Any] = {}

    def mark(s: Dict[str, Any]) -> None:
        ak = s.setdefault("answer_key", {})
        before = ak.get("status")
        ak.update(status=status, path=str(page), missing=missing, updated_at=now().isoformat(timespec="seconds"),
                  attempts=int(ak.get("attempts", 0)) + (1 if errors or missing else 0))
        if errors:
            ak["last_error"] = "; ".join(errors)[:300]
        else:
            ak.pop("last_error", None)
        state["open"] = bool(ak.pop("open_when_ready", False))
        state["completed_later"] = before in ("partial", "pending") and status == "ready"
        if state["open"]:
            ak["opened"] = True

    _update(ctx, date, mark)
    if state.get("open"):
        _open(ctx, page, session, status)
    elif state.get("completed_later"):
        macos.notify("Exec answer key complete", f"Model answers for Day {session.get('day_number')} are in.",
                     subtitle=page.name)
    log.info("answer key %s: %s (%d/%d answers)", date, status, len(known), len(session["questions"]))
    return {"status": status, "path": str(page), "missing": missing, "errors": errors}


def _open(ctx, page: Path, session: Dict[str, Any], status: str) -> None:
    if not akcfg(ctx.cfg).get("open_after_session", True):
        return
    macos.open_path(page)
    tail = ("Read each model answer, then say it back." if status == "ready" else
            "Model answers fill in when Claude is reachable; the exec shape is there to practise now.")
    macos.notify(f"Day {session.get('day_number')} exec answer key", tail)


def present(ctx, date: dt.date) -> str:
    """After the practice chain ends: open the page now, or as soon as it is written."""
    if not enabled(ctx.cfg):
        return "disabled"
    decision = {"what": "none"}

    def mark(s: Dict[str, Any]) -> None:
        ak = s.get("answer_key") or {}
        if ak.get("opened"):
            decision["what"] = "already-opened"
        elif ak.get("status") in DONE and ak.get("path"):
            ak["opened"] = True
            decision.update(what="open", path=ak["path"], status=ak["status"])
        else:
            s.setdefault("answer_key", {})["open_when_ready"] = True
            decision["what"] = "when-ready"

    session = _update(ctx, date, mark)
    if decision["what"] == "open" and session:
        _open(ctx, Path(decision["path"]), session, decision["status"])
    return decision["what"]


def tick(ctx) -> List[str]:
    """15-minute tick: fill in answer keys that Claude could not write at the time (last 3 days)."""
    if not enabled(ctx.cfg):
        return []
    out: List[str] = []
    cap = int(akcfg(ctx.cfg).get("max_attempts", 6))
    history = ctx.history()
    for back in range(0, 3):
        date = today() - dt.timedelta(days=back)
        s = history.get(date)
        if not s or not s.get("recorded"):
            continue
        ak = _status(s)
        stale = False
        if ak.get("status") == "generating" and ak.get("requested_at"):
            stale = now() - dt.datetime.fromisoformat(ak["requested_at"]) > dt.timedelta(minutes=20)
        if ak.get("status") in ("partial", "pending") or stale or (not ak and back == 0):
            if int(ak.get("attempts", 0)) >= cap:
                continue
            if macos.dry_run():
                out.append(f"{date}: {prepare(ctx, date).get('status')}")
            else:
                from .app import spawn_detached
                spawn_detached(["answers", "--prepare", "--date", date.isoformat()])
                out.append(f"{date}: retrying")
    return out


# --------------------------------------------------------------------------- page

def _e(text: Any) -> str:
    return html.escape(str(text or ""), quote=True)


def _seconds(n_words: int, cfg: Dict[str, Any]) -> int:
    return max(1, round(n_words * 60 / max(60, int(akcfg(cfg).get("words_per_minute", 150)))))


CSS = """
:root{--bg:#F6F8FB;--card:#FFFFFF;--ink:#0B2545;--muted:#5B6B7F;--faint:#8A98A9;--line:#E3E9F1;
--blue:#1F5FBF;--blue-soft:#DCE7F7;--blue-tint:#F1F6FD;--teal:#0F7B6C;--teal-soft:#DDF3EF;--amber:#A8560B;
--amber-soft:#FBEBDC;--violet:#5B4BC4;--violet-soft:#E9E6FB;--red:#B4232A;--red-soft:#FBE7E8;color-scheme:light}
@media (prefers-color-scheme:dark){:root{--bg:#0D1520;--card:#142030;--ink:#E7EEF7;--muted:#A7B4C4;--faint:#7D8B9C;
--line:#24344A;--blue:#7FB0FF;--blue-soft:#20406E;--blue-tint:#172A44;--teal:#5FD3BF;--teal-soft:#123C38;
--amber:#F2A65A;--amber-soft:#40290F;--violet:#B3A8FF;--violet-soft:#2A2652;--red:#FF8E92;--red-soft:#44191C;
--on-blue:#0B2545;color-scheme:dark}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",
Calibri,Helvetica,Arial,sans-serif;-webkit-font-smoothing:antialiased}
main{max-width:880px;margin:0 auto;padding:40px 20px 80px}
.kicker{font-size:13px;font-weight:600;letter-spacing:.12em;color:var(--blue);text-transform:uppercase}
h1{font-size:34px;line-height:1.15;margin:6px 0 4px;font-weight:600}
.sub{color:var(--muted);margin:0 0 22px}
.how{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:0 0 28px}
.how div{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px 14px;font-size:14px;
color:var(--muted)}
.how b{display:block;color:var(--ink);font-size:15px;margin-bottom:2px}
.shape-legend{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:0 0 30px;font-size:14px;color:var(--muted)}
.chip{display:inline-block;border-radius:999px;padding:3px 11px;font-size:13px;font-weight:600}
.m-headline{background:var(--blue-soft);color:var(--blue)}.m-so_what{background:var(--teal-soft);color:var(--teal)}
.m-ask{background:var(--amber-soft);color:var(--amber)}.m-offer{background:var(--violet-soft);color:var(--violet)}
.arrow{color:var(--faint)}
.card{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:26px 28px;margin:0 0 22px;
position:relative}
.meta{display:flex;flex-wrap:wrap;gap:6px 14px;align-items:center;font-size:13px;color:var(--muted);
letter-spacing:.04em}
.meta .q{font-weight:700;color:var(--blue);letter-spacing:.12em}
.badge{border:1px solid var(--blue-soft);color:var(--blue);border-radius:6px;padding:1px 7px;font-weight:600}
.to{margin:12px 0 4px;font-size:15px}.to b{font-weight:700}.to span{color:var(--muted)}
.question{color:var(--muted);font-size:15px;margin:0 0 18px;border-left:3px solid var(--line);padding-left:12px}
.label{font-size:12px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:var(--faint);margin:0 0 6px}
.breath{font-size:24px;line-height:1.3;font-weight:600;margin:0 0 22px;color:var(--ink)}
.row{display:flex;justify-content:space-between;align-items:baseline;gap:12px}
.timing{font-size:13px;color:var(--muted);white-space:nowrap}
.strip{display:flex;height:10px;border-radius:6px;overflow:hidden;margin:6px 0 4px;background:var(--line)}
.strip i{display:block;height:100%}
.s-headline{background:var(--blue)}.s-so_what{background:var(--teal)}.s-ask{background:var(--amber)}
.s-offer{background:var(--violet)}
.budget{position:relative;height:16px;font-size:11px;color:var(--faint)}
.budget span{position:absolute;top:0;transform:translateX(-100%)}
.moves{margin:6px 0 20px;padding:0;list-style:none}
.moves li{display:grid;grid-template-columns:118px 1fr;gap:12px;padding:8px 0;border-top:1px solid var(--line)}
.moves li:first-child{border-top:0}
.moves .chip{justify-self:start;align-self:start;margin-top:2px}
.speak{font-size:17px}
.reply{background:var(--blue-tint);border-radius:12px;padding:14px 16px;margin:0 0 20px}
.reply .said{font-weight:600}.reply p{margin:4px 0 0}
.cols{display:grid;grid-template-columns:3fr 2fr;gap:18px}
.hold{background:var(--blue-tint);border-radius:12px;padding:14px 16px}
.hold ul{margin:4px 0 0;padding-left:18px}.hold li{margin:4px 0;font-size:15px}
.trap{background:var(--red-soft);border-radius:12px;padding:14px 16px;font-size:15px}
.trap .label{color:var(--red)}
.pending{background:var(--amber-soft);color:var(--amber);border-radius:12px;padding:12px 16px;font-size:14px;
margin:0 0 16px}
.fill li .blank{border-bottom:1px dashed var(--faint);color:var(--faint);min-height:24px}
.coach{font-size:15px;color:var(--muted);margin:14px 0 0}
.drill{margin-top:20px;display:flex;align-items:center;gap:14px;flex-wrap:wrap}
button{font:inherit;font-size:15px;font-weight:600;border:0;border-radius:10px;padding:9px 16px;cursor:pointer;
background:var(--blue);color:var(--on-blue,#fff)}
button.secondary{background:transparent;color:var(--blue);border:1px solid var(--blue-soft)}
.timer{flex:1;min-width:160px;height:8px;border-radius:6px;background:var(--blue-soft);overflow:hidden;display:none}
.timer i{display:block;height:100%;width:100%;background:var(--blue);transform-origin:left}
.done{font-size:14px;color:var(--teal);font-weight:600;display:none}
.card.saying .breath,.card.saying .moves,.card.saying .hold,.card.saying .reply p{filter:blur(7px);
user-select:none}
.card.saying .timer{display:block}
.card.said .done{display:inline}
footer{color:var(--faint);font-size:13px;margin-top:30px}
a{color:var(--blue)}
.day{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px 20px;margin:0 0 14px}
.day h2{font-size:17px;margin:0 0 6px}.day ol{margin:0;padding-left:20px}.day li{margin:3px 0}
@media (max-width:640px){.how,.cols{grid-template-columns:1fr}.moves li{grid-template-columns:1fr;gap:4px}
h1{font-size:28px}.card{padding:20px 18px}}
@media print{body{background:#fff}.drill{display:none}.card{break-inside:avoid;border-color:#ccc}}
"""

JS = """
(function(){
  function key(c){return 'fdecoach-ak-'+document.body.dataset.date+'-'+c.dataset.slot}
  document.querySelectorAll('.card[data-slot]').forEach(function(c){
    try{ if(localStorage.getItem(key(c))==='1'){c.classList.add('said')} }catch(e){}
    var btn=c.querySelector('button.say'); if(!btn){return}
    var bar=c.querySelector('.timer i'); var secs=parseInt(c.dataset.seconds||'25',10); var t=null;
    btn.addEventListener('click',function(){
      if(c.classList.contains('saying')){
        c.classList.remove('saying'); clearTimeout(t); btn.textContent='Say it back';
        c.classList.add('said'); try{localStorage.setItem(key(c),'1')}catch(e){}
        return;
      }
      c.classList.add('saying'); btn.textContent='Reveal and compare';
      bar.style.transition='none'; bar.style.transform='scaleX(1)';
      void bar.offsetWidth;
      bar.style.transition='transform '+secs+'s linear'; bar.style.transform='scaleX(0)';
      t=setTimeout(function(){btn.textContent='Time. Reveal and compare'},secs*1000);
    });
  });
})();
"""


def _listener_html(q: Dict[str, Any]) -> str:
    if not q.get("listener"):
        return ""
    cares = f" <span>· cares about {_e(q['cares'])}</span>" if q.get("cares") else ""
    return f'<p class="to">To <b>{_e(q["listener"])}</b>{cares}</p>'


def _card(i: int, q: Dict[str, Any], a: Optional[Dict[str, Any]], cfg: Dict[str, Any]) -> str:
    window = int((cfg.get("exec_mode") or {}).get("headline_seconds", 25))
    meta = [f'<span class="q">Q{i}</span>', _e(q.get("category_label", "")), f"Difficulty {_e(q.get('difficulty'))}/5"]
    if q.get("exec"):
        meta.append(f'<span class="badge">Exec · {window} s headline window</span>')
    meta_html = meta[0] + " " + SEP.join(meta[1:])
    head = (f'<div class="meta">{meta_html}</div>'
            f"{_listener_html(q)}"
            f'<p class="question">{_e(q["text"])}' +
            (f"<br><i>Constraint: {_e(q['constraint'])}</i>" if q.get("constraint") else "") + "</p>")
    reply = q.get("exec_reply") or {}
    if a is None:
        rows = "".join(f'<li><span class="chip m-{m}">{MOVE_LABELS[m]}</span><span class="blank">&nbsp;</span></li>'
                       for m in MOVES)
        return (f'<section class="card" data-slot="{i}">{head}'
                '<div class="pending">Model answer pending: Claude wasn’t reachable. It fills in by itself; '
                'meanwhile, write your own in the exec shape below and say it aloud.</div>'
                f'<p class="label">Your exec answer, in {window} seconds</p><ul class="moves fill">{rows}</ul>'
                f'<p class="coach"><b>What a strong answer does:</b> {_e(q.get("coach_note"))}</p></section>')
    total = sum(words(p["text"]) for p in a["answer"])
    secs = _seconds(total, cfg)
    strip = "".join(f'<i class="s-{p["move"]}" style="width:{100 * words(p["text"]) / max(1, total):.1f}%" '
                    f'title="{MOVE_LABELS[p["move"]]}"></i>' for p in a["answer"])
    budget_pos = min(100.0, 100.0 * window / max(secs, window))
    budget = (f'<div class="budget"><span style="left:{budget_pos:.1f}%">{window} s window</span></div>'
              if secs > window else "")
    moves = "".join(f'<li><span class="chip m-{p["move"]}">{MOVE_LABELS[p["move"]]}</span>'
                    f'<span class="speak">{_e(p["text"])}</span></li>' for p in a["answer"])
    reply_html = ""
    if reply.get("line"):
        who = _e(q.get("listener") or "They")
        if reply.get("kind") in REPLY_NEEDS_ANSWER and a.get("reply_answer"):
            reply_html = (f'<div class="reply"><p class="label">Then the {who} replied</p>'
                          f'<div class="said">“{_e(reply["line"])}”</div>'
                          f'<p>{_e(a["reply_answer"])}</p></div>')
        else:
            reply_html = (f'<div class="reply"><p class="label">Then the {who} replied</p>'
                          f'<div class="said">“{_e(reply["line"])}”</div>'
                          '<p>“Great.” Then stop. The silence is the skill: they have what they need.</p></div>')
    return (
        f'<section class="card" data-slot="{i}" data-seconds="{window}">{head}'
        f'<p class="label">One breath</p><p class="breath">{_e(a["headline"])}</p>'
        f'<div class="row"><p class="label">The exec answer</p>'
        f'<span class="timing">{total} words · about {secs} s aloud</span></div>'
        f'<div class="strip" aria-hidden="true">{strip}</div>{budget}'
        f'<ul class="moves">{moves}</ul>{reply_html}'
        '<div class="cols">'
        f'<div class="hold"><p class="label">Hold back — offer if asked</p><ul>'
        + "".join(f"<li>{_e(d)}</li>" for d in a["detail"]) + "</ul></div>"
        f'<div class="trap"><p class="label">The trap</p>{_e(a["trap"])}</div></div>'
        '<div class="drill"><button class="say" type="button">Say it back</button>'
        f'<div class="timer" role="progressbar" aria-label="{window} second timer"><i></i></div>'
        '<span class="done">✓ Said back</span></div></section>'
    )


def render_page(session: Dict[str, Any], answers: Dict[int, Dict[str, Any]], cfg: Dict[str, Any]) -> str:
    date = dt.date.fromisoformat(session["date"])
    n = len(session["questions"])
    window = int((cfg.get("exec_mode") or {}).get("headline_seconds", 25))
    ready = sum(1 for i in range(1, n + 1) if i in answers)
    cards = "".join(_card(i, q, answers.get(i), cfg) for i, q in enumerate(session["questions"], 1))
    legend = (" <span class='arrow'>→</span> ".join(f'<span class="chip m-{m}">{MOVE_LABELS[m]}</span>'
                                                         for m in MOVES))
    status = "" if ready == n else f" · {ready} of {n} model answers so far"
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Exec answer key · Day {_e(session.get('day_number'))}</title><style>{CSS}</style></head>
<body data-date="{_e(session['date'])}"><main>
<div class="kicker">FDE impromptu · exec answer key</div>
<h1>Day {_e(session.get('day_number'))}: what landing it sounds like</h1>
<p class="sub">{_e(date.strftime('%A, %d %B %Y'))} · Level {_e(session.get('level'))} of 5{status}</p>
<div class="how">
<div><b>1 · Read the one breath</b>The line your listener must remember. Out loud.</div>
<div><b>2 · Read the exec answer</b>Once, aloud, at speaking pace: about {window} seconds.</div>
<div><b>3 · Say it back</b>The answer blurs and a {window}-second bar runs. Say it in your own words, then compare.</div>
</div>
<div class="shape-legend">The shape: {legend}</div>
{cards}
<footer>Written by Claude after your session from the rubric in references/answer_design.md. Model answers are one good
way to say it, not the only one: keep your own words, borrow the shape. <a href="index.html">Every day’s one-breath
lines</a></footer>
</main><script>{JS}</script></body></html>
"""


def write_page(ctx, session: Dict[str, Any], answers: Dict[int, Dict[str, Any]]) -> Path:
    page = html_path(ctx.paths, dt.date.fromisoformat(session["date"]))
    page.parent.mkdir(parents=True, exist_ok=True)
    tmp = page.with_name("." + page.name + ".tmp")
    tmp.write_text(render_page(session, answers, ctx.cfg), encoding="utf-8")
    os.replace(tmp, page)
    return page


def write_index(ctx) -> Path:
    """Every day's one-breath lines on one page: a revision sheet that grows with the streak."""
    history = ctx.history()
    days: List[str] = []
    for key in sorted(history.sessions, reverse=True):
        s = history.sessions[key]
        date = dt.date.fromisoformat(key)
        if not s.get("recorded") or not html_path(ctx.paths, date).exists():
            continue
        store = _read_json(json_path(ctx.paths, date), {}).get("answers") or {}
        items = []
        for i, q in enumerate(s.get("questions", []), 1):
            a = store.get(str(i))
            line = _e(a["headline"]) if a else "<i>model answer pending</i>"
            who = f"<span style='color:var(--muted)'>To {_e(q.get('listener'))}:</span> " if q.get("listener") else ""
            items.append(f"<li>{who}{line}</li>")
        days.append(f'<div class="day"><h2><a href="{_e(html_path(ctx.paths, date).name)}">Day {_e(s.get("day_number"))}'
                    f'</a> · {_e(date.strftime("%a %d %b %Y"))}</h2><ol>{"".join(items)}</ol></div>')
    body = "".join(days) or "<p class='sub'>No answer keys yet. They appear after your first recorded session.</p>"
    page = index_path(ctx.paths)
    page.parent.mkdir(parents=True, exist_ok=True)
    page.write_text(f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Exec answer keys</title><style>{CSS}</style></head><body><main>
<div class="kicker">FDE impromptu · exec answer keys</div><h1>Every one-breath line</h1>
<p class="sub">Read down the list aloud: the habit is the headline first. Open a day for the full answers.</p>
{body}</main></body></html>
""", encoding="utf-8")
    return page
