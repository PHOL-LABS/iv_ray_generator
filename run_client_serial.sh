#!/usr/bin/env bash
set -euo pipefail

SERIAL=${SERIAL:/dev/ttyUSB1}

BAUD=${BAUD:-115200}

python stream_client.py --serial "$SERIAL" --serial-baud "$BAUD" "$@"
