"""Shared engine for the practices that run a timed deck while they record:
pronunciation (pen method) and legato (connected speech), both audio only and
daily, and Weekend Stage (a TED talk a weekend), on camera and weekly.

Each practice is described by a `Practice` spec (state file, file names,
calendar prefix, and hooks for content, deck, video frames, chapters and
metadata). The flows here are the same for all of them: scheduled build,
recorded session, private YouTube upload, missed-practice calendar alerts,
status and history. An audio practice's .m4a becomes a slides+voice video; a
video practice (media "video") uploads its camera recording as it is. A weekly
practice (cadence "weekly") files each session under its weekend's Saturday.
The recording is always kept and a failure in any step never breaks a streak.

Lock order (as in app.py): session -> generate -> history; upload -> history.
"""
from __future__ import annotations

import datetime as dt
import importlib
import logging
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from . import audio, gcal, macos, youtube
from .config import APP_NAME, Paths
from .state import History, LockBusy, file_lock, lock_is_held, now, period_start, streaks, today

log = logging.getLogger("fdecoach")


@dataclass(frozen=True)
class Practice:
    key: str                 # config section and recordings subfolder ("pronunciation")
    title: str               # "Pronunciation"
    cli: str                 # CLI group ("pronounce")
    state_attr: str          # Paths attribute holding the state file
    file_stem: str           # deck / audio / video file names
    gcal_prefix: str         # calendar event ids: a-v and 0-9 only
    gcal_runtime_key: str    # runtime.json bookkeeping key
    reminder_tag: str        # tag in the Apple Reminders note
    event_summary: str       # calendar event title
    ready_body: str          # notification body when the deck is ready
    prompt_body: str         # dialog text under "<Title> practice, Day N is ready."
    generate: Callable[..., Tuple[Dict[str, Any], List[str]]]
    session_fields: Callable[[Dict[str, Any]], Dict[str, Any]]
    build_deck: Callable[..., Tuple[Path, Path]]
    render_pngs: Callable[..., List[Path]]
    durations: Callable[[Dict[str, Any]], List[int]]
    chapters: Callable[..., List[Tuple[int, str]]]
    metadata: Callable[..., Dict[str, Any]]
    feedback: Optional[Callable[[Any, dt.date], None]] = None
    describe: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None
    next_key: str = ""                       # practice offered after this one ("legato")
    media: str = "audio"                     # "video": the camera records (recorder.py), uploaded as it is
    cadence: str = "daily"                   # "weekly": one session per weekend, a streak in weeks
    timeline: Optional[Callable[[Dict[str, Any], Dict[str, Any]], List[int]]] = None  # per-session slide seconds
    on_ready: Optional[Callable[[Any, Dict[str, Any]], None]] = None  # scheduled run, before the start prompt
    extra: Dict[str, Any] = field(default_factory=dict)


_MODULES = {"pronunciation": "pronounce_session", "legato": "legato_session", "stage": "stage_session"}


def spec_for(key: str) -> Practice:
    """The Practice spec registered by its module (imported lazily)."""
    module = importlib.import_module(f"{__package__}.{_MODULES[key]}")
    return module.SPEC


def all_specs() -> List[Practice]:
    return [spec_for(k) for k in _MODULES]


def section(cfg: Dict[str, Any], spec: Practice) -> Dict[str, Any]:
    return cfg.get(spec.key, {})


def enabled(cfg: Dict[str, Any], spec: Practice) -> bool:
    return bool(section(cfg, spec).get("enabled", True))


def history(paths: Paths, spec: Practice) -> History:
    return History(paths, file=getattr(paths, spec.state_attr), cadence=spec.cadence)


def period(spec: Practice, date: Optional[dt.date] = None) -> dt.date:
    """The date this practice files a session under: today, or this weekend's Saturday."""
    return period_start(date or today(), spec.cadence)


def unit(spec: Practice) -> str:
    return "Week" if spec.cadence == "weekly" else "Day"


def media_path(session: Dict[str, Any]) -> Optional[str]:
    return session.get("audio_path") or session.get("video_path")


def recordings_dir(paths: Paths, cfg: Dict[str, Any], spec: Practice, create: bool = True) -> Path:
    folder = paths.recordings_dir(cfg, create=False) / spec.key
    if create:
        folder.mkdir(parents=True, exist_ok=True)
    return folder


