#!/usr/bin/env bash
set -euo pipefail

SERIAL=${SERIAL:/dev/ttyUSB1}

BAUD=${BAUD:-921600}

python3 stream_client.py --serial "$SERIAL" --serial-baud "$BAUD" "$@"
