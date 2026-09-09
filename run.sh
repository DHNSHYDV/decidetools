#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"

# Create virtual environment if not already present
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment in $VENV_DIR..."
    python3 -m venv "$VENV_DIR"
    "$VENV_DIR/bin/pip" install --upgrade pip
    echo "Installing required packages..."
    "$VENV_DIR/bin/pip" install -r "$SCRIPT_DIR/requirements.txt"
fi

# Dispatch command: CLI or Web
if [ "$1" = "cli" ]; then
    shift
    exec "$VENV_DIR/bin/python3" "$SCRIPT_DIR/cli.py" "$@"
else
    echo "========================================================="
    echo "   Decide Group Of Solutions - Multi-Tool SaaS Suite     "
    echo "   Dashboard: http://127.0.0.1:5000                      "
    echo "========================================================="
    exec "$VENV_DIR/bin/python3" "$SCRIPT_DIR/app.py"
fi
