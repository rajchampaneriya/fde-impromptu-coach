"""launchd LaunchAgents: the daily 05:30 FDE run, the 05:45 pronunciation and 06:00 legato
runs, the 05:50 learning-topic drop, the weekend 08:00 Weekend Stage run (Saturday, and
Sunday to catch a missed Saturday), and a 15-minute reminder/self-heal tick."""
from __future__ import annotations

import os
import plistlib
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

from .config import ENTRY_SCRIPT, Paths, parse_hhmm
from .macos import dry_run, is_macos

DAILY_LABEL = "com.fdecoach.daily"
REMIND_LABEL = "com.fdecoach.reminder"
PRON_LABEL = "com.fdecoach.pronounce"
LEGATO_LABEL = "com.fdecoach.legato"
LEARN_LABEL = "com.fdecoach.learn"
STAGE_LABEL = "com.fdecoach.stage"
ALL_LABELS = ("com.fdecoach.daily", "com.fdecoach.reminder", "com.fdecoach.pronounce", "com.fdecoach.legato",
              "com.fdecoach.learn", "com.fdecoach.stage")
REMIND_INTERVAL = 900
WEEKDAYS = {"sun": 0, "mon": 1, "tue": 2, "wed": 3, "thu": 4, "fri": 5, "sat": 6}  # launchd: 0 = Sunday


def stage_intervals(cfg: Dict[str, Any]) -> List[Dict[str, int]]:
    """One StartCalendarInterval per weekend day in stage.days (Sat, Sun by default)."""
    st = cfg.get("stage", {})
    hour, minute = parse_hhmm(st.get("time", "08:00"))
    out: List[Dict[str, int]] = []
    for day in st.get("days") or ["Sat", "Sun"]:
        n = WEEKDAYS.get(str(day).strip().lower()[:3])
        if n is None:
            raise ValueError(f"stage.days: unknown day {day!r} (use Sat, Sun, Mon ...)")
        item = {"Weekday": n, "Hour": hour, "Minute": minute}
        if item not in out:
            out.append(item)
    return out


def agents_dir() -> Path:
    override = os.environ.get("FDE_COACH_AGENTS_DIR")
    return Path(override).expanduser() if override else Path.home() / "Library" / "LaunchAgents"


def _env(cfg: Dict[str, Any], paths: Paths) -> Dict[str, str]:
    dirs: List[str] = []
    claude = cfg.get("claude_path") or ""
    if claude:
        dirs.append(str(Path(claude).parent))
    dirs += [str(Path.home() / ".local/bin"), "/opt/homebrew/bin", "/usr/local/bin", "/usr/bin", "/bin", "/usr/sbin", "/sbin"]
    seen: List[str] = []
    for d in dirs:
        if d not in seen:
            seen.append(d)
    return {"PATH": ":".join(seen), "FDE_COACH_HOME": str(paths.root), "LANG": "en_US.UTF-8", "PYTHONUNBUFFERED": "1"}


