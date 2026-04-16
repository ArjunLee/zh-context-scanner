"""
File: logger.py
Description: Main logging system for zh-context-scanner (4-field format, rotation, guard, sampling)
Author: Arjun Li
Created: 2026-04-15
Last Modified: 2026-04-16
Module: zh-context-scanner/solid_logger
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.paths import PathRegistry
from src.solid_logger.guard import GuardConfig, LoggingGuard
from src.solid_logger.rotation import (
    HeaderConfig,
    RotationConfig,
    VaultSaveRotatingHandler,
)

_HEADER_WRITTEN = False
_LAST_LOG_AT: dict[tuple[str, str, str], float] = {}


@dataclass(frozen=True)
class LogMeta:
    """Log metadata for header generation."""
    generated_at_iso: str
    source_module: str
    version: str


def _now_iso() -> str:
    """Generate current time ISO string (UTC, second precision)."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _bracket(value: str) -> str:
    """Wrap value in brackets without padding."""
    trimmed = (value or "").strip()
    return f"[{trimmed}]"


def format_5field_line(timestamp: str, level: str, module: str, action: str, status: str) -> str:
    """
    Format a 5-field log line.

    Format: [Timestamp][Level][Module] Action [Status]
    Example: [2026-04-16T10:00:00][INFO][Translator] Translation complete [200]

    Args:
        timestamp: ISO-8601 timestamp (local timezone, second precision)
        level: Log level (INFO/WARN/ERROR)
        module: Module name (Translator/Backup/System)
        action: Action description
        status: HTTP status code or ---
    """
    return (
        f"{_bracket(timestamp)}{_bracket(level)}{_bracket(module)} {action} {_bracket(status)}"
    )


def format_4field_line(timestamp: str, level: str, action: str, status: str) -> str:
    """Legacy 4-field format (deprecated, use format_5field_line)."""
    return format_5field_line(timestamp, level, "System", action, status)


def should_sample_request(action: str, cooldown_s: float = 2.0) -> bool:
    """
    Sample control: avoid logging duplicate actions within cooldown window.

    Args:
        action: Log action identifier
        cooldown_s: Cooldown seconds (default 2.0)

    Returns:
        True if should skip logging (sampled out)
    """
    if cooldown_s <= 0:
        return False

    key = ("zh-context-scanner", "translation", action)
    now = time.monotonic()
    prev = _LAST_LOG_AT.get(key)

    if prev is None:
        _LAST_LOG_AT[key] = now
        return False

    if (now - prev) < cooldown_s:
        return True

    _LAST_LOG_AT[key] = now
    return False


class HeaderOnceStreamHandler(logging.StreamHandler):
    """Stream handler that writes header only once per session."""

    def __init__(self, meta: LogMeta, guard: GuardConfig | None = None):
        super().__init__()
        self._meta = meta
        self._guard = LoggingGuard(guard)

    def emit(self, record: logging.LogRecord) -> None:
        """Emit log record with header-once and guard protection."""
        try:
            self._write_header_once()
            rendered = self.format(record)
            allowed = self._guard.filter_line(
                logger_name=record.name,
                level_name=record.levelname,
                rendered_line=rendered,
                file_path=None,
            )
            if allowed is None:
                return
            self.stream.write(allowed + self.terminator)
            self.flush()
        except Exception:
            self.handleError(record)

    def _write_header_once(self) -> None:
        global _HEADER_WRITTEN
        if _HEADER_WRITTEN:
            return
        _HEADER_WRITTEN = True
        self.stream.write("=== Normalized Log ===\n")
        self.stream.write(f"Generated At: {self._meta.generated_at_iso}\n")
        self.stream.write(f"Source Module: {self._meta.source_module}\n")
        self.stream.write(f"Version: {self._meta.version}\n")
        self.stream.write("Field Description:\n")
        self.stream.write("- Timestamp: ISO-8601 (local timezone, second precision)\n")
        self.stream.write("- Level: Log level (INFO/WARN/ERROR)\n")
        self.stream.write("- Module: Module name (Translator/Backup/System)\n")
        self.stream.write("- Action: API action or event description\n")
        self.stream.write("- Status: HTTP status code or ---\n")
        self.stream.write("\n")
        self.flush()


class HTTPFilter(logging.Filter):
    """Filter out verbose HTTP request logs from OpenAI SDK."""

    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        if "HTTP Request:" in msg and "api.deepseek.com" in msg:
            return False
        return True


