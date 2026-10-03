"""Software Factory daily video: the learning path, day planning, and the
written briefs (day-before reminder and recording-day prep sheet).

One video -> one concept -> one clear takeaway, taught Greg Tang style:
see it (a real demo) -> group it (one picture of the pattern) -> name it
(the takeaway). The curriculum lives in
assets/factory_curriculum.json; references/factory_curriculum.md is the rubric
for writing more days. Topics are consumed in order: a day that isn't
published carries over, so the path never skips a concept.
"""
from __future__ import annotations

import copy
import datetime as dt
import html
import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .config import ASSETS_DIR, Paths
from .state import History

log = logging.getLogger("fdecoach")

CURRICULUM_FILE = ASSETS_DIR / "factory_curriculum.json"
DIAGRAMS_DIR = ASSETS_DIR / "factory_diagrams"
VISUAL_TYPES = ("image", "flow", "compare", "hub", "layers", "code")
SECTIONS = ("intro", "hook", "demo", "picture", "end", "outro")
SECTION_DEFAULTS = (4, 25, 100, 22, 12, 7)
MAX_VIDEO_SECONDS = 180
LIMITS = {"title": 60, "concept": 40, "sentence": 150, "takeaway": 130, "slide_point": 40, "point": 60}
REQUIRED = ("day", "module", "id", "title", "concept", "what", "what_points", "why", "why_points", "how",
            "how_points", "visual", "analogy", "jargon", "takeaway", "references", "diagrams", "artifact",
            "demo", "verify", "builds_on")
OVERRIDABLE = set(REQUIRED) - {"day", "module", "id"}

TAKE_FOCUS = {
    1: ("Discovery", "Explain the idea naturally. Don't stop or restart; just get through it."),
    2: ("Improve", "Fix unclear explanations, cut unneeded words, check timing and technical accuracy."),
    3: ("Publish", "The cleanest natural version. Conversational, not perfect. This one ships."),
}

_CURRICULUM: Optional[Dict[str, Any]] = None


# --------------------------------------------------------------------------- curriculum

def load_curriculum() -> Dict[str, Any]:
    global _CURRICULUM
    if _CURRICULUM is None:
        _CURRICULUM = json.loads(CURRICULUM_FILE.read_text(encoding="utf-8"))
    return _CURRICULUM


def total_days(cur: Optional[Dict[str, Any]] = None) -> int:
    return len((cur or load_curriculum())["days"])


def module_info(cur: Dict[str, Any], module_id: str) -> Tuple[int, int, Dict[str, Any]]:
    """(1-based index, module count, module) for a module id."""
    mods = cur["modules"]
    for i, m in enumerate(mods, 1):
        if m["id"] == module_id:
            return i, len(mods), m
    return 0, len(mods), {"id": module_id, "title": module_id, "goal": ""}


def _visual_errors(v: Any) -> List[str]:
    if not isinstance(v, dict) or v.get("type") not in VISUAL_TYPES:
        return [f"visual.type must be one of {', '.join(VISUAL_TYPES)}"]
    kind, errs = v["type"], []
    if kind == "image":
        if not (DIAGRAMS_DIR / f"{v.get('diagram', '')}.png").exists():
            errs.append(f"visual.diagram {v.get('diagram')!r} has no PNG in assets/factory_diagrams")
    elif kind == "flow":
        nodes = v.get("nodes") or []
        if not 2 <= len(nodes) <= 5:
            errs.append("flow needs 2-5 nodes")
        for n in nodes:
            label = n.get("label") if isinstance(n, dict) else n
            if not label or len(str(label)) > 28:
                errs.append(f"flow node label missing or longer than 28 chars: {label!r}")
        arrows = v.get("arrows") or []
        if arrows and len(arrows) != len(nodes) - 1:
            errs.append("flow arrows must label every gap (len(nodes) - 1)")
    elif kind == "compare":
        for side in ("left", "right"):
            s = v.get(side) or {}
            if not s.get("title") or not 1 <= len(s.get("points") or []) <= 4:
                errs.append(f"compare.{side} needs a title and 1-4 points")
    elif kind == "hub":
        if not v.get("center") or not 3 <= len(v.get("spokes") or []) <= 6:
            errs.append("hub needs a center and 3-6 spokes")
    elif kind == "layers":
        layers = v.get("layers") or []
        if not 2 <= len(layers) <= 5 or not all(isinstance(x, dict) and x.get("label") for x in layers):
            errs.append("layers needs 2-5 items with a label")
    elif kind == "code":
        lines = v.get("lines") or []
        if not 1 <= len(lines) <= 12 or any(len(x) > 72 for x in lines):
            errs.append("code needs 1-12 lines of at most 72 characters")
    return errs


