"""
File: rotation.py
Description: Log file rotation and cleanup (size + time based, 7 days/100MB retention)
Author: Arjun Li
Created: 2026-03-02
Last Modified: 2026-04-16
Module: zh-context-scanner/solid_logger
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

from .guard import GuardConfig, LoggingGuard


@dataclass(frozen=True)
class RotationConfig:
    """
    Design Background:
    - Log write storms cause file bloat
    - File-level protection: time rotation + size rotation + auto cleanup
    """

    when: str = "midnight"
    interval: int = 1
    utc: bool = False
    max_file_bytes: int = 10 * 1024 * 1024
    retention_days: int = 7
    total_size_limit_bytes: int = 100 * 1024 * 1024


@dataclass(frozen=True)
class HeaderConfig:
    """Log file header information."""
    generated_at_iso: str
    source_module: str
    version: str


class VaultSaveRotatingHandler(TimedRotatingFileHandler):
    """
    Key Design:
    - Rotation and cleanup handled by Handler
    - LoggingGuard embedded to protect all loggers
    """

    def __init__(
        self,
        *,
        file_path: Path,
        header: HeaderConfig,
        rotation: RotationConfig | None = None,
        guard: GuardConfig | None = None,
        level: int = logging.INFO,
    ) -> None:
        self._file_path = file_path
        self._header = header
        self._rotation = rotation or RotationConfig()
        self._guard = LoggingGuard(guard)
        self._header_written_for_current_file = False
        self._header_text = _build_normalized_header(header)

        file_path.parent.mkdir(parents=True, exist_ok=True)
        super().__init__(
            filename=str(file_path),
            when=self._rotation.when,
            interval=self._rotation.interval,
            backupCount=0,
            encoding="utf-8",
            delay=False,
            utc=self._rotation.utc,
        )
        self.setLevel(level)
        self._install_suffix()

    def _install_suffix(self) -> None:
        """Extend suffix to second-level for size-based rotation."""
        self.suffix = "%Y-%m-%d_%H-%M-%S"

    def emit(self, record: logging.LogRecord) -> None:
        """Emit log record with rotation check and guard filter."""
        try:
            rendered = self.format(record)
            if self._should_rollover(record, rendered=rendered):
                self.doRollover()
            allowed = self._guard.filter_line(
                logger_name=record.name,
                level_name=record.levelname,
                rendered_line=rendered,
                file_path=Path(self.baseFilename),
            )
            if allowed is None:
                return

            self._ensure_header_written()
            stream = self.stream
            stream.write(allowed + self.terminator)
            self.flush()
        except Exception:
            self.handleError(record)

    def _should_rollover(self, record: logging.LogRecord, *, rendered: str) -> bool:
        """Check if rotation needed (time or size based)."""
        if super().shouldRollover(record):
            return True
        return _will_exceed_size_limit(
            filename=self.baseFilename,
            max_bytes=self._rotation.max_file_bytes,
            rendered=rendered,
            terminator=self.terminator,
            header_text=self._header_text if not self._header_written_for_current_file else "",
        )

    def doRollover(self) -> None:
        """Handle log rotation and cleanup."""
        super().doRollover()
        self._header_written_for_current_file = False
        self._guard.reset_file_block()
        cleanup_log_dir(
            log_dir=Path(self.baseFilename).parent,
            base_filename=Path(self.baseFilename).name,
            retention_days=self._rotation.retention_days,
            total_size_limit_bytes=self._rotation.total_size_limit_bytes,
        )

    def _ensure_header_written(self) -> None:
        """Write header once per file."""
        if self._header_written_for_current_file:
            return

        stream = self.stream
        if stream is None:
            return

        stream.write(self._header_text)
        self.flush()
        self._header_written_for_current_file = True


def _build_normalized_header(header: HeaderConfig) -> str:
    """Build normalized log header per docs/2.md spec."""
    return (
        "=== Normalized Log ===\n"
        f"Generated At: {header.generated_at_iso}\n"
        f"Source Module: {header.source_module}\n"
        f"Version: {header.version}\n"
        "Field Description:\n"
        "- Timestamp: ISO-8601 (local timezone, second precision)\n"
        "- Level: Log level (INFO/WARN/ERROR)\n"
        "- Module: Module name (Translator/Backup/System)\n"
        "- Action: API action or event description\n"
        "- Status: HTTP status code or ---\n"
        "\n"
    )


def _will_exceed_size_limit(
    *,
    filename: str,
    max_bytes: int,
    rendered: str,
    terminator: str,
    header_text: str,
) -> bool:
    """Check if writing will exceed size limit."""
    if max_bytes <= 0:
        return False
    current = _safe_size_str(filename) or 0
    extra = len((rendered + terminator).encode("utf-8", errors="ignore"))
    if header_text:
        extra += len(header_text.encode("utf-8", errors="ignore"))
    return (current + extra) >= max_bytes


def _safe_size_str(filename: str) -> int | None:
    """Safely get file size."""
    try:
        return os.path.getsize(filename)
    except OSError:
        return None


def cleanup_log_dir(
    *,
    log_dir: Path,
    base_filename: str,
    retention_days: int,
    total_size_limit_bytes: int,
) -> None:
    """
    Cleanup Strategy:
    1) Keep logs within retention_days
    2) Limit directory total size
    3) Only cleanup files matching base_filename prefix
    """
    files = _list_related_logs(log_dir=log_dir, base_filename=base_filename)
    if not files:
        return

    _delete_older_than(files=files, retention_days=retention_days)
    files = _list_related_logs(log_dir=log_dir, base_filename=base_filename)
    _trim_total_size(files=files, total_size_limit_bytes=total_size_limit_bytes)


def _list_related_logs(*, log_dir: Path, base_filename: str) -> list[Path]:
    """List log files matching base_filename prefix."""
    if not log_dir.exists() or not log_dir.is_dir():
        return []
    prefix = base_filename
    result: list[Path] = []
    for p in log_dir.iterdir():
        if not p.is_file():
            continue
        if not p.name.startswith(prefix):
            continue
        result.append(p)
    return result


def _delete_older_than(*, files: list[Path], retention_days: int) -> None:
    """Delete logs older than retention_days."""
    if retention_days <= 0:
        return
    cutoff = time.time() - (retention_days * 86400)
    for p in files:
        ts = _safe_mtime(p)
        if ts is None:
            continue
        if ts >= cutoff:
            continue
        _safe_unlink(p)


def _trim_total_size(*, files: list[Path], total_size_limit_bytes: int) -> None:
    """Trim directory to stay within total_size_limit_bytes."""
    if total_size_limit_bytes <= 0:
        return
    sized = [(p, _safe_size(p) or 0, _safe_mtime(p) or 0.0) for p in files]
    total = sum(s for _, s, _ in sized)
    if total <= total_size_limit_bytes:
        return

    sized.sort(key=lambda x: x[2])
    for p, size, _ in sized:
        if total <= total_size_limit_bytes:
            return
        _safe_unlink(p)
        total -= size


def _safe_size(path: Path) -> int | None:
    """Safely get file size."""
    try:
        return path.stat().st_size
    except OSError:
        return None


def _safe_mtime(path: Path) -> float | None:
    """Safely get file modification time."""
    try:
        return path.stat().st_mtime
    except OSError:
        return None


def _safe_unlink(path: Path) -> None:
    """Safely delete file."""
    try:
        path.unlink()
    except OSError:
        return


def default_log_file_path(*, log_dir: Path, filename: str = "backend.log") -> Path:
    """Generate default log file path."""
    return log_dir / filename


def build_default_header(*, version: str) -> HeaderConfig:
    """Build default log header."""
    iso = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    return HeaderConfig(generated_at_iso=iso, source_module="zh-context-scanner", version=version or "unknown")
