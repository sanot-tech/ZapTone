"""
🚀 __main__.py - lets you start the app with "python -m zap_tone".

This file must stay tiny. It only picks the mode:
GUI when a window is asked for, otherwise the terminal version.
"""

import sys

from .cli import main as cli_main


def entry() -> int:
    """🚪 Choose GUI or terminal, then run it."""
    # 🖥️ --gui or no arguments on a double click (Windows/macOS) opens the window
    if "--gui" in sys.argv or (len(sys.argv) == 1 and _looks_like_double_click()):
        from .ui import run_gui
        return run_gui()
    return cli_main()


def _looks_like_double_click() -> bool:
    """🖱️ On Windows a double click runs the exe with no arguments.

    Frozen apps have this attribute, real scripts do not.
    """
    return bool(getattr(sys, "frozen", False))


if __name__ == "__main__":
    sys.exit(entry())