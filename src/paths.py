"""
File: paths.py
Description: Centralized path management for zh-context-scanner tool
Author: Arjun Li
Created: 2026-04-15
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


class PathRegistry:
    """Centralized path registry for the tool.

    Manages all tool-related paths: root, logs, reports, backups, config.
    """

    def __init__(self, tool_root: Path) -> None:
        self._tool_root = tool_root

    @property
    def tool_root(self) -> Path:
        """Tool root directory: tools/zh-context-scanner/"""
        return self._tool_root

    @property
    def backup_dir(self) -> Path:
        """Backup directory: tools/zh-context-scanner/.backup/"""
        return self._tool_root / ".backup"

    @property
    def log_dir(self) -> Path:
        """Log directory: tools/zh-context-scanner/.log/"""
        return self._tool_root / ".log"

    @property
    def log_file(self) -> Path:
        """Main log file: tools/zh-context-scanner/.log/zh-context-scanner.log"""
        return self.log_dir / "zh-context-scanner.log"

    @property
    def report_dir(self) -> Path:
        """Report directory: tools/zh-context-scanner/Report/"""
        return self._tool_root / "Report"

    def get_report_path(self, timestamp: str) -> Path:
        """Get report file path with timestamp.

        Args:
            timestamp: Timestamp string (e.g., "20260415_124237")

        Returns:
            Full path to report file
        """
        self.report_dir.mkdir(parents=True, exist_ok=True)
        return self.report_dir / f"scan_report_{timestamp}.json"

    @property
    def config_dir(self) -> Path:
        """Config directory: tools/zh-context-scanner/config/"""
        return self._tool_root / "config"

    @property
    def terminology_file(self) -> Path:
        """Terminology config: tools/zh-context-scanner/config/terminology.yaml"""
        return self.config_dir / "terminology.yaml"

    @property
    def env_local(self) -> Path:
        """Local environment file: tools/zh-context-scanner/.env.local"""
        return self._tool_root / ".env.local"

    @property
    def preferences_file(self) -> Path:
        """User preferences file in user config directory.

        Cross-platform (same as project configs):
            Windows: %APPDATA%/zh-context-scanner/config/preferences.json
            macOS: ~/Library/Application Support/zh-context-scanner/config/preferences.json
            Linux: ~/.config/zh-context-scanner/config/preferences.json
        """
        return get_user_config_dir() / "preferences.json"

    def ensure_directories(self) -> None:
        """Ensure all required directories exist."""
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.report_dir.mkdir(parents=True, exist_ok=True)
        self.config_dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def detect_tool_root(cls) -> Path:
        """Auto-detect tool root directory.

        Traverses up from CWD to find tools/zh-context-scanner/
        """
        cwd = Path.cwd()
        target = Path("tools") / "zh-context-scanner"

        # Check if CWD is already the tool root
        if (cwd / "src").exists() and (cwd / "pyproject.toml").exists():
            return cwd

        # Traverse up to find the tool root
        current = cwd
        for _ in range(6):
            if (current / target).exists():
                return current / target
            if current.parent == current:
                break
            current = current.parent

        # Fallback: check if we're inside the tool directory
        if "zh-context-scanner" in cwd.parts:
            idx = cwd.parts.index("zh-context-scanner")
            return Path(*cwd.parts[: idx + 1])

        return cwd / target


def get_user_config_dir() -> Path:
    """Get user config directory for storing project configs.

    Cross-platform:
        Windows: %APPDATA%/zh-context-scanner/config/
        macOS: ~/Library/Application Support/zh-context-scanner/config/
        Linux: ~/.config/zh-context-scanner/config/
    """
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA", Path.home()))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path.home() / ".config"

    return base / "zh-context-scanner" / "config"


def get_config_save_path(project_name: str, path_registry: PathRegistry) -> Path:
    """Get config save path, prefer user directory with tool directory fallback.

    Args:
        project_name: Project name for file naming
        path_registry: Path registry for tool directory fallback

    Returns:
        Path where config file should be saved
    """
    user_dir = get_user_config_dir()

    try:
        user_dir.mkdir(parents=True, exist_ok=True)
        return user_dir / f"{project_name}_Config.yaml"
    except PermissionError:
        pass

    tool_dir = path_registry.config_dir
    tool_dir.mkdir(parents=True, exist_ok=True)
    return tool_dir / f"{project_name}_Config.yaml"
