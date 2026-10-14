#!/usr/bin/env python3
"""Keep the learning path's time estimates and the curriculum page in sync.

    python3 scripts/tools/build_curriculum.py           # recompute every topic's time, rewrite curriculum.md
    python3 scripts/tools/build_curriculum.py --check   # exit 1 if either file is out of date (the tests run this)

`assets/learning_path.json` is the source of truth. Each topic's "time" is calculated from its own content
(resource minutes, build steps, set-up, new maths, artifact type) with the rules in the file's "pace" block,
so the estimates stay honest when a topic changes. `fde-learn/references/curriculum.md` is rendered from it.

If your real times differ after project 1, change the numbers in "pace" and run this again: every topic's
mornings, the project totals and the timeline on the curriculum page follow.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, List

SKILL = Path(__file__).resolve().parents[2]
PATH_FILE = SKILL / "assets" / "learning_path.json"
CURRICULUM = SKILL.parent / "fde-learn" / "references" / "curriculum.md"
WEEKS_PER_MONTH = 4.345


def round5(x: float) -> int:
    return int(5 * math.ceil(round(x, 6) / 5))


def estimate(t: Dict[str, Any], pace: Dict[str, Any]) -> Dict[str, int]:
    """Minutes for one topic: learn, build, explain, total, and the mornings it gets."""
    e = pace["estimate"]
    learn = round5(e["learn_factor"] * sum(x["minutes"] for x in t["learn"]))
    per_step = e["build_minutes_per_step"][t["artifact"]]
    build = round5(per_step * len(t["build"]) + (e["setup_minutes"] if t.get("setup") else 0)
                   + (e["maths_minutes"] if t.get("math") else 0) + (t.get("extra") or {}).get("minutes", 0))
    explain = e["explain_minutes"].get(t["artifact"], e["explain_minutes"]["default"])
    total = learn + build + explain
    mornings = max(1, math.ceil((total - pace["grace_minutes"]) / pace["minutes_per_morning"]))
    return {"learn": learn, "build": build, "explain": explain, "total": total, "mornings": mornings}


def summary(data: Dict[str, Any]) -> Dict[str, Any]:
    pace = data["pace"]
    topics = data["topics"]
    minutes = sum(t["time"]["total"] for t in topics)
    mornings = sum(t["time"]["mornings"] for t in topics)
    weeks_fast = minutes / (pace["hours_per_week"] * 60)
    weeks_schedule = mornings / pace["mornings_per_week"]
    projects = {}
    for p in data["projects"]:
        ts = [t for t in topics if t["project"] == p["n"]]
        projects[p["n"]] = {"first": ts[0]["day"], "last": ts[-1]["day"],
                            "hours": sum(t["time"]["total"] for t in ts) / 60,
                            "mornings": sum(t["time"]["mornings"] for t in ts)}
    return {"topics": len(topics), "minutes": minutes, "hours": minutes / 60, "mornings": mornings,
            "weeks_fast": weeks_fast, "weeks_schedule": weeks_schedule,
            "months_fast": weeks_fast / WEEKS_PER_MONTH, "months_schedule": weeks_schedule / WEEKS_PER_MONTH,
            "projects": projects}


def about(data: Dict[str, Any]) -> str:
    s = summary(data)
    return ("A project-based path from software architect to first-principles AI engineer for the Forward "
            "Deployed Engineer role. A topic drops in the morning and gets one to three mornings, depending on "
            "its size: you learn it, build it and explain it on video. Each project ends with an article on "
            f"rajc.work. Maths appears only when a project needs it. About {s['hours']:.0f} hours of work: at "
            f"{data['pace']['hours_per_week']} hours a week, plan on {round(s['months_fast'])} to "
            f"{round(s['months_schedule'])} months.")


def apply(data: Dict[str, Any]) -> Dict[str, Any]:
    """Number the days and recalculate every estimate (and the 'about' line) from the content."""
    for i, t in enumerate(data["topics"], 1):
        t["day"] = i
        t["time"] = estimate(t, data["pace"])
    data["about"] = about(data)
    return data


def _plural(n: int, word: str) -> str:
    return f"{n} {word}" + ("" if n == 1 else "s")


def render(data: Dict[str, Any]) -> str:
    pace, e = data["pace"], data["pace"]["estimate"]
    s = summary(data)
    steps = e["build_minutes_per_step"]
    out: List[str] = [
        "# FDE First Principles: the curriculum",
        "",
        "Generated from `fde-impromptu-coach/assets/learning_path.json` (the source of truth) by "
        "`fde-impromptu-coach/scripts/tools/build_curriculum.py`. "
        f"{s['topics']} topics in {len(data['projects'])} projects. Every project ends with an article on "
        "[rajc.work](https://rajc.work): that is the finish line, not a date.",
        "",
        "Why this order: it starts from what you already do (calling models, building agents) and goes one layer "
        "deeper each time a project raises a question. Maths arrives only on the day a project needs it.",
        "",
        f"## Pace: plan on {round(s['months_fast'])} to {round(s['months_schedule'])} months",
        "",
        "| | |",
        "|---|---|",
        f"| Your time | {pace['hours_per_week']} hours a week: {pace['minutes_per_morning']} minutes a morning, "
        f"{pace['mornings_per_week']} mornings a week. Sunday is rest. |",
        f"| Total work | about {s['hours']:.0f} hours, estimated topic by topic below |",
        f"| Finish each topic early and pull the next one (`fde-coach learn next`) | about "
        f"{s['weeks_fast']:.0f} weeks ({s['months_fast']:.1f} months) |",
        f"| Use every morning the schedule allows | about {s['weeks_schedule']:.0f} weeks "
        f"({s['months_schedule']:.1f} months) |",
        "",
        "A topic drops in the morning and gets as many mornings as its estimate needs: one for most diagrams, two "
        "for most notebooks, three for an article. Ship it when it is done: the next topic drops the next morning, "
        "or straight away with `fde-coach learn next`. A missed deadline is never skipped: the topic comes back at "
        "minimum scope with half the mornings.",
        "",
        "### How each topic's time is calculated",
        "",
        f"- **Learn**: the resource minutes × {e['learn_factor']} (pausing, replaying and reading in a second "
        "language), rounded up to 5.",
        f"- **Build**: {steps['notebook']} minutes per build step for a notebook or code, {steps['diagram']} for a "
        f"diagram, {steps['doc']} for a document, {steps['article']} for an article; plus {e['setup_minutes']} if "
        f"there is set-up and {e['maths_minutes']} if there is new maths."
        + "".join(f" Day {t['day']} adds {t['extra']['minutes']} for {t['extra']['why']}."
                  for t in data["topics"] if t.get("extra")),
        f"- **Explain**: {e['explain_minutes']['default']} minutes for \"In my words\" and two takes of a "
        f"5-minute video ({e['explain_minutes']['article']} for an article, where the video is optional).",
        f"- **Mornings**: the total ÷ {pace['minutes_per_morning']} minutes, rounded up after a "
        f"{pace['grace_minutes']}-minute grace.",
        "",
        "If your real times differ after project 1, change the numbers in `pace` and run the tool again.",
        "",
        "## Rules that save time",
        "",
        "- **One-hour rule.** When unfamiliar maths appears, spend at most an hour on that one idea (the topic's "
        "maths note, a 3Blue1Brown lesson, a few Khan Academy exercises, or Claude explaining it with your own "
        "numbers), then go back to the code. Anything bigger goes in `later.md`.",
        "- **Finish lines, not calendars.** A project is done when its article is live on rajc.work. The article "
        "starts with about 300 words written from memory, without notes: if you can't write them, that is the "
        "part to revisit.",
        "- **Courses are references, not syllabi.** Each topic names the exact section to read or watch.",
        "- **Skip what you know** (API integration, orchestration, cloud deployment) and **postpone** "
        "eigenvectors, advanced calculus, training large models and most research papers.",
        "- **Keep it cheap.** All resources are free. Everything runs on your Mac with Ollama, and the GPT "
        "project can use free Colab time. The only paid step is the final run in project 6: a hard monthly "
        "spending cap first, an estimate before the run, cached answers so re-runs are free.",
    ]
    for p in data["projects"]:
        ps = s["projects"][p["n"]]
        out += ["", f"## Project {p['n']} · {p['title']} (days {ps['first']}–{ps['last']} · about "
                    f"{ps['hours']:.0f} hours · {_plural(ps['mornings'], 'morning')})",
                "", p["goal"], "", f"Maths you will meet: {p['math']}.", "",
                "| Day | Topic | Learn (main resource) | Maths | Artifact | Time |",
                "|---|---|---|---|---|---|"]
        for t in [t for t in data["topics"] if t["project"] == p["n"]]:
            main = t["learn"][0]
            maths = t["math"]["idea"] if t.get("math") else "–"
            tm = t["time"]
            out.append(f"| {t['day']} | {t['title']} | [{main['title']}]({main['url']}) | {maths} | "
                       f"{t['artifact']} | {tm['total']} min · {_plural(tm['mornings'], 'morning')} |")
    return "\n".join(out) + "\n"


def dumps(data: Dict[str, Any]) -> str:
    return json.dumps(data, indent=1, ensure_ascii=False) + "\n"


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--check", action="store_true", help="only check; exit 1 if a file is out of date")
    args = ap.parse_args(argv)
    raw = PATH_FILE.read_text(encoding="utf-8")
    data = apply(json.loads(raw))
    want = {PATH_FILE: dumps(data), CURRICULUM: render(data)}
    stale = [p for p, text in want.items() if not p.exists() or p.read_text(encoding="utf-8") != text]
    if args.check:
        for p in stale:
            print(f"out of date: {p} (run scripts/tools/build_curriculum.py)")
        return 1 if stale else 0
    for p in stale:
        p.write_text(want[p], encoding="utf-8")
        print(f"wrote {p}")
    s = summary(data)
    print(f"{s['topics']} topics · {s['hours']:.0f} hours · {s['mornings']} mornings · "
          f"{s['weeks_fast']:.1f}–{s['weeks_schedule']:.1f} weeks")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
