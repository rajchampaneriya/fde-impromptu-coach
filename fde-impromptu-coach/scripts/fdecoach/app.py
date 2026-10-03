"""Services behind every CLI command: build today's deck, run the daily flow,
record a session, protect the streak with reminders, and upload privately.

Lock order (always acquired in this order to avoid deadlocks):
    session -> generate -> history        upload -> history        prompt (standalone)
"""
from __future__ import annotations

import datetime as dt
import json
import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from . import gcal, macos, recorder, youtube
from .config import APP_NAME, ENTRY_SCRIPT, REFERENCES_DIR, TAG, Paths, load_config, parse_hhmm, setup_logging
from .deck import build_deck, chapters, render_thumbnail, session_seconds
from .questions import categories, generate_questions, plan_slots, questions_from_file
from .state import History, LockBusy, Runtime, file_lock, lock_is_held, now, streaks, today

log = logging.getLogger("fdecoach")


class Ctx:
    def __init__(self, verbose: bool = False):
        self.paths = Paths()
        self.paths.ensure()
        self.log = setup_logging(self.paths, verbose)
        self.cfg = load_config(self.paths)

    def history(self) -> History:
        return History(self.paths)

    def runtime(self) -> Runtime:
        return Runtime(self.paths)


# --------------------------------------------------------------------------- helpers

def reminder_title(date: dt.date) -> str:
    return f"Record FDE impromptu practice ({date.isoformat()})"


def update_session(ctx: Ctx, date: dt.date, fn: Callable[[Dict[str, Any]], None]) -> Optional[Dict[str, Any]]:
    """Read-modify-write one session under the history lock (fresh read every time)."""
    with file_lock(ctx.paths, "history", blocking=True):
        history = ctx.history()
        session = history.get(date)
        if session is None:
            return None
        fn(session)
        history.put(session)
        history.save()
        return session


def update_runtime(ctx: Ctx, fn: Callable[[Runtime], None]) -> None:
    with file_lock(ctx.paths, "runtime", blocking=True):
        rt = ctx.runtime()
        fn(rt)
        rt.save()


def notify_once(ctx: Ctx, key: str, title: str, message: str) -> None:
    """Throttle repeated notifications (e.g. 'YouTube not set up') to once per day."""
    stamp = today().isoformat()
    fired = {"yes": False}

    def mark(rt: Runtime) -> None:
        seen = rt.data.setdefault("notified", {})
        if seen.get(key) != stamp:
            seen[key] = stamp
            fired["yes"] = True

    update_runtime(ctx, mark)
    if fired["yes"]:
        macos.notify(title, message)


def _fmt_streak(n: int) -> str:
    return f"{n}-day streak" if n else "no active streak"


def _time_today(hhmm: str, date: dt.date) -> dt.datetime:
    h, m = parse_hhmm(hhmm)
    return dt.datetime.combine(date, dt.time(h, m))


def spawn_detached(args: List[str]) -> None:
    """Run another fde-coach command in the background (survives the caller exiting)."""
    log_path = Paths().logs / "background.log"
    with open(log_path, "a", encoding="utf-8") as out:
        subprocess.Popen([sys.executable, str(ENTRY_SCRIPT)] + args, stdout=out, stderr=subprocess.STDOUT,
                         stdin=subprocess.DEVNULL, start_new_session=True, env=dict(os.environ))


# --------------------------------------------------------------------------- deck

