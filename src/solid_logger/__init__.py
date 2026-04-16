"""
File: __init__.py
Description: SolidLogger - Unified logging system for zh-context-scanner
Author: Arjun Li
Created: 2026-04-16
Last Modified: 2026-04-16
Module: zh-context-scanner/solid_logger
"""

from .guard import GuardConfig, LoggingGuard
from .logger import (
    Bracket4Formatter,
    Bracket5Formatter,
    TranslationLogger,
    build_log_config,
    configure_logging,
    format_4field_line,
    format_5field_line,
    get_logger,
    should_sample_request,
)
from .rotation import (
    HeaderConfig,
    RotationConfig,
    VaultSaveRotatingHandler,
    build_default_header,
    default_log_file_path,
)

__all__ = [
    "TranslationLogger",
    "get_logger",
    "configure_logging",
    "build_log_config",
    "format_5field_line",
    "format_4field_line",
    "should_sample_request",
    "Bracket5Formatter",
    "Bracket4Formatter",
    "RotationConfig",
    "HeaderConfig",
    "VaultSaveRotatingHandler",
    "build_default_header",
    "default_log_file_path",
    "GuardConfig",
    "LoggingGuard",
]
