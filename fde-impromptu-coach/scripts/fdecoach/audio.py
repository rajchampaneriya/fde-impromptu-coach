"""Audio capture (ffmpeg avfoundation) and clean-up for the pronunciation practice.

Recording straight from an AVFoundation input device avoids QuickTime's own
input selection, which goes stale when a headset or camera is reconnected and
then records silence.

Presets:
  light — gentle noise reduction + loudness normalisation (safe default)
  none  — copy the audio through unchanged
"""
from __future__ import annotations

import logging
import os
import re
import shutil
import signal
import subprocess
import time
from pathlib import Path
from typing import List, Optional, Tuple

log = logging.getLogger("fdecoach")


def ffmpeg_path() -> Optional[str]:
    return shutil.which("ffmpeg")


def has_ffmpeg() -> bool:
    return ffmpeg_path() is not None


def avfoundation_audio_devices() -> List[Tuple[int, str]]:
    """[(index, name)] from `ffmpeg -f avfoundation -list_devices` (needs ffmpeg)."""
    exe = ffmpeg_path()
    if not exe:
        return []
    try:
        proc = subprocess.run([exe, "-f", "avfoundation", "-list_devices", "true", "-i", ""],
                              capture_output=True, text=True, timeout=30)
    except subprocess.TimeoutExpired:
        return []
    out = proc.stderr or ""
    section = out.split("AVFoundation audio devices:")[-1]
    return [(int(i), n.strip()) for i, n in
            re.findall(r"\[(\d+)\] (.+)", section.split("AVFoundation video devices:")[0])]


def resolve_audio_device(name: str) -> Optional[int]:
    """Index of the device whose name contains `name` (case-insensitive); first device otherwise."""
    devices = avfoundation_audio_devices()
    if not devices:
        return None
    if name:
        low = name.lower()
        for idx, dev in devices:
            if low in dev.lower():
                return idx
        log.warning("audio device %r not found; using %r", name, devices[0][1])
    return devices[0][0]


class AudioCapture:
    """AAC capture from an AVFoundation input until stop() (SIGINT → clean trailer)."""

    def __init__(self, dest: Path, device: str = ""):
        self.dest = dest
        self.device = device
        self.proc: Optional[subprocess.Popen] = None
        self.dry_run = os.environ.get("FDE_COACH_DRYRUN") == "1"

    def start(self, warmup: float = 1.0) -> bool:
        if self.dry_run:
            log.info("[dry-run] ffmpeg audio capture -> %s", self.dest)
            return True
        exe = ffmpeg_path()
        if not exe:
            log.warning("ffmpeg not found; cannot capture audio directly")
            return False
        idx = resolve_audio_device(self.device)
        if idx is None:
            log.warning("no AVFoundation audio input found")
            return False
        self.dest.parent.mkdir(parents=True, exist_ok=True)
        cmd = [exe, "-y", "-f", "avfoundation", "-i", f":{idx}",
               "-c:a", "aac", "-b:a", "128k", str(self.dest)]
        self.proc = subprocess.Popen(cmd, stdin=subprocess.DEVNULL,
                                     stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        time.sleep(max(0.5, warmup))
        if self.proc.poll() is not None:
            err = (self.proc.stderr.read() if self.proc.stderr else b"")[-300:]
            log.warning("ffmpeg audio capture died at once: %s", err)
            self.proc = None
            return False
        log.info("ffmpeg audio capture started (device index %d)", idx)
        return True

    def stop(self, min_bytes: int = 100_000) -> Optional[Path]:
        if self.dry_run:
            self.dest.parent.mkdir(parents=True, exist_ok=True)
            self.dest.write_bytes(b"\0" * (2 * 1024 * 1024))
            return self.dest
        if self.proc is None:
            return None
        self.proc.send_signal(signal.SIGINT)
        try:
            self.proc.wait(timeout=30)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            self.proc.wait(timeout=10)
        self.proc = None
        if self.dest.exists() and self.dest.stat().st_size >= min_bytes:
            log.info("ffmpeg audio capture saved: %s (%d bytes)", self.dest, self.dest.stat().st_size)
            return self.dest
        log.warning("ffmpeg audio capture produced no usable file: %s", self.dest)
        return None


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
