"""
File: guard.py
Description: Log writing guard (line truncation, dedup, rate limiting, file size cap)
Author: Arjun Li
Created: 2026-03-02
Last Modified: 2026-04-16
Module: zh-context-scanner/solid_logger
"""

from __future__ import annotations

import hashlib
import os
import time
from collections import deque
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class GuardConfig:
    """
    Design Background:
    - Desktop shortcuts may be triggered rapidly, causing HTTP request floods
    - Request logger writes one line per request, leading to IO write storms
    - Four-layer protection:
      1) Duplicate log dedup (10s window)
      2) Line length truncation (1000 chars)
      3) Write rate circuit breaker (100 lines/sec -> 5s pause)
      4) File size cap (20MB -> stop writing)
    """

    dedupe_window_s: float = 10.0
    max_line_chars: int = 1000
    rate_window_s: float = 1.0
    rate_max_lines: int = 100
    rate_block_s: float = 5.0
    max_file_bytes: int = 20 * 1024 * 1024


class LoggingGuard:
    """
    Design:
    - Only determines "whether to allow writing" and "truncate before writing"
    - Uses rendered text lines as input for flexibility
    - Dedup strategy: logger name + level + line hash
    """

    def __init__(self, config: GuardConfig | None = None) -> None:
        """Initialize with clean state."""
        self._cfg = config or GuardConfig()
        self._last_written_at: dict[str, float] = {}
        self._recent_writes: deque[float] = deque()
        self._blocked_until: float = 0.0
        self._file_write_stopped: bool = False

    def reset_file_block(self) -> None:
        """Reset file block status after log rotation."""
        self._file_write_stopped = False

    def filter_line(
        self,
        *,
        logger_name: str,
        level_name: str,
        rendered_line: str,
        file_path: Path | None,
    ) -> str | None:
        """
        Returns:
            str: Allow write (possibly truncated)
            None: Discard (duplicate/rate-limited/file-capped)
        """
        now = time.monotonic()

        if self._is_file_blocked(file_path=file_path):
            return None

        if self._is_rate_blocked(now=now):
            return None

        signature = self._signature(logger_name=logger_name, level_name=level_name, rendered_line=rendered_line)
        if self._is_deduped(signature=signature, now=now):
            return None

        truncated = self._truncate(rendered_line)
        self._record_write(now=now, signature=signature)
        return truncated

    def _signature(self, *, logger_name: str, level_name: str, rendered_line: str) -> str:
        """Generate hash signature for dedup."""
        raw = f"{logger_name}|{level_name}|{rendered_line}".encode("utf-8", errors="ignore")
        return hashlib.sha256(raw).hexdigest()

    def _is_deduped(self, *, signature: str, now: float) -> bool:
        """Check if log is duplicate within dedup window."""
        prev = self._last_written_at.get(signature)
        if prev is None:
            return False
        return (now - prev) < self._cfg.dedupe_window_s

    def _record_write(self, *, now: float, signature: str) -> None:
        """Record write timestamp for dedup and rate control."""
        self._last_written_at[signature] = now
        self._recent_writes.append(now)
        self._prune_rate_window(now=now)

    def _prune_rate_window(self, *, now: float) -> None:
        """Prune expired timestamps from rate window."""
        window_start = now - self._cfg.rate_window_s
        while self._recent_writes and self._recent_writes[0] < window_start:
            self._recent_writes.popleft()

    def _is_rate_blocked(self, *, now: float) -> bool:
        """Check if write rate exceeded threshold."""
        if now < self._blocked_until:
            return True

        self._prune_rate_window(now=now)
        if len(self._recent_writes) < self._cfg.rate_max_lines:
            return False

        self._blocked_until = now + self._cfg.rate_block_s
        return True

    def _is_file_blocked(self, *, file_path: Path | None) -> bool:
        """Check if file size exceeded cap."""
        if not file_path:
            return False
        if self._file_write_stopped:
            return True

        size = _safe_file_size(file_path)
        if size is None:
            return False
        if size <= self._cfg.max_file_bytes:
            return False

        self._file_write_stopped = True
        return True

    def _truncate(self, text: str) -> str:
        """Truncate long lines while preserving head and tail."""
        limit = int(self._cfg.max_line_chars)
        if limit <= 0:
            return ""
        if len(text) <= limit:
            return text

        marker = " ... [truncated] ... "
        if limit <= len(marker):
            if limit <= 3:
                return text[:limit]
            return text[: limit - 3] + "..."
        head_len = max((limit - len(marker)) // 2, 0)
        tail_len = max(limit - len(marker) - head_len, 0)
        head = text[:head_len]
        tail = text[-tail_len:] if tail_len > 0 else ""
        return f"{head}{marker}{tail}"


def _safe_file_size(path: Path) -> int | None:
    """Safely get file size."""
    try:
        return os.path.getsize(path)
    except OSError:
        return None
