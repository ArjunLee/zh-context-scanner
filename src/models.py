"""
File: models.py
Description: Data models for scan results and translations
Author: Arjun Li
Created: 2026-04-15
Last Modified: 2026-04-15
Related modules: whole_file_translator.py, backup_manager.py
"""

import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path

import yaml

from src.paths import PathRegistry

# Terminology cache (loaded from terminology.yaml)
_terminology_cache: dict | None = None


def _load_terminology() -> dict:
    """Load terminology from YAML file."""
    global _terminology_cache
    if _terminology_cache is None:
        tool_root = PathRegistry.detect_tool_root()
        yaml_path = PathRegistry(tool_root).terminology_file
        if yaml_path.exists():
            with open(yaml_path, encoding="utf-8") as f:
                _terminology_cache = yaml.safe_load(f) or {}
        else:
            _terminology_cache = {}
    return _terminology_cache


def get_file_header_translations() -> dict[str, str]:
    """Get file header key translations (zh → en)."""
    return _load_terminology().get("file_header", {})


def get_technical_terms() -> list[str]:
    """Get technical terms that should not be translated."""
    return _load_terminology().get("technical_terms", [])


def replace_file_header_keys_in_line(line: str) -> str:
    """Replace file header key in a single line with cached translation.

    Example: "// 功能描述：xxx" → "// Description: xxx"
    The value (xxx) is preserved for LLM to translate.

    Args:
        line: Single line of code

    Returns:
        Line with header key replaced, or original line if no match
    """
    match = FILE_HEADER_PATTERN.match(line)
    if not match:
        return line

    comment_prefix = match.group(1)
    chinese_key = match.group(2)
    separator = match.group(3)
    value = match.group(4)

    translations = get_file_header_translations()
    english_key = translations.get(chinese_key)
    if not english_key:
        return line

    return f"{comment_prefix}{english_key}{separator}{value}"


def replace_file_header_keys_in_content(content: str) -> str:
    """Replace file header keys in entire file content.

    Args:
        content: Full file content

    Returns:
        Content with all header keys replaced
    """
    lines = content.splitlines(keepends=True)
    replaced_lines = [replace_file_header_keys_in_line(line) for line in lines]
    return "".join(replaced_lines)


# Regex to match standard file header comment format
FILE_HEADER_PATTERN: re.Pattern = re.compile(
    r"^(\s*//\s*)(文件名|功能描述|作者|创建日期|最后修改日期|关联模块)([：:]\s*)(.*)$"
)


class TranslationMode(Enum):
    """Translation mode for whole-file translation."""
    COMMENT_ONLY = "comment_only"  # Only translate comments
    FULL = "full"                  # Translate all Chinese text


class WarningType(Enum):
    """Warning types for complex scenarios that should be skipped."""
    TEMPLATE_STRING = "template_string"
    MULTILINE_STRING = "multiline_string"
    REGEX_LITERAL = "regex_literal"
    ESCAPE_CHARS = "escape_chars"
    MULTILINE_COMMENT = "multiline_comment"


@dataclass
class ScanMatch:
    """Single Chinese text match in a file."""
    file_path: Path
    line_number: int
    column_start: int
    column_end: int
    matched_text: str       # Chinese original text
    line_content: str       # Full line content for user judgment
    warning: WarningType | None = None  # Warning if complex scenario


@dataclass
class FileScanResult:
    """Scan result for a single file."""
    file_path: Path
    matches: list[ScanMatch] = field(default_factory=list)
    total_matches: int = 0
    warnings_count: int = 0

    def __post_init__(self) -> None:
        self.total_matches = len(self.matches)
        self.warnings_count = sum(1 for m in self.matches if m.warning)


@dataclass
class ScanReport:
    """Full scan report for all files."""
    files: list[FileScanResult] = field(default_factory=list)
    total_files: int = 0
    total_matches: int = 0
    total_warnings: int = 0
    scan_time: datetime = field(default_factory=datetime.now)

    def __post_init__(self) -> None:
        self.total_files = len(self.files)
        self.total_matches = sum(f.total_matches for f in self.files)
        self.total_warnings = sum(f.warnings_count for f in self.files)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON export."""
        return {
            "scan_time": self.scan_time.isoformat(),
            "total_files": self.total_files,
            "total_matches": self.total_matches,
            "total_warnings": self.total_warnings,
            "files": [
                {
                    "path": str(f.file_path),
                    "matches": [
                        {
                            "line": m.line_number,
                            "col_start": m.column_start,
                            "col_end": m.column_end,
                            "text": m.matched_text,
                            "line_content": m.line_content,
                            "warning": m.warning.value if m.warning else None,
                        }
                        for m in f.matches
                    ],
                }
                for f in self.files
            ],
        }


@dataclass
class TranslationResult:
    """Translation result for a single text."""
    original: str
    translated: str
    cached: bool = False


@dataclass
class BackupRecord:
    """Record of a backup operation."""
    backup_id: str           # Timestamp-based ID
    backup_path: Path        # Backup directory path
    files_backed_up: list[Path] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    total_files: int = 0

    def __post_init__(self) -> None:
        # Only set total_files if files_backed_up has data and total_files not already set
        if self.files_backed_up and self.total_files == 0:
            self.total_files = len(self.files_backed_up)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON export."""
        return {
            "backup_id": self.backup_id,
            "backup_path": str(self.backup_path),
            "created_at": self.created_at.isoformat(),
            "total_files": self.total_files,
            "files": [str(f) for f in self.files_backed_up],
        }


@dataclass
class FileTranslationResult:
    """Result of translating a single file (whole-file mode)."""
    file_path: Path
    original_content: str
    translated_content: str
    mode: TranslationMode
    success: bool
    error: str | None = None

    @property
    def line_count_original(self) -> int:
        return len(self.original_content.splitlines())

    @property
    def line_count_translated(self) -> int:
        return len(self.translated_content.splitlines())

    @property
    def lines_match(self) -> bool:
        return self.line_count_original == self.line_count_translated


@dataclass
class CommentTranslationResult:
    """Result of incremental comment translation (extract, translate, replace)."""
    file_path: Path
    comments_found: int
    comments_translated: int
    replacements: list[dict]  # [{"line_no": int, "original": str, "translated": str}]
    success: bool
    error: str | None = None

    @property
    def all_translated(self) -> bool:
        """Check if all comments were successfully translated."""
        return self.comments_found == self.comments_translated

    @property
    def has_changes(self) -> bool:
        """Check if any replacements were made."""
        return len(self.replacements) > 0
