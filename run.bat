@echo off
REM File: run.bat
REM Description: Launch zh-context-scanner with auto uv installation
REM Author: Arjun Li
REM Created: 2026-04-17

setlocal enabledelayedexpansion

REM Clear external VIRTUAL_ENV to prevent uv warning
set VIRTUAL_ENV=

REM Check if uv is installed
where uv >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] uv not found, installing...
    powershell -Command "irm https://astral.sh/uv/install.ps1 | iex"
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install uv
        exit /b 1
    )
    echo [INFO] uv installed successfully
)

REM Sync dependencies
echo [INFO] Syncing dependencies...
uv sync --quiet
if %errorlevel% neq 0 (
    echo [WARN] uv sync failed, continuing anyway...
)

REM Launch the tool
echo [INFO] Launching zh-context-scanner...
uv run python -m src.main %*

endlocal