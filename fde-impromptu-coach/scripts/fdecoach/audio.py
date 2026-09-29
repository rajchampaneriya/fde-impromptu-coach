"""Audio clean-up with ffmpeg before the pronunciation video is assembled.

Presets:
  light — gentle noise reduction + loudness normalisation (safe default)
  none  — copy the audio through unchanged
"""
from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path
from typing import Optional

log = logging.getLogger("fdecoach")


def ffmpeg_path() -> Optional[str]:
    return shutil.which("ffmpeg")


def has_ffmpeg() -> bool:
    return ffmpeg_path() is not None


def audio_duration_seconds(path: Path) -> Optional[float]:
    """ffprobe-free duration read (ffprobe ships with ffmpeg)."""
    probe = shutil.which("ffprobe")
    if not probe or not path.exists():
        return None
    try:
        out = subprocess.run(
            [probe, "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1",
             str(path)], capture_output=True, text=True, timeout=30).stdout.strip()
        return float(out) if out else None
    except (ValueError, subprocess.TimeoutExpired):
        return None


def clean(src: Path, dest: Path, preset: str = "light") -> Optional[Path]:
    """Write the cleaned audio to dest. Returns dest, or None when ffmpeg is
    missing/unavailable (callers keep the original file in that case)."""
    exe = ffmpeg_path()
    if not exe:
        log.warning("ffmpeg not found; skipping audio clean-up (%s kept as-is)", src.name)
        return None
    if preset in ("", "none"):
        return src
    dest.parent.mkdir(parents=True, exist_ok=True)
    filters = {
        "light": "afftdn=nr=12:nf=-25,loudnorm=I=-16:TP=-1.5:LRA=11",
    }.get(preset, "anull")
    cmd = [exe, "-y", "-i", str(src), "-af", filters, "-c:a", "aac", "-b:a", "192k", str(dest)]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if proc.returncode != 0 or not dest.exists() or dest.stat().st_size == 0:
        log.warning("audio clean-up failed (%s): %s", preset, (proc.stderr or "")[-300:])
        return None
    log.info("audio clean-up (%s): %s -> %s", preset, src.name, dest.name)
    return dest
