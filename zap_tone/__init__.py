"""
ZapTone - video to MP3 converter.

This module holds the version number and a few small helpers.
Every module is annotated with emojis so it is easy to read fast.
"""

# 📦 version of the whole project - keep it in ONE place only
__version__ = "0.1.0"

# 🎨 app name (used in window titles and menus)
APP_NAME = "ZapTone"

# 👋 short description for --help and for GitHub
APP_TAGLINE = "Turn any video into a clean MP3. One file, every platform."

# 🎥 all video extensions we can open - used by the file dialog and by CLI
VIDEO_EXTENSIONS = (
    "mp4", "mkv", "webm", "mov", "avi", "m4v", "mpg", "mpeg",
    "wmv", "flv", "ts", "m2ts", "3gp", "ogv", "vob", "mts",
    "rmvb", "mxf", "asf", "f4v", "divx", "mp4v",
)

# 🔧 the same list but as a set with a dot, so we can test a file name fast
VIDEO_SUFFIXES = tuple(f".{ext}" for ext in VIDEO_EXTENSIONS)


def is_video_file(path: str) -> bool:
    """🧪 True if the file name looks like a video.

    Why simple: the GUI must skip pictures and mp3 files that
    the user picked by accident. A real probe is too slow here.
    """
    return str(path).lower().endswith(VIDEO_SUFFIXES)