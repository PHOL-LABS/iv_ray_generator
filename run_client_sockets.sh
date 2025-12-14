#!/usr/bin/env bash
set -euo pipefail

# HOST, PORT, and SERIAL can be provided via env vars.
HOST=${HOST:-127.0.0.1}
PORT=${PORT:-5001}
BAUD=${BAUD:-115200}
python stream_client.py --host "$HOST" --port "$PORT" "$@"
