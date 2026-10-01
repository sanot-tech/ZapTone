"""
⚙️ core.py - the engine. Builds ffmpeg commands and runs them.

Everything here is pure logic. No windows, no colors.
That way the CLI and the GUI use the same code, and the
tests can check command building without starting ffmpeg.
"""

from __future__ import annotations

import os
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path

from . import probe
from .tags import tags_from_filename

# 🎚️ MP3 bitrates we allow. Below 8 kbps it sounds broken.
MIN_BITRATE, MAX_BITRATE = 8, 320

# 🎛️ loudness target for normalise: streaming services use about -14 LUFS
LOUDNESS_TARGET = "I=-14:TP=-1.5:LRA=11"

# ✂️ silence filter: cut quiet parts at the start and at the end only
SILENCE_FILTER = (
    "silenceremove=start_periods=1:start_threshold=-50dB:detection=peak"
    ":stop_periods=-1:stop_threshold=-50dB:stop_duration=2"
)


@dataclass
class Options:
    """⚙️ All settings for one convert job. Easy to copy, easy to test."""

    bitrate: int = 192                     # 🎚️ kbps for CBR mode
    vbr_quality: int | None = None         # 🏅 0..9 for VBR mode, None = use CBR
    normalize: bool = False                # 🔊 loudnorm to -14 LUFS
    trim_silence: bool = False             # ✂️ cut silence at start and end
    cover: bool = False                    # 🖼️ put one video frame into the tag
    out_dir: Path | None = None            # 📁 where to write, None = next to source
    jobs: int = 0                          # 🚿 0 = auto (cpu count)
    overwrite: bool = False                # 💥 True = convert even if mp3 is newer
    delete_source: bool = False            # 🗑️ remove the video after success

    def __post_init__(self) -> None:
        """🛡️ Fix bad values early, so later code can trust them."""
        self.bitrate = max(MIN_BITRATE, min(MAX_BITRATE, int(self.bitrate or 192)))
        if self.vbr_quality is not None:
            self.vbr_quality = max(0, min(9, int(self.vbr_quality)))
        if self.jobs <= 0:
            self.jobs = max(1, (os.cpu_count() or 2) // 2)

    @property
    def quality_label(self) -> str:
        """🏷️ Short text for the UI: "192k CBR" or "VBR q0"."""
        return f"VBR q{self.vbr_quality}" if self.vbr_quality is not None else f"{self.bitrate}k CBR"


@dataclass
class Job:
    """📋 One file in the queue, plus the result we fill in later."""

    source: Path
    target: Path
    options: Options
    ok: bool = False
    error: str = ""
    size: int = 0
    duration: float = 0.0
    cover_path: Path | None = None
    tags: dict[str, str] = field(default_factory=dict)


def target_path(source: Path, out_dir: Path | None = None) -> Path:
    """📁 Where the MP3 will go. Same folder as the video unless told otherwise."""
    folder = Path(out_dir) if out_dir else Path(source).parent
    return folder / f"{Path(source).stem}.mp3"


def audio_filter(options: Options) -> str | None:
    """🎚️ Build the -af value. None means "do not touch the sound"."""
    chain: list[str] = []
    if options.trim_silence:
        chain.append(SILENCE_FILTER)                 # ✂️ first: cut, then level
    if options.normalize:
        chain.append(f"loudnorm={LOUDNESS_TARGET}")   # 🔊 second: make it loud
    return ",".join(chain) if chain else None


def build_command(job: Job) -> list[str]:
    """🛠️ Build the full ffmpeg command for one job. Pure function, easy to test."""
    opts = job.options
    # 📍 ffmpeg_bin() не проверяет наличие ffmpeg: строить команду можно и без него
    cmd: list[str] = [probe.ffmpeg_bin(), "-hide_banner", "-nostdin", "-y"]

    cover_ready = bool(job.cover_path and Path(job.cover_path).stat().st_size > 0)

    if cover_ready:
        # 🖼️ two inputs: the video (audio) and the picture (cover art)
        cmd += ["-i", str(job.source), "-i", str(job.cover_path)]
        cmd += ["-map", "0:a:0", "-map", "1:v:0"]
        cmd += ["-c:v", "mjpeg", "-q:v", "4", "-disposition:v:0", "attached_pic"]
    else:
        cmd += ["-i", str(job.source)]
        # 🔇 -vn would kill the cover art too, so we only add it when there is no cover
        if not cover_ready:
            cmd += ["-vn"]
    cmd += ["-sn"]                                    # 🗑️ no subtitles in an MP3

    cmd += ["-c:a", "libmp3lame"]                     # 🎵 the MP3 encoder
    if opts.vbr_quality is not None:
        cmd += ["-q:a", str(opts.vbr_quality), "-b:a", "0"]   # 🏅 variable bitrate
    else:
        cmd += ["-b:a", f"{opts.bitrate}k", "-compression_level", "5"]  # 🎚️ constant

    cmd += ["-map_metadata", "-1"]                    # 🧹 throw away container junk

    # 🏷️ tags from the file first, then ours (ours wins)
    merged = {**probe.source_tags(job.source), **job.tags}
    for key, value in merged.items():
        cmd += ["-metadata", f"{key}={value}"]

    af = audio_filter(opts)
    if af:
        cmd += ["-af", af]                            # 🎚️ sound processing
    cmd += ["-write_xing", "1"]                       # ✍️ lets players seek properly
    cmd += [str(job.target)]                           # 💾 output file
    return cmd


def grab_cover(job: Job) -> Path | None:
    """📸 Save one frame from the middle of the video to use as cover art."""
    ffmpeg = probe.ffmpeg_bin()
    tmp_dir = job.target.parent / f".zap_tone_{abs(hash(str(job.source)))}"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    cover = tmp_dir / "cover.jpg"
    total = probe.duration(job.source)
    middle = max(total / 2, 0.1) if total > 0 else 1.0
    # -update 1 is needed on ffmpeg 7+ to write a single image file
    subprocess.run(
        [ffmpeg, "-hide_banner", "-nostdin", "-y", "-ss", f"{middle:.3f}",
         "-i", str(job.source), "-frames:v", "1", "-q:v", "4", "-update", "1", str(cover)],
        capture_output=True, timeout=120,
    )
    return cover if cover.stat().st_size > 0 else None


def needs_convert(job: Job) -> bool:
    """⏭️ False when a fresh MP3 already exists (saves time on repeated runs)."""
    if job.options.overwrite:
        return True
    if not job.target.exists() or job.target.stat().st_size == 0:
        return True
    return job.target.stat().st_mtime < Path(job.source).stat().st_mtime


def make_job(source: Path, options: Options) -> Job:
    """📋 Prepare one job: find the target, read tags, plan the cover."""
    source = Path(source)
    job = Job(
        source=source,
        target=target_path(source, options.out_dir),
        options=options,
        tags=tags_from_filename(source.name),
    )
    return job


def convert_job(job: Job) -> Job:
    """🔄 Run one job. Returns the same job with ok/error filled in.

    Never raises: a broken file must not stop the whole batch.
    """
    try:
        if not Path(job.source).is_file():
            job.error = "file not found"
            return job
        # 🛡️ check the tools only here, right before a real run.
        # Building the command above works without ffmpeg, and that is how
        # the unit tests stay fast on machines that have no ffmpeg at all.
        probe.check_tools()
        if not probe.has_audio(job.source):
            job.error = "no audio track inside"
            return job
        job.target.parent.mkdir(parents=True, exist_ok=True)
        if job.options.cover:
            job.cover_path = grab_cover(job)
        subprocess.run(
            build_command(job), capture_output=True, text=True, timeout=None,
        )
        if job.target.exists() and job.target.stat().st_size > 0:
            job.ok = True
            job.size = job.target.stat().st_size
            job.duration = probe.duration(job.target)
            if job.options.delete_source:
                Path(job.source).unlink(missing_ok=True)   # 🗑️ user asked for it
        else:
            job.error = "ffmpeg did not create the file"
    except subprocess.TimeoutExpired:
        job.error = "ffmpeg ran too long and was stopped"
    except Exception as exc:                      # 🛡️ last line of defence
        job.error = str(exc) or exc.__class__.__name__
    finally:
        # 🧹 remove the temp cover folder, whatever happened
        if job.cover_path:
            folder = Path(job.cover_path).parent
            if folder.name.startswith(".zap_tone_"):
                for f in folder.glob("*"):
                    f.unlink(missing_ok=True)
                folder.rmdir()
    return job


def run_batch(sources: list[Path], options: Options,
              on_start=None, on_done=None) -> list[Job]:
    """🏊 Convert many files at once.

    on_start / on_done are callbacks, so the GUI can draw a progress bar
    without this module knowing anything about windows.
    """
    jobs = [make_job(s, options) for s in sources]

    # 📢 tell the GUI what we are about to do (so it can draw the queue)
    if on_start:
        on_start(jobs)

    results: list[Job] = []
    with ThreadPoolExecutor(max_workers=options.jobs) as pool:
        # 📤 submit everything at once; the pool limits how many really run
        futures = [pool.submit(convert_job, job) for job in jobs]
        for future in as_completed(futures):
            job = future.result()
            results.append(job)
            # 🔔 one callback per finished file -> the GUI moves its bar
            if on_done:
                on_done(job)

    # 📋 sort back into the order the user gave us, easier to read a log
    order = {str(j.source): i for i, j in enumerate(jobs)}
    results.sort(key=lambda j: order.get(str(j.source), 0))
    return results