def reminder_title(spec: Practice, date: dt.date) -> str:
    return f"Record {spec.title.lower()} practice ({date.isoformat()})"


def session_seconds(cfg: Dict[str, Any], spec: Practice, session: Optional[Dict[str, Any]] = None) -> int:
    if session is not None and spec.timeline:
        return sum(spec.timeline(session, cfg))
    return sum(spec.durations(cfg))


def pending_uploads(hist: History) -> List[Dict[str, Any]]:
    """Audio practices keep audio_path and video practices video_path; History.pending_uploads
    only ever saw the FDE video, so this is the version that knows both."""
    return [s for _, s in sorted(hist.sessions.items())
            if s.get("recorded") and media_path(s)
            and (s.get("youtube") or {}).get("status") in ("pending", "failed")]


# --------------------------------------------------------------------------- passage feedback

# The after-session list ("Anything about today's passage?") and `passage --flag` both store
# session["passage_feedback"]; library.choose reads it from either practice's state file.
PASSAGE_CHOICES = {"Too easy": "too_easy", "Too hard": "too_hard", "Read it recently": "repeated",
                   "Not useful": "unhelpful"}
FLAG_VALUES = {"too-easy": "too_easy", "too-hard": "too_hard", "repeated": "repeated", "unhelpful": "unhelpful"}


def ask_passage_feedback(cfg: Dict[str, Any]) -> bool:
    return bool((cfg.get("passages") or {}).get("ask_feedback", True))


def flag_passage(ctx, spec: Practice, date: dt.date, labels: Sequence[str]) -> Dict[str, Any]:
    """Add passage feedback labels to the session on `date` (kept on top of earlier ones)."""
    labels = [label for label in labels if label in PASSAGE_CHOICES.values()]
    with file_lock(ctx.paths, "history", blocking=True):
        hist = history(ctx.paths, spec)
        session = hist.get(date)
        if session is None:
            raise RuntimeError(f"no {spec.title.lower()} session on {date.isoformat()}")
        if not session.get("passage_id"):
            raise RuntimeError(f"the {spec.title.lower()} session on {date.isoformat()} has no library passage")
        if labels:
            session["passage_feedback"] = sorted(set(session.get("passage_feedback") or []) | set(labels))
            hist.put(session)
            hist.save()
    if labels:
        log.info("%s passage %s flagged: %s", spec.title, session["passage_id"], ", ".join(labels))
    return session


# --------------------------------------------------------------------------- daily build

def ensure_today(ctx, spec: Practice, replace: bool = False, **options: Any) -> Tuple[Dict[str, Any], bool]:
    paths, cfg = ctx.paths, ctx.cfg
    date = period(spec)
    with file_lock(paths, "generate", blocking=True):
        hist = history(paths, spec)
        existing = hist.get(date)
        if existing and existing.get("recorded") and replace:
            when = "This week's" if spec.cadence == "weekly" else "Today's"
            raise RuntimeError(f"{when} {spec.title.lower()} session is already recorded; it can't be replaced.")
        if existing and not replace:
            if not Path(existing.get("deck_path", "")).exists():
                pptx, ppsx = spec.build_deck(existing, streaks(hist, date), cfg, paths.decks)
                _put(hist, existing, pptx, ppsx)
            return existing, False
        replaced: List[str] = []
        if existing:
            # A replaced passage counts as served today and must not come straight back.
            replaced = list(existing.get("replaced") or [])
            if existing.get("passage_id") and existing["passage_id"] not in replaced:
                replaced.append(existing["passage_id"])
            hist.remove(date)
            if replaced and not options.get("passage_id"):
                options = dict(options, exclude=tuple(replaced), attempt=len(replaced))
        content, notes = spec.generate(hist, cfg, paths, date, **options)
        session: Dict[str, Any] = {
            "date": date.isoformat(),
            "day_number": hist.completed_before(date) + 1,
            "source": content.get("source", "library"),
            "notes": notes,
            "created_at": now().isoformat(timespec="seconds"),
            "recorded": False,
            "youtube": {"status": "none"},
        }
        session.update(spec.session_fields(content))
        if replaced:
            session["replaced"] = replaced
        pptx, ppsx = spec.build_deck(session, streaks(hist, date), cfg, paths.decks)
        with file_lock(paths, "history", blocking=True):
            _put(hist, session, pptx, ppsx)
        log.info("Built %s %s %s deck (source %s)", spec.title, unit(spec), session["day_number"], session["source"])
        return session, True


