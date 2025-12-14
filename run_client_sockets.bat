@echo off
setlocal enabledelayedexpansion
if "%HOST%"=="" set HOST=127.0.0.1
if "%PORT%"=="" set PORT=5001
python stream_client.py --host %HOST% --port %PORT% %*

endlocal
