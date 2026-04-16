"""
File: scanner.py
Description: Chinese text detection for whole-file translation
Author: Arjun Li
Created: 2026-04-15
Last Modified: 2026-04-15
Related modules: config.py, models.py
"""

from __future__ import annotations

import regex
from pathlib import Path

from src.config import ScanTarget
from src.models import TranslationMode


ZH_PATTERN = regex.compile(
    r'[\u4e00-\u9fff\u3400-\u4dbf\U00020000-\U0002a6df]+'
)

# Comment patterns for different languages
COMMENT_PATTERNS = {
    ".rs": [r"^\s*///.*", r"^\s*//.*"],  # Rust
    ".py": [r"^\s*#.*"],  # Python
    ".ts": [r"^\s*//.*", r"^\s*/\*.*\*/.*"],  # TypeScript
    ".tsx": [r"^\s*//.*", r"^\s*/\*.*\*/.*"],  # TSX
    ".js": [r"^\s*//.*", r"^\s*/\*.*\*/.*"],  # JavaScript
    ".jsx": [r"^\s*//.*", r"^\s*/\*.*\*/.*"],  # JSX
    ".go": [r"^\s*//.*", r"^\s*/\*.*\*/.*"],  # Go
    ".java": [r"^\s*//.*", r"^\s*/\*.*\*/.*"],  # Java
    ".c": [r"^\s*//.*", r"^\s*/\*.*\*/.*"],  # C
    ".cpp": [r"^\s*//.*", r"^\s*/\*.*\*/.*"],  # C++
    ".h": [r"^\s*//.*", r"^\s*/\*.*\*/.*"],  # Header
}


def contains_chinese(text: str) -> bool:
    """Check if text contains Chinese characters."""
    return bool(ZH_PATTERN.search(text))


def is_comment_line(line: str, file_ext: str) -> bool:
    """Check if a line is a comment line based on file extension.
    
    Args:
        line: The line to check
        file_ext: File extension (e.g., '.rs', '.py')
    
    Returns:
        True if the line is a comment, False otherwise
    """
    patterns = COMMENT_PATTERNS.get(file_ext, [])
    for pattern in patterns:
        if regex.match(pattern, line):
            return True
    return False


def file_contains_chinese(file_path: Path) -> bool:
    """Check if a file contains any Chinese text.

    Args:
        file_path: Path to the file to check

    Returns:
        True if file contains Chinese, False otherwise
    """
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                if contains_chinese(line):
                    return True
    except Exception:
        pass
    return False


def count_chinese_lines(file_path: Path, mode: TranslationMode = TranslationMode.FULL) -> int:
    """Count lines containing Chinese text in a file based on translation mode.
    
    Args:
        file_path: Path to the file to check
        mode: Translation mode - FULL counts all Chinese, COMMENT_ONLY counts only comments
    
    Returns:
        Number of lines containing Chinese text (filtered by mode)
    """
    count = 0
    file_ext = file_path.suffix.lower()
    
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                if contains_chinese(line):
                    # If mode is COMMENT_ONLY, only count comment lines
                    if mode == TranslationMode.COMMENT_ONLY:
                        if is_comment_line(line, file_ext):
                            count += 1
                    else:
                        # FULL mode counts all Chinese lines
                        count += 1
    except Exception:
        pass
    return count


def collect_files(
    root: Path,
    targets: list[ScanTarget],
    global_excludes: list[str],
) -> list[Path]:
    """Collect all files to scan based on targets and excludes."""
    files: list[Path] = []
    exclude_set = set(global_excludes)

    for target in targets:
        target_path = root / target.path
        if not target_path.exists():
            continue

        exclude_set.update(target.exclude_subdirs)

        for ext in target.extensions:
            for file in target_path.glob(f"**/*{ext}"):
                rel_path = file.relative_to(root)
                skip = False
                for part in rel_path.parts:
                    if part in exclude_set:
                        skip = True
                        break
                if not skip:
                    files.append(file)

    return sorted(files)


def find_files_with_chinese(
    root: Path,
    targets: list[ScanTarget],
    global_excludes: list[str],
) -> list[tuple[Path, int]]:
    """Find all files containing Chinese text.

    Args:
        root: Project root path
        targets: Scan targets configuration
        global_excludes: Global exclude patterns

    Returns:
        List of (file_path, chinese_line_count) tuples
    """
    files = collect_files(root, targets, global_excludes)
    results: list[tuple[Path, int]] = []

    for file in files:
        line_count = count_chinese_lines(file)
        if line_count > 0:
            results.append((file, line_count))

    return results