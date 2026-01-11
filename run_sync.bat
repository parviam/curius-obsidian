@echo off
REM Curius-Obsidian Sync Runner
REM %~dp0 auto-detects this script's directory
cd /d "%~dp0"
uv run python main.py >> sync_log.txt 2>&1