def _put(hist: History, session: Dict[str, Any], pptx: Path, ppsx: Path) -> None:
    session["deck_path"], session["show_path"] = str(pptx), str(ppsx)
    hist.put(session)
    hist.save()


def daily(ctx, spec: Practice, from_prompt: bool = False) -> Dict[str, Any]:
    if not enabled(ctx.cfg, spec):
        return {"ok": True, "disabled": True}
    try:
        session, created = ensure_today(ctx, spec)
    except Exception as exc:  # noqa: BLE001 - must never die silently
        log.exception("Could not build today's %s deck", spec.title.lower())
        macos.notify(APP_NAME, f"Couldn't build the {spec.title.lower()} deck: {exc}. Run: fde-coach doctor")
        return {"ok": False, "error": str(exc)}
    date = period(spec)
    stats = streaks(history(ctx.paths, spec), today())
    if session.get("recorded"):
        return {"ok": True, "already_recorded": True}
    if ctx.cfg.get("open_deck_when_ready", True):
        macos.powerpoint_open(Path(session["deck_path"]), ctx.cfg.get("presentation_app"))
    if spec.on_ready:
        try:
            spec.on_ready(ctx, session)
        except Exception:  # noqa: BLE001 - a prep page must never stop the practice
            log.exception("%s on_ready failed", spec.key)
    u = unit(spec)
    macos.notify(f"{spec.title} practice ready", spec.ready_body,
                 subtitle=f"{u} {session['day_number']} · {stats['current']}-{u.lower()} streak")
    rem = ctx.cfg.get("reminders", {})
    if rem.get("use_reminders_app", True):
        title = reminder_title(spec, date)
        macos.reminders_prune(rem.get("reminders_list", "FDE Practice"), spec.reminder_tag, title)
        # a weekend practice starts with ~25 minutes of study: its reminder falls due in the evening
        due_h, due_m = (18, 0) if spec.cadence == "weekly" else (7, 0)
        macos.reminders_create(rem.get("reminders_list", "FDE Practice"), title,
                               f"{spec.reminder_tag} Run: fde-coach {spec.cli} session", due_h, due_m)
    calendar_sync_safe(ctx, spec)
    if not from_prompt and not lock_is_held(ctx.paths, "session"):
        answer = macos.dialog(
            f"{spec.title} practice, {u} {session['day_number']} is ready.\n\n{spec.prompt_body}",
            APP_NAME, ["Later", "Start now"], "Start now", timeout_seconds=900)
        log.info("%s prompt -> %s", spec.key, answer or "error")
        if answer == "Start now":
            run_session(ctx, spec)
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
    if "keynote" in app.lower():
        macos.keynote_close_documents()
    return t_show


def _audio_device(cfg: Dict[str, Any], spec: Practice) -> str:
    """Each practice may name its own input; empty falls back to pronunciation's."""
    return str(section(cfg, spec).get("audio_device") or cfg.get("pronunciation", {}).get("audio_device", ""))


def _record_video(session: Dict[str, Any], cfg: Dict[str, Any], paths: Paths, spec: Practice) -> Dict[str, Any]:
    """Camera + microphone through QuickTime while the deck plays (the impromptu recorder,
    pointed at this practice's folder, length and minimum)."""
    from . import recorder
    sec = section(cfg, spec)
    dest = (recordings_dir(paths, cfg, spec)
            / f"{session['date']}_{spec.file_stem}_{unit(spec)}{session.get('day_number', 0)}.mov")
    min_secs = int(sec.get("min_video_seconds", cfg.get("recording", {}).get("min_video_seconds", 150)))
    return recorder.record(session, cfg, paths, total=session_seconds(cfg, spec, session), dest=dest,
                           min_secs=min_secs)


