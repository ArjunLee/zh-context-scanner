"""
File: config.py
Description: Configuration management (CLI args, project settings, external project support)
Author: Arjun Li
Created: 2026-04-15
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Self

from src.paths import PathRegistry

# Try to import yaml, optional dependency
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


@dataclass
class ScanTarget:
    """Single scan target configuration."""
    path: str                           # Relative path from root
    extensions: list[str]               # File extensions to scan
    exclude_subdirs: list[str] = field(default_factory=list)  # Subdirectories to exclude


@dataclass
class Config:
    """Application configuration."""
    root_path: Path                     # Project root directory
    backup_dir: Path                    # Backup directory path
    project_name: str = "VaultSave"     # Project name (for display)
    scan_targets: list[ScanTarget] = field(default_factory=lambda: DEFAULT_VAULTSAVE_TARGETS)
    global_excludes: list[str] = field(default_factory=lambda: DEFAULT_GLOBAL_EXCLUDES)

    # LLM Configuration (OpenAI-compatible API)
    llm_api_key: str | None = None      # LLM API key (supports DeepSeek, OpenAI, etc.)
    llm_base_url: str = ""              # LLM base URL (standard naming)
    llm_model: str = ""                 # LLM model name
    llm_force_model: bool = False       # Force use configured model (skip auto-binding)

    json_output: bool = False           # Output JSON format
    yes_mode: bool = False              # Skip confirmations
    restore_target: str | None = None   # Restore backup target
    restore_file: str | None = None     # Single file to restore
    input_report: Path | None = None    # Input report for --replace

    @classmethod
    def from_cli_args(cls, args: argparse.Namespace) -> Self:
        """Create config from CLI arguments."""
        root = Path(args.root) if args.root else cls._detect_root()
        tool_root = PathRegistry.detect_tool_root()
        path_registry = PathRegistry(tool_root)

        # Load config from file to get project name and global excludes
        config_data = cls._load_config_file(args.config)

        # Load LLM configuration
        llm_config = cls._load_llm_config(path_registry)

        return cls(
            root_path=root,
            project_name=config_data.get("project_name", "VaultSave"),
            scan_targets=config_data.get("scan_targets", DEFAULT_VAULTSAVE_TARGETS),
            global_excludes=config_data.get("global_excludes", DEFAULT_GLOBAL_EXCLUDES),
            backup_dir=path_registry.backup_dir,
            llm_api_key=llm_config["api_key"],
            llm_base_url=llm_config["base_url"],
            llm_model=llm_config["model"],
            llm_force_model=llm_config["force_model"],
            json_output=args.json,
            yes_mode=args.yes,
            restore_target=args.restore,
            restore_file=args.restore_file,
            input_report=Path(args.input) if args.input else None,
        )

    @staticmethod
    def _detect_root() -> Path:
        """Auto-detect project root (traverse up to find root with multiple indicators)."""
        cwd = Path.cwd()
        indicators = ["pyproject.toml", "Cargo.toml", "package.json", ".git"]

        # Traverse up to 4 levels to find project root
        current = cwd
        for _ in range(4):
            # Count how many indicators exist at this level
            count = sum(1 for ind in indicators if (current / ind).exists())
            # If 2+ indicators exist, this is likely the project root
            if count >= 2:
                return current
            if current.parent == current:  # Reached filesystem root
                break
            current = current.parent

        # Fallback: check cwd and its immediate parent
        for path in [cwd, cwd.parent]:
            for indicator in indicators:
                if (path / indicator).exists():
                    return path
        return cwd

    @staticmethod
    def _get_scan_targets(config_file: str | None) -> list[ScanTarget]:
        """Get scan targets from config file (YAML or JSON) or defaults."""
        if config_file:
            config_path = Path(config_file)
            if config_path.exists():
                content = config_path.read_text(encoding="utf-8")

                # Try YAML first
                if YAML_AVAILABLE and (config_path.suffix in ['.yaml', '.yml'] or content.strip().startswith('#') or ':' in content):
                    try:
                        data = yaml.safe_load(content)
                        return [ScanTarget(**t) for t in data.get("scan_targets", [])]
                    except Exception as e:
                        print(f"Warning: Failed to parse YAML config: {e}")
                        print("Falling back to default VaultSave targets")

                # Fallback to JSON
                try:
                    data = json.loads(content)
                    return [ScanTarget(**t) for t in data.get("targets", [])]
                except Exception:
                    print(f"Warning: Failed to parse JSON config: {config_path}")
                    print("Falling back to default VaultSave targets")

        return DEFAULT_VAULTSAVE_TARGETS

    @staticmethod
    def _load_config_file(config_file: str | None) -> dict:
        """Load configuration from YAML or JSON file."""
        if not config_file:
            return {}

        config_path = Path(config_file)
        if not config_path.exists():
            return {}

        content = config_path.read_text(encoding="utf-8")

        # Try YAML first
        if YAML_AVAILABLE and (config_path.suffix in ['.yaml', '.yml'] or content.strip().startswith('#') or ':' in content):
            try:
                return yaml.safe_load(content) or {}
            except Exception as e:
                print(f"Warning: Failed to parse YAML config: {e}")

        # Fallback to JSON
        try:
            return json.loads(content) or {}
        except Exception:
            print(f"Warning: Failed to parse config file: {config_path}")

        return {}

    @staticmethod
    def _get_global_excludes() -> list[str]:
        """Get global exclude patterns."""
        return DEFAULT_GLOBAL_EXCLUDES

    @staticmethod
    def _load_llm_config(path_registry: PathRegistry) -> dict:
        """Load LLM configuration from .env.local file.
        
        Supports multiple LLM providers with OpenAI-compatible API:
        - DeepSeek (default): https://api.deepseek.com
        - OpenAI: https://api.openai.com/v1
        - Azure OpenAI: Custom endpoint
        - Other compatible services
        
        Environment variables (priority order):
        1. LLM_API_KEY - Universal API key (recommended)
        2. DEEPSEEK_API_KEY - DeepSeek specific (deprecated, use LLM_API_KEY)
        3. OPENAI_API_KEY - OpenAI specific (deprecated, use LLM_API_KEY)
        
        Returns:
            dict with keys: api_key, base_url, model
        """
        env_path = path_registry.env_local
        config = {
            "api_key": None,
            "base_url": None,  # Must be set in .env.local
            "model": None,  # Must be set in .env.local
            "force_model": False,  # Optional: skip auto-binding
        }

        if not env_path.exists():
            return config

        content = env_path.read_text(encoding="utf-8")

        for line in content.splitlines():
            line = line.strip()
            if line.startswith("#") or not line:
                continue

            if "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()

            # Universal API key (recommended)
            if key == "LLM_API_KEY":
                config["api_key"] = value
            # DeepSeek specific (backward compatible)
            elif key == "DEEPSEEK_API_KEY":
                config["api_key"] = config["api_key"] or value
            # OpenAI specific (backward compatible)
            elif key == "OPENAI_API_KEY":
                config["api_key"] = config["api_key"] or value
            # Legacy key name (backward compatible)
            elif key == "i18n_auto_translate_k":
                config["api_key"] = config["api_key"] or value
            # Custom Base URL (standard naming)
            elif key == "LLM_BASE_URL":
                config["base_url"] = value
            # Custom model name
            elif key == "LLM_MODEL":
                config["model"] = value
            # Force model (skip auto-binding)
            elif key == "LLM_FORCE_MODEL":
                config["force_model"] = value.lower() in ("true", "1", "yes")

        return config


# VaultSave project default scan targets
DEFAULT_VAULTSAVE_TARGETS: list[ScanTarget] = [
    ScanTarget(
        path="apps/desktop/ui",
        extensions=[".tsx", ".ts", ".jsx", ".js", ".css"],
        exclude_subdirs=["locales", "DebugPage", "dist", "node_modules"],
    ),
    ScanTarget(
        path="apps/desktop/src-tauri/src",
        extensions=[".rs"],
        exclude_subdirs=["target", "gen"],
    ),
    ScanTarget(
        path="scripts/pipeline",
        extensions=[".py"],
        exclude_subdirs=["__pycache__"],
    ),
    ScanTarget(
        path="ci_pipeline.py",
        extensions=[".py"],
        exclude_subdirs=[],
    ),
    ScanTarget(
        path="shared",
        extensions=[".toml"],
        exclude_subdirs=[],
    ),
    ScanTarget(
        path="sync_app_meta.py",
        extensions=[".py"],
        exclude_subdirs=[],
    ),
]

# Global exclude patterns
DEFAULT_GLOBAL_EXCLUDES: list[str] = [
    "dist",
    "node_modules",
    "target",
    "gen",
    ".git",
    "__pycache__",
    ".venv",
]


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        prog="zh-scanner",
        description="CLI/TUI tool for detecting and translating Chinese text in source code",
    )

    # Positional/optional arguments
    parser.add_argument("--root", help="Project root directory (auto-detected if not specified)")
    parser.add_argument("--config", help="YAML/JSON config file for custom scan targets (e.g., my_project.yaml)")

    # Scan mode
    parser.add_argument("--scan", action="store_true", help="Run scan and output report")
    parser.add_argument("--incremental", action="store_true", help="Incremental scan (based on mtime)")
    parser.add_argument("--input", help="Input report JSON file for --replace")

    # Replace mode
    parser.add_argument("--replace", action="store_true", help="Execute replacements from report")
    parser.add_argument("--yes", action="store_true", help="Skip all confirmations")

    # Restore mode
    parser.add_argument("--restore", nargs="?", const="latest", help="Restore from backup")
    parser.add_argument("--restore-file", dest="restore_file", help="Restore single file")

    # Output format
    parser.add_argument("--json", action="store_true", help="Output JSON format")

    return parser.parse_args()
