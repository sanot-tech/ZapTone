"""
🧪 tests/test_zaptone.py - unit tests that need no ffmpeg.

Run them with:  python3 -m pytest tests/ -v
or without pytest:  python3 tests/test_zaptone.py

Why: the ffmpeg command must stay correct. These tests check the
command we build, without ever running it.
"""

import sys
import tempfile
import unittest
from pathlib import Path

# 📦 make the project importable when we run the file directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from zap_tone import VIDEO_EXTENSIONS, is_video_file          # 🧪 helpers
from zap_tone.core import Options, audio_filter, build_command, make_job, target_path
from zap_tone.tags import tags_from_filename                  # 🏷️ tag guessing


class TestTags(unittest.TestCase):
    """🏷️ Check that file names become nice tags."""

    def test_plain_name(self):
        """🎯 A name without dashes stays a title."""
        self.assertEqual(tags_from_filename("Holiday.mp4"), {"title": "Holiday"})

    def test_artist_and_title(self):
        """🎤 "Artist - Song" gives artist + title."""
        got = tags_from_filename("Daft Punk - Around The World.mp4")
        self.assertEqual(got["artist"], "Daft Punk")
        self.assertEqual(got["title"], "Around The World")

    def test_artist_album_title(self):
        """💿 Three parts give artist + album + title."""
        got = tags_from_filename("ACDC - Back In Black - Hells Bells.mkv")
        self.assertEqual(got["artist"], "ACDC")
        self.assertEqual(got["album"], "Back In Black")
        self.assertEqual(got["title"], "Hells Bells")

    def test_year_and_live(self):
        """📅 (2024) becomes date, [Live] becomes comment."""
        got = tags_from_filename("Artist - Album - Song (2024) [Live].mp4")
        self.assertEqual(got["date"], "2024")
        self.assertEqual(got["comment"], "[Live]")
        self.assertEqual(got["title"], "Song")

    def test_underscores_become_spaces(self):
        """🔤 Video_2024_01_01 becomes readable words."""
        got = tags_from_filename("My_Great_Video.mp4")
        self.assertEqual(got["title"], "My Great Video")

    def test_year_in_name_is_not_a_date(self):
        """🛡️ A plain date must not be eaten from the title."""
        got = tags_from_filename("Video 2026-09-30 05-02-14.mp4")
        self.assertIn("2026", got["title"])

    def test_empty_is_safe(self):
        """🧪 Weird input must not crash."""
        self.assertIsInstance(tags_from_filename(""), dict)
        self.assertIsInstance(tags_from_filename("...."), dict)


class TestVideoCheck(unittest.TestCase):
    """🎬 Check the file name filter."""

    def test_known_extensions(self):
        """✅ mp4 and mkv are videos."""
        self.assertTrue(is_video_file("a.mp4"))
        self.assertTrue(is_video_file("A.MKV"))
        self.assertTrue(is_video_file("clip.webm"))

    def test_other_files_rejected(self):
        """✅ mp3 and png are not videos."""
        self.assertFalse(is_video_file("song.mp3"))
        self.assertFalse(is_video_file("photo.png"))
        self.assertFalse(is_video_file("noext"))

    def test_extension_list(self):
        """✅ The list is not empty and has no duplicates."""
        self.assertGreater(len(VIDEO_EXTENSIONS), 10)
        self.assertEqual(len(VIDEO_EXTENSIONS), len(set(VIDEO_EXTENSIONS)))


class TestOptions(unittest.TestCase):
    """⚙️ Options must fix bad values by themselves."""

    def test_bitrate_limits(self):
        """🛡️ 9999 kbps becomes 320."""
        self.assertEqual(Options(bitrate=9999).bitrate, 320)
        self.assertEqual(Options(bitrate=1).bitrate, 8)

    def test_jobs_auto(self):
        """🚿 0 means automatic, and it must never be zero."""
        self.assertGreaterEqual(Options(jobs=0).jobs, 1)

    def test_vbr_clamped(self):
        """🛡️ VBR quality 99 becomes 9."""
        self.assertEqual(Options(vbr_quality=99).vbr_quality, 9)

    def test_quality_label(self):
        """🏷️ Label text for the interface."""
        self.assertEqual(Options(bitrate=320).quality_label, "320k CBR")
        self.assertEqual(Options(vbr_quality=0).quality_label, "VBR q0")


