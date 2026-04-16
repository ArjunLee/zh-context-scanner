# File: run.ps1
# Description: Launch zh-context-scanner without VIRTUAL_ENV interference
# Author: Arjun Li
# Created: 2026-04-15

# Clear external VIRTUAL_ENV to prevent uv warning
$env:VIRTUAL_ENV = ""

# Run the tool with project's own .venv
uv run python -m src.main $args
