"""One-time upgrade of the learner's legato and pronunciation state (state version 1 -> 2) for the
shared passage history, the passage-feedback flags and the legato prompt bank.

Run by `fde-coach migrate` and by `fde-coach setup` (so install.sh does it). Safe to run any number
of times: it acts only on a state file below version 2, copies each file it changes into
~/FDE-Impromptu/state.backup-<YYYYmmdd-HHMMSS>/ first, and only ever adds fields. No session is
removed or rewritten, so the old code still reads the new files.
"""
from __future__ import annotations

import json
import logging
import shutil
from typing import Any, Dict, List

from .config import Paths, save_config
from .legato import prompt_bank
from .state import History, file_lock, now

log = logging.getLogger("fdecoach")

STATE_VERSION = 2
NO_AUDIO_TREATMENT = ("legato", "pronunciation")


def migrate(paths: Paths) -> Dict[str, Any]:
    report: Dict[str, Any] = {"migrated": False, "backup": None, "changes": []}
    with file_lock(paths, "history", blocking=True):
        legato = History(paths, file=paths.legato_state)
        pron = History(paths, file=paths.pron_state)
        todo: List[History] = [h for h in (legato, pron)
                               if h.file.exists() and int(h.data.get("version", 1)) < STATE_VERSION]
        if not todo:
            return report
        if any(h.sessions for h in todo):
            backup = paths.root / f"state.backup-{now().strftime('%Y%m%d-%H%M%S')}"
            backup.mkdir(parents=True, exist_ok=True)
            for h in todo:
                shutil.copy2(h.file, backup / h.file.name)
            report["backup"] = str(backup)
        if legato in todo:
            report["changes"] += _legato(legato)
        for h in todo:
            h.data["version"] = STATE_VERSION
            h.save()
        report["changes"] += _no_audio_treatment(paths)
        report["migrated"] = True
    log.info("Migrated state to version %d: %s", STATE_VERSION, "; ".join(report["changes"]) or "version only")
    return report


def _legato(history: History) -> List[str]:
    changes = []
    ids = {p["text"]: p["id"] for p in prompt_bank()}
    named = 0
    for s in history.sessions.values():
        pid = ids.get(s.get("response_prompt", ""))
        if pid and not s.get("response_prompt_id"):
            s["response_prompt_id"] = pid
            named += 1
    if named:
        changes.append(f"{named} legato sessions got a response_prompt_id")
    leveled = [(k, s) for k, s in sorted(history.sessions.items()) if s.get("flow_level")]
    if leveled and not history.data.get("flow"):
        key, last = leveled[-1]
        history.data["flow"] = {"level": int(last["flow_level"]), "since": key}
        changes.append(f"flow level {last['flow_level']} kept from {key}")
    return changes


def _no_audio_treatment(paths: Paths) -> List[str]:
    """Legato and pronunciation take no audio clean-up: switch an explicit preset to "none"."""
    if not paths.config.exists():
        return []
    try:
        user = json.loads(paths.config.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    changes = []
    for key in NO_AUDIO_TREATMENT:
        section = user.get(key)
        if isinstance(section, dict) and section.get("audio_clean_preset", "none") != "none":
            changes.append(f"{key}.audio_clean_preset {section['audio_clean_preset']} -> none")
            section["audio_clean_preset"] = "none"
    if changes:
        save_config(paths, user)
    return changes
