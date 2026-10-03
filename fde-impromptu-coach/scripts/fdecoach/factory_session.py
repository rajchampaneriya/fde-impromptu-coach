"""Software Factory daily video flows: the recording-day kit, up to three voice
takes over the auto-advancing slides, video assembly with intro and outro
music, publishing, the day-before brief, reminders and Google Calendar events.

The voice is never cleaned up: no noise reduction, no loudness processing.
It is only aligned with the slides, faded out over its last second, and mixed
with quiet music under the intro and outro cards.

Lock order matches app.py: session -> generate -> history; calendar standalone.
"""
from __future__ import annotations

import datetime as dt
import logging
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from . import audio, gcal, macos, youtube
from . import factory_deck as FD
from .config import APP_NAME, Paths, parse_hhmm
from .factory import (TAKE_FOCUS, brief_doc, chapters, day_for, learning_path_doc, load_curriculum,
                      prep_doc, repo_url, segments, start_date, talk_seconds, topic, total_days,
                      video_seconds, visual_summary, outline_rows, ts)
from .state import History, LockBusy, file_lock, lock_is_held, now, streaks, today

log = logging.getLogger("fdecoach")

GCAL_BRIEF = "fdefbrief"   # event ids may only use a-v and 0-9
GCAL_PUBLISH = "fdefpub"
STUDIO_URL = "https://studio.youtube.com/"
MUSIC_EXTS = (".m4a", ".mp3", ".wav", ".aac", ".aiff", ".flac")


class FactoryNotReady(RuntimeError):
    """Before the start date, or after the last planned day."""


def fhistory(paths: Paths) -> History:
    return History(paths, file=paths.factory_state)


def _f(cfg: Dict[str, Any]) -> Dict[str, Any]:
    return cfg.get("factory", {})


def _slug(d: Dict[str, Any]) -> str:
    return f"Day{int(d['day']):02d}_{d['id']}"


def kit_dir(paths: Paths, date: dt.date, d: Dict[str, Any]) -> Path:
    return paths.factory / "kits" / f"{date.isoformat()}_{_slug(d)}"


def media_dir(ctx, date: dt.date, d: Dict[str, Any], create: bool = True) -> Path:
    folder = ctx.paths.recordings_dir(ctx.cfg, create=create) / "factory" / f"{date.isoformat()}_{_slug(d)}"
    if create:
        folder.mkdir(parents=True, exist_ok=True)
    return folder


def _at(hhmm: str, date: dt.date) -> dt.datetime:
    h, m = parse_hhmm(hhmm)
    return dt.datetime.combine(date, dt.time(h, m))


def _planned(ctx, date: dt.date) -> Tuple[Optional[int], Optional[Dict[str, Any]]]:
    n = day_for(fhistory(ctx.paths), ctx.cfg, date, today())
    return n, (topic(n, ctx.paths) if n else None)


def _require_topic(ctx, date: dt.date) -> Tuple[int, Dict[str, Any]]:
    n, d = _planned(ctx, date)
    if n is None:
        raise FactoryNotReady(f"The Software Factory series starts on {start_date(ctx.cfg).isoformat()}.")
    if d is None:
        raise FactoryNotReady(
            f"The learning path ends at Day {total_days()}. Ask Claude Code to plan the next module "
            "(references/factory_curriculum.md explains how).")
    return n, d


# --------------------------------------------------------------------------- briefs + kit

def brief_text(d: Dict[str, Any], date: dt.date, cfg: Dict[str, Any]) -> str:
    """Plain-text brief for calendar descriptions and notifications."""
    lines = [f"Day {d['day']} · {d['title']} ({date.strftime('%A %d %B %Y')})", "",
             f"Takeaway: {d['takeaway']}", "",
             f"WHAT: {d['what']}", f"WHY: {d['why']}", f"HOW: {d['how']}",
             f"On screen: {visual_summary(d['visual'])}", "", f"Analogy: {d['analogy']}"]
    if d["jargon"]:
        lines += ["Explain right away: " + "; ".join(f"{j['term']} = {j['plain']}" for j in d["jargon"])]
    lines += ["", "References:"] + [f"- {repo_url(cfg, r)}" for r in d["references"]]
    if d["diagrams"]:
        lines += ["Diagrams:"] + [f"- {repo_url(cfg, 'docs/diagrams/excalidraw-rendered/' + n + '.svg')}"
                                  for n in d["diagrams"]]
    lines += ["", f"Prepare: {d['artifact']}"]
    if d["demo"]:
        lines += ["Demo:"] + [f"  {c}" for c in d["demo"]]
    lines += ["", f"Outline ({ts(video_seconds(cfg))}):"]
    lines += [f"{r[0]} {r[1]} — {r[2].replace('**', '')}" for r in outline_rows(d, cfg)]
    return "\n".join(lines)


def write_brief(ctx, date: dt.date, d: Dict[str, Any]) -> Dict[str, str]:
    folder = ctx.paths.factory / "briefs"
    folder.mkdir(parents=True, exist_ok=True)
    doc = brief_doc(d, date, ctx.cfg)
    stem = f"{date.isoformat()}_{_slug(d)}"
    md, html_path = folder / f"{stem}.md", folder / f"{stem}.html"
    md.write_text(doc.markdown(), encoding="utf-8")
    html_path.write_text(doc.html(), encoding="utf-8")
    return {"md": str(md), "html": str(html_path), "markdown": doc.markdown()}


