#!/usr/bin/env bash
# Full-quality export (HD). Skips up-to-date silent MP4s and muxes by default.
#
# Examples:
#   ./scripts/render_and_build.sh                    # HD render (skip fresh) → mux → assemble
#   ./scripts/render_and_build.sh --segment bit13    # only bit13 (+ assemble all)
#   ./scripts/render_and_build.sh --force            # re-render/mux everything
#   ./scripts/render_and_build.sh --dry-run
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

RENDER_ARGS=()
MUX_ARGS=()
DRY=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY=1; RENDER_ARGS+=(--dry-run); MUX_ARGS+=(--dry-run); shift ;;
    --segment)
      RENDER_ARGS+=(--segment "$2")
      MUX_ARGS+=(--segment "$2")
      shift 2
      ;;
    --force)
      RENDER_ARGS+=(--force)
      MUX_ARGS+=(--force)
      shift
      ;;
    --stale)
      # Deprecated no-op: skip-up-to-date is now the default.
      shift
      ;;
    *)
      RENDER_ARGS+=("$1")
      shift
      ;;
  esac
done

MANIM_HD=1 python3 "${ROOT}/scripts/render_segments.py" ${RENDER_ARGS[@]+"${RENDER_ARGS[@]}"}
if [[ "$DRY" -eq 0 ]]; then
  python3 "${ROOT}/scripts/mux_audio.py" ${MUX_ARGS[@]+"${MUX_ARGS[@]}"}
  python3 "${ROOT}/scripts/assemble_final.py" --config "${ROOT}/config/final_assembly.json"
fi
