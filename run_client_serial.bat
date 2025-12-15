@echo off
setlocal enabledelayedexpansion
if "%SERIAL%"=="" set SERIAL=COM36
if "%BAUD%"=="" set BAUD=921600
if "%BW%"=="" set BW=0
set CMD=python stream_client.py --serial %SERIAL% --serial-baud %BAUD%
if not "%BW%"=="0" set CMD=!CMD! --bw
%CMD% %*

REM python stream_client.py --serial COM36 --serial-baud 921600 --bw
endlocal