def _record_once(session: Dict[str, Any], cfg: Dict[str, Any], paths: Paths, spec: Practice) -> Dict[str, Any]:
    if spec.media == "video":
        return _record_video(session, cfg, paths, spec)
    sec = section(cfg, spec)
    folder = recordings_dir(paths, cfg, spec)
    dest = folder / f"{session['date']}_{spec.file_stem}_Day{session.get('day_number', 0)}.m4a"
    deck = Path(session["deck_path"])
    show = Path(session.get("show_path") or deck)
    total = session_seconds(cfg, spec)
    grace = int(cfg.get("recording", {}).get("stop_grace_seconds", 4))
    result: Dict[str, Any] = {"ok": False, "audio": None, "offset": None, "ended_early": False}
    min_secs = int(sec.get("min_audio_seconds", 180))

    # Preferred: capture straight from the AVFoundation input. QuickTime's own
    # input selection goes stale when devices are reconnected and records silence.
    cap = audio.AudioCapture(dest, _audio_device(cfg, spec))
    if cap.start():
        t_rec = time.time()
        t_show = _run_show(deck, show, cfg, total, grace)
        result["offset"] = round(t_show - t_rec, 1)
        out = cap.stop()
        if out is None:
            result["error"] = "audio was not saved"
            return result
        result.update(audio=str(out), method="ffmpeg")
    else:
        # Fallback: QuickTime audio recording (needs its own microphone permission)
        t_rec = time.time()
        if not macos.quicktime_start_audio_recording(float(cfg.get("recording", {}).get("camera_warmup_seconds", 2))):
            result["error"] = "audio capture did not start (ffmpeg AVFoundation failed and QuickTime fallback failed)"
            return result
        t_show = _run_show(deck, show, cfg, total, grace)
        result["offset"] = round(t_show - t_rec, 1)
        saved, how = macos.quicktime_stop_audio_save(dest, since=t_rec)
        macos.quit_app("QuickTime Player")
        if not saved:
            result["error"] = "audio was not saved"
            return result
        result.update(audio=str(dest), method=f"quicktime:{how}")
    duration = audio.audio_duration_seconds(Path(result["audio"]))
    result["duration"] = duration
    if duration is not None and duration < min_secs:
        result["error"] = f"recording too short ({int(duration)} s < {min_secs} s)"
    else:
        result["ok"] = True
    return result


def run_session(ctx, spec: Practice, force: bool = False, max_tries: int = 2,
                offer_next: bool = True) -> Dict[str, Any]:
    try:
        with file_lock(ctx.paths, "session"):
            result = _run_session_locked(ctx, spec, force, max_tries)
    except LockBusy:
        msg = "Another practice session is already running."
        log.info(msg)
        return {"ok": False, "error": msg}
    # Offer the next practice only after the session lock is released, so the
    # follow-up session can take it (it used to be checked while still held).
    if offer_next and result.get("ok") and not result.get("already_recorded") and spec.next_key:
        offer(ctx, spec_for(spec.next_key), after=spec.title)
    return result


def _run_session_locked(ctx, spec: Practice, force: bool, max_tries: int) -> Dict[str, Any]:
    session, _ = ensure_today(ctx, spec)
    date = dt.date.fromisoformat(session["date"])
    if session.get("recorded") and not force:
        macos.notify(APP_NAME, f"Today's {spec.title.lower()} practice is already recorded.")
        return {"ok": True, "already_recorded": True}
    result: Dict[str, Any] = {}
    for attempt in range(1, max_tries + 1):
        log.info("%s session attempt %d for %s", spec.title, attempt, session["date"])
        result = _record_once(session, ctx.cfg, ctx.paths, spec)
        log.info("%s record() -> %s", spec.key, result)
        if result.get("ok"):
            break
        if result.get("error") == "cancelled":
            return result
        kept = result.get("audio") or result.get("video")
        keep = "Keep this video" if spec.media == "video" else "Keep this audio"
        buttons = ["Later", keep, "Try again"] if kept else ["Later", "Try again"]
        safe = "Your streak is safe until Sunday night." if spec.cadence == "weekly" else \
            "Your streak is safe until midnight."
        answer = macos.dialog(
            f"The {spec.title.lower()} recording didn't finish cleanly: {result.get('error')}.\n\n{safe}",
            APP_NAME, buttons, "Try again", timeout_seconds=300, icon="caution")
        if answer == keep and kept:
            result["ok"] = True
            break
        if answer != "Try again" or attempt == max_tries:
            return result
    mark_recorded(ctx, spec, date, result)
    if spec.feedback:
        try:
            spec.feedback(ctx, date)
        except Exception:  # noqa: BLE001 - feedback must never lose the recording
            log.exception("%s feedback failed", spec.key)
    if macos.dry_run():
        upload_pending(ctx, spec)
    else:
        from .app import spawn_detached
        spawn_detached([spec.cli, "upload"])
    return result