def ensure_today(ctx: Ctx, source: Optional[str] = None, replace: bool = False,
                 questions_path: Optional[Path] = None, brief: str = "") -> Tuple[Dict[str, Any], bool]:
    """Today's session (questions + deck). Builds it if missing; rebuilds a deleted deck file.
    replace=True makes a new set, but never replaces a day that is already recorded."""
    date = today()
    with file_lock(ctx.paths, "generate", blocking=True):
        history = ctx.history()
        existing = history.get(date)
        if existing and existing.get("recorded") and (replace or questions_path):
            raise RuntimeError("Today's session is already recorded; its questions can't be replaced.")
        if existing and not replace and questions_path is None:
            if not Path(existing.get("deck_path", "")).exists() or not Path(existing.get("show_path", "")).exists():
                log.info("Deck file missing; rebuilding today's deck from saved questions")
                pptx, ppsx = build_deck(existing, streaks(history, date), ctx.cfg, ctx.paths.decks)
                existing = update_session(
                    ctx, date, lambda s: s.update(deck_path=str(pptx), show_path=str(ppsx))) or existing
            return existing, False

        if existing:  # replacing: forget the old set so it is not treated as "past"
            history.remove(date)
        if questions_path is not None:
            qs, label, level, notes = questions_from_file(questions_path, history, ctx.runtime(), ctx.cfg, date)
            label = "claude-interactive" if label == "claude" else label
        else:
            src = source or ctx.cfg.get("question_source", "auto")
            qs, label, level, notes = generate_questions(history, ctx.runtime(), ctx.cfg, ctx.paths, date, src,
                                                        brief=brief)
        session: Dict[str, Any] = {
            "date": date.isoformat(),
            "day_number": history.completed_before(date) + 1,
            "level": level,
            "source": label,
            "notes": notes,
            "brief": brief,
            "created_at": now().isoformat(timespec="seconds"),
            "questions": qs,
            "recorded": False,
            "youtube": {"status": "none"},
        }
        pptx, ppsx = build_deck(session, streaks(history, date), ctx.cfg, ctx.paths.decks)
        session["deck_path"], session["show_path"] = str(pptx), str(ppsx)
        with file_lock(ctx.paths, "history", blocking=True):
            fresh = ctx.history()
            fresh.put(session)
            fresh.save()
        log.info("Built Day %s deck (level %s, source %s): %s", session["day_number"], level, label, pptx)
        for n in notes:
            log.info("generation note: %s", n)
        return session, True


# --------------------------------------------------------------------------- daily run (05:30)

def daily(ctx: Ctx, from_reminder: bool = False) -> Dict[str, Any]:
    try:
        session, created = ensure_today(ctx)
    except Exception as exc:  # noqa: BLE001 - must never die silently
        log.exception("Could not build today's deck")
        macos.notify(APP_NAME, f"Couldn't build today's deck: {exc}. Run: fde-coach doctor")
        return {"ok": False, "error": str(exc)}
    date = today()
    stats = streaks(ctx.history(), date)
    if session.get("recorded"):
        log.info("Today is already recorded; nothing to do")
        return {"ok": True, "already_recorded": True}

    if ctx.cfg.get("open_deck_when_ready", True):
        macos.powerpoint_open(Path(session["deck_path"]), ctx.cfg.get("presentation_app"))
    subtitle = f"Day {session['day_number']} \u00b7 Level {session['level']} \u00b7 {_fmt_streak(stats['current'])}"
    macos.notify(f"Today's {len(session['questions'])} questions are ready",
                 "Five minutes on camera keeps the streak alive.", subtitle=subtitle)

    rem = ctx.cfg.get("reminders", {})
    if rem.get("use_reminders_app", True):
        title = reminder_title(date)
        macos.reminders_prune(rem.get("reminders_list", "FDE Practice"), TAG, title)
        h, m = parse_hhmm(rem.get("reminders_app_due_time", "07:00"))
        body = (f"{TAG} Double-click 'Start Practice' in ~/FDE-Impromptu (or tell Claude Code: start my FDE "
                "practice). Completes automatically when the video is saved.")
        macos.reminders_create(rem.get("reminders_list", "FDE Practice"), title, body, h, m)
    calendar_sync_safe(ctx)

    if ctx.cfg.get("prompt_to_start_at_daily_run", True):
        prompt_start(ctx, reason="catch-up" if from_reminder else "daily")
    return {"ok": True, "created": created, "deck": session["deck_path"]}


# --------------------------------------------------------------------------- prompts

