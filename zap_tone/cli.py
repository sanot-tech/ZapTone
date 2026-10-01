"""
⌨️ cli.py - the command line version.

This is what powers "zap_tone file.mp4" and the drag-n-drop mode.
It must stay fast to start, so we import tkinter only inside the GUI.
"""

from __future__ import annotations

import argparse
import shutil
import sys
import threading
import time
from pathlib import Path

from . import APP_NAME, APP_TAGLINE, __version__, probe
from .core import Options, run_batch

# 🪟 Windows consoles still use cp1252, which cannot print emoji.
#    Reconfiguring stdout and stderr to UTF-8 fixes the crashes, and
#    errors="replace" makes sure a strange symbol can never kill the app.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass  # 🧓 old Python, or a stream that is already fine

# 🎨 colors, but only when a real terminal is on the other side
_IS_TTY = sys.stdout.isatty()


def _c(code: str, text: str) -> str:
    """🎨 Wrap text in a color, or return it plain when there is no terminal."""
    return f"\033[{code}m{text}\033[0m" if _IS_TTY else text


GREEN = lambda t: _c("32", t)      # ✅ good
RED = lambda t: _c("31", t)        # ❌ bad
YELLOW = lambda t: _c("33", t)     # ⚠️ warning
CYAN = lambda t: _c("36", t)       # 💬 info
BOLD = lambda t: _c("1", t)        # 🖼️ title
DIM = lambda t: _c("2", t)         # 🌫️ secondary


def human_size(num: float) -> str:
    """📏 Show bytes as 12M or 1.4G. Short and easy to scan."""
    for unit in ("B", "KB", "MB", "GB"):
        if abs(num) < 1024 or unit == "GB":
            return f"{num:.0f}{unit}" if unit == "B" else f"{num:.1f}{unit}"
        num /= 1024
    return f"{num:.1f}GB"


def find_videos(inputs: list[str], recursive: bool = True) -> list[Path]:
    """🔎 Turn file names, folders and URLs into a flat list of video files."""
    from . import is_video_file

    found: list[Path] = []
    for item in inputs:
        p = Path(item).expanduser()
        if p.is_dir():
            pattern = "**/*" if recursive else "*"
            found += sorted(q for q in p.glob(pattern) if q.is_file() and is_video_file(q))
        elif p.is_file():
            found.append(p)
        elif item.startswith(("http://", "https://")):
            found.append(Path(item))          # 🌐 URL, kept as is for yt-dlp
        else:
            print(YELLOW(f"⚠️  not found: {item}"), file=sys.stderr)
    # 🧹 remove duplicates but keep the order the user gave us
    seen, unique = set(), []
    for f in found:
        key = str(f)
        if key not in seen:
            seen.add(key)
            unique.append(f)
    return unique


def download(url: str, out_dir: Path | None) -> Path | None:
    """📥 Get audio from the internet with yt-dlp, if it is installed."""
    import shutil as _sh
    import subprocess
    if not _sh.which("yt-dlp"):
        print(YELLOW(f"⚠️  yt-dlp is not installed, cannot download: {url}"), file=sys.stderr)
        return None
    temp = Path(out_dir or ".") / ".zap_tone_dl"
    temp.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["yt-dlp", "--no-playlist", "-q", "-f", "bestaudio",
         "-o", str(temp / "%(title)s.%(ext)s"), url],
        check=False,
    )
    files = sorted(temp.glob("*"))
    return files[0] if files else None


class Progress:
    """📊 A one line progress bar for a single file on a terminal."""

    WIDTH = 26          # 📏 how many blocks to draw

    def __init__(self, label: str) -> None:
        self.label = label
        self.last = 0.0

    def update(self, percent: float, force: bool = False) -> None:
        """🖍️ Draw the bar, but not more than 5 times a second (flicker is ugly)."""
        now = time.monotonic()
        if not force and now - self.last < 0.2:
            return
        self.last = now
        percent = max(0.0, min(100.0, percent))
        filled = int(self.WIDTH * percent / 100)
        bar = "█" * filled + "░" * (self.WIDTH - filled)
        # ✍️ \r returns to the line start, then we overwrite the old text
        sys.stderr.write(f"\r  🎬 {self.label[:34]:<34} {bar} {percent:3.0f}%")
        sys.stderr.flush()

    def clear(self) -> None:
        """🧽 Wipe the bar so it does not stay on screen."""
        sys.stderr.write("\r" + " " * 80 + "\r")
        sys.stderr.flush()


def print_banner(opts: Options, count: int) -> None:
    """🏷️ Show what we are going to do before starting."""
    line = f"  🎚️ {opts.quality_label}   🚿 jobs: {opts.jobs}"
    if opts.normalize:
        line += "   🔊 normalise"
    if opts.trim_silence:
        line += "   ✂️ trim silence"
    if opts.cover:
        line += "   🖼️ cover"
    if opts.delete_source:
        line += "   🗑️ delete source"
    print(f"{BOLD(f'⚡ {APP_NAME}')} {DIM(APP_TAGLINE)}")
    print(f"{line}")
    print(f"  📋 {count} file(s) found\n")


