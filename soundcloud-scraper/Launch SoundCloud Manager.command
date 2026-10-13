#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if [[ ! -x "$SCRIPT_DIR/.venv/bin/python" ]]; then
  /usr/bin/osascript -e 'display dialog "Setup has not been completed. Double-click Install SoundCloud Manager.command first." buttons {"OK"} default button "OK" with icon caution'
  exit 1
fi

cd "$SCRIPT_DIR"
exec "$SCRIPT_DIR/.venv/bin/python" "$SCRIPT_DIR/soundcloud_easy_start.py"