def _prompt_message(cfg: Dict[str, Any], stats: Dict[str, Any], session: Dict[str, Any], reason: str,
                    fired_count: int, last_call: bool) -> Tuple[str, str]:
    streak = stats["current"]
    n = len(session.get("questions", []))
    mins = max(1, round(session_seconds(cfg, n) / 60))
    if reason == "daily":
        head = f"Good morning. Day {session['day_number']} is ready: {n} surprise questions, 60 seconds each."
    elif reason == "catch-up":
        head = f"Day {session['day_number']} is ready: {n} surprise questions, 60 seconds each."
    elif last_call:
        head = "Last call for today's practice."
    elif fired_count >= 3:
        head = "Today's practice still isn't recorded."
    else:
        head = "Your questions are waiting."
    if streak:
        tail = (f"Your {streak}-day streak ends at midnight unless you record today." if not last_call
                else f"Record now to keep your {streak}-day streak. It takes {mins + 1} minutes.")
    else:
        tail = ("Record today to start a new streak." if stats.get("total")
                else "Record your first session to start your streak.")
    msg = (f"{head}\n\n{tail}\n\nStart now: the camera recording and the slides start together and stop "
           f"on their own after about {mins} minutes.")
    return msg, ("caution" if last_call else "note")


def prompt_start(ctx: Ctx, reason: str = "reminder", fired_count: int = 0, last_call: bool = False) -> str:
    """Ask the learner to start. Returns the button pressed (or a skip reason)."""
    if lock_is_held(ctx.paths, "session"):
        return "session-running"
    rem = ctx.cfg.get("reminders", {})
    snooze = int(rem.get("snooze_minutes", 20))
    try:
        with file_lock(ctx.paths, "prompt"):
            session = ctx.history().get(today())
            if not session or session.get("recorded"):
                return "nothing-to-do"
            stats = streaks(ctx.history(), today())
            msg, icon = _prompt_message(ctx.cfg, stats, session, reason, fired_count, last_call)
            update_runtime(ctx, lambda rt: rt.data.update(last_prompt=now().isoformat(timespec="seconds")))
            if reason not in ("daily", "catch-up"):
                head, tail = msg.split("\n\n")[0], msg.split("\n\n")[1]
                macos.notify(APP_NAME, tail, subtitle=head, sound="Hero" if last_call else "Glass")
            answer = macos.dialog(msg, APP_NAME, ["Later", f"Snooze {snooze} min", "Start now"], "Start now",
                                  timeout_seconds=int(rem.get("dialog_timeout_minutes", 15)) * 60, icon=icon)
    except LockBusy:
        return "prompt-open"
    log.info("prompt (%s) -> %s", reason, answer or "error")
    if answer == "Start now":
        run_session(ctx)
    elif answer.startswith("Snooze"):
        until = now() + dt.timedelta(minutes=snooze)
        update_runtime(ctx, lambda rt: rt.set_snooze(until))
    return answer or "error"


# --------------------------------------------------------------------------- session

def run_session(ctx: Ctx, force: bool = False, max_tries: int = 2) -> Dict[str, Any]:
    try:
        with file_lock(ctx.paths, "session"):
            return _run_session_locked(ctx, force, max_tries)
    except LockBusy:
        msg = "A practice session is already running."
        log.info(msg)
        return {"ok": False, "error": msg}


