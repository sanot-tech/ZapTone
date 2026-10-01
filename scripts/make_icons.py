#!/usr/bin/env python3
"""
🎨 make_icons.py - turn one SVG into every icon format we need.

Why one SVG: draw it once, generate everything from it. No other
image file lives in the repository, so the icon never gets out of sync.

Usage:
    python3 scripts/make_icons.py                # use assets/icon.svg
    python3 scripts/make_icons.py other.svg      # use your own file

What it makes:
    assets/icons/{16,22,24,32,48,64,128,256,512,1024}.png
    assets/icons/ZapTone.ico        (Windows, 16 to 256 px)
    assets/icons/ZapTone.icns       (macOS, 16 to 1024 px)
    linux/zaptone.png                (menu icon, 256 px)

Needs: rsvg-convert (librsvg) and ImageMagick. Both are in the Arch
repositories:  sudo pacman -S librsvg imagemagick
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

# 🪟 Кто-то может запустить этот скрипт и на Windows, где консоль cp1252
#    и не умеет печатать эмодзи. Без этой строки первый же print убьёт скрипт.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass  # 🧓 старый Python или поток, который уже в порядке

# 📐 every size a Linux desktop or a Windows taskbar can ask for
SIZES = (16, 22, 24, 32, 48, 64, 128, 256, 512, 1024)

# 📦 sizes that go into a Windows .ico (Windows dislikes 512 in ico)
ICO_SIZES = (16, 24, 32, 48, 64, 128, 256)

# 🍎 sizes that go into a macOS .icns
ICNS_SIZES = (16, 32, 64, 128, 256, 512, 1024)

ROOT = Path(__file__).resolve().parent.parent
SVG = ROOT / "assets" / "icon.svg"
OUT = ROOT / "assets" / "icons"


def die(msg: str) -> None:
    """❌ Stop with a clear message."""
    print(f"❌ {msg}", file=sys.stderr)
    raise SystemExit(1)


def have(tool: str) -> bool:
    """🔧 Check that a command exists."""
    return shutil.which(tool) is not None


def svg_to_png(src: Path, dst: Path, size: int) -> None:
    """🖼️ Raster one SVG. rsvg-convert gives the cleanest edges."""
    subprocess.run(
        ["rsvg-convert", "-w", str(size), "-h", str(size), str(src), "-o", str(dst)],
        check=True, capture_output=True,
    )


def make_ico(files: list[Path], dst: Path) -> None:
    """🪟 Windows icon. ImageMagick puts all sizes into one file.

    "magick create" builds a multi resolution .ico. Older ImageMagick
    only knows "convert", so we try both.
    """
    commands = [
        ["magick", "create", *files, str(dst)],     # ImageMagick 7
        ["convert", *files, str(dst)],              # ImageMagick 6
    ]
    errors = []
    for cmd in commands:
        if not have(cmd[0]):
            continue
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return
        errors.append(f"{cmd[0]}: {result.stderr.strip()[:120]}")
    die("could not build the .ico -> " + " | ".join(errors))


def make_icns(files: list[Path], dst: Path) -> None:
    """🍎 macOS icon. The names inside the folder must follow Apple's rules."""
    tmp = ROOT / ".icns_build"
    if tmp.exists():
        shutil.rmtree(tmp)
    icons_dir = tmp / "ZapTone.iconset"
    icons_dir.mkdir(parents=True)
    # 📛 Apple wants exact names: icon_16x16.png, icon_32x32.png, ... icon_512x512@2x.png
    mapping = {
        16: ["icon_16x16.png"], 32: ["icon_16x16@2x.png"],
        64: ["icon_32x32@2x.png"], 128: ["icon_128x128.png"],
        256: ["icon_128x128@2x.png", "icon_256x256.png"],
        512: ["icon_256x256@2x.png", "icon_512x512.png"],
        1024: ["icon_512x512@2x.png"],
    }
    for size, names in mapping.items():
        src = OUT / f"{size}.png"
        if not src.exists():
            continue
        for name in names:
            shutil.copy(src, icons_dir / name)
    subprocess.run(["iconutil", "-c", "icns", str(icons_dir), "-o", str(dst)],
                   check=True, capture_output=True)
    shutil.rmtree(tmp, ignore_errors=True)


def main() -> int:
    """🚀 Generate all icon formats."""
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else SVG
    if not src.is_file():
        die(f"no SVG found: {src}")
    if not have("rsvg-convert"):
        die("rsvg-convert is missing -> sudo pacman -S librsvg")
    if not (have("magick") or have("convert")):
        die("ImageMagick is missing -> sudo pacman -S imagemagick")

    OUT.mkdir(parents=True, exist_ok=True)
    print(f"🎨 rendering {src.name} …")

    # 📐 PNG of every size. rsvg renders once per size, it takes a second.
    for size in SIZES:
        dst = OUT / f"{size}.png"
        svg_to_png(src, dst, size)
        print(f"  ✅ {dst.relative_to(ROOT)}  ({dst.stat().st_size // 1024} KB)")

    # 🪟 Windows
    if have("magick") or have("convert"):
        make_ico([OUT / f"{s}.png" for s in ICO_SIZES], OUT / "ZapTone.ico")
        print("  ✅ assets/icons/ZapTone.ico")

    # 🍎 macOS needs iconutil, which only exists on macOS. Skip it elsewhere.
    if have("iconutil"):
        make_icns([], OUT / "ZapTone.icns")
        print("  ✅ assets/icons/ZapTone.icns")
    else:
        print("  ℹ️  iconutil not found (macOS only), .icns skipped")

    # 🐧 menu icon for the KDE launcher
    linux_png = ROOT / "linux" / "zaptone.png"
    shutil.copy(OUT / "256.png", linux_png)
    print("  ✅ linux/zaptone.png")

    print(f"\n✨ done. All icons are in {OUT.relative_to(ROOT)}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())