def offer(ctx, spec: Practice, after: str) -> None:
    """One 'next practice?' prompt; runs it in this process when accepted."""
    flag = {"pronunciation": "prompt_after_fde", "legato": "prompt_after_pronunciation"}.get(spec.key, "")
    if not enabled(ctx.cfg, spec) or (flag and not section(ctx.cfg, spec).get(flag, True)):
        return
    try:
        s = history(ctx.paths, spec).get(period(spec))
        if s and s.get("recorded"):
            return
    except Exception:  # noqa: BLE001 - never disturb the finished practice
        return
    mins = max(1, round(session_seconds(ctx.cfg, spec) / 60))
    kind = "on camera" if spec.media == "video" else "audio only"
    answer = macos.dialog(f"{after} practice saved. {spec.title} practice next? ({mins} min, {kind})",
                          APP_NAME, ["Later", "Start now"], "Start now", timeout_seconds=300)
    log.info("offer %s -> %s", spec.key, answer or "error")
    if answer == "Start now":
        run_session(ctx, spec)


def mark_recorded(ctx, spec: Practice, date: dt.date, result: Dict[str, Any]) -> None:
    media = result.get("video") if spec.media == "video" else result.get("audio")
    yt_enabled = bool(ctx.cfg.get("youtube", {}).get("enabled", True)) and bool(media)
    with file_lock(ctx.paths, "history", blocking=True):
        hist = history(ctx.paths, spec)
        session = hist.get(date)
        if session is None:
            raise RuntimeError(f"No {spec.title.lower()} session for {date.isoformat()}")
        if spec.media == "video":
            session.update(video_path=media, video_duration=result.get("duration"))
        else:
            session.update(audio_path=media, audio_duration=result.get("duration"))
        session.update(recorded=True, recorded_at=now().isoformat(timespec="seconds"),
                       chapter_offset=result.get("offset"), record_method=result.get("method", ""),
                       ended_early=bool(result.get("ended_early")))
        session["youtube"] = {"status": "pending" if yt_enabled else "disabled", "attempts": 0}
        hist.put(session)
        hist.save()
    rem = ctx.cfg.get("reminders", {})
    if rem.get("use_reminders_app", True):
        macos.reminders_complete(rem.get("reminders_list", "FDE Practice"), reminder_title(spec, date))
    calendar_sync_safe(ctx, spec)
    hist = history(ctx.paths, spec)
    stats = streaks(hist, date)
    day = (hist.get(date) or {}).get("day_number", "?")
    u = unit(spec)
    best = " · new personal best!" if stats["current"] >= stats["best"] and stats["current"] > 1 else ""
    if spec.media == "video":
        body = "Video saved. Uploading privately." if yt_enabled else "Video saved."
    else:
        body = "Audio saved. Assembling the video and uploading privately." if yt_enabled else "Audio saved."
    macos.notify(f"{spec.title} {u} {day} done — {stats['current']}-{u.lower()} streak{best}", body, sound="Hero")
    log.info("Marked %s %s recorded (%s); streak %s", date, spec.key, media, stats["current"])


# --------------------------------------------------------------------------- video + upload

def _audio_for_video(session: Dict[str, Any], cfg: Dict[str, Any], spec: Practice) -> Path:
    src = Path(session["audio_path"])
    preset = section(cfg, spec).get("audio_clean_preset", "light")
    cleaned = audio.clean(src, src.with_name(src.stem + "_clean.m4a"), preset)
    return Path(cleaned or src)


