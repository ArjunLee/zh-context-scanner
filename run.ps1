# File: run.ps1
# Description: Launch zh-context-scanner with auto uv installation
# Author: Arjun Li
# Created: 2026-04-17

# Clear external VIRTUAL_ENV to prevent uv warning
$env:VIRTUAL_ENV = ""

# Check if uv is installed
$uvInstalled = Get-Command uv -ErrorAction SilentlyContinue
if (-not $uvInstalled) {
    Write-Host "[INFO] uv not found, installing..." -ForegroundColor Cyan
    try {
        irm https://astral.sh/uv/install.ps1 | iex
        Write-Host "[INFO] uv installed successfully" -ForegroundColor Green
    } catch {
        Write-Host "[ERROR] Failed to install uv: $_" -ForegroundColor Red
        exit 1
    }
}

# Sync dependencies
Write-Host "[INFO] Syncing dependencies..." -ForegroundColor Cyan
uv sync --quiet 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "[WARN] uv sync failed, continuing anyway..." -ForegroundColor Yellow
}

# Launch the tool
Write-Host "[INFO] Launching zh-context-scanner..." -ForegroundColor Cyan
uv run python -m src.main @args