"""
File: scanner.py
Description: Chinese text detection for whole-file translation
Author: Arjun Li
Created: 2026-04-15
Last Modified: 2026-04-15
Related modules: config.py, models.py
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import regex

from src.config import ScanTarget
from src.models import TranslationMode

# Timestamp file for incremental scan
LAST_SCAN_TIMESTAMP_FILE = "last_scan_timestamp.json"


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
        with open(file_path, encoding="utf-8", errors="replace") as f:
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
        with open(file_path, encoding="utf-8", errors="replace") as f:
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
        target_path = Path(target.path)
        if not target_path.is_absolute():
            target_path = root / target_path
        if not target_path.exists():
            continue

        exclude_set.update(target.exclude_subdirs)

        for ext in target.extensions:
            for file in target_path.glob(f"**/*{ext}"):
                rel_path = file.relative_to(target_path)
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


def load_last_scan_timestamp(log_dir: Path) -> float:
    """Load last scan timestamp from file.

    Args:
        log_dir: Directory where timestamp file is stored

    Returns:
        Last scan timestamp (0.0 if not exists)
    """
    timestamp_file = log_dir / LAST_SCAN_TIMESTAMP_FILE
    if not timestamp_file.exists():
        return 0.0
    try:
        data = json.loads(timestamp_file.read_text(encoding="utf-8"))
        return float(data.get("last_scan_timestamp", 0.0))
    except Exception:
        return 0.0


def save_last_scan_timestamp(log_dir: Path) -> None:
    """Save current timestamp as last scan time.

    Args:
        log_dir: Directory where timestamp file is stored
    """
    log_dir.mkdir(parents=True, exist_ok=True)
    timestamp_file = log_dir / LAST_SCAN_TIMESTAMP_FILE
    data = {
        "last_scan_timestamp": time.time(),
        "last_scan_datetime": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    timestamp_file.write_text(json.dumps(data, indent=2), encoding="utf-8")


def find_files_modified_after(
    root: Path,
    targets: list[ScanTarget],
    global_excludes: list[str],
    after_timestamp: float,
) -> list[Path]:
    """Find files modified after given timestamp.

    Args:
        root: Project root path
        targets: Scan targets configuration
        global_excludes: Global exclude patterns
        after_timestamp: Unix timestamp to compare against

    Returns:
        List of file paths modified after timestamp
    """
    files = collect_files(root, targets, global_excludes)
    modified_files: list[Path] = []

    for file in files:
        try:
            mtime = file.stat().st_mtime
            if mtime > after_timestamp:
                modified_files.append(file)
        except OSError:
            # File might not exist or be inaccessible
            continue

    return modified_files


def find_files_with_chinese_incremental(
    root: Path,
    targets: list[ScanTarget],
    global_excludes: list[str],
    log_dir: Path,
    mode: TranslationMode = TranslationMode.FULL,
) -> list[tuple[Path, int]]:
    """Incremental scan: only files modified after last scan.

    Args:
        root: Project root path
        targets: Scan targets configuration
        global_excludes: Global exclude patterns
        log_dir: Directory for timestamp storage
        mode: Translation mode for counting Chinese lines

    Returns:
        List of (file_path, chinese_line_count) tuples for modified files
    """
    last_timestamp = load_last_scan_timestamp(log_dir)
    modified_files = find_files_modified_after(
        root, targets, global_excludes, last_timestamp
    )

    results: list[tuple[Path, int]] = []
    for file in modified_files:
        line_count = count_chinese_lines(file, mode)
        if line_count > 0:
            results.append((file, line_count))

    # Update timestamp after successful scan
    save_last_scan_timestamp(log_dir)

    return results
