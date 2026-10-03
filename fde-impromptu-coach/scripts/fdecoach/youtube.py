"""Private YouTube upload via the YouTube Data API v3 (scope: youtube.upload only)."""
from __future__ import annotations

import json
import logging
import os
import random
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .config import Paths

log = logging.getLogger("fdecoach")

SCOPES = ["https://www.googleapis.com/auth/youtube.upload",
          "https://www.googleapis.com/auth/youtube.force-ssl"]  # force-ssl: thumbnails.set
RETRIABLE_STATUS = {500, 502, 503, 504}


class YouTubeNotConfigured(RuntimeError):
    pass


class YouTubeAuthExpired(RuntimeError):
    pass


def _libs() -> None:
    """Fail with a clear message when the Google client libraries are not installed."""
    import importlib

    for mod in ("google.auth.exceptions", "google.auth.transport.requests", "google.oauth2.credentials",
                "google_auth_oauthlib.flow", "googleapiclient.discovery", "googleapiclient.errors",
                "googleapiclient.http"):
        try:
            importlib.import_module(mod)
        except ImportError as exc:
            raise YouTubeNotConfigured(f"Google API libraries missing ({exc}); re-run install.sh") from exc


def is_configured(paths: Paths) -> bool:
    return paths.youtube_token.exists()


def authorize(paths: Paths) -> str:
    _libs()
    from google_auth_oauthlib.flow import InstalledAppFlow

    if not paths.client_secret.exists():
        raise YouTubeNotConfigured(
            f"Put your OAuth client file at {paths.client_secret} (see README: YouTube setup)")
    flow = InstalledAppFlow.from_client_secrets_file(str(paths.client_secret), SCOPES)
    creds = flow.run_local_server(port=0, prompt="consent", access_type="offline", open_browser=True)
    paths.youtube_token.write_text(creds.to_json(), encoding="utf-8")
    os.chmod(paths.youtube_token, 0o600)
    return "YouTube authorized. Tokens saved."


def _credentials(paths: Paths):
    _libs()
    from google.auth.exceptions import RefreshError
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials

    if not paths.youtube_token.exists():
        raise YouTubeNotConfigured("YouTube not authorized yet: run `fde-coach youtube-auth`")
    creds = Credentials.from_authorized_user_file(str(paths.youtube_token), SCOPES)
    if not creds.valid:
        if not creds.refresh_token:
            raise YouTubeAuthExpired("No refresh token; run `fde-coach youtube-auth` again")
        try:
            creds.refresh(Request())
        except RefreshError as exc:
            raise YouTubeAuthExpired(
                "YouTube authorization expired or was revoked. If this happens weekly, your Google OAuth app "
                "is still in 'Testing' mode: publish it, then run `fde-coach youtube-auth`.") from exc
        paths.youtube_token.write_text(creds.to_json(), encoding="utf-8")
    return creds


def _clean(text: str, limit: int) -> str:
    text = text.replace("<", "").replace(">", "")
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "\u2026"


def _ts(seconds: int) -> str:
    m, s = divmod(max(0, int(seconds)), 60)
    return f"{m}:{s:02d}"


def build_metadata(session: Dict[str, Any], cfg: Dict[str, Any], marks: Optional[List[Tuple[int, str]]],
                   streak: int) -> Dict[str, Any]:
    yt = cfg.get("youtube", {})
    title = yt.get("title_template", "FDE Impromptu \u00b7 Day {day} \u00b7 {date}").format(
        day=session.get("day_number", "?"), date=session["date"])
    lines = [
        f"Daily impromptu practice \u2014 {cfg.get('role', 'Forward Deployed Engineer')} communication and leadership.",
        f"Level {session.get('level')}/5 \u00b7 Streak {streak} day{'s' if streak != 1 else ''} \u00b7 "
        f"{len(session['questions'])} questions \u00d7 {cfg.get('seconds_per_question', 60)} s",
        "",
    ]
    if marks:
        lines += [f"{_ts(t)} {_clean(label, 90)}" for t, label in marks]
        lines.append("")
    lines.append("Questions")
    for i, q in enumerate(session["questions"], 1):
        lines.append(f"{i}. [{q.get('category_label', '')} \u00b7 D{q.get('difficulty')}] {q['text']}")
        if q.get("constraint"):
            lines.append(f"   Constraint: {q['constraint']}")
    lines += ["", "Self-review: clear point in 10 s \u00b7 one concrete example \u00b7 calm pace \u00b7 clean ending."]
    return {
        "snippet": {
            "title": _clean(title, 100),
            "description": _clean("\n".join(lines), 4900),
            "tags": list(yt.get("tags", []))[:15],
            "categoryId": str(yt.get("category_id", "27")),
        },
        "status": {
            "privacyStatus": yt.get("privacy_status", "private"),
            "selfDeclaredMadeForKids": False,
        },
    }


