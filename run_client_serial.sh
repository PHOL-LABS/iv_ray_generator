#!/usr/bin/env bash
set -euo pipefail

SERIAL=${SERIAL:-/dev/ttyUSB1}
BAUD=${BAUD:-921600}
BW=${BW:-0}

EXTRA=()
if [ "$BW" != "0" ]; then
  EXTRA+=(--bw)
fi

python3 stream_client.py --serial "$SERIAL" --serial-baud "$BAUD" "${EXTRA[@]}" "$@"
