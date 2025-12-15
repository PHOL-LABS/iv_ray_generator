@echo off
setlocal enabledelayedexpansion
if "%SERIAL%"=="" set SERIAL=COM35
if "%BAUD%"=="" set BAUD=921600
if "%BW%"=="" set BW=0
set CMD=python main.py --stream --stream-serial %SERIAL% --stream-serial-baud %BAUD%
if not "%BW%"=="0" set CMD=!CMD! --bw-stream
%CMD% %*

REM python main.py --stream --stream-serial COM35 --stream-serial-baud 921600 --bw-stream
endlocal
