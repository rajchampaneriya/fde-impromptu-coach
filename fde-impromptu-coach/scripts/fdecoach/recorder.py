"""Run one recording session: QuickTime camera recording + PowerPoint slide show,
kept in sync so YouTube chapters line up with each question."""
from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any, Dict, Optional

from . import macos
from .config import Paths
from .deck import session_seconds

log = logging.getLogger("fdecoach")

VIDEO_EXT = {".mov", ".mp4", ".m4v"}


def wait_for_video(folder: Path, since: float, timeout: int) -> Optional[Path]:
    """Wait for a new, fully written video file in folder (size stable across polls)."""
    deadline = time.time() + timeout
    sizes: Dict[Path, int] = {}
    while time.time() < deadline:
        for f in folder.glob("*"):
            if f.suffix.lower() not in VIDEO_EXT or f.name.startswith("."):
                continue
            try:
                st = f.stat()
            except OSError:
                continue
            if st.st_mtime < since or st.st_size < 1_000_000:
                continue
            if sizes.get(f) == st.st_size:
                return f
            sizes[f] = st.st_size
        time.sleep(3)
    return None


def _manual_save(folder: Path, since: float) -> Optional[Path]:
    macos.notify("Save your recording", "Press \u2318S in QuickTime and save into Movies \u203a FDE-Impromptu")
    macos.open_path(folder)
    macos.dialog(
        "Automatic saving didn't work this time.\n\nIn QuickTime: press \u2318S and save the recording into the "
        f"folder that just opened ({folder}).\n\nThis finishes by itself once the file appears.",
        "FDE Impromptu Coach", ["OK"], "OK", timeout_seconds=120)
    return wait_for_video(folder, since, timeout=900)


def _run_show(deck: Path, show: Path, cfg: Dict[str, Any], total: float, grace: int):
    """Start the slide show and wait for it to run its course (or Esc).
    Returns (ended_early, show_start_time)."""
    app = cfg.get("presentation_app", "Microsoft PowerPoint")
    started = macos.powerpoint_start_show(deck, app)
    if not started:
        if app == "Microsoft PowerPoint":
            log.warning("Could not start the show via AppleScript; opening the .ppsx play copy")
        else:
            log.info("%s: starting the show via the .ppsx play copy", app)
        macos.open_path(show, app)
        time.sleep(4)
    t_show = time.time()
    ended_early = False
    while True:
        time.sleep(0 if macos.dry_run() else 2)
        elapsed = time.time() - t_show
        running = macos.powerpoint_show_running(app)
        if elapsed >= total + grace or macos.dry_run():
            break
        if running is False and elapsed > 8:
            ended_early = elapsed < total - 5
            break
    macos.powerpoint_end_show(app)
    if "keynote" in app.lower():
        macos.keynote_close_documents()
    return ended_early, t_show


def record(session: Dict[str, Any], cfg: Dict[str, Any], paths: Paths) -> Dict[str, Any]:
    rec_cfg = cfg.get("recording", {})
    folder = paths.recordings_dir(cfg)
    dest = folder / f"{session['date']}_FDE-Impromptu_Day{session.get('day_number', 0)}.mov"
    deck = Path(session["deck_path"])
    show = Path(session.get("show_path") or deck)
    total = session_seconds(cfg, len(session["questions"]))
    grace = int(rec_cfg.get("stop_grace_seconds", 4))
    mode = rec_cfg.get("mode", "auto")
    result: Dict[str, Any] = {"ok": False, "video": None, "offset": None, "method": mode, "ended_early": False}

    if mode == "none":
        # Camera-less practice: run the deck show, count the day, save no video.
        result["ended_early"], _ = _run_show(deck, show, cfg, total, grace)
        result.update(ok=True, method="none")
        return result

    if mode == "auto" and not (macos.has_camera() and macos.has_microphone()):
        result["error"] = ("no camera/microphone on this Mac - practise with the deck and mark the day "
                           "(fde-coach complete --no-video), or make camera-less practice the default: "
                           "fde-coach config --set recording.mode=none")
        return result

    if mode == "auto":
        t_rec = time.time()
        if not macos.quicktime_start_recording(float(rec_cfg.get("camera_warmup_seconds", 2))):
            log.warning("QuickTime automation failed; switching to guided manual mode")
            mode = result["method"] = "manual"
    if mode == "manual":
        macos.powerpoint_open(deck, cfg.get("presentation_app"))
        macos.osascript('tell application "QuickTime Player"\nactivate\nnew movie recording\nend tell', timeout=30)
        answer = macos.dialog(
            "Guided mode\n\n1. In the QuickTime window, click the red record button.\n"
            "2. Then click \u201cStart slides\u201d here.", "FDE Impromptu Coach",
            ["Not now", "Start slides"], "Start slides", timeout_seconds=600)
        if answer != "Start slides":
            result["error"] = "cancelled"
            return result
        t_rec = time.time()

    result["ended_early"], t_show = _run_show(deck, show, cfg, total, grace)
    if mode == "auto":
        result["offset"] = round(t_show - t_rec, 1)

    if mode == "auto":
        saved, how = macos.quicktime_stop_and_save(dest, since=t_rec)
        result["method"] = f"auto:{how}"
        video = dest if saved else _manual_save(folder, t_rec - 5)
    else:
        macos.dialog("Stop the QuickTime recording (the stop button, or \u2318\u2303Esc), press \u2318S and save it "
                     f"into:\n{folder}\n\nThis finishes by itself once the file appears.",
                     "FDE Impromptu Coach", ["OK"], "OK", timeout_seconds=120)
        macos.open_path(folder)
        video = wait_for_video(folder, t_rec - 5, timeout=900)

    if not video:
        result["error"] = "no video file was saved"
        return result
    if mode == "auto":
        macos.quit_app("QuickTime Player")
    result["video"] = str(video)
    duration = macos.video_duration_seconds(video)
    result["duration"] = duration
    min_secs = int(rec_cfg.get("min_video_seconds", 150))
    if duration is not None and duration < min_secs:
        result["error"] = f"recording too short ({int(duration)} s < {min_secs} s)"
        return result
    result["ok"] = True
    return result
