"""
File: comment_patterns.py
Description: Universal comment pattern definitions and extraction utilities
Author: Arjun Li
Created: 2026-04-17
Last Modified: 2026-04-17
Related modules: comment_translator.py, scanner.py
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class CommentType(Enum):
    """Types of comments in source code."""
    LINE_COMMENT = "line_comment"
    TRAILING_COMMENT = "trailing"
    BLOCK_COMMENT_LINE = "block_line"


@dataclass
class CommentMatch:
    """A single comment containing Chinese text."""
    line_no: int
    original_text: str
    comment_type: CommentType
    comment_content: str
    prefix: str
    indent: str


CHINESE_PATTERN = re.compile(r"[\u4e00-\u9fff]+")


COMMENT_STYLES = {
    ".ts": {"line": "//", "block_start": "/*", "block_end": "*/"},
    ".tsx": {"line": "//", "block_start": "/*", "block_end": "*/"},
    ".js": {"line": "//", "block_start": "/*", "block_end": "*/"},
    ".jsx": {"line": "//", "block_start": "/*", "block_end": "*/"},
    ".rs": {"line": "//", "block_start": "/*", "block_end": "*/"},
    ".go": {"line": "//", "block_start": "/*", "block_end": "*/"},
    ".java": {"line": "//", "block_start": "/*", "block_end": "*/"},
    ".c": {"line": "//", "block_start": "/*", "block_end": "*/"},
    ".cpp": {"line": "//", "block_start": "/*", "block_end": "*/"},
    ".h": {"line": "//", "block_start": "/*", "block_end": "*/"},
    ".py": {"line": "#", "block_start": None, "block_end": None},
    ".toml": {"line": "#", "block_start": None, "block_end": None},
    ".css": {"line": None, "block_start": "/*", "block_end": "*/"},
    ".html": {"line": None, "block_start": "<!--", "block_end": "-->"},
    ".vue": {"line": "//", "block_start": "/*", "block_end": "*/"},
}


def get_comment_style(file_ext: str) -> dict:
    return COMMENT_STYLES.get(file_ext.lower(), COMMENT_STYLES.get(".ts", {}))


def is_inside_string_or_url(line: str, pos: int) -> bool:
    r"""Check if position is inside a string literal or URL.

    Uses accurate quote counting: counts unescaped quotes by checking
    preceding character is not a backslash (or backslash itself is escaped).
    """
    before = line[:pos]

    # Check for URL protocol patterns (http://, https://, ftp://, file://)
    url_patterns = [
        r'https?://',
        r'ftp://',
        r'file://',
    ]
    for pattern in url_patterns:
        if re.search(pattern, before):
            return True

    # Accurate quote counting: count quotes where preceding char is not backslash
    # or the backslash itself is escaped (preceded by another backslash)
    def count_unescaped_quotes(quote_char: str) -> int:
        count = 0
        i = 0
        while i < len(before):
            if before[i] == quote_char:
                # Check if escaped: preceding backslash not itself escaped
                if i == 0 or before[i - 1] != '\\':
                    count += 1
                elif i >= 2 and before[i - 2] == '\\':
                    # Double backslash: the quote is not escaped
                    count += 1
            i += 1
        return count

    for quote in ['"', "'"]:
        if count_unescaped_quotes(quote) % 2 == 1:
            return True

    return False


def find_real_comment_delimiter(line: str, delimiter: str) -> int:
    pos = line.find(delimiter)
    while pos != -1:
        if not is_inside_string_or_url(line, pos):
            return pos
        pos = line.find(delimiter, pos + len(delimiter))
    return -1


def extract_line_comment(line: str, line_no: int, delimiter: str) -> CommentMatch | None:
    r"""Extract a full-line comment (comment at line start)."""
    match = re.match(r"^(\s*)(" + re.escape(delimiter) + r".*)$", line)
    if not match:
        return None

    indent = match.group(1)
    comment_text = match.group(2)

    if not CHINESE_PATTERN.search(comment_text):
        return None

    return CommentMatch(
        line_no=line_no,
        original_text=line.rstrip("\n\r"),
        comment_type=CommentType.LINE_COMMENT,
        comment_content=comment_text[len(delimiter):].strip(),
        prefix=delimiter,
        indent=indent,
    )


def extract_trailing_comment(line: str, line_no: int, delimiter: str) -> CommentMatch | None:
    """Extract a trailing comment (code followed by comment)."""
    pos = find_real_comment_delimiter(line, delimiter)
    if pos == -1 or pos == 0:
        return None

    comment_part = line[pos:].rstrip()

    if not CHINESE_PATTERN.search(comment_part):
        return None

    comment_match = re.match(r"^(\s*" + re.escape(delimiter) + r"\s*)(.*)$", comment_part)
    if not comment_match:
        return None

    comment_content = comment_match.group(2)

    return CommentMatch(
        line_no=line_no,
        original_text=line.rstrip("\n\r"),
        comment_type=CommentType.TRAILING_COMMENT,
        comment_content=comment_content,
        prefix=delimiter,
        indent="",
    )


def extract_block_comments(content: str, file_ext: str) -> list[CommentMatch]:
    style = get_comment_style(file_ext)
    block_start = style.get("block_start")
    block_end = style.get("block_end")

    if not block_start or not block_end:
        return []

    lines = content.splitlines(keepends=True)
    matches = []
    in_block = False

    for i, line in enumerate(lines, start=1):
        line_text = line.rstrip("\n\r")

        if not in_block:
            start_pos = line_text.find(block_start)
            if start_pos != -1:
                in_block = True

                end_pos = line_text.find(block_end, start_pos + len(block_start))
                if end_pos != -1:
                    in_block = False
                    block_content = line_text[start_pos:end_pos + len(block_end)]
                    if CHINESE_PATTERN.search(block_content):
                        matches.append(CommentMatch(
                            line_no=i,
                            original_text=line_text,
                            comment_type=CommentType.BLOCK_COMMENT_LINE,
                            comment_content=block_content,
                            prefix=block_start,
                            indent=line_text[:start_pos],
                        ))
        else:
            end_pos = line_text.find(block_end)
            if end_pos != -1:
                in_block = False
                if end_pos > 0:
                    block_line = line_text[:end_pos]
                    if CHINESE_PATTERN.search(block_line):
                        matches.append(CommentMatch(
                            line_no=i,
                            original_text=line_text,
                            comment_type=CommentType.BLOCK_COMMENT_LINE,
                            comment_content=block_line,
                            prefix="*",
                            indent="",
                        ))
            else:
                if CHINESE_PATTERN.search(line_text):
                    matches.append(CommentMatch(
                        line_no=i,
                        original_text=line_text,
                        comment_type=CommentType.BLOCK_COMMENT_LINE,
                        comment_content=line_text,
                        prefix="*",
                        indent="",
                    ))

    return matches


def extract_all_comments(file_path: Path) -> list[CommentMatch]:
    file_ext = file_path.suffix.lower()
    style = get_comment_style(file_ext)

    content = file_path.read_text(encoding="utf-8", errors="replace")
    lines = content.splitlines(keepends=True)

    matches = []
    line_delimiter = style.get("line")

    if line_delimiter:
        for i, line in enumerate(lines, start=1):
            line_text = line.rstrip("\n\r")

            line_match = extract_line_comment(line_text, i, line_delimiter)
            if line_match:
                matches.append(line_match)
                continue

            trailing_match = extract_trailing_comment(line_text, i, line_delimiter)
            if trailing_match:
                matches.append(trailing_match)

    block_matches = extract_block_comments(content, file_ext)
    matches.extend(block_matches)

    return sorted(matches, key=lambda m: m.line_no)


def is_comment_line(line: str, file_ext: str) -> bool:
    style = get_comment_style(file_ext)
    line_delimiter = style.get("line")

    if line_delimiter:
        if re.match(r"^\s*" + re.escape(line_delimiter), line):
            return True

        pos = find_real_comment_delimiter(line, line_delimiter)
        if pos > 0:
            return True

    block_start = style.get("block_start")
    block_end = style.get("block_end")
    if block_start and block_end:
        if re.match(r"^\s*" + re.escape(block_start), line):
            return True
        if re.match(r"^\s*\*", line):
            return True

    return False


COMMENT_PATTERNS_COMPAT = {
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
    ".toml": [r"^\s*#.*"],
    ".css": [r"^\s*/\*.*\*/.*"],
}


def get_compiled_patterns(file_ext: str) -> re.Pattern | None:
    patterns = COMMENT_PATTERNS_COMPAT.get(file_ext.lower(), [])
    if not patterns:
        patterns = [r"^\s*//.*", r"^\s*#.*"]

    return re.compile("|".join(patterns)) if patterns else None
