@echo off
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
    python -X utf8 distribution\start.py
) else (
    py -3 -X utf8 distribution\start.py
)
pause
