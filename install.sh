#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════
#  🚀 install.sh - put ZapTone on this computer
#
#  Two ways to run it:
#      ./install.sh              install into your home folder, no root needed
#      ./install.sh --system     install into /usr, needs your password
#
#  What it does:
#      1. checks that ffmpeg and python are there
#      2. copies the python code
#      3. makes a "zaptone" command you can type
#      4. adds the icon to the menu
#      5. adds the Dolphin right click menu
# ═══════════════════════════════════════════════════════════════════════
set -euo pipefail

# ─── 📍 where are we? ───
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SYSTEM=0                                        # 🏠 or 🖥️ system-wide?

if [[ "${1:-}" == "--system" ]]; then
  SYSTEM=1
fi

if (( SYSTEM )); then
  # 🖥️ system install: everybody on this computer can use ZapTone
  BIN=/usr/bin
  LIBS=/usr/lib/plasmarip
  APPS=/usr/share/applications
  MENU=/usr/share/kservices6/dolphin/service-menus
  ICONS=/usr/share/icons/hicolor/256x256/apps
  DOCS=/usr/share/doc/plasmarip
  SUDO="sudo"                                   # 🔑 we need root for this
  MODE="system wide"
else
  # 🏠 home install: only for you, nothing needs a password
  BIN="$HOME/.local/bin"
  LIBS="$HOME/.local/lib/plasmarip"
  APPS="$HOME/.local/share/applications"
  MENU="$HOME/.local/share/dolphin/service-menus"
  ICONS="$HOME/.local/share/icons/hicolor/256x256/apps"
  DOCS="$HOME/.local/share/doc/plasmarip"
  SUDO=""
  MODE="your home folder"
fi

# ─── 💬 small talk ───
say()  { printf '\033[36m⚡\033[0m %s\n' "$*"; }         # 💬 news
ok()   { printf '\033[32m  ✅\033[0m %s\n' "$*"; }        # ✅ done
warn() { printf '\033[33m  ⚠️\033[0m  %s\n' "$*" >&2; }  # ⚠️ careful
die()  { printf '\033[31m❌\033[0m  %s\n' "$*" >&2; exit 1; }  # ❌ stop

printf '\n\033[1m⚡ ZapTone installer\033[0m  (installing into %s)\n\n' "$MODE"

# ─── 🔍 step 1: what do we need? ───
say "Checking what is already on this computer..."

command -v ffmpeg >/dev/null || die "ffmpeg is missing.
    Arch / CachyOS:   sudo pacman -S ffmpeg
    Ubuntu / Debian:   sudo apt install ffmpeg
    macOS:             brew install ffmpeg"

PYTHON=""
for candidate in python3 python; do            # 🐍 python3 first, then python
  if command -v "$candidate" >/dev/null; then
    PYTHON="$candidate"; break
  fi
done
[[ -n "$PYTHON" ]] || die "python3 is missing.
    Arch / CachyOS:   sudo pacman -S python tk
    Ubuntu / Debian:   sudo apt install python3 python3-tk"

ok "ffmpeg found:  $(command -v ffmpeg)"
ok "python found:  $($PYTHON --version 2>&1)"

# 🎨 tkinter is only needed for the window. Warn, but keep going.
if ! $PYTHON -c "import tkinter" 2>/dev/null; then
  warn "tkinter is not available, so the window will not open."
  warn "Install it:  sudo pacman -S tk   (Debian: sudo apt install python3-tk)"
  warn "The terminal version still works fine."
else
  ok "tkinter found, the window will work"
fi

# ─── 📂 step 2: make the folders ───
say "Creating folders…"
for folder in "$BIN" "$LIBS" "$APPS" "$MENU" "$ICONS" "$DOCS"; do
  $SUDO mkdir -p "$folder"
done
ok "folders are ready"

# ─── 📥 step 3: copy the code ───
say "Copying the program…"
rm -rf "$LIBS/zap_tone"
$SUDO cp -r "$ROOT/zap_tone" "$LIBS/"
# 🧹 никто не любит мусор в /usr
$SUDO find "$LIBS/zap_tone" -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true
ok "code is in $LIBS/zap_tone"

