"""
File: __init__.py
Description: zh-context-scanner package initialization
Author: Arjun Li
Created: 2026-04-15
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version


def _get_version() -> str:
    try:
        return version("zh-context-scanner")
    except PackageNotFoundError:
        from pathlib import Path

        import tomllib
        pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
        if pyproject_path.exists():
            data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
            return data.get("project", {}).get("version", "unknown")
        return "unknown"


__version__ = _get_version()
