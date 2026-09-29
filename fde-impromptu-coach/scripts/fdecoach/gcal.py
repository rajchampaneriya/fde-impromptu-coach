"""Google Calendar "missed practice" notifications.

Each upcoming day gets a safety-net event in Google Calendar with its own alerts
(popup and email). Recording a day deletes that day's event, so the alerts only
reach you when you have missed the practice. Because the events for the next
days already live in Google Calendar, the alerts still arrive on your phone,
browser or email when the Mac is closed or off.

Scope: calendar.events only (create/delete events; no reading of other events).
"""
from __future__ import annotations

import datetime as dt
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Tuple

from .config import Paths, parse_hhmm

log = logging.getLogger("fdecoach")

SCOPES = ["https://www.googleapis.com/auth/calendar.events"]
ID_PREFIX = "fdecoach"  # event ids may only use a-v and 0-9
MAX_OVERRIDES = 5       # Google Calendar limit for reminder overrides per event
MAX_MINUTES = 40320


class CalendarNotConfigured(RuntimeError):
    pass


class CalendarAuthExpired(RuntimeError):
    pass


def _dry_run() -> bool:
    return os.environ.get("FDE_COACH_DRYRUN") == "1"


def token_path(paths: Paths) -> Path:
    return paths.secrets / "calendar_token.json"


def is_configured(paths: Paths) -> bool:
    return token_path(paths).exists()


def event_id(date: dt.date, prefix: str = ID_PREFIX) -> str:
    return f"{prefix}{date.strftime('%Y%m%d')}"


# --------------------------------------------------------------------------- auth

def authorize(paths: Paths) -> str:
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError as exc:
        raise CalendarNotConfigured(f"Google libraries missing ({exc}); re-run install.sh") from exc
    if not paths.client_secret.exists():
        raise CalendarNotConfigured(
            f"Put your OAuth client file at {paths.client_secret} (see README: Google setup)")
    flow = InstalledAppFlow.from_client_secrets_file(str(paths.client_secret), SCOPES)
    creds = flow.run_local_server(port=0, prompt="consent", access_type="offline", open_browser=True)
    token_path(paths).write_text(creds.to_json(), encoding="utf-8")
    os.chmod(token_path(paths), 0o600)
    return "Google Calendar connected."


def _credentials(paths: Paths):
    try:
        from google.auth.exceptions import RefreshError
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
    except ImportError as exc:
        raise CalendarNotConfigured(f"Google libraries missing ({exc}); re-run install.sh") from exc
    if not is_configured(paths):
        raise CalendarNotConfigured("Google Calendar not connected yet: run `fde-coach calendar-auth`")
    creds = Credentials.from_authorized_user_file(str(token_path(paths)), SCOPES)
    if not creds.valid:
        if not creds.refresh_token:
            raise CalendarAuthExpired("No refresh token; run `fde-coach calendar-auth` again")
        try:
            creds.refresh(Request())
        except RefreshError as exc:
            raise CalendarAuthExpired(
                "Google Calendar authorization expired or was revoked. If this happens weekly, your Google "
                "OAuth app is still in 'Testing': publish it, then run `fde-coach calendar-auth`.") from exc
        token_path(paths).write_text(creds.to_json(), encoding="utf-8")
    return creds


def _service(paths: Paths):
    import google_auth_httplib2
    import httplib2
    from googleapiclient.discovery import build

    http = google_auth_httplib2.AuthorizedHttp(_credentials(paths), http=httplib2.Http(timeout=30))
    return build("calendar", "v3", http=http, cache_discovery=False)


# --------------------------------------------------------------------------- event

def _local(date: dt.date, hhmm: str) -> dt.datetime:
    h, m = parse_hhmm(hhmm)
    return dt.datetime.combine(date, dt.time(h, m)).astimezone()  # local time zone, DST-aware


def event_window(date: dt.date, cfg: Dict[str, Any]) -> Tuple[dt.datetime, dt.datetime]:
    gc = cfg.get("google_calendar", {})
    start = _local(date, gc.get("event_time", "21:30"))
    return start, start + dt.timedelta(minutes=int(gc.get("event_minutes", 15)))