def build_plists(cfg: Dict[str, Any], paths: Paths, python: str = "") -> Dict[str, Dict[str, Any]]:
    python = python or sys.executable
    hour, minute = parse_hhmm(cfg.get("daily_time", "05:30"))
    common = {
        "EnvironmentVariables": _env(cfg, paths),
        "ProcessType": "Interactive",
        "LimitLoadToSessionType": "Aqua",
        "WorkingDirectory": str(paths.root),
    }
    daily = dict(common)
    daily.update({
        "Label": DAILY_LABEL,
        "ProgramArguments": [python, str(ENTRY_SCRIPT), "daily"],
        "StartCalendarInterval": {"Hour": hour, "Minute": minute},
        "RunAtLoad": False,
        "StandardOutPath": str(paths.logs / "daily.out.log"),
        "StandardErrorPath": str(paths.logs / "daily.err.log"),
    })
    remind = dict(common)
    remind.update({
        "Label": REMIND_LABEL,
        "ProgramArguments": [python, str(ENTRY_SCRIPT), "remind"],
        "StartInterval": REMIND_INTERVAL,
        "RunAtLoad": True,
        "StandardOutPath": str(paths.logs / "reminder.out.log"),
        "StandardErrorPath": str(paths.logs / "reminder.err.log"),
    })
    pron_hour, pron_minute = parse_hhmm(cfg.get("pronunciation", {}).get("daily_time", "05:45"))
    pron = dict(common)
    pron.update({
        "Label": PRON_LABEL,
        "ProgramArguments": [python, str(ENTRY_SCRIPT), "pronounce", "daily"],
        "StartCalendarInterval": {"Hour": pron_hour, "Minute": pron_minute},
        "RunAtLoad": False,
        "StandardOutPath": str(paths.logs / "pronounce.out.log"),
        "StandardErrorPath": str(paths.logs / "pronounce.err.log"),
    })
    leg_hour, leg_minute = parse_hhmm(cfg.get("legato", {}).get("daily_time", "06:00"))
    leg = dict(common)
    leg.update({
        "Label": LEGATO_LABEL,
        "ProgramArguments": [python, str(ENTRY_SCRIPT), "legato", "daily"],
        "StartCalendarInterval": {"Hour": leg_hour, "Minute": leg_minute},
        "RunAtLoad": False,
        "StandardOutPath": str(paths.logs / "legato.out.log"),
        "StandardErrorPath": str(paths.logs / "legato.err.log"),
    })
    learn_hour, learn_minute = parse_hhmm(cfg.get("learn", {}).get("drop_time", "05:50"))
    learn = dict(common)
    learn.update({
        "Label": LEARN_LABEL,
        "ProgramArguments": [python, str(ENTRY_SCRIPT), "learn", "drop", "--scheduled"],
        "StartCalendarInterval": {"Hour": learn_hour, "Minute": learn_minute},
        "RunAtLoad": False,
        "StandardOutPath": str(paths.logs / "learn.out.log"),
        "StandardErrorPath": str(paths.logs / "learn.err.log"),
    })
    stage = dict(common)
    stage.update({
        "Label": STAGE_LABEL,
        "ProgramArguments": [python, str(ENTRY_SCRIPT), "stage", "daily"],
        "StartCalendarInterval": stage_intervals(cfg),
        "RunAtLoad": False,
        "StandardOutPath": str(paths.logs / "stage.out.log"),
        "StandardErrorPath": str(paths.logs / "stage.err.log"),
    })
    return {DAILY_LABEL: daily, REMIND_LABEL: remind, PRON_LABEL: pron, LEGATO_LABEL: leg, LEARN_LABEL: learn,
            STAGE_LABEL: stage}


def _launchctl(*args: str) -> Tuple[int, str]:
    if dry_run() or not is_macos():
        return 0, "[dry-run] launchctl " + " ".join(args)
    proc = subprocess.run(["/bin/launchctl", *args], capture_output=True, text=True)
    return proc.returncode, (proc.stdout + proc.stderr).strip()


def install(cfg: Dict[str, Any], paths: Paths, python: str = "") -> List[str]:
    out: List[str] = []
    target = agents_dir()
    target.mkdir(parents=True, exist_ok=True)
    domain = f"gui/{os.getuid()}"
    for label, plist in build_plists(cfg, paths, python).items():
        path = target / f"{label}.plist"
        _launchctl("bootout", f"{domain}/{label}")
        with open(path, "wb") as fh:
            plistlib.dump(plist, fh)
        with open(path, "rb") as fh:
            plistlib.load(fh)  # round-trip validation
        code, msg = _launchctl("bootstrap", domain, str(path))
        out.append(f"{label}: {'loaded' if code == 0 else 'load failed: ' + msg} ({path})")
    return out


def uninstall() -> List[str]:
    out: List[str] = []
    domain = f"gui/{os.getuid()}"
    for label in ALL_LABELS:
        _launchctl("bootout", f"{domain}/{label}")
        path = agents_dir() / f"{label}.plist"
        if path.exists():
            path.unlink()
        out.append(f"{label}: removed")
    return out


def status() -> Dict[str, bool]:
    result = {}
    for label in ALL_LABELS:
        code, _ = _launchctl("print", f"gui/{os.getuid()}/{label}")
        result[label] = code == 0 and (agents_dir() / f"{label}.plist").exists()
    return result


def kickstart(label: str) -> None:
    _launchctl("kickstart", f"gui/{os.getuid()}/{label}")
