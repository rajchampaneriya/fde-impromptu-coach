"""Pronunciation practice flows: daily build, recorded session (QuickTime audio
only), video assembly (ffmpeg) and private YouTube upload. The .m4a is always
kept; failures never break either streak."""
from __future__ import annotations

import datetime as dt
import logging
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from . import audio, gcal, macos, youtube
from .config import APP_NAME, Paths
from .pronounce import due_words, generate_content, update_after_session, word_state
from .pronounce_deck import build_deck, chapters, render_slide_pngs, session_seconds, slide_durations
from .state import History, LockBusy, file_lock, lock_is_held, now, streaks, today

log = logging.getLogger("fdecoach")

GCAL_PREFIX = "fdepron"  # event ids: a-v and 0-9 only


def pron_history(paths: Paths) -> History:
    return History(paths, file=paths.pron_state)


def _recordings_dir(ctx_paths: Paths, cfg: Dict[str, Any], create: bool = True) -> Path:
    folder = ctx_paths.recordings_dir(cfg, create=False) / "pronunciation"
    if create:
        folder.mkdir(parents=True, exist_ok=True)
    return folder


def reminder_title(date: dt.date) -> str:
    return f"Record pronunciation practice ({date.isoformat()})"


# --------------------------------------------------------------------------- daily build

def ensure_today(ctx, replace: bool = False) -> Tuple[Dict[str, Any], bool]:
    paths, cfg = ctx.paths, ctx.cfg
    date = today()
    with file_lock(paths, "generate", blocking=True):
        history = pron_history(paths)
        existing = history.get(date)
        if existing and existing.get("recorded") and replace:
            raise RuntimeError("Today's pronunciation session is already recorded; it can't be replaced.")
        if existing and not replace:
            if not Path(existing.get("deck_path", "")).exists():
                stats = streaks(history, date)
                pptx, ppsx = build_deck(existing, stats, cfg, paths.decks)
                _put(history, existing, pptx, ppsx)
            return existing, False
        if existing:
            history.remove(date)
        content, notes = generate_content(history, cfg, paths, date)
        session: Dict[str, Any] = {
            "date": date.isoformat(),
            "day_number": history.completed_before(date) + 1,
            "source": content.get("source", "bank"),
            "notes": notes,
            "created_at": now().isoformat(timespec="seconds"),
            "paragraph": content["paragraph"],
            "target_words": content["target_words"],
            "focus_sounds": content.get("focus_sounds", []),
            "words": [t["word"] for t in content["target_words"]],
            "recorded": False,
            "youtube": {"status": "none"},
        }
        stats = streaks(history, date)
        pptx, ppsx = build_deck(session, stats, cfg, paths.decks)
        with file_lock(paths, "history", blocking=True):
            _put(history, session, pptx, ppsx)
        log.info("Built pronunciation Day %s deck (source %s)", session["day_number"], session["source"])
        return session, True


def _put(history: History, session: Dict[str, Any], pptx: Path, ppsx: Path) -> None:
    session["deck_path"], session["show_path"] = str(pptx), str(ppsx)
    history.put(session)
    history.save()


def daily(ctx, from_prompt: bool = False) -> Dict[str, Any]:
    try:
        session, created = ensure_today(ctx)
    except Exception as exc:  # noqa: BLE001
        log.exception("Could not build today's pronunciation deck")
        macos.notify(APP_NAME, f"Couldn't build the pronunciation deck: {exc}. Run: fde-coach doctor")
        return {"ok": False, "error": str(exc)}
    date = today()
    history = pron_history(ctx.paths)
    stats = streaks(history, date)
    if session.get("recorded"):
        return {"ok": True, "already_recorded": True}
    if ctx.cfg.get("open_deck_when_ready", True):
        macos.powerpoint_open(Path(session["deck_path"]), ctx.cfg.get("presentation_app"))
    macos.notify("Pronunciation practice ready",
                 "Five minutes with the pen method keeps the streak alive.",
                 subtitle=f"Day {session['day_number']} · {stats['current']}-day streak")
    rem = ctx.cfg.get("reminders", {})
    if rem.get("use_reminders_app", True):
        title = reminder_title(date)
        macos.reminders_prune(rem.get("reminders_list", "FDE Practice"), "[pronunciation]", title)
        macos.reminders_create(rem.get("reminders_list", "FDE Practice"), title,
                               "[pronunciation] Run: fde-coach pronounce session", 7, 0)
    calendar_sync_safe(ctx)
    if not from_prompt and not lock_is_held(ctx.paths, "session"):
        answer = macos.dialog(
            f"Pronunciation practice, Day {session['day_number']} is ready.\n\n"
            "Audio only, about 5 minutes. Pen ready for Round 2.",
            APP_NAME, ["Later", "Start now"], "Start now", timeout_seconds=900)
        log.info("pronunciation prompt -> %s", answer or "error")
        if answer == "Start now":
            run_session(ctx)
    return {"ok": True, "created": created, "deck": session["deck_path"]}


