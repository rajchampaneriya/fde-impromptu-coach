"""Paths and configuration for FDE Impromptu Coach.

Python 3.9 compatible (macOS system Python). All user data lives outside the
skill folder so the skill can be updated without losing history.
"""
from __future__ import annotations

import copy
import json
import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Dict

SKILL_DIR = Path(__file__).resolve().parents[2]
ASSETS_DIR = SKILL_DIR / "assets"
REFERENCES_DIR = SKILL_DIR / "references"
SCRIPTS_DIR = SKILL_DIR / "scripts"
ENTRY_SCRIPT = SCRIPTS_DIR / "fde_coach.py"

APP_NAME = "FDE Impromptu Coach"
TAG = "[fde-impromptu-coach]"

DEFAULTS: Dict[str, Any] = {
    "role": "Forward Deployed Engineer",
    "learner_context": "",
    "questions_per_day": 5,
    "seconds_per_question": 60,
    "read_seconds": 0,
    "intro_seconds": 10,
    "wrap_up_cue_seconds": 45,
    "start_level": 2,
    "sessions_per_level": 6,
    "show_framework_hint_until_level": 2,
    "focus_categories": [],
    "daily_time": "05:30",
    "question_source": "auto",
    "claude_path": "",
    "claude_model": "",
    "claude_timeout_seconds": 240,
    "presentation_app": "Microsoft PowerPoint",
    "open_deck_when_ready": True,
    "prompt_to_start_at_daily_run": True,
    "ask_difficulty_feedback": True,
    "recordings_dir": "~/Movies/FDE-Impromptu",
    "keep_recordings_days": None,
    "recording": {
        "mode": "auto",
        "camera_warmup_seconds": 2,
        "stop_grace_seconds": 4,
        "min_video_seconds": 150,
    },
    "pronunciation": {
        "daily_time": "05:45",
        "prompt_after_fde": True,
        "words": [],
        "audio_device": "Brio 100",
        "focus_sounds": [],
        "intro_seconds": 10,
        "warmup_seconds": 45,
        "round1_seconds": 60,
        "round2_seconds": 75,
        "round3_seconds": 60,
        "words_seconds": 30,
        "min_audio_seconds": 180,
        "audio_clean_preset": "light",
    },
    "reminders": {
        "times": ["06:30", "07:30", "09:00", "12:30", "17:30", "19:30", "21:00", "22:00"],
        "snooze_minutes": 20,
        "quiet_after": "22:45",
        "dialog_timeout_minutes": 15,
        "use_reminders_app": True,
        "reminders_list": "FDE Practice",
        "reminders_app_due_time": "07:00",
    },
    "google_calendar": {
        "enabled": True,
        "calendar_id": "primary",
        "event_time": "21:30",
        "event_minutes": 15,
        "popup_times": ["07:30", "12:30", "18:00", "21:30"],
        "email_times": ["12:30"],
        "days_ahead": 2,
        "color_id": "11",
    },
    "youtube": {
        "enabled": True,
        "privacy_status": "private",
        "category_id": "27",
        "title_template": "FDE Impromptu \u00b7 Day {day} \u00b7 {date}",
        "tags": ["impromptu speaking", "forward deployed engineer", "communication practice"],
        "max_attempts": 12,
        "pronunciation_playlist_id": "",
    },
}


def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    out = copy.deepcopy(base)
    for key, value in (override or {}).items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = deep_merge(out[key], value)
        else:
            out[key] = value
    return out


class Paths:
    """All runtime locations. FDE_COACH_HOME overrides the data root (used in tests)."""

    def __init__(self, root: "Path | None" = None):
        root = root or Path(os.environ.get("FDE_COACH_HOME", "~/FDE-Impromptu")).expanduser()
        self.root = root
        self.config = root / "config.json"
        self.state_dir = root / "state"
        self.history = self.state_dir / "history.json"
        self.pron_state = self.state_dir / "pronunciation.json"
        self.runtime = self.state_dir / "runtime.json"
        self.incoming = self.state_dir / "incoming"
        self.locks = self.state_dir / "locks"
        self.decks = root / "decks"
        self.logs = root / "logs"
        self.secrets = root / "secrets"
        self.client_secret = self.secrets / "client_secret.json"
        self.youtube_token = self.secrets / "youtube_token.json"
        self.bin_dir = root / "bin"
        self.start_command = root / "Start Practice.command"

    def ensure(self) -> None:
        for d in (self.root, self.state_dir, self.incoming, self.locks, self.decks, self.logs, self.secrets):
            d.mkdir(parents=True, exist_ok=True)
        try:
            os.chmod(self.secrets, 0o700)
        except OSError:
            pass

    def recordings_dir(self, cfg: Dict[str, Any], create: bool = True) -> Path:
        override = os.environ.get("FDE_COACH_RECORDINGS")
        path = Path(override or cfg.get("recordings_dir") or "~/Movies/FDE-Impromptu").expanduser()
        # Read-only commands (status/doctor) pass create=False so a bad
        # recordings path degrades to a report instead of crashing.
        if create:
            path.mkdir(parents=True, exist_ok=True)
        return path


def load_config(paths: Paths) -> Dict[str, Any]:
    user: Dict[str, Any] = {}
    if paths.config.exists():
        try:
            user = json.loads(paths.config.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            logging.getLogger("fdecoach").error("config.json unreadable (%s); using defaults", exc)
    return deep_merge(DEFAULTS, user)


def save_config(paths: Paths, cfg: Dict[str, Any]) -> None:
    paths.ensure()
    tmp = paths.config.with_suffix(".tmp")
    tmp.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, paths.config)


def setup_logging(paths: Paths, verbose: bool = False) -> logging.Logger:
    paths.ensure()
    logger = logging.getLogger("fdecoach")
    if logger.handlers:
        return logger
    logger.setLevel(logging.DEBUG)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    fh = RotatingFileHandler(paths.logs / "fde_coach.log", maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    fh.setFormatter(fmt)
    fh.setLevel(logging.DEBUG)
    sh = logging.StreamHandler()
    sh.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
    sh.setLevel(logging.DEBUG if verbose else logging.INFO)
    logger.addHandler(fh)
    logger.addHandler(sh)
    return logger


def parse_hhmm(value: str) -> "tuple[int, int]":
    hh, mm = value.strip().split(":")
    h, m = int(hh), int(mm)
    if not (0 <= h < 24 and 0 <= m < 60):
        raise ValueError(f"bad time {value!r}")
    return h, m