def _run_session_locked(ctx: Ctx, force: bool, max_tries: int) -> Dict[str, Any]:
    session, _ = ensure_today(ctx)
    date = dt.date.fromisoformat(session["date"])
    if session.get("recorded") and not force:
        macos.notify(APP_NAME, "Today's practice is already recorded. See you tomorrow.")
        return {"ok": True, "already_recorded": True}
    folder = ctx.paths.recordings_dir(ctx.cfg)
    free_gb = shutil.disk_usage(str(folder)).free / 1e9
    if free_gb < 2:
        macos.notify(APP_NAME, f"Only {free_gb:.1f} GB free; the recording may fail. Free some space.")

    result: Dict[str, Any] = {}
    for attempt in range(1, max_tries + 1):
        log.info("Session attempt %d for %s", attempt, session["date"])
        result = recorder.record(session, ctx.cfg, ctx.paths)
        log.info("record() -> %s", json.dumps(result))
        if result.get("ok"):
            break
        if result.get("error") == "cancelled":
            return result
        buttons = ["Later", "Keep this video", "Try again"] if result.get("video") else ["Later", "Try again"]
        answer = macos.dialog(
            f"The recording didn't finish cleanly: {result.get('error')}.\n\nYour streak is safe until midnight.",
            APP_NAME, buttons, "Try again", timeout_seconds=300, icon="caution")
        if answer == "Keep this video" and result.get("video"):
            result["ok"] = True
            result["kept_despite"] = result.pop("error", "")
            break
        if answer != "Try again" or attempt == max_tries:
            return result

    mark_recorded(ctx, date, video=result.get("video"), offset=result.get("offset"),
                  duration=result.get("duration"), method=result.get("method", ""),
                  ended_early=bool(result.get("ended_early")))
    ask_feedback(ctx, date)
    upload_async(ctx)
    offer_pronunciation(ctx)
    return result


def offer_pronunciation(ctx: Ctx) -> None:
    """After the FDE session: one prompt for the pronunciation practice."""
    pron_cfg = ctx.cfg.get("pronunciation", {})
    if not pron_cfg.get("prompt_after_fde", True) or lock_is_held(ctx.paths, "session"):
        return
    try:
        from . import pronounce_session
        history = pronounce_session.pron_history(ctx.paths)
        s = history.get(today())
        if s and s.get("recorded"):
            return
    except Exception:  # noqa: BLE001 - never disturb the FDE flow
        return
    answer = macos.dialog("FDE practice saved. Pronunciation practice next? (5 min, audio only)",
                          APP_NAME, ["Later", "Start now"], "Start now", timeout_seconds=300)
    if answer == "Start now":
        spawn_detached(["pronounce", "session"])


def mark_recorded(ctx: Ctx, date: dt.date, video: Optional[str], offset: Optional[float] = None,
                  duration: Optional[float] = None, method: str = "", ended_early: bool = False,
                  note: str = "") -> Dict[str, Any]:
    yt_enabled = bool(ctx.cfg.get("youtube", {}).get("enabled", True)) and bool(video)

    def apply(s: Dict[str, Any]) -> None:
        s.update(recorded=True, recorded_at=now().isoformat(timespec="seconds"), video_path=video,
                 video_duration=duration, chapter_offset=offset, record_method=method, ended_early=ended_early)
        if note:
            s["note"] = note
        s["youtube"] = {"status": "pending" if yt_enabled else "disabled", "attempts": 0}

    session = update_session(ctx, date, apply)
    if session is None:
        raise RuntimeError(f"No session for {date.isoformat()}")
    rem = ctx.cfg.get("reminders", {})
    if rem.get("use_reminders_app", True):
        macos.reminders_complete(rem.get("reminders_list", "FDE Practice"), reminder_title(date))
    update_runtime(ctx, lambda rt: rt.set_snooze(None))
    calendar_sync_safe(ctx)  # deletes today's "missed" event so its alerts never fire
    stats = streaks(ctx.history(), date)
    best = " \u00b7 new personal best!" if stats["current"] >= stats["best"] and stats["current"] > 1 else ""
    macos.notify(f"Day {session['day_number']} done \u2014 {_fmt_streak(stats['current'])}{best}",
                 "Saved. Uploading privately to YouTube." if yt_enabled else "Saved.", sound="Hero")
    log.info("Marked %s recorded (%s); streak %s", date, video, stats["current"])
    return session


def ask_feedback(ctx: Ctx, date: dt.date) -> None:
    """One tap after each session calibrates difficulty (level adjustment kept within -2..+2)."""
    if not ctx.cfg.get("ask_difficulty_feedback", True):
        return
    answer = macos.dialog("How did today's questions feel?", APP_NAME, ["Too easy", "About right", "Too hard"],
                          "About right", timeout_seconds=120)
    if answer not in ("Too easy", "About right", "Too hard"):
        return
    update_session(ctx, date, lambda s: s.update(feedback=answer))
    delta = {"Too easy": 1, "Too hard": -1}.get(answer, 0)
    if delta:
        update_runtime(ctx, lambda rt: rt.data.update(
            level_adjust=max(-2, min(2, int(rt.data.get("level_adjust", 0)) + delta))))
        log.info("Difficulty calibration %+d", delta)


