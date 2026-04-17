#!/bin/bash
# File: run.sh
# Description: Launch zh-context-scanner with auto uv installation (Linux/macOS)
# Author: Arjun Li
# Created: 2026-04-17

# Clear external VIRTUAL_ENV to prevent uv warning
unset VIRTUAL_ENV

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo -e "${CYAN}[INFO] uv not found, installing...${NC}"
    curl -LsSf https://astral.sh/uv/install.sh | sh
    if [ $? -ne 0 ]; then
        echo -e "${RED}[ERROR] Failed to install uv${NC}"
        exit 1
    fi
    # Reload PATH to include newly installed uv
    export PATH="$HOME/.local/bin:$PATH"
    echo -e "${GREEN}[INFO] uv installed successfully${NC}"
fi

# Sync dependencies
echo -e "${CYAN}[INFO] Syncing dependencies...${NC}"
uv sync --quiet 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}[WARN] uv sync failed, continuing anyway...${NC}"
fi

# Launch the tool
echo -e "${CYAN}[INFO] Launching zh-context-scanner...${NC}"
uv run python -m src.main "$@"