def validate_day(d: Dict[str, Any]) -> List[str]:
    errs = [f"missing {k}" for k in REQUIRED if k not in d]
    if errs:
        return errs
    if len(d["title"]) > LIMITS["title"]:
        errs.append(f"title longer than {LIMITS['title']}")
    if len(d["concept"]) > LIMITS["concept"]:
        errs.append(f"concept longer than {LIMITS['concept']}")
    for k in ("what", "why", "how"):
        if not d[k] or len(d[k]) > LIMITS["sentence"]:
            errs.append(f"{k} must be one sentence of at most {LIMITS['sentence']} characters")
    if not d["takeaway"] or len(d["takeaway"]) > LIMITS["takeaway"]:
        errs.append(f"takeaway must be one sentence of at most {LIMITS['takeaway']} characters")
    for k in ("what_points", "why_points"):
        pts = d[k]
        if not isinstance(pts, list) or not 2 <= len(pts) <= 3 or any(len(p) > LIMITS["slide_point"] for p in pts):
            errs.append(f"{k}: 2-3 slide points of at most {LIMITS['slide_point']} characters")
    hp = d["how_points"]
    if not isinstance(hp, list) or not 2 <= len(hp) <= 5 or any(len(p) > LIMITS["point"] for p in hp):
        errs.append(f"how_points: 2-5 points of at most {LIMITS['point']} characters")
    errs += _visual_errors(d["visual"])
    from .factory_demo import validate_demo
    errs += [f"demo: {e}" for e in validate_demo(d["demo"])]
    for name in d["diagrams"]:
        if not (DIAGRAMS_DIR / f"{name}.png").exists():
            errs.append(f"diagram {name!r} has no PNG")
    if not d["references"]:
        errs.append("at least one repository reference")
    for ref in d["references"]:
        if ref.startswith(("/", "http")):
            errs.append(f"reference {ref!r} must be a path relative to the repository root")
    if not d["verify"]:
        errs.append("at least one point to verify")
    for j in d["jargon"]:
        if not isinstance(j, dict) or not j.get("term") or not j.get("plain"):
            errs.append("jargon items need term and plain")
    return errs


def validate_curriculum(cur: Dict[str, Any]) -> List[str]:
    errs: List[str] = []
    ids, modules = set(), {m["id"] for m in cur.get("modules", [])}
    for i, d in enumerate(cur.get("days", []), 1):
        where = f"day {d.get('day', i)}"
        if d.get("day") != i:
            errs.append(f"{where}: days must be numbered 1, 2, 3 ... in order")
        if d.get("module") not in modules:
            errs.append(f"{where}: unknown module {d.get('module')!r}")
        if d.get("id") in ids:
            errs.append(f"{where}: duplicate id {d.get('id')!r}")
        for b in d.get("builds_on") or []:
            if b not in ids:
                errs.append(f"{where}: builds_on {b!r} is not an earlier day")
        ids.add(d.get("id"))
        errs += [f"{where}: {e}" for e in validate_day(d)]
    return errs


def _merge(base: Dict[str, Any], over: Dict[str, Any]) -> Dict[str, Any]:
    out = copy.deepcopy(base)
    for k, v in over.items():
        if k in OVERRIDABLE:
            out[k] = v
    return out


def override_path(paths: Paths, topic_id: str) -> Path:
    return paths.factory / "overrides" / f"{topic_id}.json"


