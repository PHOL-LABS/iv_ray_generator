#!/usr/bin/env bash
set -euo pipefail

HOST=${HOST:-127.0.0.1}
PORT=${PORT:-5001}
BW=${BW:-0}

EXTRA=()
if [ "$BW" != "0" ]; then
  EXTRA+=(--bw)
fi

python stream_client.py --host "$HOST" --port "$PORT" "${EXTRA[@]}" "$@"
