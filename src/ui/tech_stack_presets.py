"""
File: tech_stack_presets.py
Description: Tech stack preset definitions for setup wizard
Author: Arjun Li
Created: 2026-04-16
Last Modified: 2026-04-16
Related modules: setup_wizard.py, config_generator.py
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TechStackPreset:
    """Single tech stack preset with default extensions and excludes."""

    key: str
    name: str
    emoji: str
    extensions: list[str]
    exclude_subdirs: list[str] = field(default_factory=list)


TECH_STACK_PRESETS: dict[str, TechStackPreset] = {
    "rust": TechStackPreset(
        key="rust",
        name="Rust",
        emoji="🦀",
        extensions=[".rs"],
        exclude_subdirs=["target", "gen"],
    ),
    "react_ts": TechStackPreset(
        key="react_ts",
        name="React/TypeScript",
        emoji="💎",
        extensions=[".tsx", ".ts", ".jsx", ".js"],
        exclude_subdirs=["node_modules", "dist", "build", "locales", ".next"],
    ),
    "python": TechStackPreset(
        key="python",
        name="Python",
        emoji="🐍",
        extensions=[".py"],
        exclude_subdirs=["__pycache__", ".venv", "venv", "env", ".pytest_cache"],
    ),
    "css": TechStackPreset(
        key="css",
        name="CSS/SCSS",
        emoji="🎨",
        extensions=[".css", ".scss", ".sass", ".less"],
        exclude_subdirs=["node_modules", "dist"],
    ),
    "vue_ts": TechStackPreset(
        key="vue_ts",
        name="Vue/TypeScript",
        emoji="🟢",
        extensions=[".vue", ".ts", ".js"],
        exclude_subdirs=["node_modules", "dist"],
    ),
    "go": TechStackPreset(
        key="go",
        name="Go",
        emoji="🐹",
        extensions=[".go"],
        exclude_subdirs=["vendor"],
    ),
    "java": TechStackPreset(
        key="java",
        name="Java",
        emoji="☕",
        extensions=[".java"],
        exclude_subdirs=["target", "build", ".gradle"],
    ),
    "csharp": TechStackPreset(
        key="csharp",
        name="C#/.NET",
        emoji="🎯",
        extensions=[".cs"],
        exclude_subdirs=["bin", "obj", ".vs"],
    ),
    "svelte": TechStackPreset(
        key="svelte",
        name="Svelte",
        emoji="🔥",
        extensions=[".svelte", ".ts", ".js"],
        exclude_subdirs=["node_modules", "dist", ".svelte-kit"],
    ),
    "angular": TechStackPreset(
        key="angular",
        name="Angular",
        emoji="🏰",
        extensions=[".ts", ".html"],
        exclude_subdirs=["node_modules", "dist"],
    ),
    "yaml_toml": TechStackPreset(
        key="yaml_toml",
        name="YAML/TOML",
        emoji="📜",
        extensions=[".yaml", ".yml", ".toml"],
        exclude_subdirs=[],
    ),
    "json": TechStackPreset(
        key="json",
        name="JSON",
        emoji="📦",
        extensions=[".json"],
        exclude_subdirs=["node_modules"],
    ),
    "markdown": TechStackPreset(
        key="markdown",
        name="Markdown",
        emoji="📝",
        extensions=[".md", ".mdx"],
        exclude_subdirs=["node_modules"],
    ),
    "sql": TechStackPreset(
        key="sql",
        name="SQL",
        emoji="💾",
        extensions=[".sql"],
        exclude_subdirs=[],
    ),
}


def get_all_presets() -> list[TechStackPreset]:
    """Get all tech stack presets as a list."""
    return list(TECH_STACK_PRESETS.values())


def get_preset_by_key(key: str) -> TechStackPreset | None:
    """Find preset by dictionary key."""
    return TECH_STACK_PRESETS.get(key)


def merge_presets(preset_keys: list[str]) -> tuple[list[str], list[str]]:
    """Merge multiple presets into combined extensions and excludes.

    Args:
        preset_keys: List of preset keys to merge

    Returns:
        Tuple of (merged_extensions, merged_excludes) with duplicates removed
    """
    if not preset_keys:
        return [], []

    all_extensions: list[str] = []
    all_excludes: list[str] = []

    for key in preset_keys:
        preset = get_preset_by_key(key)
        if preset:
            all_extensions.extend(preset.extensions)
            all_excludes.extend(preset.exclude_subdirs)

    merged_extensions = list(set(all_extensions))
    merged_excludes = list(set(all_excludes))

    return merged_extensions, merged_excludes


def get_default_global_excludes() -> list[str]:
    """Get default global exclude patterns for all projects."""
    return [
        "node_modules",
        "dist",
        "target",
        ".git",
        "__pycache__",
        ".venv",
        "venv",
        "build",
        "gen",
    ]
