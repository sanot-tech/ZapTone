"""
🖥️ ui.py - the window. Tkinter only, no other libraries.

Why tkinter: it is part of every normal Python build on Windows,
macOS and Linux. That means our one-file build works everywhere
without shipping 100 MB of Qt.

Style: flat, dark, two accent colors. No external theme files, so
the app looks the same on every computer.
"""

from __future__ import annotations

import queue
import sys
import threading
from pathlib import Path

from . import APP_NAME, APP_TAGLINE, VIDEO_EXTENSIONS, __version__, probe
from .core import Options, run_batch

# 🧠 tkinter can break in three different ways, and each one needs its own fix:
#      1. the python-tk package is not installed        -> install it
#      2. tk is installed but a system library is gone   -> install tk itself
#      3. tkinter works, but there is no screen          -> run in terminal mode
# We catch all of them here, so the user gets advice instead of a traceback.
TK_ERROR: str | None = None
try:
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk
except Exception as exc:                        # 🧯 any broken tk install
    tk = None                                   # 🛑 type: ignore[assignment]
    ttk = filedialog = messagebox = None        # 🛑 nothing can be built
    TK_ERROR = f"{exc.__class__.__name__}: {exc}"

# 📋 the fix message, printed when the window cannot start
TK_HELP = """🖥️ The ZapTone window needs tkinter, and it does not work here.

What went wrong:
  {error}

How to fix it:

  🐧 Arch / CachyOS:   sudo pacman -S python-tk tk
  🐧 Debian / Ubuntu:  sudo apt install python3-tk
  🍎 macOS:            brew install python-tkinter tk
  🪟 Windows:          python -m pip install tk

Then start ZapTone again.

💡 The terminal mode works right now and needs none of this:
      zaptone YOUR_VIDEO.mp4"""

# 🎨 our little design system. One place to change the look.
BG = "#12141c"           # 🌑 window background
PANEL = "#1b1f2b"        # ▦ cards and inputs
FG = "#e8ecf4"           # ⚪ main text
MUTED = "#8b93a7"        # 🌫️ secondary text
ORANGE = "#ff8c42"       # 🔶 Plasma orange - main accent
PINK = "#ff5f8d"         # 🌸 second accent, used for the bar
GREEN = "#3ddc84"        # ✅ success
RED = "#ff5f5f"          # ❌ error

# 📏 sizes in pixels, so the window looks the same everywhere
PAD = 18
ROW_H = 34

BITRATES = ("128", "160", "192", "256", "320")


def _filetypes() -> list[tuple[str, str]]:
    """🎬 Build the video filter list once, used by the open dialog."""
    patterns = " ".join(f"*.{ext}" for ext in VIDEO_EXTENSIONS)
    return [("Video files", patterns), ("All files", "*.*")]


