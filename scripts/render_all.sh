#!/usr/bin/env bash
# Render every segment (preview by default). Skips up-to-date silent MP4s; use --force to rebuild all.
# Full HD: MANIM_HD=1 ./scripts/render_all.sh
# Extra arguments are forwarded to render_segments.py (e.g. --force, --segment bit13).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
exec python3 "${ROOT}/scripts/render_segments.py" "$@"
