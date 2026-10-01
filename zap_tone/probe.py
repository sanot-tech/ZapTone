"""
🔎 probe.py - ask ffmpeg/ffprobe about a video file.

Why a separate file: reading metadata is slow (it starts a process),
so we keep it in one place and cache results. This way the GUI can
ask the same question many times without paying for it twice.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from functools import lru_cache

from . import VIDEO_SUFFIXES

# 🪟 This flag makes ffprobe quiet. We do not want its noise in the GUI.
_PROBE_QUIET = ["-v", "error"]

# ⏱️ Timeout for every ffprobe call. A slow network disk must not freeze the app.
_PROBE_TIMEOUT = 30


class ToolMissing(RuntimeError):
    """❌ ffmpeg or ffprobe is not installed on this computer."""


def check_tools() -> tuple[str, str]:
    """🔧 Find ffmpeg and ffprobe. Raises ToolMissing with a clear message."""
    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    if not ffmpeg or not ffprobe:
        raise ToolMissing(
            "ffmpeg is not installed.\n"
            "Arch / CachyOS:  sudo pacman -S ffmpeg\n"
            "Ubuntu / Debian:  sudo apt install ffmpeg\n"
            "macOS:            brew install ffmpeg\n"
            "Windows:          winget install Gyan.FFmpeg"
        )
    return ffmpeg, ffprobe


def ffmpeg_bin() -> str:
    """📍 Path to ffmpeg, or just the name if we cannot find it.

    Why this is different from check_tools(): we use it while BUILDING a
    command line, and building a command must work on a computer without
    ffmpeg. Our tests rely on that, and CI runners have no ffmpeg either.
    The real check happens in convert_job(), right before we run it.
    """
    return shutil.which("ffmpeg") or "ffmpeg"


@lru_cache(maxsize=4096)
def probe_json(path: str) -> dict:
    """📦 Read all stream info as JSON. Cached, because it never changes for a file."""
    _, ffprobe = check_tools()
    cmd = [
        ffprobe, *_PROBE_QUIET,
        "-print_format", "json",
        "-show_format", "-show_streams",
        path,
    ]
    # 🛡️ errors="replace" - a broken filename must not crash the whole app
    try:
        raw = subprocess.run(
            cmd, capture_output=True, text=True,
            timeout=_PROBE_TIMEOUT, errors="replace",
        ).stdout
        return json.loads(raw or "{}")
    except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError):
        # 🧹 bad file or strange disk - return empty info instead of dying
        return {}


def duration(path: str) -> float:
    """⏱️ Length of the video in seconds. 0.0 when we cannot read it."""
    info = probe_json(path)
    raw = info.get("format", {}).get("duration")
    try:
        return float(raw)
    except (TypeError, ValueError):
        return 0.0


def has_audio(path: str) -> bool:
    """🎤 True if the file has at least one audio track (needed for MP3)."""
    return any(s.get("codec_type") == "audio" for s in probe_json(path).get("streams", []))


def audio_stream_index(path: str) -> int:
    """🎧 Index of the first audio track. -1 when there is no audio."""
    for i, s in enumerate(probe_json(path).get("streams", [])):
        if s.get("codec_type") == "audio":
            return i
    return -1


def video_size(path: str) -> tuple[int, int]:
    """📐 Width and height of the video track. (0, 0) if it is audio only."""
    for s in probe_json(path).get("streams", []):
        if s.get("codec_type") == "video":
            return int(s.get("width") or 0), int(s.get("height") or 0)
    return 0, 0


def source_tags(path: str) -> dict[str, str]:
    """🏷️ Human tags from the container (title, artist, album...).

    We drop technical junk like major_brand or encoder, because
    it looks ugly in music players.
    """
    # 📋 only tags a person actually wants to see in a player
    wanted = (
        "title", "artist", "album", "album_artist", "date", "genre",
        "composer", "performer", "copyright", "comment", "disc", "track",
    )
    info = probe_json(path)
    out: dict[str, str] = {}
    # 🔎 look in stream tags first, then container tags (better quality)
    sources = [s.get("tags", {}) for s in info.get("streams", []) if s.get("codec_type") == "audio"]
    sources.append(info.get("format", {}).get("tags", {}))
    for source in sources:
        for key in wanted:
            # 🧽 ffprobe uses UPPERCASE keys (TAG:title), so compare case free
            for real_key, value in source.items():
                if real_key.lower() == key and value:
                    out[key] = str(value)
    return out


def is_video_name(path: str) -> bool:
    """🧪 Same check as in __init__, kept here so callers need one import only."""
    return str(path).lower().endswith(VIDEO_SUFFIXES)


def clear_cache() -> None:
    """🧹 Forget all cached info. Call it after a file was changed on disk."""
    probe_json.cache_clear()