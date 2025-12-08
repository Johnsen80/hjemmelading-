#!/usr/bin/env bash
# Cross-platform helper (Unix-like) to run the headless smoke test.
# Usage:
#   ./tools/run_smoke.sh          # runs using .venv/python if present or `python3`
#   ./tools/run_smoke.sh create   # create a venv at .venv if missing (requires python3 on PATH)

set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
PY_VENV="$ROOT/.venv/bin/python"
PY_SYS=""

if [ "$1" = "create" ] 2>/dev/null; then
  if command -v python3 >/dev/null 2>&1; then
    python3 -m venv "$ROOT/.venv"
  else
    echo "No python3 on PATH to create a venv" >&2
    exit 1
  fi
fi

if [ -x "$PY_VENV" ]; then
  PY_SYS="$PY_VENV"
elif command -v python3 >/dev/null 2>&1; then
  PY_SYS=$(command -v python3)
elif command -v python >/dev/null 2>&1; then
  PY_SYS=$(command -v python)
else
  echo "No Python found. Install Python or create a .venv" >&2
  exit 1
fi

echo "Using Python: $PY_SYS"
"$PY_SYS" "$ROOT/tools/headless_smoke_test.py" "$@"