class Bracket5Formatter(logging.Formatter):
    """
    Formatter that outputs 5-field bracket format.

    Format: [Timestamp][Level][Module] Action [Status]
    """

    def __init__(self, *args: object, use_colors: bool | None = None, **kwargs: object):
        _ = use_colors
        super().__init__(*args, **kwargs)

    def format(self, record: logging.LogRecord) -> str:
        ts = datetime.fromtimestamp(record.created).astimezone().strftime("%Y-%m-%dT%H:%M:%S")
        level = record.levelname
        status = getattr(record, "status", "---")
        status_s = str(status) if status is not None else "---"

        message = record.getMessage()
        module, action = self._extract_module_and_action(message)

        return format_5field_line(ts, level, module, action, status_s)

    def _extract_module_and_action(self, message: str) -> tuple[str, str]:
        """
        Extract module name and action from message.

        Returns:
            (module, action) tuple
        """
        if message.startswith("[20"):
            message = message.split("] ", 1)[-1]

        if message.startswith("[INFO]") or message.startswith("[WARNING]") or message.startswith("[ERROR]"):
            message = message.split("] ", 1)[-1]

        if "HTTP Request:" in message:
            return "OpenAI SDK", "HTTP " + message.split("HTTP Request:")[1].strip()

        if "Translation Request" in message:
            return "Translator", message

        if "Translation Success" in message or "Translation Complete" in message:
            return "Translator", message

        if "Backup saved:" in message:
            return "Backup", message

        if "Parse result:" in message:
            return "Translator", message

        return "System", message


class Bracket4Formatter(Bracket5Formatter):
    """Legacy 4-field formatter (deprecated, use Bracket5Formatter)."""


def build_log_config(
    version: str = "0.1.0",
    path_registry: PathRegistry | None = None,
) -> dict[str, Any]:
    """
    Build logging configuration dict for dictConfig.

    Args:
        version: Tool version string
        path_registry: PathRegistry for log file path (auto-detected if None)

    Returns:
        Logging config dict
    """
    if path_registry is None:
        tool_root = PathRegistry.detect_tool_root()
        path_registry = PathRegistry(tool_root)

    meta = LogMeta(
        generated_at_iso=_now_iso(),
        source_module="zh-context-scanner",
        version=version,
    )

    path_registry.log_dir.mkdir(parents=True, exist_ok=True)
    file_path = path_registry.log_file

    header = HeaderConfig(
        generated_at_iso=meta.generated_at_iso,
        source_module=meta.source_module,
        version=meta.version,
    )

    return {
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {
            "http_filter": {"()": "src.solid_logger.logger.HTTPFilter"},
        },
        "formatters": {
            "bracket4": {"()": "src.solid_logger.logger.Bracket4Formatter"},
        },
        "handlers": {
            "file": {
                "()": "src.solid_logger.logger.make_rotating_file_handler",
                "header": header,
                "file_path": file_path,
                "filters": ["http_filter"],
            },
            "console": {
                "()": "src.solid_logger.logger.make_console_handler",
                "meta": meta,
                "filters": ["http_filter"],
            },
        },
        "root": {
            "level": "INFO",
            "handlers": ["file", "console"],
        },
        "loggers": {
            "zh_context_scanner": {
                "level": "INFO",
                "handlers": ["file", "console"],
                "propagate": False,
            },
        },
    }


def make_rotating_file_handler(header: HeaderConfig, file_path: Path) -> logging.Handler:
    """Create rotating file handler with guard protection."""
    handler = VaultSaveRotatingHandler(
        file_path=file_path,
        header=header,
        rotation=RotationConfig(),
        guard=GuardConfig(),
        level=logging.INFO,
    )
    handler.setFormatter(Bracket5Formatter())
    return handler


def make_console_handler(meta: LogMeta) -> logging.Handler:
    """Create console handler with header-once and warning level."""
    handler = HeaderOnceStreamHandler(meta=meta, guard=GuardConfig())
    handler.setLevel(logging.WARNING)
    handler.setFormatter(Bracket5Formatter())
    return handler


def configure_logging(version: str = "0.1.0", path_registry: PathRegistry | None = None) -> dict[str, Any]:
    """
    Configure runtime logging with 4-field format, rotation, and guard.

    Args:
        version: Tool version string
        path_registry: Optional path registry

    Returns:
        Applied logging config dict
    """
    import logging.config

    cfg = build_log_config(version=version, path_registry=path_registry)
    logging.config.dictConfig(cfg)
    return cfg


