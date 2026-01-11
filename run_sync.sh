#!/bin/bash
# Curius-Obsidian Sync Runner (Mac/Linux)
# This script auto-detects its directory

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

uv run python main.py >> sync_log.txt 2>&1
