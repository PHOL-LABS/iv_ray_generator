@echo off
setlocal enabledelayedexpansion
if "%HOST%"=="" set HOST=127.0.0.1
if "%PORT%"=="" set PORT=5001
if "%BW%"=="" set BW=0
set CMD=python stream_client.py --host %HOST% --port %PORT%
if not "%BW%"=="0" set CMD=!CMD! --bw
%CMD% %*
endlocal