class TranslationLogger:
    """
    High-level translation logger with sampling and 4-field format.

    Wraps standard logging.Logger with translation-specific methods.
    """

    def __init__(self, logger: logging.Logger):
        self._logger = logger

    @staticmethod
    def utc_now_iso() -> str:
        """Get current UTC time ISO string."""
        return datetime.now(timezone.utc).isoformat(timespec="seconds")

    def log_api_request(
        self,
        base_url: str,
        model: str,
        file_name: str,
        comment_count: int,
    ) -> None:
        """
        Log API request with sampling control.

        Args:
            base_url: API endpoint base URL
            model: LLM model name
            file_name: Source file being translated
            comment_count: Number of comments to translate
        """
        action = f"LLM Translation Request - File:{file_name} | Model:{model} | Comments:{comment_count}"

        if not should_sample_request(action, cooldown_s=2.0):
            self._logger.info(action, extra={"status": "---"})

    def log_api_response(
        self,
        file_name: str,
        success_count: int,
        fail_count: int,
        duration_ms: float,
        http_status: int = 200,
    ) -> None:
        """
        Log API response with result summary and HTTP status code.

        Args:
            file_name: Source file name
            success_count: Successful translation count
            fail_count: Failed translation count
            duration_ms: API call duration in milliseconds
            http_status: HTTP status code (200/404/502), default 200
        """
        if fail_count > 0:
            status_label = "partial_failure" if success_count > 0 else "all_failed"
            action = f"Translation Complete - File:{file_name} | Success:{success_count} | Failed:{fail_count} | Duration:{duration_ms:.0f}ms [{status_label}]"
            self._logger.warning(action, extra={"status": http_status})
        else:
            action = f"Translation Success - File:{file_name} | Success:{success_count} | Duration:{duration_ms:.0f}ms"
            self._logger.info(action, extra={"status": http_status})

    def log_translation_detail(
        self,
        original_text: str,
        translated_text: str,
        duration_ms: float,
        tokens_used: int | None = None,
    ) -> None:
        """
        Log translation detail.

        Records original text summary (first 50 chars), translated summary,
        duration, and tokens.

        Args:
            original_text: Original Chinese text
            translated_text: Translated English text
            duration_ms: Translation duration in milliseconds
            tokens_used: Token count (optional)
        """
        orig_summary = original_text[:50] + "..." if len(original_text) > 50 else original_text
        trans_summary = translated_text[:50] + "..." if len(translated_text) > 50 else translated_text
        tokens_str = f" | Tokens:{tokens_used}" if tokens_used else ""
        action = f"Translation Detail - Original:{repr(orig_summary)} | Translated:{repr(trans_summary)} | Duration:{duration_ms:.0f}ms{tokens_str}"
        self._logger.info(action, extra={"status": 200})

    def log_from_api_response(
        self,
        original_text: str,
        translated_text: str,
        duration_ms: float,
        api_response,
    ) -> None:
        """
        Extract tokens from OpenAI API response and log translation detail.

        Unified method for both CommentTranslator and WholeFileTranslator.
        Avoids duplicate logic across translation modules.

        Args:
            original_text: Original text (full or summary)
            translated_text: Translated text (full or summary)
            duration_ms: Translation duration in milliseconds
            api_response: OpenAI ChatCompletion response object
        """
        tokens_used = None
        if api_response and hasattr(api_response, "usage") and api_response.usage:
            tokens_used = api_response.usage.total_tokens
        self.log_translation_detail(original_text, translated_text, duration_ms, tokens_used)

    def log_parse_result(self, count: int, sample: str | None = None) -> None:
        """
        Log JSON parse result.

        Args:
            count: Number of items parsed
            sample: Sample of parsed items (optional)
        """
        sample_str = f" | Sample:{sample}" if sample else ""
        action = f"Parse result - Count:{count}{sample_str}"
        self._logger.info(action, extra={"status": 200})

    def info(self, message: str) -> None:
        """Log info message."""
        self._logger.info(message, extra={"status": "---"})

    def warning(self, message: str) -> None:
        """Log warning message."""
        self._logger.warning(message, extra={"status": "---"})

    def error(self, message: str) -> None:
        """Log error message."""
        self._logger.error(message, extra={"status": "---"})

    def debug(self, message: str) -> None:
        """Log debug message."""
        self._logger.debug(message, extra={"status": "---"})


def get_logger() -> TranslationLogger:
    """Get or create translation logger instance."""
    return TranslationLogger(logging.getLogger("zh_context_scanner"))
