#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
export PATH="/usr/local/bin:/opt/homebrew/bin:$PATH"

exec "$SCRIPT_DIR/.venv/bin/python" "$SCRIPT_DIR/scdl.py" "$@"