def complete_manually(ctx: Ctx, video: Optional[Path], no_video: bool = False, note: str = "") -> Dict[str, Any]:
    """For sessions recorded outside the automation (manual QuickTime, phone, etc.)."""
    session, _ = ensure_today(ctx)
    date = dt.date.fromisoformat(session["date"])
    if video is not None:
        video = video.expanduser().resolve()
        if not video.exists():
            raise FileNotFoundError(str(video))
    elif not no_video:
        video = latest_video_today(ctx)
        if video is None:
            raise FileNotFoundError("No video from today in the recordings folder; pass --video PATH or --no-video")
    mark_recorded(ctx, date, str(video) if video else None, method="manual",
                  note=note or ("practised without video" if no_video else ""))
    upload_async(ctx)
    return ctx.history().get(date) or {}


def latest_video_today(ctx: Ctx) -> Optional[Path]:
    folder = ctx.paths.recordings_dir(ctx.cfg)
    start = dt.datetime.combine(today(), dt.time(0, 0)).timestamp()
    vids = [f for f in folder.glob("*") if f.suffix.lower() in recorder.VIDEO_EXT and f.stat().st_mtime >= start]
    return max(vids, key=lambda f: f.stat().st_mtime) if vids else None


# --------------------------------------------------------------------------- YouTube

def upload_async(ctx: Ctx) -> None:
    if not ctx.cfg.get("youtube", {}).get("enabled", True):
        return
    if macos.dry_run():
        upload_pending(ctx)
    else:
        spawn_detached(["upload"])


def _chapter_marks(s: Dict[str, Any], cfg: Dict[str, Any]) -> Optional[List[Tuple[int, str]]]:
    """Chapters only when the recording is known to be in sync with the slides."""
    offset = s.get("chapter_offset")
    if offset is None or s.get("ended_early"):
        return None
    marks = chapters(s, cfg, float(offset))
    dur = s.get("video_duration")
    if dur:
        marks = [m for m in marks if m[0] < float(dur) - 10]
    return marks if len(marks) >= 3 else None


def upload_pending(ctx: Ctx, interactive: bool = False) -> List[str]:
    out: List[str] = []
    yt_cfg = ctx.cfg.get("youtube", {})
    if not yt_cfg.get("enabled", True):
        return ["YouTube upload is disabled in config."]
    try:
        with file_lock(ctx.paths, "upload"):
            pending = ctx.history().pending_uploads()
            if not pending:
                return ["Nothing to upload."]
            if not youtube.is_configured(ctx.paths) and not macos.dry_run():
                msg = "Recording saved locally. Connect YouTube once: run `fde-coach youtube-auth` (see README)."
                if not interactive:
                    notify_once(ctx, "yt-not-configured", APP_NAME, msg)
                return [msg]
            max_attempts = int(yt_cfg.get("max_attempts", 12))
            for s in pending:
                date = dt.date.fromisoformat(s["date"])
                if int((s.get("youtube") or {}).get("attempts", 0)) >= max_attempts:
                    continue
                video = Path(s["video_path"])
                if not video.exists():
                    update_session(ctx, date, lambda x: x["youtube"].update(status="missing"))
                    out.append(f"{s['date']}: video file missing ({video})")
                    continue
                stats = streaks(ctx.history(), date)
                meta = youtube.build_metadata(s, ctx.cfg, _chapter_marks(s, ctx.cfg), stats["current"])
                thumb = render_thumbnail(s, stats, ctx.cfg, ctx.paths.decks / f"{s['date']}_thumb.png")
                try:
                    vid = youtube.upload(ctx.paths, video, meta, thumbnail=thumb)
                except (youtube.YouTubeAuthExpired, youtube.YouTubeNotConfigured) as exc:
                    notify_once(ctx, "yt-auth", "YouTube needs you", str(exc))
                    out.append(f"{s['date']}: {exc}")
                    break
                except Exception as exc:  # noqa: BLE001
                    log.warning("Upload failed for %s: %s", s["date"], exc)
                    err = str(exc)[:300]
                    update_session(ctx, date, lambda x: x["youtube"].update(
                        status="failed", attempts=int(x["youtube"].get("attempts", 0)) + 1, last_error=err,
                        last_attempt=now().isoformat(timespec="seconds")))
                    out.append(f"{s['date']}: upload failed, will retry ({exc})")
                    continue
                url = f"https://youtu.be/{vid}"
                update_session(ctx, date, lambda x: x["youtube"].update(
                    status="uploaded", video_id=vid, url=url, uploaded_at=now().isoformat(timespec="seconds")))
                macos.notify("Uploaded to YouTube (private)", url,
                             subtitle=f"Day {s.get('day_number')} \u00b7 {s['date']}")
                out.append(f"{s['date']}: uploaded privately -> {url}")
    except LockBusy:
        return ["An upload is already running."]
    return out