def assemble_video(session: Dict[str, Any], cfg: Dict[str, Any], paths: Paths, spec: Practice) -> Optional[Path]:
    """Slides + cleaned audio -> MP4 exactly as long as the audio."""
    out = recordings_dir(paths, cfg, spec) / f"{session['date']}_{spec.file_stem}_Day{session['day_number']}.mp4"
    if macos.dry_run():
        out.write_bytes(b"\0" * (2 * 1024 * 1024))
        log.info("[dry-run] %s video -> %s", spec.key, out)
        return out
    exe = audio.ffmpeg_path()
    if not exe:
        macos.notify(APP_NAME, f"{spec.title} video skipped: ffmpeg not found",
                     "Install it with: brew install ffmpeg — the .m4a is kept.")
        return None
    audio_path = _audio_for_video(session, cfg, spec)
    dur = audio.audio_duration_seconds(audio_path)
    if not dur:
        log.warning("Unknown audio duration; cannot sync the video")
        return None
    frames = paths.decks / f"{session['date']}_{spec.file_stem.lower()}_frames"
    pngs = spec.render_pngs(session, cfg, frames)
    if not pngs:
        return None
    durs = spec.durations(cfg)
    offset = max(0.0, float(session.get("chapter_offset") or 0.0))
    rest = dur - offset - durs[0]
    closing = max(1.0, rest - sum(durs[1:]))
    times = [durs[0] + offset] + list(durs[1:]) + [closing]
    lst = frames / "concat.txt"
    with open(lst, "w", encoding="utf-8") as fh:
        for png, secs in zip(pngs, times):
            fh.write(f"file '{png}'\nduration {secs:.3f}\n")
        fh.write(f"file '{pngs[-1]}'\n")
    cmd = [exe, "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-i", str(audio_path),
           "-vf", "format=yuv420p", "-c:v", "libx264", "-tune", "stillimage", "-r", "30",
           "-c:a", "aac", "-b:a", "192k", "-t", f"{dur:.3f}", str(out)]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
    if proc.returncode != 0 or not out.exists():
        log.warning("ffmpeg video assembly failed: %s", (proc.stderr or "")[-400:])
        macos.notify(APP_NAME, f"{spec.title} video failed", "The .m4a is safe. Run: fde-coach doctor")
        return None
    log.info("%s video assembled: %s", spec.title, out)
    return out


def upload_pending(ctx, spec: Practice, interactive: bool = False) -> List[str]:
    out: List[str] = []
    yt_cfg = ctx.cfg.get("youtube", {})
    if not yt_cfg.get("enabled", True):
        return ["YouTube upload is disabled in config."]
    max_attempts = int(yt_cfg.get("max_attempts", 12))
    try:
        with file_lock(ctx.paths, "upload"):
            pending = pending_uploads(history(ctx.paths, spec))
            if not pending:
                return ["Nothing to upload."]
            if not youtube.is_configured(ctx.paths) and not macos.dry_run():
                return ["Recording saved locally. Connect YouTube once: run `fde-coach youtube-auth`."]
            for s in pending:
                date = dt.date.fromisoformat(s["date"])
                if int((s.get("youtube") or {}).get("attempts", 0)) >= max_attempts and not interactive:
                    continue
                if spec.media == "video":
                    # the camera recording goes up as it is: nothing else is mixed into it
                    video = Path(s["video_path"]) if Path(s["video_path"]).exists() else None
                    if video is None:
                        _set_yt(ctx, spec, date, status="failed", last_error="recording not found")
                        out.append(f"{s['date']}: recording not found at {s['video_path']}")
                        continue
                else:
                    video = assemble_video(s, ctx.cfg, ctx.paths, spec)
                if video is None:
                    _set_yt(ctx, spec, date, status="failed",
                            last_error="video assembly failed (ffmpeg missing or errored)")
                    out.append(f"{s['date']}: video not assembled; the .m4a is kept")
                    continue
                marks = None
                if s.get("chapter_offset") is not None and not s.get("ended_early"):
                    marks = spec.chapters(s, ctx.cfg, float(s["chapter_offset"]))
                stats = streaks(history(ctx.paths, spec), date)
                meta = spec.metadata(s, ctx.cfg, marks, stats["current"])
                try:
                    vid = youtube.upload(ctx.paths, video, meta)
                except (youtube.YouTubeAuthExpired, youtube.YouTubeNotConfigured) as exc:
                    out.append(f"{s['date']}: {exc}")
                    break
                except Exception as exc:  # noqa: BLE001
                    log.warning("%s upload failed for %s: %s", spec.title, s["date"], exc)
                    _set_yt(ctx, spec, date, status="failed", last_error=str(exc)[:300])
                    out.append(f"{s['date']}: upload failed, will retry ({exc})")
                    continue
                url = f"https://youtu.be/{vid}"
                _set_yt(ctx, spec, date, status="uploaded", video_id=vid, url=url)
                playlist = yt_cfg.get(f"{spec.key}_playlist_id")
                if playlist and not macos.dry_run():
                    youtube.add_to_playlist(ctx.paths, vid, str(playlist))
                macos.notify(f"{spec.title} uploaded (private)", url)
                out.append(f"{s['date']}: uploaded privately -> {url}")
    except LockBusy:
        return ["An upload is already running."]
    return out


