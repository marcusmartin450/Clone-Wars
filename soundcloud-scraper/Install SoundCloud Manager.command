#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_FILE="$SCRIPT_DIR/setup.log"
NONINTERACTIVE="${SOUNDCLOUD_SETUP_NONINTERACTIVE:-0}"
NO_LAUNCH="${SOUNDCLOUD_SETUP_NO_LAUNCH:-0}"

message() {
  local text="$1"
  printf '%s\n' "$text" | tee -a "$LOG_FILE"
  if [[ "$NONINTERACTIVE" != "1" ]]; then
    /usr/bin/osascript -e 'on run argv' -e 'display dialog (item 1 of argv) buttons {"OK"} default button "OK"' -e 'end run' "$text" >/dev/null
  fi
}

open_download() {
  local url="$1"
  local text="$2"
  if [[ "$NONINTERACTIVE" != "1" ]]; then
    /usr/bin/open "$url"
  fi
  message "$text"
  exit 1
}

find_brew() {
  if command -v brew >/dev/null 2>&1; then command -v brew; return; fi
  if [[ -x /opt/homebrew/bin/brew ]]; then echo /opt/homebrew/bin/brew; return; fi
  if [[ -x /usr/local/bin/brew ]]; then echo /usr/local/bin/brew; return; fi
  return 1
}

: > "$LOG_FILE"
message "SoundCloud Manager setup is starting. Keep this window open."
BREW_BIN="$(find_brew || true)"

if ! command -v python3 >/dev/null 2>&1; then
  if [[ -n "$BREW_BIN" ]]; then
    message "Python 3 is missing. Homebrew will install it now."
    "$BREW_BIN" install python 2>&1 | tee -a "$LOG_FILE"
    export PATH="$(dirname "$BREW_BIN"):$PATH"
  else
    open_download "https://www.python.org/downloads/macos/" "Python 3 is required. Install it from the official page that opened, then double-click this installer again."
  fi
fi

if [[ ! -x "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser" && ! -x "$HOME/Applications/Brave Browser.app/Contents/MacOS/Brave Browser" ]]; then
  if [[ -n "$BREW_BIN" ]]; then
    message "Brave Browser is missing. Homebrew will install it now."
    "$BREW_BIN" install --cask brave-browser 2>&1 | tee -a "$LOG_FILE"
  else
    open_download "https://brave.com/download/" "Brave Browser is required for private scraping. Install it from the page that opened, then double-click this installer again."
  fi
fi

if ! command -v ffmpeg >/dev/null 2>&1; then
  if [[ -n "$BREW_BIN" ]]; then
    message "FFmpeg is missing. Homebrew will install it now."
    "$BREW_BIN" install ffmpeg 2>&1 | tee -a "$LOG_FILE"
  else
    open_download "https://brew.sh/" "FFmpeg is required for MP3 downloads. Install Homebrew from the official page that opened, then double-click this installer again."
  fi
fi

message "Downloading the private Python environment and app packages."
python3 -m venv "$SCRIPT_DIR/.venv" 2>&1 | tee -a "$LOG_FILE"
"$SCRIPT_DIR/.venv/bin/python" -m pip install --upgrade pip 2>&1 | tee -a "$LOG_FILE"
"$SCRIPT_DIR/.venv/bin/python" -m pip install -r "$SCRIPT_DIR/requirements.txt" 2>&1 | tee -a "$LOG_FILE"

PYTHONDONTWRITEBYTECODE=1 "$SCRIPT_DIR/.venv/bin/python" -c "import openpyxl, playwright, yt_dlp; import soundcloud_easy_start; ready, text = soundcloud_easy_start.app.setup_message(); assert ready, text; print(text)" 2>&1 | tee -a "$LOG_FILE"

chmod +x "$SCRIPT_DIR/Launch SoundCloud Manager.command"
chmod +x "$SCRIPT_DIR/SoundCloud Manager.app/Contents/MacOS/SoundCloud Manager"
message "Setup finished. From now on, open SoundCloud Manager.app."

if [[ "$NO_LAUNCH" != "1" ]]; then
  /usr/bin/open "$SCRIPT_DIR/SoundCloud Manager.app"
fi