# --------------------------------------------------------------------------- Google Calendar

def calendar_sync(ctx: Ctx, clear: bool = False) -> List[str]:
    """Reconcile Google Calendar with the practice log: an event (with alerts) exists for each
    unrecorded day from today to today + days_ahead; recorded days have theirs deleted.
    Local bookkeeping means the API is only called when something changes."""
    gc = ctx.cfg.get("google_calendar", {})
    enabled = bool(gc.get("enabled", True)) and not clear
    if not gcal.is_configured(ctx.paths) and not macos.dry_run():
        return ["Google Calendar not connected (run: fde-coach calendar-auth)."]
    try:
        with file_lock(ctx.paths, "calendar"):
            state: Dict[str, str] = dict(ctx.runtime().data.get("gcal_events") or {})
            history, date, t = ctx.history(), today(), now()
            want: Dict[str, str] = {}
            if enabled:
                for i in range(int(gc.get("days_ahead", 2)) + 1):
                    d = date + dt.timedelta(days=i)
                    s = history.get(d)
                    if s and s.get("recorded"):
                        want[d.isoformat()] = "deleted"
                    elif gcal.event_window(d, ctx.cfg)[0].replace(tzinfo=None) > t:
                        want[d.isoformat()] = "created"
            else:  # disabled or clearing: remove every upcoming event this tool created
                for iso, st in state.items():
                    if st == "created" and iso >= date.isoformat():
                        want[iso] = "deleted"
            out: List[str] = []
            cal = str(gc.get("calendar_id", "primary"))
            for iso in sorted(want):
                if state.get(iso) == want[iso]:
                    continue
                d = dt.date.fromisoformat(iso)
                try:
                    if want[iso] == "created":
                        body = gcal.build_event(d, ctx.cfg, streaks(history, date)["current"])
                        result = gcal.ensure_event(ctx.paths, cal, body)
                    else:
                        result = gcal.delete_event(ctx.paths, cal, gcal.event_id(d))
                except (gcal.CalendarAuthExpired, gcal.CalendarNotConfigured) as exc:
                    notify_once(ctx, "gcal-auth", "Google Calendar needs you", str(exc))
                    out.append(f"{iso}: {exc}")
                    break
                except Exception as exc:  # noqa: BLE001 - offline etc.: retried on the next tick
                    log.warning("Google Calendar %s for %s failed: %s", want[iso], iso, exc)
                    out.append(f"{iso}: failed, will retry ({exc})")
                    continue
                state[iso] = want[iso]
                out.append(f"{iso}: missed-practice alert {result}")
                log.info("Google Calendar %s: %s", iso, result)
            cutoff = (date - dt.timedelta(days=14)).isoformat()
            state = {k: v for k, v in state.items() if k >= cutoff}
            update_runtime(ctx, lambda r: r.data.update(gcal_events=state))
            return out or ["Google Calendar already up to date."]
    except LockBusy:
        return ["Google Calendar sync already running."]