# --------------------------------------------------------------------------- session

def _run_show(deck: Path, show: Path, cfg: Dict[str, Any], total: int, grace: int) -> float:
    app = cfg.get("presentation_app", "Microsoft PowerPoint")
    if not macos.powerpoint_start_show(deck, app):
        macos.open_path(show, app)
        time.sleep(4)
    t_show = time.time()
    if macos.dry_run():
        return t_show
    deadline = t_show + total + grace
    while time.time() < deadline:
        time.sleep(2)
        running = macos.powerpoint_show_running(app)
        if running is False and time.time() - t_show > 8:
            break
    macos.powerpoint_end_show(app)
    return t_show


def _record_once(session: Dict[str, Any], cfg: Dict[str, Any], paths: Paths) -> Dict[str, Any]:
    rec_cfg = cfg.get("pronunciation", {})
    folder = _recordings_dir(paths, cfg)
    dest = folder / f"{session['date']}_Pronunciation_Day{session.get('day_number', 0)}.m4a"
    deck = Path(session["deck_path"])
    show = Path(session.get("show_path") or deck)
    total = session_seconds(cfg)
    grace = int(cfg.get("recording", {}).get("stop_grace_seconds", 4))
    result: Dict[str, Any] = {"ok": False, "audio": None, "offset": None, "ended_early": False}

    t_rec = time.time()
    if not macos.quicktime_start_audio_recording(float(cfg.get("recording", {}).get("camera_warmup_seconds", 2))):
        result["error"] = "QuickTime audio recording did not start"
        return result
    t_show = _run_show(deck, show, cfg, total, grace)
    result["offset"] = round(t_show - t_rec, 1)
    saved, how = macos.quicktime_stop_audio_save(dest, since=t_rec)
    if not saved:
        result["error"] = "audio was not saved"
        return result
    result.update(audio=str(dest), method=how)
    duration = audio.audio_duration_seconds(dest)
    result["duration"] = duration
    min_secs = int(rec_cfg.get("min_audio_seconds", 180))
    if duration is not None and duration < min_secs:
        result["error"] = f"recording too short ({int(duration)} s < {min_secs} s)"
    else:
        result["ok"] = True
    return result


def run_session(ctx, force: bool = False, max_tries: int = 2) -> Dict[str, Any]:
    try:
        with file_lock(ctx.paths, "session"):
            return _run_session_locked(ctx, force, max_tries)
    except LockBusy:
        msg = "Another practice session is already running."
        log.info(msg)
        return {"ok": False, "error": msg}


def _run_session_locked(ctx, force: bool, max_tries: int) -> Dict[str, Any]:
    session, _ = ensure_today(ctx)
    date = dt.date.fromisoformat(session["date"])
    if session.get("recorded") and not force:
        macos.notify(APP_NAME, "Today's pronunciation practice is already recorded.")
        return {"ok": True, "already_recorded": True}
    result: Dict[str, Any] = {}
    for attempt in range(1, max_tries + 1):
        log.info("Pronunciation session attempt %d for %s", attempt, session["date"])
        result = _record_once(session, ctx.cfg, ctx.paths)
        log.info("pronunciation record() -> %s", result)
        if result.get("ok"):
            break
        if result.get("error") == "cancelled":
            return result
        buttons = ["Later", "Keep this audio", "Try again"] if result.get("audio") else ["Later", "Try again"]
        answer = macos.dialog(
            f"The pronunciation recording didn't finish cleanly: {result.get('error')}.\n\n"
            "Your streak is safe until midnight.", APP_NAME, buttons, "Try again",
            timeout_seconds=300, icon="caution")
        if answer == "Keep this audio" and result.get("audio"):
            result["ok"] = True
            break
        if answer != "Try again" or attempt == max_tries:
            return result
    mark_recorded(ctx, date, result)
    ask_words_feedback(ctx, date)
    if macos.dry_run():
        upload_pending(ctx)
    else:
        from .app import spawn_detached
        spawn_detached(["pronounce", "upload"])
    return result