def build_kit(ctx, date: dt.date, d: Dict[str, Any]) -> Dict[str, Any]:
    """Slides (frames + take deck), prep sheet and brief for one recording day."""
    cfg, cur = ctx.cfg, load_curriculum()
    folder = kit_dir(ctx.paths, date, d)
    frames = FD.render_frames(d, cfg, cur, topic(int(d["day"]) + 1, ctx.paths), folder / "frames")
    countdown = FD.render_countdown(d, cfg, 1, folder / "frames")
    stem = f"{date.isoformat()}_SoftwareFactory_Day{int(d['day']):02d}"
    pptx, ppsx = FD.build_take_deck(d, cfg, frames, countdown, folder, stem)
    kit: Dict[str, Any] = {"dir": str(folder), "deck": str(pptx), "show": str(ppsx),
                           "frames": {k: str(v) for k, v in frames.items()}, "how_png": "frames/how.png"}
    doc = prep_doc(d, date, cfg, kit, cur)
    (folder / "prep.md").write_text(doc.markdown(), encoding="utf-8")
    (folder / "prep.html").write_text(doc.html(), encoding="utf-8")
    brief = brief_doc(d, date, cfg, cur)
    (folder / "brief.md").write_text(brief.markdown(), encoding="utf-8")
    (folder / "brief.html").write_text(brief.html(), encoding="utf-8")
    kit.update(prep_md=str(folder / "prep.md"), prep_html=str(folder / "prep.html"))
    log.info("Software Factory kit for %s (Day %s): %s", date, d["day"], folder)
    return kit


def _kit_ok(s: Dict[str, Any]) -> bool:
    kit = s.get("kit") or {}
    return Path(kit.get("deck", "")).exists() and all(Path(p).exists() for p in (kit.get("frames") or {}).values()) \
        and bool(kit.get("frames"))


def ensure_kit(ctx, rebuild: bool = False) -> Dict[str, Any]:
    """Today's session with its kit. Builds the kit when missing (or on rebuild)."""
    date = today()
    with file_lock(ctx.paths, "generate", blocking=True):
        history = fhistory(ctx.paths)
        s = history.get(date)
        n, d = _require_topic(ctx, date)
        if s and _kit_ok(s) and not rebuild:
            return s
        if s and s.get("recorded") and rebuild:
            raise RuntimeError("Today's video is already published; its kit can't be rebuilt.")
        kit = build_kit(ctx, date, d)
        with file_lock(ctx.paths, "history", blocking=True):
            history = fhistory(ctx.paths)
            s = history.get(date)
            if s is None:
                carried = any(int(x.get("day", 0)) == n and not x.get("recorded")
                              for k, x in history.sessions.items() if k < date.isoformat())
                s = {"date": date.isoformat(), "day": n, "topic": d["id"], "title": d["title"],
                     "created_at": now().isoformat(timespec="seconds"), "carried_over": carried,
                     "takes": [], "recorded": False, "youtube": {"status": "none"}}
            s["kit"] = kit
            s["title"] = d["title"]
            history.put(s)
            history.save()
        return s


def prepare(ctx, date: Optional[dt.date] = None, rebuild: bool = False) -> Dict[str, Any]:
    """Kit for today (stored with today's session) or for a future date (files only)."""
    date = date or today()
    if date == today():
        s = ensure_kit(ctx, rebuild=rebuild)
        return {"date": s["date"], "day": s["day"], "title": s["title"], **s["kit"]}
    if date < today():
        raise ValueError("Past days can't be prepared; record today's topic instead.")
    n, d = _require_topic(ctx, date)
    kit = build_kit(ctx, date, d)
    return {"date": date.isoformat(), "day": n, "title": d["title"], **kit}


def update_session(ctx, date: dt.date, fn) -> Optional[Dict[str, Any]]:
    with file_lock(ctx.paths, "history", blocking=True):
        history = fhistory(ctx.paths)
        s = history.get(date)
        if s is None:
            return None
        fn(s)
        history.put(s)
        history.save()
        return s


# --------------------------------------------------------------------------- takes