def calendar_sync_safe(ctx: Ctx) -> None:
    """Never let a calendar problem interrupt recording or reminders."""
    try:
        calendar_sync(ctx)
    except Exception:  # noqa: BLE001
        log.exception("Google Calendar sync failed")


# --------------------------------------------------------------------------- reminder tick (every 15 min)

def run_warmup(ctx: Ctx) -> List[str]:
    results = macos.warmup(ctx.cfg.get("presentation_app", "Microsoft PowerPoint"))
    results.append(f"camera/microphone: {'ok' if macos.quicktime_camera_check() else 'failed'}")
    update_runtime(ctx, lambda r: r.data.update(warmup_pending=False, warmup_results=results,
                                               warmup_at=now().isoformat(timespec="seconds")))
    log.info("permission warm-up: %s", results)
    return results


def remind(ctx: Ctx) -> str:
    rt = ctx.runtime()
    if rt.data.get("warmup_pending"):
        run_warmup(ctx)
        macos.notify(APP_NAME, "Permissions checked. Daily practice is scheduled.")
        rt = ctx.runtime()
    calendar_sync_safe(ctx)
    try:
        from . import factory_session
        factory_session.tick_safe(ctx)
    except Exception:  # noqa: BLE001 - the video series must never break the FDE reminders
        log.exception("Software Factory tick unavailable")

    date, t = today(), now()
    daily_at = _time_today(ctx.cfg.get("daily_time", "05:30"), date)
    if any(lock_is_held(ctx.paths, name) for name in ("session", "prompt", "generate")):
        return "busy"
    session = ctx.history().get(date)
    if session and session.get("recorded"):
        upload_pending(ctx)
        cleanup_recordings(ctx)
        return "recorded"
    if t < daily_at:
        upload_pending(ctx)
        return "before-daily-time"

    rem = ctx.cfg.get("reminders", {})
    quiet = _time_today(rem.get("quiet_after", "22:45"), date)
    if session is None:  # the 05:30 run was missed (Mac off/asleep, crash): self-heal now
        if t >= quiet:
            ensure_today(ctx)
            return "built-quietly"
        daily(ctx, from_reminder=True)
        return "catch-up"
    if t >= quiet:
        return "quiet-hours"

    snooze = rt.snooze_until()
    if snooze is not None and snooze > t:
        return "snoozed"
    snooze_due = snooze is not None and snooze.date() == date
    times = sorted(rem.get("times", []))
    fired = list(rt.fired_today(date))
    new_due = [x for x in times if _time_today(x, date) <= t and x not in fired]
    if not new_due and not snooze_due:
        upload_pending(ctx)
        return "nothing-due"

    def mark(r: Runtime) -> None:
        f = r.fired_today(date)
        f.extend(x for x in new_due if x not in f)
        if snooze is not None:
            r.set_snooze(None)

    update_runtime(ctx, mark)
    last_prompt = rt.data.get("last_prompt")
    recently = bool(last_prompt) and (t - dt.datetime.fromisoformat(last_prompt)) < dt.timedelta(minutes=30)
    if recently and not snooze_due:
        return "recently-prompted"
    last_call = bool(times) and t >= _time_today(times[-1], date)
    answer = prompt_start(ctx, reason="snooze" if snooze_due else "reminder",
                          fired_count=len(fired) + len(new_due), last_call=last_call)
    return f"prompted:{answer}"


def cleanup_recordings(ctx: Ctx) -> None:
    keep = ctx.cfg.get("keep_recordings_days")
    if not keep:
        return
    cutoff = (today() - dt.timedelta(days=int(keep))).isoformat()
    for s in list(ctx.history().sessions.values()):
        if s.get("date", "9999") >= cutoff or (s.get("youtube") or {}).get("status") != "uploaded":
            continue
        vp = s.get("video_path")
        if vp and Path(vp).exists():
            Path(vp).unlink()
            log.info("Deleted local recording older than %s days (already on YouTube): %s", keep, vp)


# --------------------------------------------------------------------------- read-only views