def mark_recorded(ctx, date: dt.date, result: Dict[str, Any]) -> None:
    yt_enabled = bool(ctx.cfg.get("youtube", {}).get("enabled", True)) and bool(result.get("audio"))
    with file_lock(ctx.paths, "history", blocking=True):
        history = pron_history(ctx.paths)
        session = history.get(date)
        if session is None:
            raise RuntimeError(f"No pronunciation session for {date.isoformat()}")
        session.update(recorded=True, recorded_at=now().isoformat(timespec="seconds"),
                       audio_path=result.get("audio"), audio_duration=result.get("duration"),
                       chapter_offset=result.get("offset"), record_method=result.get("method", ""),
                       ended_early=bool(result.get("ended_early")))
        session["youtube"] = {"status": "pending" if yt_enabled else "disabled", "attempts": 0}
        history.put(session)
        history.save()
    rem = ctx.cfg.get("reminders", {})
    if rem.get("use_reminders_app", True):
        macos.reminders_complete(rem.get("reminders_list", "FDE Practice"), reminder_title(date))
    calendar_sync_safe(ctx)
    history = pron_history(ctx.paths)
    stats = streaks(history, date)
    day = (history.get(date) or {}).get("day_number", "?")
    best = " · new personal best!" if stats["current"] >= stats["best"] and stats["current"] > 1 else ""
    macos.notify(f"Pronunciation Day {day} done — "
                 f"{stats['current']}-day streak{best}",
                 "Audio saved. Assembling the video and uploading privately." if yt_enabled else "Audio saved.",
                 sound="Hero")
    log.info("Marked %s pronunciation recorded (%s); streak %s", date, result.get("audio"), stats["current"])


def ask_words_feedback(ctx, date: dt.date) -> None:
    """Multi-select: hard words come back tomorrow, easy ones space out."""
    history = pron_history(ctx.paths)
    session = history.get(date)
    if not session or not session.get("words"):
        return
    picked = macos.choose_from_list("Which words still felt hard? (unselected ones get easier)",
                                    "Pronunciation practice", session["words"])
    with file_lock(ctx.paths, "history", blocking=True):
        history = pron_history(ctx.paths)
        update_after_session(history, ctx.cfg, date, session["words"], picked)
        history.save()
    if picked:
        log.info("Hard words (back tomorrow): %s", ", ".join(picked))


# --------------------------------------------------------------------------- video + upload

def _audio_for_video(session: Dict[str, Any], cfg: Dict[str, Any]) -> Path:
    src = Path(session["audio_path"])
    preset = cfg.get("pronunciation", {}).get("audio_clean_preset", "light")
    cleaned = audio.clean(src, src.with_name(src.stem + "_clean.m4a"), preset)
    return Path(cleaned or src)


def assemble_video(session: Dict[str, Any], cfg: Dict[str, Any], paths: Paths) -> Optional[Path]:
    """Slides + cleaned audio -> MP4 exactly as long as the audio."""
    if macos.dry_run():
        out = _recordings_dir(paths, cfg) / f"{session['date']}_Pronunciation_Day{session['day_number']}.mp4"
        out.write_bytes(b"\0" * (2 * 1024 * 1024))
        log.info("[dry-run] pronunciation video -> %s", out)
        return out
    exe = audio.ffmpeg_path()
    if not exe:
        macos.notify(APP_NAME, "Pronunciation video skipped: ffmpeg not found",
                     "Install it with: brew install ffmpeg — the .m4a is kept.")
        return None
    audio_path = _audio_for_video(session, cfg)
    dur = audio.audio_duration_seconds(audio_path)
    if not dur:
        log.warning("Unknown audio duration; cannot sync the video")
        return None
    pngs = render_slide_pngs(session, cfg, paths.decks / f"{session['date']}_pron_frames")
    if not pngs:
        return None
    durs = slide_durations(cfg)
    offset = max(0.0, float(session.get("chapter_offset") or 0.0))
    first = durs[0] + offset
    rest = dur - offset - durs[0]
    closing = max(1.0, rest - sum(durs[1:]))
    times = [first] + list(durs[1:]) + [closing]
    lst = paths.decks / f"{session['date']}_pron_frames" / "concat.txt"
    with open(lst, "w", encoding="utf-8") as fh:
        for png, secs in zip(pngs, times):
            fh.write(f"file '{png}'\nduration {secs:.3f}\n")
        fh.write(f"file '{pngs[-1]}'\n")
    out = _recordings_dir(paths, cfg) / f"{session['date']}_Pronunciation_Day{session['day_number']}.mp4"
    cmd = [exe, "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-i", str(audio_path),
           "-vf", "format=yuv420p", "-c:v", "libx264", "-tune", "stillimage", "-r", "30",
           "-c:a", "aac", "-b:a", "192k", "-shortest", "-t", f"{dur:.3f}", str(out)]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
    if proc.returncode != 0 or not out.exists():
        log.warning("ffmpeg video assembly failed: %s", (proc.stderr or "")[-400:])
        macos.notify(APP_NAME, "Pronunciation video failed", "The .m4a is safe. Run: fde-coach doctor")
        return None
    log.info("Pronunciation video assembled: %s", out)
    return out


