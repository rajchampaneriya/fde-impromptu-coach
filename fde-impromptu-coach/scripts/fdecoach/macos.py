"""macOS automation via osascript (AppleScript). Every call is best-effort and
returns a result instead of raising, so a missing permission never breaks the
daily run. FDE_COACH_DRYRUN=1 simulates everything (used for tests on Linux).
"""
from __future__ import annotations

import logging
import os
import platform
import shutil
import subprocess
import time
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

log = logging.getLogger("fdecoach")

GAVE_UP = "__gave_up__"


def dry_run() -> bool:
    return os.environ.get("FDE_COACH_DRYRUN") == "1"


def is_macos() -> bool:
    return platform.system() == "Darwin"


def q(text: str) -> str:
    """AppleScript string literal."""
    return '"' + str(text).replace("\\", "\\\\").replace('"', '\\"') + '"'


def osascript(script: str, timeout: int = 60) -> Tuple[bool, str]:
    if dry_run() or not is_macos():
        log.debug("[dry-run] osascript: %s", script.strip().splitlines()[0][:120] if script.strip() else "")
        return True, ""
    try:
        proc = subprocess.run(["/usr/bin/osascript", "-"], input=script, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        log.warning("osascript timed out after %ss", timeout)
        return False, "timeout"
    if proc.returncode != 0:
        log.debug("osascript error: %s", proc.stderr.strip()[:300])
        return False, proc.stderr.strip()
    return True, proc.stdout.strip()


# --------------------------------------------------------------------------- user-facing

def notify(title: str, message: str, subtitle: str = "", sound: str = "Glass") -> None:
    parts = [f"display notification {q(message)} with title {q(title)}"]
    if subtitle:
        parts.append(f"subtitle {q(subtitle)}")
    if sound:
        parts.append(f"sound name {q(sound)}")
    ok, _ = osascript(" ".join(parts), timeout=15)
    log.info("notify: %s | %s", title, message)


def dialog(message: str, title: str, buttons: Sequence[str], default: str,
           timeout_seconds: int = 900, icon: str = "note") -> str:
    """Returns the clicked button, GAVE_UP on timeout, or '' on error.
    FDE_COACH_DRYRUN_ANSWERS='Start now,Later' feeds answers in order during tests."""
    if dry_run() or not is_macos():
        answers = [a for a in os.environ.get("FDE_COACH_DRYRUN_ANSWERS", "").split(",") if a]
        answer = answers.pop(0) if answers else GAVE_UP
        os.environ["FDE_COACH_DRYRUN_ANSWERS"] = ",".join(answers)
        log.info("[dry-run] dialog %r -> %s", message[:80], answer)
        return answer
    btns = ", ".join(q(b) for b in buttons)
    script = f"""
activate
try
    set r to display dialog {q(message)} with title {q(title)} buttons {{{btns}}} default button {q(default)} with icon {icon} giving up after {int(timeout_seconds)}
    if gave up of r then return "{GAVE_UP}"
    return button returned of r
on error number -128
    return "{GAVE_UP}"
end try
"""
    ok, out = osascript(script, timeout=int(timeout_seconds) + 30)
    return out if ok else ""


def open_path(path: Path, app: Optional[str] = None) -> bool:
    if dry_run() or not is_macos():
        log.info("[dry-run] open %s %s", f"-a {app}" if app else "", path)
        return True
    cmd = ["/usr/bin/open"]
    if app and app_exists(app):
        cmd += ["-a", app]
    cmd.append(str(path))
    return subprocess.run(cmd, capture_output=True).returncode == 0


def open_url(url: str) -> bool:
    if dry_run() or not is_macos():
        log.info("[dry-run] open %s", url)
        return True
    return subprocess.run(["/usr/bin/open", url], capture_output=True).returncode == 0


def copy_to_clipboard(text: str) -> bool:
    if dry_run() or not is_macos():
        log.info("[dry-run] clipboard <- %d characters", len(text))
        return True
    try:
        return subprocess.run(["/usr/bin/pbcopy"], input=text, text=True, timeout=10).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def ask_text(message: str, title: str, buttons: Sequence[str] = ("Later", "Save"), default: str = "Save",
             timeout_seconds: int = 900) -> Tuple[str, str]:
    """Dialog with a text field. Returns (button, text); ('', '') on error, GAVE_UP on timeout.
    In dry-run the next FDE_COACH_DRYRUN_ANSWERS item is the typed text (button = default)."""
    if dry_run() or not is_macos():
        answers = [a for a in os.environ.get("FDE_COACH_DRYRUN_ANSWERS", "").split(",") if a]
        answer = answers.pop(0) if answers else ""
        os.environ["FDE_COACH_DRYRUN_ANSWERS"] = ",".join(answers)
        log.info("[dry-run] ask %r -> %r", message[:60], answer)
        return (default, answer) if answer else (GAVE_UP, "")
    btns = ", ".join(q(b) for b in buttons)
    script = f"""
activate
try
    set r to display dialog {q(message)} with title {q(title)} default answer "" buttons {{{btns}}} default button {q(default)} giving up after {int(timeout_seconds)}
    if gave up of r then return "{GAVE_UP}" & linefeed
    return (button returned of r) & linefeed & (text returned of r)
on error number -128
    return "{GAVE_UP}" & linefeed
end try
"""
    ok, out = osascript(script, timeout=int(timeout_seconds) + 30)
    if not ok:
        return "", ""
    button, _, text = out.partition("\n")
    return button, text.strip()


def quit_app(name: str) -> None:
    osascript(f"tell application {q(name)} to quit", timeout=30)


def keynote_close_documents() -> None:
    """Close every open Keynote document (a finished show leaves the deck open)."""
    osascript("""
tell application "Keynote"
    try
        repeat with d in documents
            close d saving no
        end repeat
    end try
end tell
""", timeout=60)


def app_exists(name: str) -> bool:
    if dry_run():
        return True
    for base in ("/Applications", "/System/Applications", str(Path.home() / "Applications")):
        if Path(base, f"{name}.app").exists():
            return True
    return False


def video_duration_seconds(path: Path) -> Optional[float]:
    """Spotlight metadata; None when unknown (e.g. not indexed yet)."""
    if dry_run() or not is_macos() or not shutil.which("mdls"):
        return None
    try:
        out = subprocess.run(["mdls", "-raw", "-name", "kMDItemDurationSeconds", str(path)],
                             capture_output=True, text=True, timeout=10).stdout.strip()
        return float(out) if out and out != "(null)" else None
    except (ValueError, subprocess.TimeoutExpired):
        return None


# --------------------------------------------------------------------------- PowerPoint

def powerpoint_open(path: Path, app: str = "Microsoft PowerPoint") -> bool:
    return open_path(path, app)


def powerpoint_close(filename: str) -> None:
    osascript(f"""
if application "Microsoft PowerPoint" is running then
    tell application "Microsoft PowerPoint"
        repeat with p in presentations
            if name of p is {q(filename)} then close p saving no
        end repeat
    end tell
end if
""", timeout=30)


def powerpoint_start_show(path: Path, app: str = "Microsoft PowerPoint") -> bool:
    """Open the deck (if needed) and start the slide show from slide 1. True if a show window appears."""
    if app != "Microsoft PowerPoint":
        # Keynote 14.5 has no usable slideshow AppleScript; start via the .ppsx play copy instead.
        return False
    if dry_run() or not is_macos():
        log.info("[dry-run] start slide show %s", path.name)
        return True
    subprocess.run(["/usr/bin/open", "-b", "com.microsoft.Powerpoint", str(path)], capture_output=True)
    script = f"""
tell application "Microsoft PowerPoint"
    activate
    set target to missing value
    repeat 40 times
        repeat with p in presentations
            if name of p is {q(path.name)} then set target to p
        end repeat
        if target is not missing value then exit repeat
        delay 0.5
    end repeat
    if target is missing value then return "no-presentation"
    set sss to slide show settings of target
    try
        set starting slide of sss to 1
        set ending slide of sss to (count of slides of target)
    end try
    run slide show sss
    delay 1
    return (count of slide show windows) as text
end tell
"""
    ok, out = osascript(script, timeout=60)
    log.info("PowerPoint start show: ok=%s out=%s", ok, out)
    return ok and out.isdigit() and int(out) > 0


def powerpoint_show_running(app: str = "Microsoft PowerPoint") -> Optional[bool]:
    if app != "Microsoft PowerPoint" or dry_run() or not is_macos():
        return None
    ok, out = osascript('tell application "Microsoft PowerPoint" to return (count of slide show windows) as text', 10)
    if not ok or not out.isdigit():
        return None
    return int(out) > 0


def powerpoint_end_show(app: str = "Microsoft PowerPoint") -> None:
    if app != "Microsoft PowerPoint":
        return
    osascript("""
tell application "Microsoft PowerPoint"
    try
        repeat while (count of slide show windows) > 0
            exit slide show (slide show view of slide show window 1)
            delay 0.3
        end repeat
    end try
end tell
""", timeout=20)


# --------------------------------------------------------------------------- QuickTime

def quicktime_start_recording(warmup: float = 2.0) -> bool:
    if dry_run() or not is_macos():
        log.info("[dry-run] QuickTime: new movie recording + start")
        return True
    ok, out = osascript(f"""
tell application "QuickTime Player"
    activate
    set rec to new movie recording
    delay {warmup}
    tell rec to start
    return "started"
end tell
""", timeout=60)
    log.info("QuickTime start: ok=%s out=%s", ok, out)
    return ok and out == "started"


def _recover_composition(dest: Path, since: float, inner_names: Sequence[str] = ("Movie Recording.mov",),
                         min_bytes: int = 1_000_000) -> bool:
    """Modern QuickTime (macOS 26+) silently ignores AppleScript save/export
    targets (exit 0, empty file); a stopped recording instead auto-saves as a
    .qtpxcomposition bundle. Pull the media out of the newest such bundle."""
    dirs = {dest.parent, Path("~/Movies").expanduser()}
    deadline = time.time() + 10
    while time.time() < deadline:
        bundles = []
        for d in dirs:
            if d.exists():
                bundles += [b for b in d.glob("*.qtpxcomposition")
                            if b.stat().st_mtime >= since - 5]
        if bundles:
            bundle = max(bundles, key=lambda b: b.stat().st_mtime)
            inner = next((bundle / n for n in inner_names
                          if (bundle / n).exists() and (bundle / n).stat().st_size > min_bytes), None)
            if inner is not None:
                try:
                    shutil.copyfile(inner, dest)
                except OSError as exc:
                    log.warning("composition copy failed: %s", exc)
                    return False
                osascript('tell application "QuickTime Player" to close front document saving no', timeout=30)
                shutil.rmtree(bundle, ignore_errors=True)
                size = dest.stat().st_size if dest.exists() else 0
                log.info("QuickTime composition recover: %s (%d bytes)", dest, size)
                return size > min_bytes
        time.sleep(3)
    return False


def _finish_sidecar(dest: Path, inner_names: Sequence[str] = ("Movie Recording.mov",),
                    min_bytes: int = 1_000_000) -> bool:
    """macOS 26+ QuickTime rewrites the save target to '<dest>.qtpxcomposition' —
    either a flat media file (rename it) or a bundle (extract the recording).
    Returns True when dest holds a file larger than min_bytes."""
    side = dest.with_name(dest.name + ".qtpxcomposition")
    if dest.exists() and dest.stat().st_size > min_bytes:
        return True
    if side.is_file() and side.stat().st_size > min_bytes:
        side.replace(dest)
        return True
    if side.is_dir():
        inner = next((side / n for n in inner_names
                      if (side / n).exists() and (side / n).stat().st_size > min_bytes), None)
        if inner is not None:
            shutil.copyfile(inner, dest)
            shutil.rmtree(side, ignore_errors=True)
            return dest.exists() and dest.stat().st_size > min_bytes
    return False


def _sidecar_with_retry(dest: Path, inner_names: Sequence[str], min_bytes: int, tries: int = 8) -> bool:
    """macOS 26 writes the '<dest>.qtpxcomposition' sidecar asynchronously after the
    save command returns ok — poll briefly before giving up."""
    for _ in range(tries):
        if _finish_sidecar(dest, inner_names, min_bytes):
            return True
        time.sleep(1)
    return _finish_sidecar(dest, inner_names, min_bytes)


def _stop_and_save(dest: Path, since: float, inner_names: Sequence[str], export_presets: Sequence[str],
                   min_bytes: int = 1_000_000, dry_bytes: int = 2 * 1024 * 1024) -> Tuple[bool, str]:
    """Stop the front QuickTime recording and save it to dest. Tries the auto-saved
    composition bundle first (modern macOS), then save/export AppleScript."""
    if dry_run() or not is_macos():
        dest.parent.mkdir(parents=True, exist_ok=True)
        with open(dest, "wb") as fh:
            fh.write(b"\0" * dry_bytes)
        log.info("[dry-run] QuickTime stop + save -> %s", dest)
        return True, "dry-run"
    osascript("""
tell application "QuickTime Player"
    repeat with d in documents
        try
            stop d
        end try
    end repeat
end tell
""", timeout=60)
    time.sleep(4)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if since and _recover_composition(dest, since, inner_names, min_bytes):
        _finish_sidecar(dest, inner_names, min_bytes)
        osascript('tell application "QuickTime Player" to close front document saving no', timeout=30)
        if dest.exists() and dest.stat().st_size > min_bytes:
            return True, "composition"
    attempts: List[Tuple[str, str]] = [("save", "save theDoc in (POSIX file {p})")]
    for preset in export_presets:
        attempts.append((f"export-{preset}", f'export theDoc in (POSIX file {{p}}) using settings preset "{preset}"'))
    for label, command in attempts:
        if dest.exists():
            dest.unlink()
        dest.touch()  # pre-create so the sandboxed app receives write access via the file reference
        script = f"""
with timeout of 1800 seconds
    tell application "QuickTime Player"
        set theDoc to front document
        {command.format(p=q(str(dest)))}
    end tell
end timeout
return "ok"
"""
        ok, out = osascript(script, timeout=1860)
        if ok and _sidecar_with_retry(dest, inner_names, min_bytes):
            osascript('tell application "QuickTime Player" to close front document saving no', timeout=30)
            size = dest.stat().st_size
            log.info("QuickTime %s: sidecar finalised (%d bytes)", label, size)
            return True, f"{label}-sidecar"
        size = dest.stat().st_size if dest.exists() else 0
        log.info("QuickTime %s: ok=%s size=%s %s", label, ok, size, out[:200])
        if ok and size > min_bytes:
            osascript('tell application "QuickTime Player" to close front document saving no', timeout=30)
            return True, label
    if dest.exists() and dest.stat().st_size == 0:
        dest.unlink()
    return False, "save-failed"


def quicktime_stop_and_save(dest: Path, since: float = 0.0) -> Tuple[bool, str]:
    return _stop_and_save(dest, since, ("Movie Recording.mov",), ("1080p", "720p"))


def quicktime_start_audio_recording(warmup: float = 2.0) -> bool:
    if dry_run() or not is_macos():
        log.info("[dry-run] QuickTime: new audio recording + start")
        return True
    ok, out = osascript(f"""
tell application "QuickTime Player"
    activate
    set rec to new audio recording
    delay {warmup}
    tell rec to start
    return "started"
end tell
""", timeout=60)
    log.info("QuickTime audio start: ok=%s out=%s", ok, out)
    return ok and out == "started"


def quicktime_stop_audio_save(dest: Path, since: float = 0.0) -> Tuple[bool, str]:
    # speech is mono AAC: a valid 5-minute take can be well under 1 MB
    return _stop_and_save(dest, since, ("Audio Recording.m4a", "Movie Recording.mov"), (), min_bytes=100_000)


# --------------------------------------------------------------------------- Reminders (syncs to iPhone)

def reminders_create(list_name: str, title: str, body: str, hour: int, minute: int) -> bool:
    ok, out = osascript(f"""
tell application "Reminders"
    if not (exists list {q(list_name)}) then make new list with properties {{name:{q(list_name)}}}
    set dueD to current date
    set time of dueD to ({hour} * hours + {minute} * minutes)
    if dueD < (current date) then set dueD to (current date) + (10 * minutes)
    tell list {q(list_name)}
        if not (exists (first reminder whose name is {q(title)} and completed is false)) then
            make new reminder with properties {{name:{q(title)}, body:{q(body)}, due date:dueD, remind me date:dueD, priority:1}}
        end if
    end tell
end tell
return "ok"
""", timeout=90)
    return ok


def reminders_complete(list_name: str, title: str) -> bool:
    ok, _ = osascript(f"""
tell application "Reminders"
    if exists list {q(list_name)} then
        repeat with r in (reminders of list {q(list_name)} whose name is {q(title)} and completed is false)
            set completed of r to true
        end repeat
    end if
end tell
""", timeout=90)
    return ok


def reminders_prune(list_name: str, tag: str, keep_title: str) -> None:
    """Delete stale, incomplete reminders created by this tool on earlier days."""
    osascript(f"""
tell application "Reminders"
    if exists list {q(list_name)} then
        repeat with r in (reminders of list {q(list_name)} whose completed is false and body contains {q(tag)})
            if name of r is not {q(keep_title)} then delete r
        end repeat
    end if
end tell
""", timeout=90)


# --------------------------------------------------------------------------- hardware probes

def has_camera() -> bool:
    if dry_run() or not is_macos():
        return True
    try:
        out = subprocess.run(["system_profiler", "SPCameraDataType"], capture_output=True,
                             text=True, timeout=60).stdout
    except Exception:  # noqa: BLE001
        return True  # assume present; QuickTime will surface the real error
    return "Camera" in out


def has_microphone() -> bool:
    if dry_run() or not is_macos():
        return True
    try:
        out = subprocess.run(["system_profiler", "SPAudioDataType"], capture_output=True,
                             text=True, timeout=60).stdout
    except Exception:  # noqa: BLE001
        return True
    return "Input Source" in out or "Input Channels" in out


# --------------------------------------------------------------------------- permissions warm-up

def warmup(presentation_app: str) -> List[str]:
    """Touch each automation target once so macOS asks for permissions while the user is present."""
    results = []
    checks = [
        ("Notifications", 'display notification "Permissions check" with title "FDE Impromptu Coach"'),
        ("Reminders", 'tell application "Reminders" to return (count of lists) as text'),
        ("QuickTime Player", 'tell application "QuickTime Player" to return (count of documents) as text'),
    ]
    if app_exists(presentation_app):
        # PowerPoint exposes `presentations`; Keynote calls the same thing `documents`.
        obj = "documents" if "keynote" in presentation_app.lower() else "presentations"
        checks.append((presentation_app, f'tell application {q(presentation_app)} to return (count of {obj}) as text'))
    for name, script in checks:
        ok, out = osascript(script, timeout=120)
        results.append(f"{name}: {'ok' if ok else 'blocked (' + out[:80] + ')'}")
    return results


def quicktime_camera_check() -> bool:
    """Opens a camera preview for 3 s so macOS asks QuickTime for camera/microphone access."""
    ok, _ = osascript("""
tell application "QuickTime Player"
    activate
    set rec to new movie recording
    delay 3
    close rec saving no
end tell
""", timeout=60)
    return ok


def quicktime_audio_check() -> bool:
    """Opens an audio recording for 2 s so macOS asks QuickTime for microphone access."""
    ok, _ = osascript("""
tell application "QuickTime Player"
    activate
    set rec to new audio recording
    delay 2
    close rec saving no
end tell
""", timeout=60)
    return ok


def choose_from_list(message: str, title: str, items: Sequence[str],
                     default_items: Sequence[str] = ()) -> List[str]:
    """Multi-select list dialog. Returns the chosen items ([] on cancel/timeout).
    FDE_COACH_DRYRUN_ANSWERS feeds one answer per dialog; the dry-run encoding
    for a selection is a single item with '+' between the chosen words."""
    if dry_run() or not is_macos():
        answers = [a for a in os.environ.get("FDE_COACH_DRYRUN_ANSWERS", "").split(",") if a]
        answer = answers.pop(0) if answers else ""
        os.environ["FDE_COACH_DRYRUN_ANSWERS"] = ",".join(answers)
        log.info("[dry-run] choose %r -> %s", message[:60], answer)
        return [w for w in answer.split("+") if w]
    items_xml = ", ".join(q(i) for i in items)
    default_part = ""
    if default_items:
        default_part = " default items {" + ", ".join(q(i) for i in default_items) + "}"
    script = f"""
try
    set picked to choose from list {{{items_xml}}} with title {q(title)} with prompt {q(message)}{default_part} \
with multiple selections allowed
    if picked is false then return ""
    set AppleScript's text item delimiters to "\\n"
    return (picked as text)
on error number -128
    return ""
end try
"""
    ok, out = osascript(script, timeout=300)
    if not ok or not out:
        return []
    return [line.strip() for line in out.splitlines() if line.strip()]
