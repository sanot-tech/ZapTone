# 📦 Changelog

All notable changes to ZapTone are written here.
The format follows [Keep a Changelog](https://keepachangelog.com/).

---

## [0.1.0] - 2026-10-01

🎉 **First release.**

### ✨ Added

- 🖥️ A window: file queue, bitrate picker, progress bar, dark flat design
- ⌨️ A terminal mode with colors, a progress bar and drag-and-drop support
- 🎚️ Constant bitrate from 96 to 320 kbps
- 🏅 VBR mode, quality 0 to 9 (0 is about 245 kbps)
- 🖼️ Cover art: one frame from the middle of the video goes into the MP3
- 🏷️ Tag guessing: `Artist - Album - Song (2024) [Live].mp4` becomes a tagged MP3
- 🔊 Loudness fixing to -14 LUFS, so no song is much louder than another
- ✂️ Cutting the silence at the start and at the end
- 🚿 Parallel converting, half of the CPU cores by default
- 📁 One output folder for a whole batch
- 📥 Downloading from YouTube when `yt-dlp` is installed
- 🐧 🪟 🍏 Builds for Linux (AppImage), Windows (.exe) and macOS (.dmg)
- 🐬 A Dolphin right click menu entry
- 🎨 One SVG icon that renders into every size, plus .ico and .icns
- 🧪 29 unit tests that need no ffmpeg to run

### 🐛 Fixed along the way

Real bugs that existed in the first bash prototype and are now gone forever:

- `-vn` used to delete the cover art, because it removes every video stream
- A backslash before a comment glued an empty `" "` argument onto the ffmpeg call
- `-metadata:s:a:s:0 -1` is not valid, so container junk stayed in the tags
- `xargs -P` could not see shell functions, so parallel mode silently ran once
- GNU regex reads `[^]` as "not ]", which broke the year parsing in file names
- A tab is IFS whitespace, so `read` glued empty tag fields together
- ffmpeg 7 and newer need `-update 1` to write a single image file

---

## [Unreleased]

### 🧪 Tests

- Test suite runs on all three platforms in CI before any build