def main(argv: list[str] | None = None) -> int:
    """🚀 Entry point for the command line. Returns a process exit code."""
    parser = argparse.ArgumentParser(
        prog="zaptone",
        description=f"{APP_NAME} - {APP_TAGLINE}",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  zap_tone clip.mp4                  turn one video into MP3
  zap_tone -b 320 -c ~/Videos        320 kbps + cover art, whole folder
  zap_tone -n -t concert.mp4         normalise loudness and cut silence
  zap_tone -o ~/Music ~/Downloads    put every MP3 in one folder
  zap_tone --gui                     open the window instead of the terminal
  zap_tone --version                 show the version
""",
    )
    # 📥 what the user gives us: files, folders or links (nothing = drag-n-drop)
    parser.add_argument("inputs", nargs="*", metavar="FILE",
                        help="video files, folders, or youtube links")

    # 🎚️ sound options
    parser.add_argument("-b", "--bitrate", type=int, default=192, metavar="N",
                        help="MP3 bitrate in kbps: 96, 128, 160, 192, 256, 320 (default 192)")
    parser.add_argument("-q", "--vbr", type=int, default=None, metavar="N",
                        help="VBR quality 0-9 instead of CBR (0 is about 245 kbps)")
    parser.add_argument("-n", "--normalize", action="store_true",
                        help="make the volume even (loudnorm, -14 LUFS)")
    parser.add_argument("-t", "--trim", action="store_true",
                        help="cut silence at the start and at the end")
    parser.add_argument("-c", "--cover", action="store_true",
                        help="put one video frame into the file as cover art")
    # 📁 file options
    parser.add_argument("-o", "--out", type=Path, default=None, metavar="DIR",
                        help="folder for the MP3 files (default: next to the video)")
    parser.add_argument("-j", "--jobs", type=int, default=0, metavar="N",
                        help="how many files at the same time (default: cpu/2)")
    parser.add_argument("--no-recurse", action="store_true",
                        help="do not look inside sub folders")
    parser.add_argument("--overwrite", action="store_true",
                        help="convert again even if the MP3 is newer")
    parser.add_argument("--keep", action="store_true",
                        help="delete the source video after a successful convert")
    parser.add_argument("--dry-run", action="store_true",
                        help="print the commands and change nothing")
    parser.add_argument("--gui", action="store_true", help="open the graphical window")
    parser.add_argument("--version", action="version", version=f"{APP_NAME} {__version__}")

    args = parser.parse_args(argv)

    # 🖥️ GUI mode: no files needed on the command line
    if args.gui:
        from .ui import run_gui          # 🐢 imported late: tkinter is slow to load
        return run_gui(initial_files=args.inputs)

    # 🖱️ drag and drop: the terminal sends file names on stdin when there are no arguments
    if not args.inputs and not sys.stdin.isatty():
        dragged = [line.strip().strip("'\"") for line in sys.stdin if line.strip()]
        if dragged:
            print(CYAN("  🖱️  files from drag and drop:"))
            args.inputs = dragged

    if not args.inputs:
        parser.print_help()
        return 1

    try:
        probe.check_tools()
    except probe.ToolMissing as exc:
        print(RED(f"❌ {exc}"), file=sys.stderr)
        return 1

    sources = find_videos(args.inputs, recursive=not args.no_recurse)

    # 🌐 internet links: download first, then treat like a normal file
    for item in list(sources):
        if str(item).startswith("http"):
            got = download(str(item), args.out)
            if got:
                sources[sources.index(item)] = got

    if not sources:
        print(RED("❌ no video files found"), file=sys.stderr)
        return 1

    options = Options(
        bitrate=args.bitrate, vbr_quality=args.vbr, normalize=args.normalize,
        trim_silence=args.trim, cover=args.cover, out_dir=args.out,
        jobs=args.jobs, overwrite=args.overwrite, delete_source=args.keep,
    )
    print_banner(options, len(sources))

    if args.dry_run:
        # 🧪 show what would run, without touching any file
        from .core import make_job, build_command
        for src in sources:
            print(DIM("  🧪 ffmpeg " + " ".join(build_command(make_job(src, options)))))
        return 0

    done = {"n": 0}
    lock = threading.Lock()
    total = len(sources)
    bar = Progress("starting")             # 📊 one line bar, only if we have a terminal

    def on_done(job) -> None:
        # 🔔 this runs in a worker thread, so we only print here (keeps output clean)
        with lock:
            done["n"] += 1
            # 📈 move the bar: done files / all files
            bar.update(done["n"] * 100 / total, force=True)
            if job.ok:
                tag = job.tags.get("artist", "")
                who = f"{tag} - " if tag else ""
                print(GREEN(f"  ✅ {job.target.name}  🎚️ {job.options.quality_label}  "
                            f"💾 {human_size(job.size)}  🏷️ {who}{job.tags.get('title', '')}"))
            else:
                print(RED(f"  ❌ {Path(job.source).name}: {job.error}"))

    try:
        results = run_batch(sources, options, on_done=on_done)
    finally:
        bar.clear()                        # 🧽 always remove the bar, even on a crash

    good = sum(1 for r in results if r.ok)
    if good == len(results):
        print(GREEN(f"\n  ✨ done! {good}/{len(results)} files converted"))
        return 0
    print(YELLOW(f"\n  🏁 done: {good}/{len(results)} converted, the rest failed above"))
    return 1


if __name__ == "__main__":
    sys.exit(main())