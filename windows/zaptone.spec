# -*- mode: python ; coding: utf-8 -*-
"""
🪟 PyInstaller build recipe for ZapTone on Windows and macOS.

Run it with:
    pyinstaller --clean --noconfirm zap_tone.spec

It produces ONE file:
    Windows:  dist/ZapTone.exe          (double click, no Python needed)
    macOS:    dist/ZapTone.app          (drag into Applications)

Why one file: --onefile packs python, tkinter and our code into a single
executable. The user downloads one thing and it just works.
"""

# 📦 standard library bits
import sys
from pathlib import Path

# PyInstaller is only available while building, so this import is safe here
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# 📍 paths: this file lives in windows/, the code is one level up
ROOT = Path(SPECPATH).resolve().parent
ICON_SRC = ROOT / "assets" / "icons" / "ZapTone.ico"

# 🖥️ one file, no console window, GUI stays on top when the user clicks it
EXE_OPTS = [
    "--onefile",            # 📦 everything in one executable
    "--windowed",           # 🙈 no black terminal window behind the app
    "--name", "ZapTone",    # 🏷️ the file that appears for the user
    "--clean",              # 🧹 drop old build files first
    "--noconfirm",          # 🙈 do not ask questions
    "--noupx",              # 📦 UPX breaks tkinter on some AV tools, skip it
    "--hidden-import", "tkinter.filedialog",  # 🔍 tkinter hides this one
    "--hidden-import", "tkinter.ttk",         # 🔍 and this one
]

# 🍎 macOS needs its own options: a windowed bundle, not a bare executable
if sys.platform == "darwin":
    EXE_OPTS = [
        "--onefile",
        "--windowed",
        "--name", "ZapTone",
        "--clean",
        "--noconfirm",
        "--noupx",
        "--osx-bundle-identifier", "tech.sanot.zaptone",
        "--target-arch", "universal2",     # 🍏 runs on Apple silicon and Intel
        "--hidden-import", "tkinter.filedialog",
        "--hidden-import", "tkinter.ttk",
    ]

# 📦 Collect tkinter completely. PyInstaller often misses parts of it,
#    and then the built app crashes on the first file dialog.
hiddenimports = [
    "tkinter", "tkinter.ttk", "tkinter.filedialog", "tkinter.messagebox",
    "tkinter.font", "tkinter.constants", "tkinter.scrolledtext",
] + collect_submodules("tkinter")

block_cipher = None   # 🗝️ PyInstaller 6 uses a different key name

a = Analysis(
    [str(ROOT / "run_zaptone.py")],              # 🎯 not __main__.py!
    #   PyInstaller runs the given file as a plain script, so the relative
    #   imports inside zap_tone/__main__.py would fail. run_zaptone.py has
    #   no relative imports, so it behaves the same in every situation.
    pathex=[str(ROOT)],                        # 📚 where to find our package
    binaries=collect_data_files("zap_tone"),   # 📦 any data inside the package
    datas=[],                                  # 📦 extra files (none right now)
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["numpy", "pandas", "PyQt5", "PySide2"],   # 🗑️ cut dead weight
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# 🖼️ icon: Windows uses .ico, macOS uses .icns. Missing icon is fine, we skip it.
icon_arg = []
if ICON_SRC.is_file():
    if sys.platform == "win32":
        icon_arg = [str(ICON_SRC)]
    elif sys.platform == "darwin":
        # 🍏 macOS wants a .icns inside an .iconset folder
        iconset = ROOT / "assets" / "icons" / "ZapTone.iconset"
        if iconset.is_dir():
            icon_arg = [str(iconset)]

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="ZapTone",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None if not icon_arg else icon_arg[0],
)

# ══════════════════════════════════════════════════════════════════════
# 🍎 macOS only: wrap the executable into ZapTone.app.
#
# Why this block exists: a plain EXE gives us a bare binary on macOS, and
# hdiutil then fails with "create failed - No such file or directory"
# because dist/ZapTone.app was never made. The BUNDLE call is what
# creates the .app folder that macOS users double click.
# ══════════════════════════════════════════════════════════════════════
if sys.platform == "darwin":
    app = BUNDLE(
        exe,
        name="ZapTone.app",
        icon=None if not icon_arg else icon_arg[0],
        bundle_identifier="tech.sanot.zaptone",
        info_plist={
            # 🍎 категория в «Программах»
            "CFBundleName": "ZapTone",
            "CFBundleDisplayName": "ZapTone",
            "CFBundleInfoDictionaryVersion": "6.0",
            "CFBundleShortVersionString": "0.1.0",
            "CFBundleVersion": "0.1.0",
            "CFBundlePackageType": "APPL",
            "LSApplicationCategoryType": "public.app-category.music",
            "NSHighResolutionCapable": True,
            # 🖥️ мы просим нормальный вид окна (без скроллбаров-полосок)
            "NSRequiresAquaSystemAppearance": False,
            "LSMinimumSystemVersion": "10.15",
            "CFBundleGetInfoString": "Turn any video into a clean MP3 file",
        },
    )