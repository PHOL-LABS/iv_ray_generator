#!/usr/bin/env bash
set -euo pipefail

PORT=${PORT:-5001}
BW=${BW:-0}

EXTRA=()
if [ "$BW" != "0" ]; then
  EXTRA+=(--bw-stream)
fi

python main.py --stream --stream-port "$PORT" "${EXTRA[@]}" "$@"