def _set_yt(ctx, spec: Practice, date: dt.date, **fields: Any) -> None:
    with file_lock(ctx.paths, "history", blocking=True):
        hist = history(ctx.paths, spec)
        session = hist.get(date)
        if session is None:
            return
        yt = session.setdefault("youtube", {})
        if fields.get("status") == "failed":
            yt["attempts"] = int(yt.get("attempts", 0)) + 1
        yt.update(fields)
        hist.put(session)
        hist.save()


def passage_credit(passage: Optional[Dict[str, Any]]) -> str:
    """'Author, Work (Year), Section. Translated by X. Source: Name — URL'."""
    if not passage:
        return ""
    head = f"{passage.get('author', '')}, {passage.get('work', '')}"
    if passage.get("year"):
        head += f" ({passage['year']})"
    if passage.get("section"):
        head += f", {passage['section']}"
    if passage.get("translator"):
        head += f". Translated by {passage['translator']}"
    src = passage.get("source") or {}
    if src.get("name") or src.get("url"):
        head += f". Source: {src.get('name', '')} — {src.get('url', '')}".rstrip(" —")
    return head + "."


# --------------------------------------------------------------------------- calendar

def _alert_day(spec: Practice, key: dt.date) -> dt.date:
    """The day the missed-practice alert sits on: the session's own day, or for a weekly
    practice the Sunday of its weekend (the last chance to record it)."""
    return key + dt.timedelta(days=1) if spec.cadence == "weekly" else key


def calendar_sync(ctx, spec: Practice, clear: bool = False) -> List[str]:
    gc = ctx.cfg.get("google_calendar", {})
    on = bool(gc.get("enabled", True)) and enabled(ctx.cfg, spec) and not clear
    if not gcal.is_configured(ctx.paths) and not macos.dry_run():
        return ["Google Calendar not connected (run: fde-coach calendar-auth)."]
    try:
        with file_lock(ctx.paths, "calendar"):
            state: Dict[str, str] = dict(ctx.runtime().data.get(spec.gcal_runtime_key) or {})
            hist, date, t = history(ctx.paths, spec), today(), now()
            want: Dict[str, str] = {}
            if on:
                for i in range(int(gc.get("days_ahead", 2)) + 1):
                    d = period(spec, date + dt.timedelta(days=i))
                    if d.isoformat() in want:
                        continue
                    s = hist.get(d)
                    if s and s.get("recorded"):
                        want[d.isoformat()] = "deleted"
                    elif gcal.event_window(_alert_day(spec, d), ctx.cfg)[0].replace(tzinfo=None) > t:
                        want[d.isoformat()] = "created"
            else:
                for iso, st in state.items():
                    if st == "created" and iso >= period(spec, date).isoformat():
                        want[iso] = "deleted"
            out: List[str] = []
            cal = str(gc.get("calendar_id", "primary"))
            for iso in sorted(want):
                if state.get(iso) == want[iso]:
                    continue
                d = dt.date.fromisoformat(iso)
                eid = gcal.event_id(d, spec.gcal_prefix)
                try:
                    if want[iso] == "created":
                        day = _alert_day(spec, d)
                        start, end = gcal.event_window(day, ctx.cfg)
                        when = "this weekend's" if spec.cadence == "weekly" else "today's"
                        body = {
                            "id": eid, "summary": spec.event_summary,
                            "description": (f"You haven't recorded {when} {spec.title.lower()} practice yet.\n\n"
                                            f"On your Mac: fde-coach {spec.cli} session\n\n"
                                            "Created by FDE Impromptu Coach."),
                            "start": {"dateTime": start.isoformat()}, "end": {"dateTime": end.isoformat()},
                            "reminders": {"useDefault": False, "overrides": gcal.alert_overrides(day, ctx.cfg)},
                            "colorId": str(gc.get("color_id", "11")), "transparency": "transparent",
                            "visibility": "private",
                            "extendedProperties": {"private": {spec.gcal_prefix: iso}},
                        }
                        result = gcal.ensure_event(ctx.paths, cal, body)
                    else:
                        result = gcal.delete_event(ctx.paths, cal, eid)
                except (gcal.CalendarAuthExpired, gcal.CalendarNotConfigured) as exc:
                    out.append(f"{iso}: {exc}")
                    break
                except Exception as exc:  # noqa: BLE001 - offline etc.: retried on the next tick
                    log.warning("%s calendar %s for %s failed: %s", spec.title, want[iso], iso, exc)
                    out.append(f"{iso}: failed, will retry ({exc})")
                    continue
                state[iso] = want[iso]
                out.append(f"{iso}: {spec.key} alert {result}")
            cutoff = (date - dt.timedelta(days=14)).isoformat()
            state = {k: v for k, v in state.items() if k >= cutoff}
            from .app import update_runtime
            update_runtime(ctx, lambda r: r.data.update({spec.gcal_runtime_key: state}))
            return out or [f"{spec.title} calendar already up to date."]
    except LockBusy:
        return [f"{spec.title} calendar sync already running."]