def upload(paths: Paths, video: Path, metadata: Dict[str, Any], thumbnail: Optional[Path] = None) -> str:
    """Resumable upload with retries. Returns the YouTube video id."""
    if os.environ.get("FDE_COACH_DRYRUN") == "1":
        log.info("[dry-run] YouTube upload %s: %s", video.name, metadata["snippet"]["title"])
        return "DRYRUN" + str(int(time.time()))[-5:]
    creds = _credentials(paths)
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    from googleapiclient.http import MediaFileUpload

    service = build("youtube", "v3", credentials=creds, cache_discovery=False)
    mimetype = "video/quicktime" if video.suffix.lower() == ".mov" else "video/mp4"
    media = MediaFileUpload(str(video), chunksize=8 * 1024 * 1024, resumable=True, mimetype=mimetype)
    request = service.videos().insert(part="snippet,status", body=metadata, media_body=media)
    response = None
    retry = 0
    while response is None:
        try:
            status, response = request.next_chunk()
            if status:
                log.info("YouTube upload %d%%", int(status.progress() * 100))
        except HttpError as exc:
            if exc.resp.status in RETRIABLE_STATUS and retry < 8:
                retry += 1
                time.sleep(min(64, 2 ** retry) + random.random())
                continue
            detail = exc.content.decode("utf-8", "ignore")[:300] if getattr(exc, "content", None) else str(exc)
            raise RuntimeError(f"YouTube API error {exc.resp.status}: {detail}") from exc
        except (OSError, ConnectionError):
            if retry < 8:
                retry += 1
                time.sleep(min(64, 2 ** retry) + random.random())
                continue
            raise
    if "id" not in response:
        raise RuntimeError(f"Unexpected upload response: {json.dumps(response)[:300]}")
    if thumbnail and Path(thumbnail).exists():
        try:  # custom thumbnails need a phone-verified channel; skip gracefully
            from googleapiclient.http import MediaFileUpload
            service.thumbnails().set(
                videoId=response["id"],
                media_body=MediaFileUpload(str(thumbnail), mimetype="image/png")).execute()
            log.info("YouTube thumbnail set from %s", thumbnail)
        except Exception as exc:  # noqa: BLE001 - thumbnail is cosmetic, never fail the upload
            log.warning("YouTube thumbnail not set (%s); channel may need phone verification", exc)
    return response["id"]


def add_to_playlist(paths: Paths, video_id: str, playlist_id: str) -> bool:
    """Best-effort: a failed playlist add never fails the upload."""
    if os.environ.get("FDE_COACH_DRYRUN") == "1":
        log.info("[dry-run] playlist add %s -> %s", video_id, playlist_id)
        return True
    try:
        from googleapiclient.discovery import build
        service = build("youtube", "v3", credentials=_credentials(paths), cache_discovery=False)
        service.playlistItems().insert(part="snippet", body={
            "snippet": {"playlistId": playlist_id, "resourceId": {"kind": "youtube#video", "videoId": video_id}}
        }).execute()
        log.info("Added %s to playlist %s", video_id, playlist_id)
        return True
    except Exception as exc:  # noqa: BLE001
        log.warning("Playlist add failed (%s); check youtube.pronunciation_playlist_id", exc)
        return False
