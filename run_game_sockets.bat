@echo off
setlocal enabledelayedexpansion
if "%PORT%"=="" set PORT=5001
if "%BW%"=="" set BW=0
set CMD=python main.py --stream --stream-port %PORT%
if not "%BW%"=="0" set CMD=!CMD! --bw-stream
%CMD% %*
endlocal