def calendar_sync_safe(ctx, spec: Practice) -> None:
    try:
        calendar_sync(ctx, spec)
    except Exception:  # noqa: BLE001
        log.exception("%s calendar sync failed", spec.title)


def tick(ctx) -> None:
    """Called by the 15-minute reminder agent: keeps every practice's calendar
    alerts rolling forward and retries failed uploads. No prompts."""
    for spec in all_specs():
        calendar_sync_safe(ctx, spec)
        try:
            if pending_uploads(history(ctx.paths, spec)):
                upload_pending(ctx, spec)
        except Exception:  # noqa: BLE001 - never break the reminder tick
            log.exception("%s upload retry failed", spec.title)


# --------------------------------------------------------------------------- views

def status(ctx, spec: Practice) -> Dict[str, Any]:
    """`today` is this period's session: today's, or this weekend's for a weekly practice."""
    hist = history(ctx.paths, spec)
    date = today()
    s = hist.get(period(spec, date))
    today_info = None
    if s:
        today_info = {"day_number": s.get("day_number"), "recorded": bool(s.get("recorded")),
                      "source": s.get("source"), "deck": s.get("deck_path"), "audio": s.get("audio_path"),
                      "youtube": s.get("youtube")}
        if spec.media == "video":
            today_info["video"] = s.get("video_path")
        if spec.describe:
            today_info.update(spec.describe(s))
    return {
        "date": date.isoformat(),
        "period": period(spec, date).isoformat(),
        "cadence": spec.cadence,
        "enabled": enabled(ctx.cfg, spec),
        "streak": streaks(hist, date),
        "today": today_info,
        "pending_uploads": [x["date"] for x in pending_uploads(hist)],
    }


def history_rows(ctx, spec: Practice, limit: int = 14, reveal_today: bool = False) -> List[Dict[str, Any]]:
    """Recent sessions. This period's text stays hidden until recorded (cold read)."""
    hist = history(ctx.paths, spec)
    rows = []
    for key in sorted(hist.sessions, reverse=True)[:limit]:
        s = hist.sessions[key]
        yt = s.get("youtube") or {}
        hide = key == period(spec).isoformat() and not s.get("recorded") and not reveal_today
        text = s.get("paragraph", "")
        row = {"date": key, "day": s.get("day_number"), "recorded": bool(s.get("recorded")),
               "youtube": yt.get("url") or yt.get("status"),
               "paragraph": "(hidden until you record today)" if hide else
               ((text[:120] + "…") if len(text) > 120 else text)}
        if spec.describe:
            row.update(spec.describe(s))
        rows.append(row)
    return rows