def build_metadata(session: Dict[str, Any], cfg: Dict[str, Any], marks: Optional[List[Tuple[int, str]]],
                   streak: int) -> Dict[str, Any]:
    yt = cfg.get("youtube", {})
    title = "Pronunciation · Day {day} · {date}".format(day=session.get("day_number", "?"),
                                                                 date=session["date"])
    lines = [
        "Daily pronunciation practice (pen method) — Forward Deployed Engineer.",
        f"Streak {streak} day{'s' if streak != 1 else ''} · {len(session.get('target_words', []))} target words",
        "",
    ]
    if marks:
        lines += [f"{m // 60}:{m % 60:02d} {label}" for m, label in marks]
        lines.append("")
    lines.append("Paragraph")
    lines.append(session.get("paragraph", ""))
    lines += ["", "Target words"]
    for t in session.get("target_words", []):
        lines.append(f"- {t['word']} ({t.get('stress') or t.get('respelling', '')}) — {t.get('tip', '')}")
    return {
        "snippet": {
            "title": youtube._clean(title, 100),
            "description": youtube._clean("\n".join(lines), 4900),
            "tags": ["pronunciation", "pen method", "forward deployed engineer"],
            "categoryId": str(yt.get("category_id", "27")),
        },
        "status": {"privacyStatus": yt.get("privacy_status", "private"), "selfDeclaredMadeForKids": False},
    }


def upload_pending(ctx, interactive: bool = False) -> List[str]:
    out: List[str] = []
    yt_cfg = ctx.cfg.get("youtube", {})
    if not yt_cfg.get("enabled", True):
        return ["YouTube upload is disabled in config."]
    try:
        with file_lock(ctx.paths, "upload"):
            history = pron_history(ctx.paths)
            pending = [s for k, s in sorted(history.sessions.items())
                       if s.get("recorded") and s.get("audio_path")
                       and (s.get("youtube") or {}).get("status") in ("pending", "failed")]
            if not pending:
                return ["Nothing to upload."]
            if not youtube.is_configured(ctx.paths) and not macos.dry_run():
                return ["Recording saved locally. Connect YouTube once: run `fde-coach youtube-auth`."]
            for s in pending:
                date = dt.date.fromisoformat(s["date"])
                video = assemble_video(s, ctx.cfg, ctx.paths)
                if video is None:
                    _set_yt(ctx, date, status="failed",
                            last_error="video assembly failed (ffmpeg missing or errored)")
                    out.append(f"{s['date']}: video not assembled; the .m4a is kept")
                    continue
                marks = None
                if s.get("chapter_offset") is not None and not s.get("ended_early"):
                    marks = chapters(s, ctx.cfg, float(s["chapter_offset"]))
                stats = streaks(pron_history(ctx.paths), date)
                meta = build_metadata(s, ctx.cfg, marks, stats["current"])
                try:
                    vid = youtube.upload(ctx.paths, video, meta)
                except Exception as exc:  # noqa: BLE001
                    log.warning("Pronunciation upload failed for %s: %s", s["date"], exc)
                    _set_yt(ctx, date, status="failed", last_error=str(exc)[:300])
                    out.append(f"{s['date']}: upload failed, will retry ({exc})")
                    continue
                url = f"https://youtu.be/{vid}"
                _set_yt(ctx, date, status="uploaded", video_id=vid, url=url)
                playlist = yt_cfg.get("pronunciation_playlist_id")
                if playlist and not macos.dry_run():
                    youtube.add_to_playlist(ctx.paths, vid, str(playlist))
                macos.notify("Pronunciation uploaded (private)", url)
                out.append(f"{s['date']}: uploaded privately -> {url}")
    except LockBusy:
        return ["An upload is already running."]
    return out


def _set_yt(ctx, date: dt.date, **fields: Any) -> None:
    with file_lock(ctx.paths, "history", blocking=True):
        history = pron_history(ctx.paths)
        session = history.get(date)
        if session is None:
            return
        yt = session.setdefault("youtube", {})
        if fields.get("status") == "failed":
            yt["attempts"] = int(yt.get("attempts", 0)) + 1
        yt.update(fields)
        history.put(session)
        history.save()


# --------------------------------------------------------------------------- calendar

def pron_event_summary() -> str:
    return "Pronunciation practice not recorded yet — 5 minutes with the pen"


