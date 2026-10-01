#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════
#  📦 build_appimage.sh - build one AppImage for Linux
#
#  What it makes:
#     dist/ZapTone-<version>-x86_64.AppImage
#
#  How it works:
#     1. copy the python code into AppDir/usr/lib
#     2. write a small launcher script (AppRun)
#     3. add the .desktop file and the icons
#     4. compress everything with appimagetool
#
#  ffmpeg is NOT packed inside. It stays on the host computer, because
#  ffmpeg is 80 MB and almost every Linux already has it. This keeps the
#  AppImage around 12 MB instead of 95 MB.
# ═══════════════════════════════════════════════════════════════════════
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APPDIR="$ROOT/AppDir"                    # 📦 staging folder that appimagetool wants
DIST="$ROOT/dist"                        # 📤 final output folder
VERSION=$(grep -oP '__version__\s*=\s*"\K[^"]+' "$ROOT/zap_tone/__init__.py")
ARCH="${ARCH:-x86_64}"                  # 🏗️ which cpu we build for
APP_NAME="ZapTone"

say()  { printf '\033[36m📦\033[0m %s\n' "$*"; }
warn() { printf '\033[33m⚠️\033[0m  %s\n' "$*" >&2; }
die()  { printf '\033[31m❌\033[0m  %s\n' "$*" >&2; exit 1; }

# ─── 🔍 проверки ───
say "ZapTone $VERSION for $ARCH"
command -v appimagetool >/dev/null || die "appimagetool not found.
  Download it once:  https://github.com/AppImage/AppImageKit/releases
  or use the CI build, it has the tool already."
[[ -d "$ROOT/zap_tone" ]] || die "zap_tone folder not found, wrong directory?"

# ─── 🧹 clean staging ───
rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/lib" "$APPDIR/usr/share/applications" \
         "$APPDIR/usr/share/icons/hicolor/256x256/apps" \
         "$APPDIR/usr/share/metainfo" "$DIST"

# ─── 📥 код приложения (весь пакет целиком) ───
cp -r "$ROOT/zap_tone" "$APPDIR/usr/lib/"
# 🧹 чистим кэш байткода, он не нужен внутри AppImage
find "$APPDIR/usr/lib" -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true

# ─── 🚀 launcher (AppRun) ───
# 🐍 ищем python: сначала системный, потом тот, что лежит внутри образа
cat > "$APPDIR/AppRun" <<'LAUNCH'
#!/usr/bin/env bash
# 🚀 ZapTone AppRun - the file AppImage runs when you double click it
HERE="$(dirname "$(readlink -f "${0}")")"
# 📚 our own copy of the code
if [ -d "$HERE/usr/lib/zap_tone" ]; then
  export PYTHONPATH="$HERE/usr/lib:${PYTHONPATH:-}"
fi
# 🐍 choose an interpreter: bundled first, then the system one
for py in "$HERE/usr/bin/python3" python3 python; do
  if command -v "$py" >/dev/null 2>&1; then
    exec "$py" -m zap_tone "$@"
  fi
done
# 🆘 no python at all: tell the user exactly what to install
echo "❌ Python 3 was not found on this computer."
echo "   Install it:  sudo pacman -S python   (Debian/Ubuntu: sudo apt install python3)"
exit 1
LAUNCH
chmod +x "$APPDIR/AppRun"

# ─── 📋 .desktop для меню приложений ───
sed -e "s|^Exec=.*|Exec=AppRun|" \
    -e "s|^Name=.*|Name=ZapTone|" \
    -e "s|^Icon=.*|Icon=zaptone|" \
    "$ROOT/linux/zaptone.desktop" > "$APPDIR/usr/share/applications/zaptone.desktop"

# ⚠️ ВАЖНО: appimagetool ищет .desktop В КОРНЕ AppDir, без этого он пишет
#    "Desktop file not found, aborting" и не собирает образ вообще.
cp "$APPDIR/usr/share/applications/zaptone.desktop" "$APPDIR/zaptone.desktop"

# ─── 🎨 иконки для hicolor-темы (KDE/GTK найдут их сами) ───
if [[ -f "$ROOT/linux/zaptone.png" ]]; then
  cp "$ROOT/linux/zaptone.png" \
     "$APPDIR/usr/share/icons/hicolor/256x256/apps/zaptone.png"
fi

# ─── 📦 метаинфо (нужно для GNOME Software / KDE Discover) ───
if [[ -f "$ROOT/linux/zaptone.appdata.xml" ]]; then
  cp "$ROOT/linux/zaptone.appdata.xml" "$APPDIR/usr/share/metainfo/zaptone.appdata.xml"
fi

# ─── 🔨 собираем ───
OUT="$DIST/${APP_NAME}-${VERSION}-${ARCH}.AppImage"
say "running appimagetool, this takes about 30 seconds…"
appimagetool --no-appstream                      "$APPDIR" "$OUT"

# ─── 🧹 уборка ───
rm -rf "$APPDIR"

# ─── ✅ результат ───
chmod +x "$OUT"
SIZE=$(du -h "$OUT" | cut -f1)
printf '\n\033[32m✅\033[0m built: %s  (%s)\n' "$OUT" "$SIZE"
say "test it:  $OUT --help"
say "run it:   $OUT"