# ─── ⌨️ step 4: make the "zaptone" command ───
say "Making the zaptone command…"
cat > "$BIN/zaptone" <<LAUNCHER
#!/usr/bin/env bash
# 🚀 zap_tone launcher, made by install.sh
PYTHONPATH="$LIBS:\${PYTHONPATH:-}" exec $PYTHON -m zap_tone "\$@"
LAUNCHER
$SUDO chmod 755 "$BIN/zaptone"
ok "type 'zaptone' to start it"

# 🖱️ the drag and drop helper: reads file names until you press Ctrl+D
cat > "$BIN/zaptone-dragdrop" <<'DRAG'
#!/usr/bin/env bash
# 🖱️ drag and drop helper: reads file names from the terminal until Ctrl+D
PYTHONPATH="$LIBS:${PYTHONPATH:-}" exec $PYTHON -m zap_tone
DRAG
$SUDO chmod 755 "$BIN/zaptone-dragdrop"

# ─── 📋 step 5: menu entry ───
say "Adding it to the application menu…"
SED_NAME="ZapTone"
$SUDO cp "$ROOT/linux/zaptone.desktop" "$APPS/zaptone.desktop"
$SUDO chmod 644 "$APPS/zaptone.desktop"
ok "menu entry is in $APPS"

# ─── 🐬 step 6: Dolphin right click menu ───
if command -v dolphin >/dev/null; then
  say "Adding the Dolphin right click menu…"
  $SUDO cp "$ROOT/linux/dolphin-menu.desktop" "$MENU/zaptone.desktop"
  $SUDO chmod 644 "$MENU/zaptone.desktop"
  ok "right click a video in Dolphin to see ZapTone"
else
  warn "Dolphin was not found, skipping the right click menu"
fi

# ─── 🎨 step 7: the icon ───
ICON_SRC="$ROOT/linux/zaptone.png"
if [[ ! -f "$ICON_SRC" && -f "$ROOT/assets/icons/256.png" ]]; then
  say "Making the icon from the SVG…"
  if command -v rsvg-convert >/dev/null; then
    rsvg-convert -w 256 -h 256 "$ROOT/assets/icon.svg" -o "$ICON_SRC" 2>/dev/null && ok "icon rendered"
  fi
fi
if [[ -f "$ICON_SRC" ]]; then
  $SUDO cp "$ICON_SRC" "$ICONS/zaptone.png"
  $SUDO chmod 644 "$ICONS/zaptone.png"
  ok "icon installed"
fi

# ─── 📚 step 8: the docs ───
[[ -f "$ROOT/README.md" ]] && $SUDO cp "$ROOT/README.md" "$DOCS/README.md"
ok "documentation is in $DOCS"

# ─── 🔄 step 9: refresh the menus ───
command -v update-desktop-database >/dev/null && $SUDO update-desktop-database "$APPS" 2>/dev/null
command -v kbuildsycoca6 >/dev/null && kbuildsycoca6 --noincremental 2>/dev/null

# ─── 🎉 done ───
VERSION=$(grep -oE '__version__ = "[^"]+"' "$ROOT/zap_tone/__init__.py" | grep -oE '"[^"]+"' | tr -d '"')
cat <<EOF

✨ ZapTone $VERSION is ready!

  🖥️  Window:        zaptone --gui
  ⌨️  Terminal:      zaptone YOUR_VIDEO.mp4
  🐧 Menu:          search for "ZapTone" in your applications
  🐬 Dolphin:       right click a video -> "ZapTone"
  📖 All options:   zaptone --help

EOF

# 🛡️ предупреждаем только если папка с командой реально не в PATH
# ⚠️ важно: обе строки warn должны быть в одной цепочке &&,
#    иначе вторая напечатается всегда (был такой баг)
if (( SYSTEM == 0 )) && [[ ":$PATH:" != *":$BIN:"* ]]; then
  warn "$BIN is not in your PATH. Add this line to ~/.bashrc:"
  warn "    export PATH=\"\$HOME/.local/bin:\$PATH\""
fi

command -v dolphin >/dev/null && say "Restart Dolphin to see the new menu item."
exit 0