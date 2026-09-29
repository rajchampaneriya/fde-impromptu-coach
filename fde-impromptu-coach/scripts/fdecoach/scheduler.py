"""launchd LaunchAgents: the daily 05:30 run and a 15-minute reminder/self-heal tick."""
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
REMIND_INTERVAL = 900


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
    return {DAILY_LABEL: daily, REMIND_LABEL: remind, PRON_LABEL: pron}


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
    for label in (DAILY_LABEL, REMIND_LABEL, PRON_LABEL):
        _launchctl("bootout", f"{domain}/{label}")
        path = agents_dir() / f"{label}.plist"
        if path.exists():
            path.unlink()
        out.append(f"{label}: removed")
    return out


def status() -> Dict[str, bool]:
    result = {}
    for label in (DAILY_LABEL, REMIND_LABEL, PRON_LABEL):
        code, _ = _launchctl("print", f"gui/{os.getuid()}/{label}")
        result[label] = code == 0 and (agents_dir() / f"{label}.plist").exists()
    return result


def kickstart(label: str) -> None:
    _launchctl("kickstart", f"gui/{os.getuid()}/{label}")
