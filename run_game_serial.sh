#!/usr/bin/env bash
set -euo pipefail

# SERIAL should be provided via env var or CLI override.
SERIAL=${SERIAL:-/dev/ttyUSB0}
BAUD=${BAUD:-921600}
BW=${BW:-0}

EXTRA=()
if [ "$BW" != "0" ]; then
  EXTRA+=(--bw-stream)
fi

python3 main.py --stream --stream-serial "$SERIAL" --stream-serial-baud "$BAUD" "${EXTRA[@]}" "$@"
