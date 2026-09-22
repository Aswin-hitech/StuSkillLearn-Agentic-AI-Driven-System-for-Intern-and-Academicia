#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")/../frontend"
npm run dev -- --host 0.0.0.0