class TestFilters(unittest.TestCase):
    """🎚️ The sound filter chain."""

    def test_no_filter_by_default(self):
        """🤷 No options means no changes to the sound."""
        self.assertIsNone(audio_filter(Options()))

    def test_trim_only(self):
        """✂️ Trim uses silenceremove."""
        got = audio_filter(Options(trim_silence=True))
        self.assertIn("silenceremove", got)
        self.assertNotIn("loudnorm", got)

    def test_both_filters(self):
        """🔊✨ Both filters join with a comma (ffmpeg syntax)."""
        got = audio_filter(Options(normalize=True, trim_silence=True))
        self.assertIn("silenceremove", got)
        self.assertIn("loudnorm", got)
        self.assertEqual(got.count(","), 1)

    def test_silence_has_no_commas(self):
        """🛡️ A comma inside silenceremove would break the ffmpeg filter chain."""
        got = audio_filter(Options(trim_silence=True))
        self.assertNotIn(",", got)


class TestCommand(unittest.TestCase):
    """🛠️ The ffmpeg command line."""

    def setUp(self):
        """🧪 Make a fake video file, no real ffmpeg needed."""
        self.tmp = tempfile.TemporaryDirectory()
        self.src = Path(self.tmp.name) / "Artist - Song.mp4"
        self.src.write_bytes(b"fake")

    def tearDown(self):
        """🧹 Clean the temp folder."""
        self.tmp.cleanup()

    def test_mp3_encoder(self):
        """🎵 We must use libmp3lame and not keep video."""
        cmd = build_command(make_job(self.src, Options(bitrate=256)))
        self.assertIn("libmp3lame", cmd)
        self.assertIn("-vn", cmd)
        self.assertIn("256k", cmd)

    def test_output_name(self):
        """📁 mp4 becomes mp3 in the same folder."""
        job = make_job(self.src, Options())
        self.assertEqual(job.target.name, "Artist - Song.mp3")
        self.assertEqual(job.target.parent, self.src.parent)

    def test_output_dir(self):
        """📁 -o moves the result."""
        job = make_job(self.src, Options(out_dir=Path("/tmp/other")))
        self.assertEqual(job.target.parent, Path("/tmp/other"))

    def test_metadata_cleaned(self):
        """🧹 Container junk must not be copied."""
        cmd = build_command(make_job(self.src, Options()))
        self.assertIn("-map_metadata", cmd)
        self.assertEqual(cmd[cmd.index("-map_metadata") + 1], "-1")

    def test_tags_are_passed(self):
        """🏷️ "Artist - Song.mp4" gives artist=Artist and title=Song."""
        cmd = build_command(make_job(self.src, Options()))
        self.assertIn("title=Song", cmd)
        self.assertIn("artist=Artist", cmd)

    def test_vbr_switches_bitrate(self):
        """🏅 VBR mode uses q:a, not b:a."""
        cmd = build_command(make_job(self.src, Options(vbr_quality=0)))
        self.assertIn("-q:a", cmd)
        self.assertNotIn("192k", cmd)

    def test_cover_needs_two_inputs(self):
        """🖼️ With cover art we must NOT use -vn (it would kill the picture)."""
        job = make_job(self.src, Options(cover=True))
        job.cover_path = job.target.parent / "cover.jpg"
        job.cover_path.write_bytes(b"jpg")
        cmd = build_command(job)
        self.assertNotIn("-vn", cmd)
        self.assertIn("attached_pic", cmd)
        self.assertEqual(cmd.count("-i"), 2)

    def test_no_cover_uses_vn(self):
        """🎬 Without cover art video is dropped."""
        cmd = build_command(make_job(self.src, Options(cover=False)))
        self.assertIn("-vn", cmd)

    def test_no_broken_empty_arguments(self):
        """🛡️ No argument may be a space (that was a real bug once)."""
        cmd = build_command(make_job(self.src, Options(cover=True, normalize=True)))
        self.assertNotIn("", cmd)
        self.assertNotIn(" ", cmd)

    def test_xing_for_seeking(self):
        """✍️ Players need the Xing header to seek properly."""
        self.assertIn("-write_xing", build_command(make_job(self.src, Options())))

    def test_target_helper(self):
        """📦 target_path does simple name work."""
        self.assertEqual(target_path(Path("/a/b/c.mkv")).name, "c.mp3")


if __name__ == "__main__":
    # 🏃 run without pytest:  python3 tests/test_zaptone.py
    unittest.main(verbosity=2)