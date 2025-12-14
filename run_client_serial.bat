@echo off
setlocal enabledelayedexpansion

python stream_client.py --serial COM36 --serial-baud 921600

endlocal