def topic(n: int, paths: Optional[Paths] = None, cur: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """Curriculum day n (1-based), with the learner's override file merged in when it is valid."""
    cur = cur or load_curriculum()
    if not 1 <= n <= len(cur["days"]):
        return None
    d = copy.deepcopy(cur["days"][n - 1])
    if paths is not None:
        path = override_path(paths, d["id"])
        if path.exists():
            try:
                merged = _merge(d, json.loads(path.read_text(encoding="utf-8")))
                problems = validate_day(merged)
                if problems:
                    log.warning("override %s ignored: %s", path, "; ".join(problems))
                else:
                    merged["overridden"] = True
                    d = merged
            except (OSError, ValueError) as exc:
                log.warning("override %s unreadable: %s", path, exc)
    return d


# --------------------------------------------------------------------------- timing

def segments(cfg: Dict[str, Any]) -> Dict[str, int]:
    f = cfg.get("factory", {})
    return {s: int(f.get(f"{s}_seconds", d)) for s, d in zip(SECTIONS, SECTION_DEFAULTS)}


def talk_seconds(cfg: Dict[str, Any]) -> int:
    seg = segments(cfg)
    return sum(seg[s] for s in ("intro", "hook", "demo", "picture", "end"))


def video_seconds(cfg: Dict[str, Any]) -> int:
    return talk_seconds(cfg) + segments(cfg)["outro"]


def starts(cfg: Dict[str, Any]) -> Dict[str, int]:
    seg, t, out = segments(cfg), 0, {}
    for s in SECTIONS:
        out[s] = t
        t += seg[s]
    return out


def ts(seconds: float) -> str:
    m, s = divmod(max(0, int(seconds)), 60)
    return f"{m}:{s:02d}"


def chapters(d: Dict[str, Any], cfg: Dict[str, Any]) -> List[Tuple[int, str]]:
    """YouTube chapters: the first starts at 0:00 and each lasts 10 s or more, so the short
    intro is folded into the WHAT chapter."""
    st = starts(cfg)
    return [(0, f"What and why: {d['concept']}"), (st["demo"], f"Demo: {d['demo']['title']}"),
            (st["picture"], "The picture"), (st["end"], "Takeaway")]


# --------------------------------------------------------------------------- planning

def start_date(cfg: Dict[str, Any]) -> dt.date:
    return dt.date.fromisoformat(str(cfg.get("factory", {}).get("start_date", "2026-10-10")))


def _published_before(history: History, date: dt.date) -> int:
    days = [int(s.get("day", 0)) for k, s in history.sessions.items()
            if s.get("recorded") and k < date.isoformat()]
    return max(days, default=0)


def day_for(history: History, cfg: Dict[str, Any], date: dt.date, ref: dt.date) -> Optional[int]:
    """Curriculum day planned for `date`, seen from `ref` (today). Past and present dates
    follow what was actually published; future dates assume one video per day from today."""
    start = start_date(cfg)
    if date < start:
        return None
    existing = history.get(date)
    if existing:
        return int(existing["day"])
    if date <= ref:
        return _published_before(history, date) + 1
    if ref < start:
        return (date - start).days + 1
    return int(day_for(history, cfg, ref, ref) or 0) + (date - ref).days


# --------------------------------------------------------------------------- documents

_INLINE = re.compile(r"(\*\*[^*]+\*\*|`[^`]+`)")


def _inline_html(text: str) -> str:
    out = []
    for part in _INLINE.split(text):
        if part.startswith("**") and part.endswith("**") and len(part) > 4:
            out.append(f"<strong>{html.escape(part[2:-2])}</strong>")
        elif part.startswith("`") and part.endswith("`") and len(part) > 2:
            out.append(f"<code>{html.escape(part[1:-1])}</code>")
        else:
            out.append(html.escape(part))
    return "".join(out)


_CSS = """
:root { --navy:#0B2545; --blue:#1F5FBF; --soft:#DCE7F7; --tint:#F1F6FD; --gray:#5B6B7F; }
* { box-sizing: border-box; }
body { margin: 0; background: #fff; color: var(--navy);
       font-family: Calibri, Carlito, "Segoe UI", "Helvetica Neue", Arial, sans-serif; font-size: 18px;
       line-height: 1.5; }
main { max-width: 860px; margin: 0 auto; padding: 32px 16px 64px; }
.kicker { color: var(--blue); font-weight: 700; letter-spacing: .12em; text-transform: uppercase; font-size: 14px; }
h1 { font-size: 34px; line-height: 1.2; margin: 6px 0 4px; }
.meta { color: var(--gray); margin-bottom: 24px; }
h2 { font-size: 22px; color: var(--blue); border-bottom: 2px solid var(--soft); padding-bottom: 4px; margin-top: 32px; }
blockquote { margin: 12px 0; padding: 12px 18px; background: var(--tint); border-left: 4px solid var(--blue);
             font-size: 21px; }
table { border-collapse: collapse; width: 100%; font-size: 16px; }
th, td { text-align: left; padding: 8px 10px; border-bottom: 1px solid var(--soft); vertical-align: top; }
th { color: var(--gray); font-weight: 600; }
pre { background: var(--navy); color: #E6EEF9; padding: 14px 16px; border-radius: 8px; overflow-x: auto;
      font-size: 15px; line-height: 1.45; }
code { font-family: Menlo, Consolas, "DejaVu Sans Mono", monospace; font-size: .92em; }
p code, li code, td code { background: var(--tint); padding: 1px 5px; border-radius: 4px; }
a { color: var(--blue); }
ul.check { list-style: none; padding-left: 4px; }
ul.check li::before { content: "\\2610\\00a0\\00a0"; color: var(--blue); }
img { max-width: 100%; border: 1px solid var(--soft); border-radius: 8px; }
@media print { main { padding: 0; } }
"""


class Doc:
    """A tiny document model rendered to both Markdown and HTML (same content)."""

    def __init__(self, title: str, kicker: str = "", meta: str = ""):
        self.title, self.kicker, self.meta = title, kicker, meta
        self.blocks: List[Tuple[str, Any]] = []

    def h2(self, text: str) -> "Doc":
        self.blocks.append(("h2", text))
        return self

    def h3(self, text: str) -> "Doc":
        self.blocks.append(("h3", text))
        return self

    def p(self, text: str) -> "Doc":
        self.blocks.append(("p", text))
        return self

    def quote(self, text: str) -> "Doc":
        self.blocks.append(("quote", text))
        return self

    def bullets(self, items: Sequence[str]) -> "Doc":
        self.blocks.append(("ul", list(items)))
        return self

    def numbered(self, items: Sequence[str]) -> "Doc":
        self.blocks.append(("ol", list(items)))
        return self

    def checklist(self, items: Sequence[str]) -> "Doc":
        self.blocks.append(("check", list(items)))
        return self

    def table(self, header: Sequence[str], rows: Sequence[Sequence[str]]) -> "Doc":
        self.blocks.append(("table", (list(header), [list(r) for r in rows])))
        return self

    def code(self, lines: Sequence[str]) -> "Doc":
        self.blocks.append(("code", list(lines)))
        return self

    def links(self, items: Sequence[Tuple[str, str, str]]) -> "Doc":
        self.blocks.append(("links", list(items)))
        return self

    def image(self, src: str, alt: str) -> "Doc":
        self.blocks.append(("img", (src, alt)))
        return self

    def markdown(self) -> str:
        out = [f"# {self.title}", ""]
        if self.kicker:
            out[0:0] = [f"**{self.kicker}**", ""]
        if self.meta:
            out += [self.meta, ""]
        for kind, body in self.blocks:
            if kind == "h2":
                out += [f"## {body}", ""]
            elif kind == "h3":
                out += [f"### {body}", ""]
            elif kind == "p":
                out += [body, ""]
            elif kind == "quote":
                out += [f"> {body}", ""]
            elif kind == "ul":
                out += [f"- {x}" for x in body] + [""]
            elif kind == "ol":
                out += [f"{i}. {x}" for i, x in enumerate(body, 1)] + [""]
            elif kind == "check":
                out += [f"- [ ] {x}" for x in body] + [""]
            elif kind == "table":
                header, rows = body
                out.append("| " + " | ".join(header) + " |")
                out.append("|" + "|".join("---" for _ in header) + "|")
                out += ["| " + " | ".join(c.replace("|", "\\|") for c in r) + " |" for r in rows]
                out.append("")
            elif kind == "code":
                out += ["```"] + body + ["```", ""]
            elif kind == "links":
                out += [f"- [{label}]({url})" + (f" — {note}" if note else "") for label, url, note in body] + [""]
            elif kind == "img":
                out += [f"![{body[1]}]({body[0]})", ""]
        return "\n".join(out).rstrip() + "\n"

    def html(self) -> str:
        out = ["<!doctype html>", '<html lang="en"><head><meta charset="utf-8">',
               '<meta name="viewport" content="width=device-width, initial-scale=1">',
               f"<title>{html.escape(self.title)}</title><style>{_CSS}</style></head><body><main>"]
        if self.kicker:
            out.append(f'<div class="kicker">{html.escape(self.kicker)}</div>')
        out.append(f"<h1>{_inline_html(self.title)}</h1>")
        if self.meta:
            out.append(f'<div class="meta">{_inline_html(self.meta)}</div>')
        for kind, body in self.blocks:
            if kind == "h2":
                out.append(f"<h2>{_inline_html(body)}</h2>")
            elif kind == "h3":
                out.append(f"<h3>{_inline_html(body)}</h3>")
            elif kind == "p":
                out.append(f"<p>{_inline_html(body)}</p>")
            elif kind == "quote":
                out.append(f"<blockquote>{_inline_html(body)}</blockquote>")
            elif kind in ("ul", "ol", "check"):
                tag = "ol" if kind == "ol" else "ul"
                cls = ' class="check"' if kind == "check" else ""
                out.append(f"<{tag}{cls}>" + "".join(f"<li>{_inline_html(x)}</li>" for x in body) + f"</{tag}>")
            elif kind == "table":
                header, rows = body
                out.append("<table><thead><tr>" + "".join(f"<th>{_inline_html(h)}</th>" for h in header)
                           + "</tr></thead><tbody>"
                           + "".join("<tr>" + "".join(f"<td>{_inline_html(c)}</td>" for c in r) + "</tr>"
                                     for r in rows) + "</tbody></table>")
            elif kind == "code":
                out.append("<pre><code>" + html.escape("\n".join(body)) + "</code></pre>")
            elif kind == "links":
                out.append("<ul>" + "".join(
                    f'<li><a href="{html.escape(url)}">{html.escape(label)}</a>'
                    + (f" — {_inline_html(note)}" if note else "") + "</li>" for label, url, note in body) + "</ul>")
            elif kind == "img":
                out.append(f'<p><img src="{html.escape(body[0])}" alt="{html.escape(body[1])}"></p>')
        out.append("</main></body></html>")
        return "\n".join(out) + "\n"


# --------------------------------------------------------------------------- brief + prep

def repo_url(cfg: Dict[str, Any], path: str) -> str:
    f = cfg.get("factory", {})
    repo = str(f.get("gascity_repo", "https://github.com/gastownhall/gascity")).rstrip("/")
    return f"{repo}/blob/{f.get('gascity_ref', 'main')}/{path}"


def diagram_url(cfg: Dict[str, Any], name: str) -> str:
    return repo_url(cfg, f"docs/diagrams/excalidraw-rendered/{name}.svg")


def visual_summary(v: Dict[str, Any]) -> str:
    kind = v["type"]
    if kind == "image":
        return f"Gas City diagram `{v['diagram']}`"
    if kind == "flow":
        labels = [n["label"] if isinstance(n, dict) else n for n in v["nodes"]]
        return "Flow: " + " → ".join(labels) + (" (loops back)" if v.get("loop") else "")
    if kind == "compare":
        return f"Side by side: {v['left']['title']} vs. {v['right']['title']}"
    if kind == "hub":
        return f"Hub: {v['center']} with {', '.join(v['spokes'])}"
    if kind == "layers":
        return "Layers: " + " / ".join(x["label"] for x in v["layers"])
    return f"Code ({v.get('lang', 'text')}), {len(v['lines'])} lines"


def demo_steps(d: Dict[str, Any]) -> List[Tuple[str, str]]:
    """(command as shown, what to point out) for every visible demo step; saved values appear as <name>."""
    from .factory_demo import VAR
    out = []
    for st in d["demo"]["steps"]:
        if "write" in st or st.get("hidden"):
            continue
        cmd = VAR.sub(lambda m: {"rig": "~/hello-factory", "city": "~/lab", "scratch": "."}.get(
            m.group(1), f"<{m.group(1)}>"), st.get("run") or st["wait_for"])
        if "wait_for" in st:
            cmd = f"{cmd}   # time-lapse until '{st['until']}'"
        out.append((cmd, st.get("say", "")))
    return out


def demo_where(d: Dict[str, Any]) -> str:
    demo = d["demo"]
    store = "file-based demo city (no Dolt)" if demo.get("store") == "file" else "default demo city (bd + Dolt)"
    agent = "uses Claude Code (tokens), slow parts become time-lapse cuts" if demo.get("agent") else "no agent, fast"
    return f"{store}; {agent}"


def outline_rows(d: Dict[str, Any], cfg: Dict[str, Any]) -> List[List[str]]:
    seg, st = segments(cfg), starts(cfg)

    def span(s: str) -> str:
        return f"{ts(st[s])}–{ts(st[s] + seg[s])}"

    return [
        [span("intro"), "Intro", "Title card and music. Stay silent, settle, smile."],
        [span("hook"), "What & why", f"**{d['concept']}** · " + " · ".join(d["what_points"][:2])
         + " · why: " + d["why_points"][0]],
        [span("demo"), "See it", f"Demo: {d['demo']['title']}. " + " → ".join(say for _, say in demo_steps(d) if say)],
        [span("picture"), "Group it", " → ".join(d["how_points"]) + f" (on screen: {visual_summary(d['visual'])})"],
        [span("end"), "Name it", f"“{d['takeaway']}”"],
        [span("outro"), "Outro", "Soft music on the closing card. Say nothing."],
    ]


def _header(cur: Dict[str, Any], d: Dict[str, Any], date: dt.date) -> Tuple[str, str]:
    idx, n_mods, mod = module_info(cur, d["module"])
    meta = (f"{date.strftime('%A %d %B %Y')} · Module {idx} of {n_mods}: {mod['title']} · "
            f"Day {d['day']} of {total_days(cur)}")
    return mod["title"], meta


def _builds_on(cur: Dict[str, Any], d: Dict[str, Any]) -> str:
    titles = {x["id"]: f"Day {x['day']}: {x['title']}" for x in cur["days"]}
    return "; ".join(titles.get(b, b) for b in d["builds_on"]) or "Nothing — this is where the path starts."


def brief_doc(d: Dict[str, Any], date: dt.date, cfg: Dict[str, Any], cur: Optional[Dict[str, Any]] = None) -> Doc:
    """The day-before reminder: topic, WHAT/WHY/HOW, references, diagrams, artifact, outline."""
    cur = cur or load_curriculum()
    series = cfg.get("factory", {}).get("series", "Software Factory")
    _, meta = _header(cur, d, date)
    doc = Doc(f"Tomorrow: {d['title']}", kicker=f"{series} · Day {d['day']}", meta=meta)
    doc.quote(f"Takeaway: {d['takeaway']}")
    doc.h2("WHAT").p(d["what"]).bullets(d["what_points"])
    doc.h2("WHY").p(d["why"]).bullets(d["why_points"])
    doc.h2("HOW").p(d["how"]).bullets(d["how_points"])
    doc.p(f"After the demo, the picture groups what viewers saw: {visual_summary(d['visual'])}.")
    doc.h2(f"Demo: {d['demo']['title']}")
    doc.p(f"Real commands, run in the {demo_where(d)}. The output is captured on your Mac tonight and "
          "becomes the animated terminal in the video, so nothing is screen-recorded.")
    doc.code([c for c, _ in demo_steps(d)])
    doc.bullets([f"`{c.split('   #')[0][:60]}` — {say}" for c, say in demo_steps(d) if say])
    doc.h2("Say it simply")
    doc.p(f"Analogy: {d['analogy']}")
    if d["jargon"]:
        doc.p("Jargon to explain the moment you use it:")
        doc.bullets([f"**{j['term']}** — {j['plain']}" for j in d["jargon"]])
    doc.h2("Key repository references")
    doc.links([(r, repo_url(cfg, r), "") for r in d["references"]])
    doc.h2("Relevant existing diagrams")
    if d["diagrams"]:
        doc.links([(name, diagram_url(cfg, name), "Gas City docs") for name in d["diagrams"]])
    else:
        doc.p("None in the repository for this one; the slide draws a simple diagram for you.")
    doc.h2("Artifact to prepare")
    doc.p(d["artifact"])
    doc.h2("3-minute outline: see it, group it, name it")
    doc.table(["Time", "Section", "Say (keywords, not a script)"], outline_rows(d, cfg))
    doc.h2("Builds on")
    doc.p(_builds_on(cur, d))
    doc.h2("Tonight, 10 minutes")
    doc.numbered([
        "Skim the references above; stop when the WHAT makes sense.",
        "Say the takeaway out loud twice, in your own words.",
        "Explain the HOW to an imaginary engineer who has never used Gas City.",
        "Watch the demo capture notification. If a step failed, fix it tonight (fde-coach factory demo capture).",
        "Tomorrow's slides, outline and checks are built for you in the morning.",
    ])
    return doc


def prep_doc(d: Dict[str, Any], date: dt.date, cfg: Dict[str, Any], kit: Dict[str, str],
             cur: Optional[Dict[str, Any]] = None) -> Doc:
    """The recording-day sheet: outline, slides, diagram, demo, checks, final flow, takes."""
    cur = cur or load_curriculum()
    f = cfg.get("factory", {})
    series = f.get("series", "Software Factory")
    _, meta = _header(cur, d, date)
    seg = segments(cfg)
    doc = Doc(f"Recording day: {d['title']}", kicker=f"{series} · Day {d['day']}", meta=meta)
    doc.quote(f"One concept: {d['concept']}. One takeaway: {d['takeaway']}")
    doc.h2("Speaking outline (keywords, not a script)")
    doc.p(f"**What & why ({seg['hook']} s)** — open with: “Today: {d['concept'].lower()}.” Then: "
          + " · ".join(d["what_points"]) + ". Why: " + " · ".join(d["why_points"]))
    doc.p(f"**See it ({seg['demo']} s)** — narrate the demo; the terminal moves by itself:")
    doc.bullets([say for _, say in demo_steps(d) if say])
    doc.p(f"**Group it ({seg['picture']} s)** — map what they just saw onto the picture: "
          + " → ".join(d["how_points"]))
    doc.p(f"**Name it ({seg['end']} s)** — close with: “{d['takeaway']}”")
    doc.p(f"Analogy if you need one: {d['analogy']}")
    if d["jargon"]:
        doc.bullets([f"Say **{j['term']}**, then right away: “{j['plain']}”." for j in d["jargon"]])
    doc.h2("Slides")
    doc.p(f"Deck: `{kit.get('deck', '')}` (minimal blue theme, Calibri). It runs by itself: "
          f"{seg['intro']} s countdown, the hook, one slide per demo step, the picture and the takeaway, "
          "each with a progress bar.")
    if kit.get("how_png"):
        doc.image(kit["how_png"], "The picture slide")
    doc.h2(f"Demo: {d['demo']['title']}")
    doc.p(kit.get("demo_status") or "Not captured yet: fde-coach factory demo capture")
    doc.p(f"Runs in the {demo_where(d)}.")
    doc.code([c for c, _ in demo_steps(d)])
    doc.h2("Diagram")
    if d["visual"]["type"] == "image":
        doc.p(f"The HOW slide shows the Gas City diagram `{d['visual']['diagram']}`. Walk through it left to "
              "right, top to bottom; point at one box per sentence.")
    else:
        doc.p(f"The HOW slide draws it for you: {visual_summary(d['visual'])}.")
    if d["diagrams"]:
        doc.links([(name, diagram_url(cfg, name), "") for name in d["diagrams"]])
    doc.h2("Artifact")
    doc.p(d["artifact"])
    doc.h2("Key technical points to verify before Take 1")
    doc.checklist(list(d["verify"]) + ["The demo capture passed and its output says what you plan to point at.",
                                        "Open each reference below and check the words you plan to say."])
    doc.links([(r, repo_url(cfg, r), "") for r in d["references"]])
    doc.h2("Final 3-minute flow")
    doc.table(["Time", "Section", "Say"], outline_rows(d, cfg))
    doc.p(f"Total: {ts(video_seconds(cfg))}. Under three minutes, every time.")
    doc.h2(f"Three takes, then publish (max {int(f.get('max_takes', 3))})")
    doc.bullets([f"**Take {n} — {name}:** {text}" for n, (name, text) in TAKE_FOCUS.items()])
    doc.p("After Take 3, stop. Publish the take you have; tomorrow is a new video.")
    doc.h2("Commands")
    doc.code([
        "fde-coach factory take        # or double-click 'Start Video' in ~/FDE-Impromptu",
        "fde-coach factory publish --take 3",
        "fde-coach factory published --url https://youtu.be/...",
    ])
    return doc


def _anchor(text: str) -> str:
    """GitHub-style heading anchor."""
    return re.sub(r"[^a-z0-9 -]", "", text.lower()).replace(" ", "-")


def learning_path_doc(cfg: Dict[str, Any], cur: Optional[Dict[str, Any]] = None) -> Doc:
    """The whole path, every day in full (references/factory_learning_path.md is generated from it)."""
    cur = cur or load_curriculum()
    start = start_date(cfg)
    series = cfg.get("factory", {}).get("series", "Software Factory")
    doc = Doc(f"{series}: the learning path", kicker="Daily video series",
              meta=(f"{total_days(cur)} videos from {start.strftime('%d %B %Y')} · one concept a day · "
                    f"source: {cur['source']['repo']} (verified at {cur['source']['verified_commit'][:10]})"))
    doc.p("Generated from `assets/factory_curriculum.json` by "
          "`fde-coach factory plan --markdown --write references/factory_learning_path.md`. "
          "Dates assume one video a day; a missed day carries its topic over, so no concept is skipped.")
    doc.p("Rule for every video: one video, one concept, one clear takeaway, under three minutes. "
          "Understand → Explain → Demonstrate → Publish → Repeat.")
    doc.p("Every video teaches Greg Tang style: **see it** (a real demo with real output), **group it** "
          "(one picture of the pattern), **name it** (the takeaway). Days 1–7 run in a file-based demo city; "
          "from Day 8 the demos use the default setup (bd + Dolt). Your face is never recorded.")
    seg = segments(cfg)
    doc.p(f"Video format ({ts(video_seconds(cfg))}): intro {seg['intro']} s · what & why {seg['hook']} s · "
          f"demo {seg['demo']} s · picture {seg['picture']} s · takeaway {seg['end']} s · outro {seg['outro']} s.")

    doc.h2("All days at a glance")
    rows = []
    for d in cur["days"]:
        date = start + dt.timedelta(days=d["day"] - 1)
        heading = f"Day {d['day']}: {d['title']}"
        rows.append([str(d["day"]), date.strftime("%a %d %b"), f"[{d['title']}](#{_anchor(heading)})",
                     d["demo"]["title"], d["takeaway"]])
    doc.table(["Day", "Date", "Topic", "Demo", "Takeaway"], rows)

    for idx, m in enumerate(cur["modules"], 1):
        days = [d for d in cur["days"] if d["module"] == m["id"]]
        if not days:
            continue
        doc.h2(f"Module {idx}: {m['title']}")
        doc.p(m["goal"])
        for d in days:
            date = start + dt.timedelta(days=d["day"] - 1)
            doc.h3(f"Day {d['day']}: {d['title']}")
            doc.p(f"{date.strftime('%A %d %B %Y')} · concept: **{d['concept']}** · builds on: "
                  + _builds_on(cur, d))
            doc.quote(f"Takeaway: {d['takeaway']}")
            doc.p(f"**WHAT** — {d['what']}")
            doc.bullets(d["what_points"])
            doc.p(f"**WHY** — {d['why']}")
            doc.bullets(d["why_points"])
            doc.p(f"**HOW** — {d['how']}")
            doc.bullets(d["how_points"])
            doc.p(f"**See it — demo: {d['demo']['title']}** ({demo_where(d)})")
            doc.code([c for c, _ in demo_steps(d)])
            doc.bullets([say for _, say in demo_steps(d) if say])
            doc.p(f"**Group it — picture:** {visual_summary(d['visual'])}"
                  + (f" ({d['visual']['caption']})" if d["visual"].get("caption") else "") + ".")
            doc.p(f"**Say it simply:** {d['analogy']}")
            if d["jargon"]:
                doc.bullets([f"**{j['term']}** — {j['plain']}" for j in d["jargon"]])
            doc.table(["Time", "Section", "Say (keywords, not a script)"], outline_rows(d, cfg))
            doc.p(f"**Prepare:** {d['artifact']}")
            doc.p("**Repository references:**")
            doc.links([(r, repo_url(cfg, r), "") for r in d["references"]]
                      + [(f"diagram: {n}", diagram_url(cfg, n), "") for n in d["diagrams"]])
            doc.p("**Verify before Take 1:**")
            doc.checklist(d["verify"])
    return doc
