#!/usr/bin/env python3
"""
🎯 run_zaptone.py - the entry point for build tools.

Why this file exists: PyInstaller runs the file we give it as a normal
script, not as a package. So "python -m zap_tone" (a relative import)
cannot be used there. This file has no relative imports, so it works
the same way for PyInstaller, for a double click, and for a terminal.

Do not put any logic here. Everything lives in zap_tone/.
"""

import sys

# 📦 our own package, found next to this file
sys.path.insert(0, __file__.rsplit("/", 1)[0] if "/" in __file__ else ".")
sys.path.insert(0, __file__.rsplit("\\", 1)[0] if "\\" in __file__ else ".")

from zap_tone.__main__ import entry   # 🚀 the real start function

if __name__ == "__main__":
    sys.exit(entry())                  # 🎬 turn the return code into a process result