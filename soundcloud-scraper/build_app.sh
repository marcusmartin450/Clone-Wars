#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_DIR="$SCRIPT_DIR/scdl.app"
RESOURCES_DIR="$APP_DIR/Contents/Resources"
YTDLP_SOURCE_DIR="$SCRIPT_DIR/.venv/lib/python3.14/site-packages/yt_dlp"

mkdir -p "$RESOURCES_DIR"

cp "$SCRIPT_DIR/scdl.py" "$RESOURCES_DIR/scdl.py"
cp "$SCRIPT_DIR/soundcloud_backend.py" "$RESOURCES_DIR/soundcloud_backend.py"
cp "$SCRIPT_DIR/soundcloud_scraper_backend.py" "$RESOURCES_DIR/soundcloud_scraper_backend.py"
cp "$SCRIPT_DIR/soundcloud_gui.py" "$RESOURCES_DIR/soundcloud_gui.py"
cp "$SCRIPT_DIR/sc_likes_scraper4_organized_outputs.py" "$RESOURCES_DIR/sc_likes_scraper4_organized_outputs.py"
rm -rf "$RESOURCES_DIR/yt_dlp"
cp -R "$YTDLP_SOURCE_DIR" "$RESOURCES_DIR/yt_dlp"

cat > "$RESOURCES_DIR/README-share.txt" <<'EOF'
This app bundle includes the downloader script and the yt-dlp Python package.

For another Mac to use it successfully:
1. Python 3 must be available as `python3`.
2. FFmpeg must be installed and available on PATH.

The app saves downloads into the current Mac user's Downloads folder.
EOF