def status(ctx: Ctx) -> Dict[str, Any]:
    from . import scheduler

    history, rt = ctx.history(), ctx.runtime()
    date = today()
    stats = streaks(history, date)
    s = history.get(date)
    rem = ctx.cfg.get("reminders", {})
    t = now()
    upcoming = [x for x in sorted(rem.get("times", [])) if _time_today(x, date) > t]
    try:
        from . import pronounce_session
        pron = pronounce_session.status(ctx)
    except Exception as exc:  # noqa: BLE001 - pronunciation must never break the FDE status
        log.debug("pronunciation status unavailable: %s", exc)
        pron = None
    try:
        from . import factory_session
        factory = factory_session.status(ctx)
    except Exception as exc:  # noqa: BLE001
        log.debug("Software Factory status unavailable: %s", exc)
        factory = None
    return {
        "date": date.isoformat(),
        "streak": stats,
        "pronunciation": pron,
        "factory": factory,
        "level": s.get("level") if s else plan_slots(history, rt, ctx.cfg, date)["level"],
        "level_adjust": rt.data.get("level_adjust", 0),
        "today": None if not s else {
            "day_number": s.get("day_number"), "recorded": bool(s.get("recorded")), "source": s.get("source"),
            "deck": s.get("deck_path"), "video": s.get("video_path"), "youtube": s.get("youtube"),
            "categories": [q.get("category_label") for q in s.get("questions", [])],
        },
        "next_reminder": None if (s and s.get("recorded")) else (upcoming[0] if upcoming else None),
        "snooze_until": rt.data.get("snooze_until"),
        "pending_uploads": [x["date"] for x in history.pending_uploads()],
        "youtube_configured": youtube.is_configured(ctx.paths),
        "calendar_configured": gcal.is_configured(ctx.paths),
        "calendar_today": (rt.data.get("gcal_events") or {}).get(date.isoformat()),
        "agents": scheduler.status(),
        "data_dir": str(ctx.paths.root),
        "recordings_dir": str(ctx.paths.recordings_dir(ctx.cfg, create=False)),
    }


def history_rows(ctx: Ctx, limit: int = 14, reveal_today: bool = False) -> List[Dict[str, Any]]:
    """Recent sessions. Today's questions stay hidden until recorded, to keep the surprise."""
    history = ctx.history()
    rows = []
    for key in sorted(history.sessions, reverse=True)[:limit]:
        s = history.sessions[key]
        hide = key == today().isoformat() and not s.get("recorded") and not reveal_today
        yt = s.get("youtube") or {}
        rows.append({
            "date": key, "day": s.get("day_number"), "level": s.get("level"), "recorded": bool(s.get("recorded")),
            "youtube": yt.get("url") or yt.get("status"), "feedback": s.get("feedback"),
            "questions": ["(hidden until you record today)"] if hide else
            [f"[{q.get('category')} D{q.get('difficulty')}] {q.get('text')}" for q in s.get("questions", [])],
        })
    return rows


def authoring_plan(ctx: Ctx) -> Dict[str, Any]:
    """Everything Claude needs to author today's questions interactively."""
    history, rt = ctx.history(), ctx.runtime()
    date = today()
    plan = plan_slots(history, rt, ctx.cfg, date)
    cats = categories()
    out_file = ctx.paths.incoming / f"questions-{date.isoformat()}.json"
    return {
        "date": date.isoformat(),
        "level": plan["level"],
        "slots": [dict(s, label=cats[s["category"]]["label"], description=cats[s["category"]]["description"])
                  for s in plan["slots"]],
        "rubric": str(REFERENCES_DIR / "question_design.md"),
        "learner_context": ctx.cfg.get("learner_context", ""),
        "write_json_to": str(out_file),
        "then_run": f"fde-coach build --questions '{out_file}' --replace",
        "past_questions": [q.get("text", "") for q in history.all_questions(exclude_date=date)[-80:]],
        "already_built_today": history.get(date) is not None,
        "already_recorded_today": bool((history.get(date) or {}).get("recorded")),
    }
