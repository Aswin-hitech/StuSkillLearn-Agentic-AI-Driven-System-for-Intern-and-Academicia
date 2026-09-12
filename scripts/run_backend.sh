#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")/../backend"
if [ -x .venv/bin/python ]; then
  exec .venv/bin/python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
fi
exec python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
