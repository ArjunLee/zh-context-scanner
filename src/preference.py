"""
File: preference.py
Description: User preferences management with JSON persistence
Author: Arjun Li
Created: 2026-04-16
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from src.models import TranslationMode
from src.paths import PathRegistry
from src.ui.i18n import I18n


@dataclass
class UserPreferences:
    """User preferences data model."""

    language: str = "zh"
    translation_mode: str = "comment_only"
    last_config_file: str | None = None
    setup_completed: bool = False

    def to_dict(self) -> dict[str, str | bool | None]:
        """Convert preferences to dictionary for JSON serialization."""
        return {
            "language": self.language,
            "translation_mode": self.translation_mode,
            "last_config_file": self.last_config_file,
            "setup_completed": self.setup_completed,
        }

    @classmethod
    def from_dict(cls, data: dict) -> UserPreferences:
        """Create preferences from dictionary."""
        return cls(
            language=data.get("language", "zh"),
            translation_mode=data.get("translation_mode", "comment_only"),
            last_config_file=data.get("last_config_file"),
            setup_completed=data.get("setup_completed", False),
        )

    def get_translation_mode(self) -> TranslationMode:
        """Convert string mode to TranslationMode enum."""
        if self.translation_mode == "full":
            return TranslationMode.FULL
        return TranslationMode.COMMENT_ONLY


class PreferenceManager:
    """Manager for user preferences with file persistence."""

    DEFAULT_PREFS = UserPreferences()

    def __init__(self, preferences_file: Path | None = None) -> None:
        if preferences_file is None:
            tool_root = PathRegistry.detect_tool_root()
            path_registry = PathRegistry(tool_root)
            preferences_file = path_registry.preferences_file
        self._file = preferences_file
        self._prefs: UserPreferences | None = None

    def load(self) -> UserPreferences:
        """Load preferences from file, return defaults if not exists."""
        if self._prefs is not None:
            return self._prefs

        if not self._file.exists():
            self._prefs = self.DEFAULT_PREFS
            return self._prefs

        try:
            data = json.loads(self._file.read_text(encoding="utf-8"))
            self._prefs = UserPreferences.from_dict(data)
        except (json.JSONDecodeError, KeyError):
            self._prefs = self.DEFAULT_PREFS

        return self._prefs

    def save(self, prefs: UserPreferences) -> None:
        """Save preferences to file."""
        self._prefs = prefs
        self._file.parent.mkdir(parents=True, exist_ok=True)
        self._file.write_text(
            json.dumps(prefs.to_dict(), indent=2),
            encoding="utf-8",
        )

    def update_language(self, lang: str) -> UserPreferences:
        """Update language preference and save."""
        prefs = self.load()
        prefs.language = lang
        self.save(prefs)
        I18n.set_lang(lang)
        return prefs

    def update_translation_mode(self, mode: TranslationMode) -> UserPreferences:
        """Update translation mode preference and save."""
        prefs = self.load()
        prefs.translation_mode = "full" if mode == TranslationMode.FULL else "comment_only"
        self.save(prefs)
        return prefs

    def apply_to_system(self) -> TranslationMode:
        """Apply loaded preferences to system state."""
        prefs = self.load()
        I18n.set_lang(prefs.language)
        return prefs.get_translation_mode()

    def update_config_file(self, config_path: str) -> UserPreferences:
        """Update last config file path and mark setup completed."""
        prefs = self.load()
        prefs.last_config_file = config_path
        prefs.setup_completed = True
        self.save(prefs)
        return prefs

    def has_valid_config(self) -> bool:
        """Check if a valid config file exists and is accessible."""
        prefs = self.load()
        if not prefs.setup_completed:
            return False
        if not prefs.last_config_file:
            return False
        config_path = Path(prefs.last_config_file)
        return config_path.exists() and config_path.is_file()

    def reset_if_invalid(self) -> None:
        """Reset invalid config state if file is missing."""
        prefs = self.load()
        if prefs.last_config_file:
            config_path = Path(prefs.last_config_file)
            if not config_path.exists():
                prefs.last_config_file = None
                prefs.setup_completed = False
                self.save(prefs)
