#!/usr/bin/env bash
# =============================================================================
# SecureFS — Linux GUI Launcher Script
# =============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Prioritize local virtual environments
if [ -f "$SCRIPT_DIR/.venv/bin/python" ]; then
    PYTHON_BIN="$SCRIPT_DIR/.venv/bin/python"
elif [ -f "$SCRIPT_DIR/venv/bin/python" ]; then
    PYTHON_BIN="$SCRIPT_DIR/venv/bin/python"
else
    PYTHON_BIN="python3"
fi

echo "🛡️ Starting SecureFS Encrypted File Vault using: $PYTHON_BIN"
exec "$PYTHON_BIN" gui/main.py "$@"
