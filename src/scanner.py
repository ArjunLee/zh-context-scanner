"""
File: scanner.py
Description: Chinese text detection for whole-file translation (flat config structure)
Author: Arjun Li
Created: 2026-04-15
Last Modified: 2026-04-17
Related modules: config.py, models.py
"""

from __future__ import annotations

import json
import os
import time
from collections.abc import Generator
from pathlib import Path

import regex

from src.models import TranslationMode

LAST_SCAN_TIMESTAMP_FILE = "last_scan_timestamp.json"


ZH_PATTERN = regex.compile(
    r'[\u4e00-\u9fff\u3400-\u4dbf\U00020000-\U0002a6df]+'
)

COMMENT_PATTERNS = {
    ".rs": [r"^\s*///.*", r"^\s*//.*"],
    ".py": [r"^\s*#.*"],
    ".ts": [r"^\s*//.*", r"^\s*/\*.*\*/.*"],
    ".tsx": [r"^\s*//.*", r"^\s*/\*.*\*/.*"],
    ".js": [r"^\s*//.*", r"^\s*/\*.*\*/.*"],
    ".jsx": [r"^\s*//.*", r"^\s*/\*.*\*/.*"],
    ".go": [r"^\s*//.*", r"^\s*/\*.*\*/.*"],
    ".java": [r"^\s*//.*", r"^\s*/\*.*\*/.*"],
    ".c": [r"^\s*//.*", r"^\s*/\*.*\*/.*"],
    ".cpp": [r"^\s*//.*", r"^\s*/\*.*\*/.*"],
    ".h": [r"^\s*//.*", r"^\s*/\*.*\*/.*"],
}


def contains_chinese(text: str) -> bool:
    """Check if text contains Chinese characters."""
    return bool(ZH_PATTERN.search(text))


def is_comment_line(line: str, file_ext: str) -> bool:
    """Check if a line is a comment line based on file extension."""
    patterns = COMMENT_PATTERNS.get(file_ext, [])
    for pattern in patterns:
        if regex.match(pattern, line):
            return True
    return False


def file_contains_chinese(file_path: Path) -> bool:
    """Check if a file contains any Chinese text."""
    try:
        with open(file_path, encoding="utf-8", errors="replace") as f:
            for line in f:
                if contains_chinese(line):
                    return True
    except Exception:
        pass
    return False


def count_chinese_lines(file_path: Path, mode: TranslationMode = TranslationMode.FULL) -> int:
    """Count lines containing Chinese text in a file based on translation mode."""
    count = 0
    file_ext = file_path.suffix.lower()

    try:
        with open(file_path, encoding="utf-8", errors="replace") as f:
            for line in f:
                if contains_chinese(line):
                    if mode == TranslationMode.COMMENT_ONLY:
                        if is_comment_line(line, file_ext):
                            count += 1
                    else:
                        count += 1
    except Exception:
        pass
    return count


def collect_files(
    root: Path,
    paths: list[str],
    extensions: list[str],
    excludes: list[str],
) -> list[Path]:
    """Collect all files to scan based on flat config structure."""
    files: list[Path] = []
    exclude_set = set(excludes)

    for path_str in paths:
        target_path = Path(path_str)
        if not target_path.is_absolute():
            target_path = root / target_path
        if not target_path.exists():
            continue

        for ext in extensions:
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


def stream_files_for_scan(
    root: Path,
    paths: list[str],
    extensions: list[str],
    excludes: list[str],
) -> Generator[Path, None, int]:
    """Stream files one-by-one for real-time progress updates."""
    exclude_set = set(excludes)
    total = 0

    for path_str in paths:
        target_path = Path(path_str)
        if not target_path.is_absolute():
            target_path = root / target_path
        if not target_path.exists():
            continue

        for root_dir, dirs, files in os.walk(target_path):
            dirs[:] = [d for d in dirs if d not in exclude_set]

            for file in files:
                if any(file.endswith(ext) for ext in extensions):
                    yield Path(root_dir) / file
                    total += 1

    return total


def stream_files_modified_after(
    root: Path,
    paths: list[str],
    extensions: list[str],
    excludes: list[str],
    after_timestamp: float,
) -> Generator[Path, None, int]:
    """Stream modified files one-by-one for incremental scan progress."""
    exclude_set = set(excludes)
    total = 0

    for path_str in paths:
        target_path = Path(path_str)
        if not target_path.is_absolute():
            target_path = root / target_path
        if not target_path.exists():
            continue

        for root_dir, dirs, files in os.walk(target_path):
            dirs[:] = [d for d in dirs if d not in exclude_set]

            for file in files:
                if any(file.endswith(ext) for ext in extensions):
                    file_path = Path(root_dir) / file
                    try:
                        mtime = file_path.stat().st_mtime
                        if mtime > after_timestamp:
                            yield file_path
                            total += 1
                    except OSError:
                        continue

    return total


def find_files_with_chinese(
    root: Path,
    paths: list[str],
    extensions: list[str],
    excludes: list[str],
) -> list[tuple[Path, int]]:
    """Find all files containing Chinese text."""
    files = collect_files(root, paths, extensions, excludes)
    results: list[tuple[Path, int]] = []

    for file in files:
        line_count = count_chinese_lines(file)
        if line_count > 0:
            results.append((file, line_count))

    return results


def load_last_scan_timestamp(log_dir: Path) -> float:
    """Load last scan timestamp from file."""
    timestamp_file = log_dir / LAST_SCAN_TIMESTAMP_FILE
    if not timestamp_file.exists():
        return 0.0
    try:
        data = json.loads(timestamp_file.read_text(encoding="utf-8"))
        return float(data.get("last_scan_timestamp", 0.0))
    except Exception:
        return 0.0


def save_last_scan_timestamp(log_dir: Path) -> None:
    """Save current timestamp as last scan time."""
    log_dir.mkdir(parents=True, exist_ok=True)
    timestamp_file = log_dir / LAST_SCAN_TIMESTAMP_FILE
    data = {
        "last_scan_timestamp": time.time(),
        "last_scan_datetime": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    timestamp_file.write_text(json.dumps(data, indent=2), encoding="utf-8")


def find_files_modified_after(
    root: Path,
    paths: list[str],
    extensions: list[str],
    excludes: list[str],
    after_timestamp: float,
) -> list[Path]:
    """Find files modified after given timestamp."""
    files = collect_files(root, paths, extensions, excludes)
    modified_files: list[Path] = []

    for file in files:
        try:
            mtime = file.stat().st_mtime
            if mtime > after_timestamp:
                modified_files.append(file)
        except OSError:
            continue

    return modified_files


def find_files_with_chinese_incremental(
    root: Path,
    paths: list[str],
    extensions: list[str],
    excludes: list[str],
    log_dir: Path,
    mode: TranslationMode = TranslationMode.FULL,
) -> list[tuple[Path, int]]:
    """Incremental scan: only files modified after last scan."""
    last_timestamp = load_last_scan_timestamp(log_dir)
    modified_files = find_files_modified_after(
        root, paths, extensions, excludes, last_timestamp
    )

    results: list[tuple[Path, int]] = []
    for file in modified_files:
        line_count = count_chinese_lines(file, mode)
        if line_count > 0:
            results.append((file, line_count))

    return results
