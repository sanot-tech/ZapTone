# 🤝 Contributing to ZapTone

Thanks for helping! This file explains how to work on ZapTone without
stepping on anyone.

## 🚀 Quick start

```bash
git clone https://github.com/sanot-tech/ZapTone.git
cd ZapTone
python3 -m unittest discover -s tests -v    # 🧪 must be green before you start
./install.sh                                # ⚡ try it on your own computer
```

## 💻 The code

Plain Python, standard library only. **Please keep it that way.** No
`requirements.txt`, no framework, no lock file. That is what lets one small
file run on Linux, Windows and macOS.

| File | What lives there |
|---|---|
| `zap_tone/core.py` | builds ffmpeg commands, runs the thread pool |
| `zap_tone/probe.py` | asks ffprobe about a file, caches answers |
| `zap_tone/tags.py` | guesses tags from the file name |
| `zap_tone/ui.py` | the tkinter window |
| `zap_tone/cli.py` | the terminal mode |

### 📏 Rules we follow

1. 🧪 **Every new feature needs a test.** Put it in `tests/test_zaptone.py`.
   Tests must run without ffmpeg installed.
2. 💬 **Simple English in comments.** Short sentences, no long words.
   Explain *why* something is done, not what the line obviously does.
3. 🛡️ **Never raise in a worker thread.** A broken file must not stop the batch.
   Return a `Job` with `error` filled in.
4. 🚦 **No new dependencies.** If you really need one, open an issue first.
5. 🌐 **UI text in English.** Keep it short enough to fit a button.

## 🧪 Before you open a pull request

```bash
python3 -m unittest discover -s tests -v     # 🧪 tests must pass
python3 -m zap_tone --dry-run -n -c file.mp4 # 🧪 the command must look sane
./install.sh                                 # ⚡ install it and try it
```

## 💬 Commit messages

Write them for a human, not for a machine:

```
fix: keep the cover art when the video has no audio track 🖼️

Before, -vn deleted every video stream, including the picture we
attached as cover art. Now -vn is only added when there is no cover.
```

- Use `feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, `test:`
- One thing per commit
- Explain the reason in the body, it is more useful than the diff

## 🎨 Icons

One SVG is the source of truth: `assets/icon.svg`. Never commit a PNG by hand.

```bash
python3 scripts/make_icons.py          # rebuild every size
python3 scripts/make_icons.py     # rebuild every size and the .ico

The PNG sizes are not in git, they get built from the SVG every time.
`assets/icons/ZapTone.ico` **is** in git, because the Windows build
cannot make it on its own (no librsvg on a clean Windows machine).
If you change the icon, run the script and commit the new .ico too.
```

## 🐛 Reporting a bug

Tell us:

- 🖥️ your system (`uname -a` or Windows version)
- 📋 the exact command you ran
- ❌ what you expected and what happened instead
- 📎 the error text, in a code block

Run this first, it often explains the problem:

```bash
zaptone --dry-run YOUR_FILE
```

## 💬 Questions

Use [Discussions](https://github.com/sanot-tech/ZapTone/discussions). A
question is not a bug report, and the answer helps the next person too.

## 📄 License

By contributing you agree that your work goes out under GPL-3.0-or-later.