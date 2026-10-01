# 🔒 Security Policy

## 🎯 Our promise

ZapTone works with files on your own computer. Nothing is uploaded, no
account is needed, no network calls are made, except when you ask for a
YouTube download.

## 📦 Supported versions

| Version | Supported |
|---|---|
| 0.1.x | ✅ yes |
| older | ❌ no, please update |

## 🚨 Reporting a vulnerability

Please **do not** open a public issue for a security problem.

Email the maintainer, or use GitHub's private reporting:
[Security advisories](https://github.com/sanot-tech/ZapTone/security/advisories/new)

Please include:

- 🖥️ your system and the ZapTone version
- 📋 the exact steps to reproduce
- 💥 what an attacker could do
- 📎 any proof or example file

We answer within 72 hours. Confirmed problems get a fix and a credit,
unless you prefer to stay anonymous.

## 🛡️ What we already do

| Risk | What we do about it |
|---|---|
| 📄 Path with quotes or spaces | every path is passed as a separate list item, never as a string |
| 💀 Command injection | we never build shell commands, we pass a list to `subprocess` |
| 🕵️ Untrusted file names | tags are read from names but only written as metadata, never run |
| 🧠 DoS with a huge file | ffprobe has a 30 second timeout |
| 🧹 Temp folder leftovers | the cover art temp folder is removed in a `finally` block |
| 🔑 Secrets | the app has no config file and reads no tokens |
| ⬆️ Running as root | the Windows manifest asks for `asInvoker`, no elevation |

## 🔍 Scope

**In scope:** the ZapTone code in this repository, the AppImage, the
Windows .exe, the macOS .dmg.

**Out of scope:** ffmpeg itself (report it to
[FFmpeg](https://ffmpeg.org/bugreports.html)) and yt-dlp
(report it to [yt-dlp](https://github.com/yt-dlp/yt-dlp/issues)).