def _valid_takes(s: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [t for t in s.get("takes", []) if t.get("audio")]


def _record_take(ctx, s: Dict[str, Any], d: Dict[str, Any], n: int) -> Dict[str, Any]:
    from .recorder import _run_show
    cfg, f = ctx.cfg, _f(ctx.cfg)
    date = dt.date.fromisoformat(s["date"])
    folder = media_dir(ctx, date, d)
    dest = folder / f"take{n}.m4a"
    kit = s["kit"]
    frames = {k: Path(v) for k, v in kit["frames"].items()}
    countdown = FD.render_countdown(d, cfg, n, Path(kit["dir"]) / "frames")
    stem = f"{date.isoformat()}_SoftwareFactory_Day{int(d['day']):02d}_take{n}"
    deck, show = FD.build_take_deck(d, cfg, frames, countdown, Path(kit["dir"]), stem)
    total = FD.take_seconds(cfg)
    grace = int(cfg.get("recording", {}).get("stop_grace_seconds", 4))
    device = str(f.get("audio_device") or cfg.get("pronunciation", {}).get("audio_device", ""))
    result: Dict[str, Any] = {"ok": False, "n": n, "audio": None, "offset": None, "ended_early": False}

    t_rec = time.time()
    cap = audio.AudioCapture(dest, device)
    if cap.start():
        ended_early, t_show = _run_show(deck, show, cfg, total, grace)
        saved = cap.stop()
        result["method"] = "ffmpeg"
    else:
        t_rec = time.time()
        if not macos.quicktime_start_audio_recording(float(cfg.get("recording", {}).get("camera_warmup_seconds", 2))):
            result["error"] = "audio capture did not start (ffmpeg and the QuickTime fallback both failed)"
            return result
        ended_early, t_show = _run_show(deck, show, cfg, total, grace)
        ok, how = macos.quicktime_stop_audio_save(dest, since=t_rec)
        macos.quit_app("QuickTime Player")
        saved = dest if ok else None
        result["method"] = f"quicktime:{how}"
    result["offset"] = round(max(0.0, t_show - t_rec), 2)
    result["ended_early"] = bool(ended_early)
    if saved is None:
        result["error"] = "the take's audio was not saved"
        return result
    result["audio"] = str(saved)
    duration = audio.audio_duration_seconds(Path(saved))
    result["duration"] = duration
    min_secs = int(f.get("min_take_seconds", 60))
    if duration is not None and duration < min_secs:
        result["error"] = f"take too short ({int(duration)} s < {min_secs} s)"
        result["too_short"] = True
        return result
    result["ok"] = True
    return result


def run_takes(ctx) -> Dict[str, Any]:
    try:
        with file_lock(ctx.paths, "session"):
            return _run_takes_locked(ctx)
    except LockBusy:
        msg = "Another recording session is already running."
        log.info(msg)
        return {"ok": False, "error": msg}


def _run_takes_locked(ctx) -> Dict[str, Any]:
    s = ensure_kit(ctx)
    date = dt.date.fromisoformat(s["date"])
    d = topic(int(s["day"]), ctx.paths)
    if s.get("recorded"):
        macos.notify(APP_NAME, "Today's video is already published. See you tomorrow.")
        return {"ok": True, "already_published": True}
    max_takes = int(_f(ctx.cfg).get("max_takes", 3))
    confirmed = False
    while True:
        s = fhistory(ctx.paths).get(date) or s
        n = len(_valid_takes(s)) + 1
        if n > max_takes:
            last = max_takes
            answer = macos.dialog(
                f"All {max_takes} takes are done. Avoid chasing perfection: publish one and move on.",
                APP_NAME, ["Choose a take", "Later", f"Publish take {last}"], f"Publish take {last}",
                timeout_seconds=600)
            return _after_last_take(ctx, date, answer, last)
        name, focus = TAKE_FOCUS.get(n, ("Extra", "Natural and clear. Then publish."))
        start_btn = f"Start take {n}"
        if not confirmed:
            answer = macos.dialog(
                f"Day {s['day']}: {s['title']}\n\nTake {n} of {max_takes} · {name}\n{focus}\n\n"
                "Voice only, about 3 minutes. The slides run by themselves and the recording stops on its own.",
                APP_NAME, ["Later", start_btn], start_btn, timeout_seconds=600)
            if answer != start_btn:
                return {"ok": False, "error": "not started", "take": n}
        confirmed = False
        log.info("Software Factory take %d for %s (Day %s)", n, date, s["day"])
        result = _record_take(ctx, s, d, n)
        log.info("factory take -> %s", result)
        if not result.get("ok"):
            why = result.get("error", "unknown error")
            answer = macos.dialog(f"Take {n} didn't count: {why}.\n\nIt isn't one of your {max_takes} takes.",
                                  APP_NAME, ["Later", "Try again"], "Try again", timeout_seconds=300, icon="caution")
            if answer == "Try again":
                confirmed = True
                continue
            return result
        entry = {k: result.get(k) for k in ("n", "audio", "duration", "offset", "method", "ended_early")}
        entry["at"] = now().isoformat(timespec="seconds")
        s = update_session(ctx, date, lambda x: x.setdefault("takes", []).append(entry)) or s
        if n < max_takes:
            next_name, next_focus = TAKE_FOCUS.get(n + 1, ("Extra", ""))
            nxt = f"Start take {n + 1}"
            answer = macos.dialog(
                f"Take {n} saved ({name}).\n\nNext, Take {n + 1} · {next_name}: {next_focus}\n\n"
                "Or publish this one if it already says what you mean.",
                APP_NAME, ["Publish this take", "Listen first", nxt], nxt, timeout_seconds=600)
            if answer == nxt:
                confirmed = True
                continue
            if answer == "Listen first":
                macos.open_path(Path(entry["audio"]), "QuickTime Player")
                macos.notify(APP_NAME, f"When you're ready: Take {n + 1}, or publish Take {n}.",
                             subtitle="fde-coach factory take  ·  fde-coach factory publish")
                return {"ok": True, "take": n, "next": "listen"}
            if answer == "Publish this take":
                return publish(ctx, date, n)
            return {"ok": True, "take": n}
        answer = macos.dialog(
            f"Take {n} saved. That's the publish take: conversational beats perfect.",
            APP_NAME, ["Choose a take", "Later", f"Publish take {n}"], f"Publish take {n}", timeout_seconds=600)
        return _after_last_take(ctx, date, answer, n)


def _after_last_take(ctx, date: dt.date, answer: str, last: int) -> Dict[str, Any]:
    if answer == f"Publish take {last}":
        return publish(ctx, date, last)
    if answer == "Choose a take":
        s = fhistory(ctx.paths).get(date) or {}
        labels = [f"Take {t['n']}" for t in _valid_takes(s)]
        picked = macos.choose_from_list("Which take should be published?", APP_NAME, labels,
                                        default_items=labels[-1:])
        if picked:
            return publish(ctx, date, int(picked[0].split()[-1]))
    return {"ok": True, "take": last, "published": False}


# --------------------------------------------------------------------------- music + video

def _music_expr(kind: str) -> str:
    chords = {
        "intro": [(261.63, 0.64), (329.63, 0.48), (392.00, 0.40), (587.33, 0.20)],   # C add9: bright, simple
        "outro": [(174.61, 0.60), (220.00, 0.48), (261.63, 0.40), (329.63, 0.28)],   # Fmaj7: soft, settled
    }[kind]
    swell = "0.25" if kind == "intro" else "0.15"
    tones = "+".join(f"{a}*sin(2*PI*{f}*t)" for f, a in chords)
    return f"(0.85+0.15*sin(2*PI*{swell}*t))*({tones})"


def music_file(ctx, kind: str) -> Optional[Path]:
    """Your track (config path, or ~/FDE-Impromptu/factory/music/<kind>.*), else a gentle generated chord."""
    configured = str(_f(ctx.cfg).get(f"{kind}_music") or "")
    if configured and Path(configured).expanduser().exists():
        return Path(configured).expanduser()
    folder = ctx.paths.factory / "music"
    for ext in MUSIC_EXTS:
        if (folder / f"{kind}{ext}").exists():
            return folder / f"{kind}{ext}"
    generated = folder / f".generated_{kind}.m4a"
    if generated.exists() and generated.stat().st_size > 0:
        return generated
    exe = audio.ffmpeg_path()
    if not exe:
        return None
    folder.mkdir(parents=True, exist_ok=True)
    secs = 10 if kind == "intro" else 14
    cmd = [exe, "-y", "-f", "lavfi", "-i", f"aevalsrc=exprs={_music_expr(kind)}:s=48000:d={secs}",
           "-af", f"afade=t=in:d=0.6,afade=t=out:st={secs - 3}:d=3,aecho=0.8:0.5:90:0.25",
           "-ac", "2", "-c:a", "aac", "-b:a", "160k", str(generated)]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if proc.returncode != 0 or not generated.exists():
        log.warning("could not generate %s music: %s", kind, (proc.stderr or "")[-300:])
        return None
    return generated


def music_report(ctx) -> Dict[str, str]:
    out = {}
    folder = ctx.paths.factory / "music"
    for kind in ("intro", "outro"):
        configured = str(_f(ctx.cfg).get(f"{kind}_music") or "")
        mine = next((folder / f"{kind}{e}" for e in MUSIC_EXTS if (folder / f"{kind}{e}").exists()), None)
        if configured and Path(configured).expanduser().exists():
            out[kind] = configured
        elif mine:
            out[kind] = str(mine)
        else:
            out[kind] = "generated soft chord (add your own: " + str(folder / f"{kind}.mp3") + ")"
    return out


def audio_channels(path: Path) -> Optional[int]:
    probe = shutil.which("ffprobe")
    if not probe:
        return None
    try:
        out = subprocess.run([probe, "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=channels",
                              "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
                             capture_output=True, text=True, timeout=30).stdout.strip()
        return int(out) if out else None
    except (ValueError, subprocess.TimeoutExpired):
        return None


def assemble_video(ctx, s: Dict[str, Any], d: Dict[str, Any], take: Dict[str, Any]) -> Optional[Path]:
    """Intro card + WHAT/WHY/HOW/Takeaway frames + outro card, with the take's voice (unprocessed)
    aligned to the slides and quiet music under the intro and outro."""
    cfg = ctx.cfg
    date = dt.date.fromisoformat(s["date"])
    out = media_dir(ctx, date, d) / "final.mp4"
    if macos.dry_run():
        out.write_bytes(b"\0" * (2 * 1024 * 1024))
        log.info("[dry-run] factory video -> %s", out)
        return out
    exe = audio.ffmpeg_path()
    if not exe:
        macos.notify(APP_NAME, "Video not assembled: ffmpeg not found", "Install it: brew install ffmpeg")
        return None
    if not _kit_ok(s):
        s = ensure_kit(ctx) if date == today() else s
    frames = {k: Path(v) for k, v in s["kit"]["frames"].items()}
    seg = segments(cfg)
    talk, total = talk_seconds(cfg), video_seconds(cfg)
    lst = Path(s["kit"]["dir"]) / "video_frames.txt"
    with open(lst, "w", encoding="utf-8") as fh:
        for name in ("intro", "what", "why", "how", "end", "outro"):
            fh.write(f"file '{frames[name]}'\nduration {seg[name]:.3f}\n")
        fh.write(f"file '{frames['outro']}'\n")
    vol = float(_f(cfg).get("music_volume", 0.5))
    off = max(0.0, float(take.get("offset") or 0.0))
    fmt = "aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo"
    # A mono microphone goes to both channels at full level (ffmpeg's default upmix is 3 dB quieter).
    voice_fmt = "pan=stereo|c0=c0|c1=c0," + fmt if audio_channels(Path(take["audio"])) == 1 else fmt
    inputs = ["-f", "concat", "-safe", "0", "-i", str(lst), "-i", str(take["audio"])]
    intro_len, outro_len = seg["intro"] + 1.5, float(seg["outro"])
    for kind, length in (("intro", intro_len), ("outro", outro_len)):
        track = music_file(ctx, kind)
        if track:
            inputs += ["-i", str(track)]
        else:
            inputs += ["-f", "lavfi", "-t", f"{length:.3f}", "-i", "anullsrc=r=48000:cl=stereo"]
    talk_ms = int(talk * 1000)
    graph = ";".join([
        "[0:v]fps=30,format=yuv420p[v]",
        f"[1:a]atrim=start={off:.3f},asetpts=PTS-STARTPTS,atrim=end={talk + 1:.3f},{voice_fmt},"
        f"afade=t=out:st={talk:.3f}:d=1,apad=whole_dur={total:.3f}[voice]",
        f"[2:a]atrim=end={intro_len:.3f},asetpts=PTS-STARTPTS,{fmt},afade=t=in:d=0.4,"
        f"afade=t=out:st={intro_len - 1.5:.3f}:d=1.5,volume={vol}[m1]",
        f"[3:a]atrim=end={outro_len:.3f},asetpts=PTS-STARTPTS,{fmt},afade=t=in:d=1.2,"
        f"afade=t=out:st={max(0.0, outro_len - 3):.3f}:d=3,volume={vol},adelay={talk_ms}|{talk_ms}[m2]",
        "[voice][m1][m2]amix=inputs=3:duration=first:normalize=0[a]",
    ])
    cmd = [exe, "-y", *inputs, "-filter_complex", graph, "-map", "[v]", "-map", "[a]",
           "-c:v", "libx264", "-tune", "stillimage", "-preset", "veryfast", "-crf", "20",
           "-c:a", "aac", "-b:a", "192k", "-t", f"{total:.3f}", "-movflags", "+faststart", str(out)]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
    if proc.returncode != 0 or not out.exists():
        log.warning("factory video assembly failed: %s", (proc.stderr or "")[-600:])
        macos.notify(APP_NAME, "Video assembly failed", "The take audio is safe. Run: fde-coach doctor")
        return None
    log.info("Software Factory video assembled: %s", out)
    return out


# --------------------------------------------------------------------------- publish

def youtube_metadata(d: Dict[str, Any], cfg: Dict[str, Any]) -> Dict[str, Any]:
    f = _f(cfg)
    series = f.get("series", "Software Factory")
    n_total = total_days()
    title = f"{d['title']} · {series} Day {d['day']}"
    lines = [d["what"], d["why"], ""]
    lines += [f"{ts(t)} {label}" for t, label in chapters(d, cfg)]
    lines += ["", f"Takeaway: {d['takeaway']}", "", "Go deeper (Gas City, open source):"]
    lines += [repo_url(cfg, r) for r in d["references"]]
    if d["visual"]["type"] == "image" or d["diagrams"]:
        lines.append("Diagrams: Gas City documentation (MIT licence).")
    lines += ["", f"{series}: one concept a day, under three minutes. Day {d['day']} of {n_total}."]
    prev, nxt = topic(int(d["day"]) - 1), topic(int(d["day"]) + 1)
    if prev:
        lines.append(f"Previous: Day {prev['day']} · {prev['title']}")
    if nxt:
        lines.append(f"Next: Day {nxt['day']} · {nxt['title']}")
    lines += ["", "#SoftwareFactory #GasCity #AIAgents"]
    tags: List[str] = []
    for tag in list(f.get("tags", [])) + [d["concept"].lower()]:
        if tag not in tags:
            tags.append(tag)
    return {
        "snippet": {
            "title": youtube._clean(title, 100),
            "description": youtube._clean("\n".join(lines), 4900),
            "tags": tags[:15],
            "categoryId": str(f.get("category_id", "28")),
        },
        "status": {"privacyStatus": str(f.get("privacy_status", "public")), "selfDeclaredMadeForKids": False},
    }


def _write_youtube_txt(path: Path, meta: Dict[str, Any], thumb: Path) -> None:
    sn = meta["snippet"]
    path.write_text("\n".join([
        "TITLE", sn["title"], "", "DESCRIPTION", sn["description"], "",
        "TAGS", ", ".join(sn["tags"]), "", "THUMBNAIL", thumb.name, "",
        "VISIBILITY", "Public (set it in YouTube Studio)", ""]), encoding="utf-8")


def publish(ctx, date: Optional[dt.date] = None, take: Optional[int] = None) -> Dict[str, Any]:
    """Assemble the final video from a take and publish it (YouTube Studio by default)."""
    date = date or today()
    s = fhistory(ctx.paths).get(date)
    if not s:
        raise RuntimeError(f"No Software Factory session for {date.isoformat()}.")
    takes = _valid_takes(s)
    if not takes:
        raise RuntimeError("No takes recorded yet: run fde-coach factory take")
    chosen = next((t for t in takes if int(t["n"]) == int(take)), None) if take else takes[-1]
    if chosen is None:
        raise RuntimeError(f"Take {take} doesn't exist (have: {', '.join(str(t['n']) for t in takes)}).")
    d = topic(int(s["day"]), ctx.paths)
    folder = media_dir(ctx, date, d)
    video = assemble_video(ctx, s, d, chosen)
    if video is None:
        update_session(ctx, date, lambda x: x["youtube"].update(status="failed", last_error="video assembly"))
        return {"ok": False, "error": "video assembly failed (ffmpeg missing or errored)"}
    thumb = FD.render_thumbnail(d, ctx.cfg, folder / "thumbnail.png")
    meta = youtube_metadata(d, ctx.cfg)
    txt = folder / "youtube.txt"
    _write_youtube_txt(txt, meta, thumb)
    update_session(ctx, date, lambda x: x.update(
        final_take=int(chosen["n"]), video_path=str(video), thumbnail=str(thumb), youtube_txt=str(txt),
        youtube=dict(x.get("youtube") or {}, status="ready")))
    mode = str(_f(ctx.cfg).get("publish_mode", "studio"))
    if mode == "api":
        try:
            vid = youtube.upload(ctx.paths, video, meta, thumbnail=thumb)
        except Exception as exc:  # noqa: BLE001
            log.warning("factory upload failed: %s", exc)
            err = str(exc)[:300]
            update_session(ctx, date, lambda x: x["youtube"].update(status="failed", last_error=err))
            macos.notify(APP_NAME, "Upload failed; the video is saved", str(exc)[:120])
            return {"ok": False, "error": str(exc), "video": str(video)}
        playlist = str(_f(ctx.cfg).get("playlist_id") or "")
        if playlist and not macos.dry_run():
            youtube.add_to_playlist(ctx.paths, vid, playlist)
        url = f"https://youtu.be/{vid}"
        mark_published(ctx, date, url)
        return {"ok": True, "video": str(video), "url": url, "mode": "api"}
    macos.copy_to_clipboard(meta["snippet"]["description"])
    macos.open_path(folder)
    macos.open_url(STUDIO_URL)
    button, text = macos.ask_text(
        f"Final video ready: Day {d['day']}, take {chosen['n']}.\n\n"
        "In YouTube Studio (just opened): Create → Upload videos → final.mp4 from the folder that opened.\n"
        f"Title: {meta['snippet']['title']}\nThe description is on your clipboard; thumbnail.png is in the folder; "
        "visibility Public.\n\nPaste the video link here once it's live:",
        APP_NAME, ["Later", "Save"], "Save")
    if text.strip().startswith(("http://", "https://")):
        mark_published(ctx, date, text.strip())
        return {"ok": True, "video": str(video), "url": text.strip(), "mode": "studio"}
    macos.notify(APP_NAME, "Video ready to upload", "When it's live: fde-coach factory published --url LINK")
    return {"ok": True, "video": str(video), "url": None, "mode": "studio", "folder": str(folder)}


def mark_published(ctx, date: dt.date, url: str) -> Dict[str, Any]:
    if not url.startswith(("http://", "https://")):
        raise ValueError("Pass the video link, for example https://youtu.be/abc123")

    def apply(x: Dict[str, Any]) -> None:
        x.update(recorded=True, published_at=now().isoformat(timespec="seconds"))
        x["youtube"] = dict(x.get("youtube") or {}, status="published", url=url)

    s = update_session(ctx, date, apply)
    if s is None:
        raise RuntimeError(f"No Software Factory session for {date.isoformat()}.")
    calendar_sync_safe(ctx)
    stats = streaks(fhistory(ctx.paths), date)
    macos.notify(f"Day {s['day']} published · {stats['current']}-day streak", url, sound="Hero")
    log.info("Software Factory Day %s published: %s", s["day"], url)
    return s


# --------------------------------------------------------------------------- reminder tick

def _notified(ctx, date: dt.date) -> List[str]:
    return list(((ctx.runtime().data.get("factory_notified") or {}).get(date.isoformat())) or [])


def _mark(ctx, date: dt.date, *kinds: str) -> None:
    from .app import update_runtime

    def apply(rt) -> None:
        book = rt.data.setdefault("factory_notified", {})
        cutoff = (date - dt.timedelta(days=14)).isoformat()
        for k in [k for k in book if k < cutoff]:
            book.pop(k)
        day = book.setdefault(date.isoformat(), [])
        day.extend(k for k in kinds if k not in day)

    update_runtime(ctx, apply)


def tick(ctx) -> str:
    """Runs from the 15-minute reminder agent: morning kit, recording-day nudges, evening brief."""
    f = _f(ctx.cfg)
    if not f.get("enabled", True):
        return "disabled"
    calendar_sync_safe(ctx)
    date, t = today(), now()
    quiet = _at(ctx.cfg.get("reminders", {}).get("quiet_after", "22:45"), date)
    if t >= quiet:
        return "quiet-hours"
    busy = lock_is_held(ctx.paths, "session")
    done: List[str] = []
    seen = _notified(ctx, date)
    history = fhistory(ctx.paths)
    s = history.get(date)
    n, d = _planned(ctx, date)
    if d and t >= _at(f.get("prep_time", "07:00"), date) and not (s and s.get("recorded")):
        if "kit" not in seen and not busy:
            s = ensure_kit(ctx)
            carried = " (carried over)" if s.get("carried_over") else ""
            macos.notify("Today's video kit is ready", f"Day {n}: {d['title']}{carried}",
                         subtitle="Slides, outline and checks. Three takes max, then publish.")
            macos.open_path(Path(s["kit"]["prep_html"]))
            _mark(ctx, date, "kit")
            done.append("kit")
        due = [x for x in sorted(f.get("reminder_times", [])) if _at(x, date) <= t and f"rem-{x}" not in seen]
        if due and ("kit" in seen or "kit" in done):
            macos.notify("Today's video isn't published yet", f"Day {n}: {d['title']}",
                         subtitle="fde-coach factory take, or double-click Start Video")
            _mark(ctx, date, *[f"rem-{x}" for x in due])
            done.append("reminder")
    if t >= _at(f.get("brief_time", "19:00"), date) and "brief" not in seen and not busy:
        tomorrow = date + dt.timedelta(days=1)
        n2 = day_for(fhistory(ctx.paths), ctx.cfg, tomorrow, date)
        d2 = topic(n2, ctx.paths) if n2 else None
        if d2:
            files = write_brief(ctx, tomorrow, d2)
            macos.notify("Tomorrow's video", f"Day {n2}: {d2['title']}",
                         subtitle="Brief opened: WHAT, WHY, HOW, references, outline")
            macos.open_path(Path(files["html"]))
            done.append("brief")
        _mark(ctx, date, "brief")
    return ",".join(done) or "nothing-due"


def tick_safe(ctx) -> None:
    try:
        tick(ctx)
    except Exception:  # noqa: BLE001 - never disturb the other practices
        log.exception("Software Factory tick failed")


# --------------------------------------------------------------------------- calendar

def _overrides(start: dt.datetime, date: dt.date, times: List[str], email: Optional[str]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for method, items in (("popup", times), ("email", [email] if email else [])):
        for hhmm in items:
            minutes = int((start - gcal._local(date, hhmm)).total_seconds() // 60)
            item = {"method": method, "minutes": minutes}
            if 0 <= minutes <= gcal.MAX_MINUTES and item not in out:
                out.append(item)
    return out[:gcal.MAX_OVERRIDES]


def _brief_event(ctx, video_date: dt.date, d: Dict[str, Any]) -> Dict[str, Any]:
    f = _f(ctx.cfg)
    day_before = video_date - dt.timedelta(days=1)
    start = gcal._local(day_before, f.get("brief_time", "19:00"))
    end = start + dt.timedelta(minutes=int(f.get("brief_event_minutes", 15)))
    text = brief_text(d, video_date, ctx.cfg)
    text += ("\n\nOn your Mac the full brief opens by itself; it lives in ~/FDE-Impromptu/factory/briefs/.\n"
             "Created by FDE Impromptu Coach.")
    return {
        "id": gcal.event_id(video_date, GCAL_BRIEF),
        "summary": f"Tomorrow's video · Day {d['day']}: {d['title']}",
        "description": text[:7900],
        "start": {"dateTime": start.isoformat()}, "end": {"dateTime": end.isoformat()},
        "reminders": {"useDefault": False, "overrides": [{"method": "popup", "minutes": 0},
                                                         {"method": "email", "minutes": 0}]},
        "colorId": "9", "transparency": "transparent", "visibility": "private",
        "extendedProperties": {"private": {"fdefactory": f"brief:{video_date.isoformat()}"}},
    }


def _publish_event(ctx, date: dt.date, d: Dict[str, Any]) -> Dict[str, Any]:
    f = _f(ctx.cfg)
    at = f.get("publish_event_time", "21:00")
    start = gcal._local(date, at)
    return {
        "id": gcal.event_id(date, GCAL_PUBLISH),
        "summary": f"Video not published yet · Day {d['day']}: {d['title']}",
        "description": ("Today's Software Factory video isn't published yet.\n\n"
                        "On your Mac: double-click 'Start Video' in ~/FDE-Impromptu, or run: fde-coach factory take\n"
                        "Three takes max, then publish.\n\n"
                        f"Takeaway: {d['takeaway']}\n\n"
                        "This event disappears when the video is published.\nCreated by FDE Impromptu Coach."),
        "start": {"dateTime": start.isoformat()},
        "end": {"dateTime": (start + dt.timedelta(minutes=15)).isoformat()},
        "reminders": {"useDefault": False,
                      "overrides": _overrides(start, date, list(f.get("publish_popup_times") or []), at)},
        "colorId": "9", "transparency": "transparent", "visibility": "private",
        "extendedProperties": {"private": {"fdefactory": f"publish:{date.isoformat()}"}},
    }


def _eid_date(eid: str) -> str:
    raw = eid[-8:]
    return f"{raw[:4]}-{raw[4:6]}-{raw[6:]}"


def calendar_sync(ctx, clear: bool = False) -> List[str]:
    """Day-before brief events (kept) and a not-published safety net per day (deleted on publish)."""
    gc, f = ctx.cfg.get("google_calendar", {}), _f(ctx.cfg)
    enabled = bool(gc.get("enabled", True)) and bool(f.get("enabled", True)) and bool(f.get("calendar", True)) \
        and not clear
    if not gcal.is_configured(ctx.paths) and not macos.dry_run():
        return ["Google Calendar not connected (run: fde-coach calendar-auth)."]
    from .app import notify_once, update_runtime
    try:
        with file_lock(ctx.paths, "calendar"):
            state: Dict[str, str] = dict(ctx.runtime().data.get("gcal_factory_events") or {})
            date, t = today(), now()
            want: Dict[str, Tuple[str, Optional[Dict[str, Any]]]] = {}
            if enabled:
                history = fhistory(ctx.paths)
                for i in range(int(gc.get("days_ahead", 2)) + 1):
                    day = date + dt.timedelta(days=i)
                    n = day_for(history, ctx.cfg, day, date)
                    d = topic(n, ctx.paths) if n else None
                    if d:
                        eid = gcal.event_id(day, GCAL_PUBLISH)
                        s = history.get(day)
                        if s and s.get("recorded"):
                            want[eid] = ("deleted", None)
                        elif gcal._local(day, f.get("publish_event_time", "21:00")).replace(tzinfo=None) > t:
                            want[eid] = (f"created:{d['id']}", _publish_event(ctx, day, d))
                    nxt = day + dt.timedelta(days=1)
                    n2 = day_for(history, ctx.cfg, nxt, date)
                    d2 = topic(n2, ctx.paths) if n2 else None
                    if d2 and gcal._local(day, f.get("brief_time", "19:00")).replace(tzinfo=None) > t:
                        want[gcal.event_id(nxt, GCAL_BRIEF)] = (f"created:{d2['id']}", _brief_event(ctx, nxt, d2))
            else:
                for eid, st in state.items():
                    if st.startswith("created") and _eid_date(eid) >= date.isoformat():
                        want[eid] = ("deleted", None)
            out: List[str] = []
            cal = str(gc.get("calendar_id", "primary"))
            for eid in sorted(want):
                marker, body = want[eid]
                if state.get(eid) == marker:
                    continue
                try:
                    if body is not None:
                        result = gcal.ensure_event(ctx.paths, cal, body)
                    else:
                        result = gcal.delete_event(ctx.paths, cal, eid)
                except (gcal.CalendarAuthExpired, gcal.CalendarNotConfigured) as exc:
                    notify_once(ctx, "gcal-auth", "Google Calendar needs you", str(exc))
                    out.append(f"{eid}: {exc}")
                    break
                except Exception as exc:  # noqa: BLE001 - offline etc.: retried on the next tick
                    log.warning("Software Factory calendar %s failed: %s", eid, exc)
                    out.append(f"{eid}: failed, will retry ({exc})")
                    continue
                state[eid] = marker
                out.append(f"{eid}: {result}")
            cutoff = (date - dt.timedelta(days=14)).isoformat()
            state = {k: v for k, v in state.items() if _eid_date(k) >= cutoff}
            update_runtime(ctx, lambda r: r.data.update(gcal_factory_events=state))
            return out or ["Software Factory calendar already up to date."]
    except LockBusy:
        return ["Software Factory calendar sync already running."]


def calendar_sync_safe(ctx) -> None:
    try:
        calendar_sync(ctx)
    except Exception:  # noqa: BLE001
        log.exception("Software Factory calendar sync failed")


# --------------------------------------------------------------------------- views

def status(ctx) -> Dict[str, Any]:
    history = fhistory(ctx.paths)
    date = today()
    f = _f(ctx.cfg)
    n, d = _planned(ctx, date)
    n2 = day_for(history, ctx.cfg, date + dt.timedelta(days=1), date)
    d2 = topic(n2, ctx.paths) if n2 else None
    s = history.get(date)
    return {
        "enabled": bool(f.get("enabled", True)),
        "date": date.isoformat(),
        "start_date": start_date(ctx.cfg).isoformat(),
        "streak": streaks(history, date),
        "published": len(history.recorded_dates()),
        "path_days": total_days(),
        "today_topic": {"day": n, "title": d["title"]} if d else None,
        "tomorrow_topic": {"day": n2, "title": d2["title"]} if d2 else None,
        "today": None if not s else {
            "day": s.get("day"), "title": s.get("title"), "published": bool(s.get("recorded")),
            "takes": len(_valid_takes(s)), "max_takes": int(f.get("max_takes", 3)),
            "final_take": s.get("final_take"), "video": s.get("video_path"),
            "prep": (s.get("kit") or {}).get("prep_html"), "deck": (s.get("kit") or {}).get("deck"),
            "youtube": s.get("youtube"), "carried_over": bool(s.get("carried_over")),
        },
        "brief_time": f.get("brief_time"), "prep_time": f.get("prep_time"),
        "publish_mode": f.get("publish_mode", "studio"),
    }


def history_rows(ctx, limit: int = 14) -> List[Dict[str, Any]]:
    history = fhistory(ctx.paths)
    rows = []
    for key in sorted(history.sessions, reverse=True)[:limit]:
        s = history.sessions[key]
        yt = s.get("youtube") or {}
        rows.append({"date": key, "day": s.get("day"), "title": s.get("title"),
                     "published": bool(s.get("recorded")), "takes": len(_valid_takes(s)),
                     "final_take": s.get("final_take"), "youtube": yt.get("url") or yt.get("status")})
    return rows


def plan_rows(ctx) -> List[Dict[str, Any]]:
    """Every curriculum day with its status and its actual or projected date."""
    history = fhistory(ctx.paths)
    date = today()
    published = {int(s["day"]): (k, s) for k, s in history.sessions.items() if s.get("recorded")}
    base_date = max(date, start_date(ctx.cfg))
    base_day = day_for(history, ctx.cfg, base_date, date) or 1
    rows = []
    for d in load_curriculum()["days"]:
        n = int(d["day"])
        if n in published:
            k, s = published[n]
            rows.append({"day": n, "date": k, "title": d["title"], "status": "published",
                         "url": (s.get("youtube") or {}).get("url")})
            continue
        when = base_date + dt.timedelta(days=n - base_day) if n >= base_day else None
        status = "today" if when == date else "planned"
        rows.append({"day": n, "date": when.isoformat() if when else "-", "title": d["title"], "status": status,
                     "url": None})
    return rows


def learning_path_markdown(ctx) -> str:
    return learning_path_doc(ctx.cfg).markdown()


def remove_generated_music(ctx) -> None:
    for kind in ("intro", "outro"):
        p = ctx.paths.factory / "music" / f".generated_{kind}.m4a"
        if p.exists():
            p.unlink()


def copy_music(ctx, src: Path, kind: str) -> Path:
    folder = ctx.paths.factory / "music"
    folder.mkdir(parents=True, exist_ok=True)
    for ext in MUSIC_EXTS:
        old = folder / f"{kind}{ext}"
        if old.exists():
            old.unlink()
    dest = folder / f"{kind}{src.suffix.lower()}"
    shutil.copyfile(src, dest)
    return dest
