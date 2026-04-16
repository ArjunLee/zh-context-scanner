@echo off
REM File: run.bat
REM Description: Launch zh-context-scanner without VIRTUAL_ENV interference
REM Author: Arjun Li
REM Created: 2026-04-15

REM Clear external VIRTUAL_ENV to prevent uv warning
set VIRTUAL_ENV=

REM Run the tool with project's own .venv
uv run python -m src.main %*