class ZapToneApp:
    """🎛️ The whole window: queue, settings, progress, buttons."""

    def __init__(self, root: tk.Tk, initial_files: list[str] | None = None) -> None:
        self.root = root
        self.queue: list[Path] = []                 # 📥 files waiting to convert
        self.results: list = []                     # 📤 finished jobs
        self.worker: threading.Thread | None = None
        self.events: queue.Queue = queue.Queue()   # 📬 messages from worker thread
        self.running = False

        # ⚙️ settings stored in tk variables, so the widgets stay simple
        self.bitrate = tk.StringVar(value="192")
        self.vbr = tk.BooleanVar(value=False)
        self.normalize = tk.BooleanVar(value=False)
        self.trim = tk.BooleanVar(value=False)
        self.cover = tk.BooleanVar(value=True)
        self.delete_after = tk.BooleanVar(value=False)
        self.out_dir = tk.StringVar(value="")
        self.status = tk.StringVar(value="Drop videos here or press Add files")
        self.progress = tk.DoubleVar(value=0.0)

        self._build_window()
        self._build_style()
        self._build_layout()
        for f in initial_files or []:
            self.add_path(f)

    # ── 🪟 window ──────────────────────────────────────────────
    def _build_window(self) -> None:
        """🪟 Title, size and dark background."""
        self.root.title(f"{APP_NAME} {__version__}")
        self.root.geometry("820x600")
        self.root.minsize(700, 520)
        self.root.configure(bg=BG)

    def _build_style(self) -> None:
        """🎨 Make ttk widgets match our dark palette."""
        style = ttk.Style(self.root)
        style.theme_use("clam")                     # 🔧 clam is the only theme we can restyle
        style.configure("Dark.TFrame", background=BG)
        style.configure("Panel.TFrame", background=PANEL)
        style.configure("Dark.TLabel", background=BG, foreground=FG, font=("TkDefaultFont", 11))
        style.configure("Muted.TLabel", background=BG, foreground=MUTED, font=("TkDefaultFont", 10))
        style.configure("Title.TLabel", background=BG, foreground=FG, font=("TkDefaultFont", 22, "bold"))
        style.configure("Panel.TLabel", background=PANEL, foreground=FG)
        style.configure("MutedPanel.TLabel", background=PANEL, foreground=MUTED)
        style.configure("Orange.TButton", background=ORANGE, foreground="#1a1206",
                        font=("TkDefaultFont", 11, "bold"), borderwidth=0, padding=(14, 9))
        style.map("Orange.TButton", background=[("active", "#ffa060")], relief=[("pressed", "flat")])
        style.configure("Ghost.TButton", background=PANEL, foreground=FG, borderwidth=0, padding=(12, 8))
        style.map("Ghost.TButton", background=[("active", "#262c3d")])
        style.configure("Dark.Horizontal.TProgressbar", background=ORANGE, troughcolor=PANEL,
                        borderwidth=0, thickness=8)
        style.configure("Dark.TCheckbutton", background=BG, foreground=FG,
                        indicatorcolor=PANEL, focuscolor=BG)
        style.map("Dark.TCheckbutton", background=[("active", BG)],
                  foreground=[("active", ORANGE)], indicatorcolor=[("selected", ORANGE)])
        style.configure("Dark.TCombobox", fieldbackground=PANEL, background=PANEL,
                        foreground=FG, arrowcolor=MUTED, borderwidth=0)
        style.configure("Dark.Treeview", background=PANEL, fieldbackground=PANEL,
                        foreground=FG, rowheight=26, borderwidth=0)
        style.configure("Dark.Treeview.Heading", background=PANEL, foreground=MUTED,
                        relief="flat", borderwidth=0)
        style.map("Dark.Treeview", background=[("selected", "#2b3244")], foreground=[("selected", FG)])

    # ── 🧱 layout ──────────────────────────────────────────────
    def _build_layout(self) -> None:
        """🧱 Put every widget on the screen, top to bottom."""
        main = ttk.Frame(self.root, style="Dark.TFrame", padding=PAD)
        main.pack(fill="both", expand=True)

        # 🏷️ header
        head = ttk.Frame(main, style="Dark.TFrame")
        head.pack(fill="x")
        ttk.Label(head, text=f"⚡ {APP_NAME}", style="Title.TLabel").pack(side="left")
        ttk.Label(head, text=APP_TAGLINE, style="Muted.TLabel").pack(side="left", padx=12, pady=(8, 0))

        # 📥 queue card
        queue_card = ttk.Frame(main, style="Panel.TFrame", padding=12)
        queue_card.pack(fill="both", expand=True, pady=(14, 10))

        top_row = ttk.Frame(queue_card, style="Panel.TFrame")
        top_row.pack(fill="x")
        ttk.Label(top_row, text="📥 FILES", style="MutedPanel.TLabel").pack(side="left")
        ttk.Button(top_row, text="➕ Add files", style="Ghost.TButton",
                   command=self.add_files).pack(side="right")
        ttk.Button(top_row, text="➕ Add folder", style="Ghost.TButton",
                   command=self.add_folder).pack(side="right", padx=6)
        ttk.Button(top_row, text="🧹 Clear", style="Ghost.TButton",
                   command=self.clear_files).pack(side="right")

        columns = ("name", "size", "length", "status")
        self.tree = ttk.Treeview(queue_card, columns=columns, show="headings",
                                 style="Dark.Treeview", selectmode="extended")
        for col, title, width in zip(columns, ("File", "Size", "Length", "Status"), (320, 90, 90, 150)):
            self.tree.heading(col, text=title)
            self.tree.column(col, width=width, anchor="w" if col == "name" else "center")
        self.tree.pack(fill="both", expand=True, pady=(10, 0))
        self.tree.tag_configure("ok", foreground=GREEN)      # ✅ finished
        self.tree.tag_configure("fail", foreground=RED)      # ❌ failed
        self.tree.tag_configure("wait", foreground=MUTED)     # ⏳ waiting

        # ⚙️ settings card
        set_card = ttk.Frame(main, style="Panel.TFrame", padding=12)
        set_card.pack(fill="x")

        row1 = ttk.Frame(set_card, style="Panel.TFrame")
        row1.pack(fill="x")
        ttk.Label(row1, text="🎚️ Bitrate", style="MutedPanel.TLabel").pack(side="left")
        self.bitrate_box = ttk.Combobox(row1, values=BITRATES, textvariable=self.bitrate,
                                        state="readonly", width=7, style="Dark.TCombobox")
        self.bitrate_box.pack(side="left", padx=(10, 16))
        ttk.Checkbutton(row1, text="VBR mode", variable=self.vbr,
                        style="Dark.TCheckbutton").pack(side="left")
        ttk.Label(row1, text="🔊 Loudness", style="MutedPanel.TLabel").pack(side="left", padx=(24, 0))
        ttk.Checkbutton(row1, text="even it out", variable=self.normalize,
                        style="Dark.TCheckbutton").pack(side="left")
        ttk.Label(row1, text="✂️ Silence", style="MutedPanel.TLabel").pack(side="left", padx=(24, 0))
        ttk.Checkbutton(row1, text="trim ends", variable=self.trim,
                        style="Dark.TCheckbutton").pack(side="left")

        row2 = ttk.Frame(set_card, style="Panel.TFrame")
        row2.pack(fill="x", pady=(10, 0))
        ttk.Checkbutton(row2, text="🖼️ Cover art from video", variable=self.cover,
                        style="Dark.TCheckbutton").pack(side="left")
        ttk.Checkbutton(row2, text="🗑️ Delete source after", variable=self.delete_after,
                        style="Dark.TCheckbutton").pack(side="left", padx=16)
        ttk.Label(row2, text="📁 Output", style="MutedPanel.TLabel").pack(side="left", padx=(16, 0))
        ttk.Label(row2, textvariable=self.out_dir, style="MutedPanel.TLabel").pack(side="left", padx=8)
        ttk.Button(row2, text="Browse", style="Ghost.TButton",
                   command=self.pick_out_dir).pack(side="left")
        ttk.Button(row2, text="Same as video", style="Ghost.TButton",
                   command=lambda: self.out_dir.set("")).pack(side="left", padx=6)

        # 📊 progress + start button
        bottom = ttk.Frame(main, style="Dark.TFrame")
        bottom.pack(fill="x", pady=(14, 0))
        self.bar = ttk.Progressbar(bottom, variable=self.progress, maximum=100,
                                   style="Dark.Horizontal.TProgressbar")
        self.bar.pack(side="left", fill="x", expand=True)
        self.start_btn = ttk.Button(bottom, text="⚡  CONVERT", style="Orange.TButton",
                                    command=self.start)
        self.start_btn.pack(side="right", padx=(12, 0))

        ttk.Label(main, textvariable=self.status, style="Muted.TLabel").pack(fill="x", pady=(8, 0))

        # 🖱️ drop videos straight onto the window
        for widget in (main, queue_card, set_card, bottom):
            widget.bind("<Button-1>", lambda _e: self._drop_target())
        self.root.bind("<Button-4>", lambda _e: self.tree.yview_scroll(-1, "units"))
        self.root.bind("<Button-5>", lambda _e: self.tree.yview_scroll(1, "units"))

    def _drop_target(self) -> None:
        """💡 Small helper: clicking the queue area is harmless, so we just ignore it."""
        return None

    # ── 📥 adding files ────────────────────────────────────────
    def add_files(self) -> None:
        """📂 Ask the system for video files."""
        chosen = filedialog.askopenfilenames(title="Choose videos", filetypes=_filetypes())
        for f in chosen:
            self.add_path(f)

    def add_folder(self) -> None:
        """📁 Ask the system for a folder, then walk through it."""
        folder = filedialog.askdirectory(title="Choose a folder")
        if not folder:
            return
        for f in sorted(Path(folder).rglob("*")):
            if f.is_file() and f.suffix.lower() in tuple(f".{e}" for e in VIDEO_EXTENSIONS):
                self.add_path(f)

    def add_path(self, path: str) -> None:
        """✅ Add one file to the queue, unless it is already there."""
        p = Path(path)
        if p in self.queue:
            return
        if p.suffix.lower() not in tuple(f".{e}" for e in VIDEO_EXTENSIONS):
            self.status.set(f"⚠️  {p.name} is not a video, skipped")
            return
        self.queue.append(p)
        size = p.stat().st_size
        length = probe.duration(p)
        mins, secs = divmod(int(length), 60)
        self.tree.insert("", "end", iid=str(p),
                         values=(p.name, self._size(size), f"{mins}:{secs:02d}", "waiting"),
                         tags=("wait",))
        self.status.set(f"📋 {len(self.queue)} file(s) ready")

    def clear_files(self) -> None:
        """🧹 Empty the queue (only when we are not busy)."""
        if self.running:
            return
        self.queue.clear()
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.status.set("Queue cleared")

    @staticmethod
    def _size(num: float) -> str:
        """📏 12M / 1.4G"""
        for unit in ("B", "KB", "MB", "GB"):
            if abs(num) < 1024 or unit == "GB":
                return f"{num:.0f}{unit}" if unit == "B" else f"{num:.1f}{unit}"
            num /= 1024
        return f"{num:.1f}GB"

    def pick_out_dir(self) -> None:
        """📁 Choose where the MP3 files should go."""
        folder = filedialog.askdirectory(title="Where to save the MP3 files")
        if folder:
            self.out_dir.set(folder)

    # ── ⚙️ the work ────────────────────────────────────────────
    def _read_options(self) -> Options:
        """📖 Turn the widgets into an Options object."""
        return Options(
            bitrate=int(self.bitrate.get()),
            vbr_quality=2 if self.vbr.get() else None,
            normalize=self.normalize.get(),
            trim_silence=self.trim.get(),
            cover=self.cover.get(),
            out_dir=Path(self.out_dir.get()) if self.out_dir.get() else None,
            delete_source=self.delete_after.get(),
        )

    def start(self) -> None:
        """🚀 Kick off the batch in a background thread so the window stays alive."""
        if self.running:
            return
        if not self.queue:
            messagebox.showinfo(APP_NAME, "Add some video files first.")
            return
        try:
            probe.check_tools()
        except probe.ToolMissing as exc:
            messagebox.showerror(APP_NAME, str(exc))
            return

        options = self._read_options()
        self.running = True
        self.progress.set(0)
        self.start_btn.state(["disabled"])
        self.status.set("⚙️ working...")
        total = len(self.queue)
        finished = {"n": 0}

        def on_done(job) -> None:
            # 🔔 worker thread: only push to the queue, the UI reads it later
            finished["n"] += 1
            self.events.put(("done", job, finished["n"] * 100 / total))

        def work() -> None:
            try:
                run_batch(list(self.queue), options, on_done=on_done)
            except Exception as exc:                      # 🛡️ never crash silently
                self.events.put(("error", str(exc), 0))
            finally:
                self.events.put(("finished", None, 0))

        self.worker = threading.Thread(target=work, daemon=True)
        self.worker.start()
        self.root.after(80, self._pump_events)             # 🔄 keep reading messages

    def _pump_events(self) -> None:
        """📬 Move worker messages onto the screen. Runs on the UI thread only."""
        try:
            while True:
                kind, payload, percent = self.events.get_nowait()
                if kind == "done":
                    job = payload
                    if job.ok:
                        self.tree.item(str(job.source), values=(
                            Path(job.source).name, self._size(job.size),
                            f"{int(job.duration // 60)}:{int(job.duration % 60):02d}", "done"),
                            tags=("ok",))
                    else:
                        self.tree.item(str(job.source),
                                       values=(Path(job.source).name, "-", "-", job.error),
                                       tags=("fail",))
                    self.progress.set(percent)
                    self.status.set(f"✅ {int(percent)}% - {Path(payload.target).name}"
                                    if job.ok else f"❌ {payload.error}")
                elif kind == "error":
                    self.status.set(f"❌ {payload}")
                elif kind == "finished":
                    self.running = False
                    self.start_btn.state(["!disabled"])
                    self.progress.set(100)
                    good = sum(1 for r in self.results if r.ok)
                    self.status.set(f"✨ finished!")
                    if good:
                        messagebox.showinfo(APP_NAME, f"Finished! {good} file(s) converted.")
        except queue.Empty:
            pass
        finally:
            if self.running:
                self.root.after(80, self._pump_events)     # 🔁 ask again later


def run_gui(initial_files: list[str] | None = None) -> int:
    """🪟 Create the window and run the event loop. This is the app entry point."""

    # 🧠 no tkinter at all -> print how to fix it and stop.
    # Exit code 2 means "this is a setup problem", so scripts can react to it.
    if tk is None:
        print(TK_HELP.format(error=TK_ERROR or "tkinter is missing"), file=sys.stderr)
        return 2

    try:
        root = tk.Tk()
    except Exception as exc:
        # 🖥️ no display at all: a server, or a Wayland session without XWayland
        print(f"❌ cannot open a window: {exc}", file=sys.stderr)
        print("   Tip: use the terminal mode instead:  zaptone YOUR_VIDEO.mp4", file=sys.stderr)
        return 2

    ZapToneApp(root, initial_files)
    root.mainloop()
    return 0