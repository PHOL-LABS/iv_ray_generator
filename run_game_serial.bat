@echo off
setlocal enabledelayedexpansion
python main.py --stream --stream-serial COM35 --stream-serial-baud 921600
endlocal
