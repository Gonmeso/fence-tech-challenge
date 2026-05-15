#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$REPO_ROOT/backend"

HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8000}"

exec uv run uvicorn main:app --host "$HOST" --port "$PORT" --reload --loop uvloop "$@"
