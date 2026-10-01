#!/usr/bin/env python3
"""
🪟 make_icons_windows.py - icon generator for Windows build machines.

The normal script (scripts/make_icons.py) needs rsvg-convert, which is a
Linux tool. Windows GitHub runners have no such tool, so this version uses
Python libraries instead: cairosvg to raster and Pillow to pack the .ico.

Both libraries are tiny and install fast:
    python -m pip install cairosvg pillow

It makes the same files as the Linux script, so the icon never differs
between platforms.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SVG = ROOT / "assets" / "icon.svg"
OUT = ROOT / "assets" / "icons"

# 📐 same size list as the Linux version, so both platforms look identical
SIZES = (16, 22, 24, 32, 48, 64, 128, 256, 512, 1024)
ICO_SIZES = (16, 24, 32, 48, 64, 128, 256)


def die(msg: str) -> None:
    """❌ Stop with a clear message."""
    print(f"❌ {msg}", file=sys.stderr)
    raise SystemExit(1)


def render_all(sizes: tuple[int, ...]) -> list[Path]:
    """🖼️ Turn the SVG into PNGs of every given size."""
    try:
        import cairosvg
    except ImportError:
        die("cairosvg is missing -> python -m pip install cairosvg pillow")

    OUT.mkdir(parents=True, exist_ok=True)
    made: list[Path] = []
    for size in sizes:
        dst = OUT / f"{size}.png"
        # 📐 width and height in pixels; cairosvg keeps the aspect ratio
        cairosvg.svg2png(url=str(SVG), write_to=str(dst),
                         output_width=size, output_height=size)
        made.append(dst)
        print(f"  ✅ {dst.relative_to(ROOT)}")
    return made


def pack_ico(files: list[Path], dst: Path) -> None:
    """
    🪟 Pack several PNGs into one .ico.

    Pillow does this in one call: it stores the biggest image and a table
    of the smaller sizes, which is exactly the Windows format.
    """
    try:
        from PIL import Image
    except ImportError:
        die("Pillow is missing -> python -m pip install pillow")

    # 🖼️ открываем biggest picture, указываем список размеров
    images = [Image.open(f).convert("RGBA") for f in files]
    images.sort(key=lambda im: im.width, reverse=True)   # 📏 biggest first
    biggest = images[0]
    biggest.save(dst, format="ICO", sizes=[(im.width, im.height) for im in images])
    print(f"  ✅ {dst.relative_to(ROOT)}")


def main() -> int:
    """🚀 Render and pack. Same output as the Linux script."""
    if not SVG.is_file():
        die(f"SVG not found: {SVG}")
    print(f"🎨 rendering {SVG.name} on Windows …")
    pngs = render_all(SIZES)
    pack_ico([p for p in pngs if p.stem.isdigit() and int(p.stem) in ICO_SIZES],
             OUT / "ZapTone.ico")

    # 🐧 та же иконка для linux/ (в репозитории она нужна для сборки AppImage)
    linux_png = ROOT / "linux" / "zaptone.png"
    shutil.copy(OUT / "256.png", linux_png)
    print(f"  ✅ {linux_png.relative_to(ROOT)}")
    print("\n✨ done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())