def calendar_sync(ctx, clear: bool = False) -> List[str]:
    gc = ctx.cfg.get("google_calendar", {})
    enabled = bool(gc.get("enabled", True)) and not clear
    if not gcal.is_configured(ctx.paths) and not macos.dry_run():
        return ["Google Calendar not connected (run: fde-coach calendar-auth)."]
    try:
        with file_lock(ctx.paths, "calendar"):
            state: Dict[str, str] = dict(ctx.runtime().data.get("gcal_pron_events") or {})
            history, date, t = pron_history(ctx.paths), today(), now()
            want: Dict[str, str] = {}
            if enabled:
                for i in range(int(gc.get("days_ahead", 2)) + 1):
                    d = date + dt.timedelta(days=i)
                    s = history.get(d)
                    if s and s.get("recorded"):
                        want[d.isoformat()] = "deleted"
                    elif gcal.event_window(d, ctx.cfg)[0].replace(tzinfo=None) > t:
                        want[d.isoformat()] = "created"
            else:
                for iso, st in state.items():
                    if st == "created" and iso >= date.isoformat():
                        want[iso] = "deleted"
            out: List[str] = []
            cal = str(gc.get("calendar_id", "primary"))
            for iso in sorted(want):
                if state.get(iso) == want[iso]:
                    continue
                d = dt.date.fromisoformat(iso)
                eid = gcal.event_id(d, GCAL_PREFIX)
                try:
                    if want[iso] == "created":
                        start, end = gcal.event_window(d, ctx.cfg)
                        body = {
                            "id": eid, "summary": pron_event_summary(),
                            "description": ("You haven't recorded today's 5-minute pronunciation practice yet.\n\n"
                                            "On your Mac: fde-coach pronounce session\n\n"
                                            "Created by FDE Impromptu Coach."),
                            "start": {"dateTime": start.isoformat()}, "end": {"dateTime": end.isoformat()},
                            "reminders": {"useDefault": False, "overrides": gcal.alert_overrides(d, ctx.cfg)},
                            "colorId": str(gc.get("color_id", "11")), "transparency": "transparent",
                            "visibility": "private",
                            "extendedProperties": {"private": {"fdepron": iso}},
                        }
                        result = gcal.ensure_event(ctx.paths, cal, body)
                    else:
                        result = gcal.delete_event(ctx.paths, cal, eid)
                except Exception as exc:  # noqa: BLE001
                    log.warning("Pronunciation calendar %s for %s failed: %s", want[iso], iso, exc)
                    out.append(f"{iso}: failed, will retry ({exc})")
                    continue
                state[iso] = want[iso]
                out.append(f"{iso}: pronunciation alert {result}")
            cutoff = (date - dt.timedelta(days=14)).isoformat()
            state = {k: v for k, v in state.items() if k >= cutoff}
            from .app import update_runtime
            update_runtime(ctx, lambda r: r.data.update(gcal_pron_events=state))
            return out or ["Pronunciation calendar already up to date."]
    except LockBusy:
        return ["Pronunciation calendar sync already running."]


def calendar_sync_safe(ctx) -> None:
    try:
        calendar_sync(ctx)
    except Exception:  # noqa: BLE001
        log.exception("Pronunciation calendar sync failed")


# --------------------------------------------------------------------------- views

def status(ctx) -> Dict[str, Any]:
    history = pron_history(ctx.paths)
    date = today()
    stats = streaks(history, date)
    s = history.get(date)
    return {
        "streak": stats,
        "today": None if not s else {
            "day_number": s.get("day_number"), "recorded": bool(s.get("recorded")),
            "source": s.get("source"), "deck": s.get("deck_path"), "audio": s.get("audio_path"),
            "youtube": s.get("youtube"), "words": s.get("words"),
        },
        "pending_uploads": [x["date"] for x in history.pending_uploads()],
        "due_words": due_words(history, ctx.cfg, date),
        "all_words": sorted(word_state(history)),
    }


def history_rows(ctx, limit: int = 14) -> List[Dict[str, Any]]:
    history = pron_history(ctx.paths)
    rows = []
    for key in sorted(history.sessions, reverse=True)[:limit]:
        s = history.sessions[key]
        yt = s.get("youtube") or {}
        rows.append({
            "date": key, "day": s.get("day_number"), "recorded": bool(s.get("recorded")),
            "youtube": yt.get("url") or yt.get("status"),
            "words": s.get("words", []),
            "paragraph": (s.get("paragraph", "")[:120] + "…") if len(s.get("paragraph", "")) > 120
                         else s.get("paragraph", ""),
        })
    return rows
