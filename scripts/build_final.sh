#!/usr/bin/env bash
# Mux segments then assemble the full cut with music.
#
# Incremental by default (skip up-to-date muxes):
#   ./scripts/build_final.sh
#   ./scripts/build_final.sh --segment bit13
#   ./scripts/build_final.sh --force              # remux everything
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

MUX_ARGS=()
FORCE=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --stale)
      # Deprecated no-op: skip-up-to-date is now the default.
      shift
      ;;
    --force) FORCE=1; shift ;;
    --dry-run) MUX_ARGS+=("$1"); shift ;;
    --segment)
      MUX_ARGS+=(--segment "$2")
      shift 2
      ;;
    *) MUX_ARGS+=("$1"); shift ;;
  esac
done

if [[ "$FORCE" -eq 1 ]]; then
  MUX_ARGS+=(--force)
fi

python3 "${ROOT}/scripts/mux_audio.py" --manifest "${ROOT}/config/audio_manifest.json" ${MUX_ARGS[@]+"${MUX_ARGS[@]}"}
python3 "${ROOT}/scripts/assemble_final.py" --config "${ROOT}/config/final_assembly.json"