def alert_overrides(date: dt.date, cfg: Dict[str, Any]) -> List[Dict[str, Any]]:
    """popup_times / email_times (clock times on that day) as minutes before the event start."""
    gc = cfg.get("google_calendar", {})
    start, _ = event_window(date, cfg)
    out: List[Dict[str, Any]] = []
    for method, key in (("popup", "popup_times"), ("email", "email_times")):
        for hhmm in gc.get(key) or []:
            minutes = int((start - _local(date, hhmm)).total_seconds() // 60)
            item = {"method": method, "minutes": minutes}
            if 0 <= minutes <= MAX_MINUTES and item not in out:
                out.append(item)
            elif minutes < 0:
                log.warning("google_calendar.%s %s is after event_time; ignored", key, hhmm)
    if len(out) > MAX_OVERRIDES:
        log.warning("Google Calendar allows %d alerts per event; keeping the first %d", MAX_OVERRIDES, MAX_OVERRIDES)
    return out[:MAX_OVERRIDES]


def build_event(date: dt.date, cfg: Dict[str, Any], streak: int) -> Dict[str, Any]:
    gc = cfg.get("google_calendar", {})
    start, end = event_window(date, cfg)
    streak_line = (f"Your streak when this was scheduled: {streak} day{'s' if streak != 1 else ''}."
                   if streak else "Record today to start a new streak.")
    description = (
        "You haven't recorded today's 5-minute FDE impromptu practice yet.\n\n"
        "On your Mac: double-click 'Start Practice' in the FDE-Impromptu folder in your home folder, "
        "or tell Claude Code: start my FDE practice.\n\n"
        f"{streak_line}\n\n"
        "This event only exists while the day is unrecorded: recording deletes it automatically, "
        "so its alerts reach you only when you miss the practice.\n"
        "Created by FDE Impromptu Coach."
    )
    return {
        "id": event_id(date),
        "summary": gc.get("title", "FDE practice not recorded yet \u2014 record now to keep your streak"),
        "description": description,
        "start": {"dateTime": start.isoformat()},
        "end": {"dateTime": end.isoformat()},
        "reminders": {"useDefault": False, "overrides": alert_overrides(date, cfg)},
        "colorId": str(gc.get("color_id", "11")),
        "transparency": "transparent",   # does not block your free/busy time
        "visibility": "private",
        "extendedProperties": {"private": {"fdecoach": date.isoformat()}},
    }


# --------------------------------------------------------------------------- dry-run store (tests)

def _dry_store(paths: Paths) -> Path:
    return paths.state_dir / "dryrun_calendar.json"


def _dry_update(paths: Paths, eid: str, status: str, body: Any = None) -> None:
    path = _dry_store(paths)
    data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    entry = data.get(eid, {})
    entry["status"] = status
    if body is not None:
        entry["body"] = body
    data[eid] = entry
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


# --------------------------------------------------------------------------- API calls

def ensure_event(paths: Paths, calendar_id: str, body: Dict[str, Any]) -> str:
    """Create the event (or restore/refresh it if its id already exists). Returns 'created' or 'updated'."""
    if _dry_run():
        log.info("[dry-run] calendar create %s at %s", body["id"], body["start"]["dateTime"])
        _dry_update(paths, body["id"], "confirmed", body)
        return "created"
    from googleapiclient.errors import HttpError

    service = _service(paths)
    try:
        service.events().insert(calendarId=calendar_id, body=body, sendUpdates="none").execute()
        return "created"
    except HttpError as exc:
        if exc.resp.status != 409:  # 409 = id exists (possibly a previously deleted event)
            raise
    service.events().update(calendarId=calendar_id, eventId=body["id"],
                            body=dict(body, status="confirmed"), sendUpdates="none").execute()
    return "updated"


def delete_event(paths: Paths, calendar_id: str, eid: str) -> str:
    if _dry_run():
        log.info("[dry-run] calendar delete %s", eid)
        _dry_update(paths, eid, "cancelled")
        return "deleted"
    from googleapiclient.errors import HttpError

    try:
        _service(paths).events().delete(calendarId=calendar_id, eventId=eid, sendUpdates="none").execute()
        return "deleted"
    except HttpError as exc:
        if exc.resp.status in (404, 410):
            return "already gone"
        raise
