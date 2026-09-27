"""History, streaks, difficulty level, runtime state and inter-process locks."""
from __future__ import annotations

import contextlib
import datetime as dt
import fcntl
import json
import os
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

from .config import Paths


def today() -> dt.date:
    override = os.environ.get("FDE_COACH_TODAY")
    if override:
        return dt.date.fromisoformat(override)
    if os.environ.get("FDE_COACH_NOW"):
        return now().date()
    return dt.date.today()


def now() -> dt.datetime:
    override = os.environ.get("FDE_COACH_NOW")
    if override:
        return dt.datetime.fromisoformat(override)
    return dt.datetime.now()


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        backup = path.with_suffix(path.suffix + ".corrupt")
        try:
            path.replace(backup)
        except OSError:
            pass
        return default


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, path)


# --------------------------------------------------------------------------- locks

class LockBusy(RuntimeError):
    pass


@contextlib.contextmanager
def file_lock(paths: Paths, name: str, blocking: bool = False) -> Iterator[None]:
    paths.ensure()
    lock_path = paths.locks / f"{name}.lock"
    fh = open(lock_path, "a+")
    try:
        flags = fcntl.LOCK_EX if blocking else fcntl.LOCK_EX | fcntl.LOCK_NB
        try:
            fcntl.flock(fh.fileno(), flags)
        except BlockingIOError as exc:
            raise LockBusy(name) from exc
        fh.seek(0)
        fh.truncate()
        fh.write(str(os.getpid()))
        fh.flush()
        yield
    finally:
        try:
            fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
        finally:
            fh.close()


def lock_is_held(paths: Paths, name: str) -> bool:
    try:
        with file_lock(paths, name):
            return False
    except LockBusy:
        return True


# --------------------------------------------------------------------------- history

class History:
    """sessions keyed by ISO date. A session is 'recorded' once a video is saved."""

    def __init__(self, paths: Paths):
        self.paths = paths
        self.data: Dict[str, Any] = _read_json(paths.history, {"version": 1, "sessions": {}})
        self.data.setdefault("sessions", {})

    def save(self) -> None:
        # Embed the computed streak so raw readers of history.json see the
        # same numbers the CLI reports (unrecorded days never count).
        snapshot = streaks(self)
        snapshot["as_of"] = today().isoformat()
        self.data["streak"] = snapshot
        _write_json(self.paths.history, self.data)

    @property
    def sessions(self) -> Dict[str, Dict[str, Any]]:
        return self.data["sessions"]

    def get(self, date: dt.date) -> Optional[Dict[str, Any]]:
        return self.sessions.get(date.isoformat())

    def put(self, session: Dict[str, Any]) -> None:
        self.sessions[session["date"]] = session

    def remove(self, date: dt.date) -> None:
        self.sessions.pop(date.isoformat(), None)

    def recorded_dates(self) -> List[dt.date]:
        return sorted(dt.date.fromisoformat(k) for k, s in self.sessions.items() if s.get("recorded"))

    def completed_before(self, date: dt.date) -> int:
        return sum(1 for d in self.recorded_dates() if d < date)

    def all_questions(self, exclude_date: Optional[dt.date] = None) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        for key in sorted(self.sessions):
            if exclude_date and key == exclude_date.isoformat():
                continue
            for q in self.sessions[key].get("questions", []):
                item = dict(q)
                item["date"] = key
                out.append(item)
        return out

    def category_counts(self, exclude_date: Optional[dt.date] = None) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for q in self.all_questions(exclude_date):
            counts[q.get("category", "")] = counts.get(q.get("category", ""), 0) + 1
        return counts

    def pending_uploads(self) -> List[Dict[str, Any]]:
        out = []
        for key in sorted(self.sessions):
            s = self.sessions[key]
            yt = s.get("youtube") or {}
            if s.get("recorded") and s.get("video_path") and yt.get("status") in ("pending", "failed"):
                out.append(s)
        return out


def streaks(history: History, on: Optional[dt.date] = None) -> Dict[str, Any]:
    """current: consecutive recorded days ending today, or ending yesterday if today
    is not recorded yet (the streak is still alive until midnight)."""
    on = on or today()
    days = set(history.recorded_dates())
    cursor = on if on in days else on - dt.timedelta(days=1)
    current = 0
    while cursor in days:
        current += 1
        cursor -= dt.timedelta(days=1)
    best = run = 0
    prev: Optional[dt.date] = None
    for d in sorted(days):
        run = run + 1 if prev and d - prev == dt.timedelta(days=1) else 1
        best = max(best, run)
        prev = d
    yesterday = on - dt.timedelta(days=1)
    broken = bool(days) and on not in days and yesterday not in days and current == 0
    return {
        "current": current,
        "best": best,
        "total": len(days),
        "recorded_today": on in days,
        "broken": broken,
    }


def level_for(history: History, cfg: Dict[str, Any], runtime: "Runtime", on: Optional[dt.date] = None) -> int:
    on = on or today()
    done = history.completed_before(on)
    base = int(cfg.get("start_level", 2)) + done // max(1, int(cfg.get("sessions_per_level", 6)))
    adjust = int(runtime.data.get("level_adjust", 0))
    return max(1, min(5, base + adjust))


def difficulty_curve(level: int, n: int) -> List[int]:
    offsets = [0, 0, 1, 1, 2]
    while len(offsets) < n:
        offsets.append(offsets[-1])
    return [max(1, min(5, level + o)) for o in offsets[:n]]


# --------------------------------------------------------------------------- runtime

class Runtime:
    """Small mutable state: reminder bookkeeping, snooze, calibration."""

    def __init__(self, paths: Paths):
        self.paths = paths
        self.data: Dict[str, Any] = _read_json(paths.runtime, {})

    def save(self) -> None:
        _write_json(self.paths.runtime, self.data)

    def fired_today(self, date: dt.date) -> List[str]:
        fired = self.data.setdefault("reminders_fired", {})
        for key in list(fired):
            if key < (date - dt.timedelta(days=7)).isoformat():
                fired.pop(key)
        return fired.setdefault(date.isoformat(), [])

    def snooze_until(self) -> Optional[dt.datetime]:
        raw = self.data.get("snooze_until")
        return dt.datetime.fromisoformat(raw) if raw else None

    def set_snooze(self, until: Optional[dt.datetime]) -> None:
        self.data["snooze_until"] = until.isoformat(timespec="seconds") if until else None
