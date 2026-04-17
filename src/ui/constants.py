"""
File: constants.py
Description: TUI configuration constants (pagination, display limits)
Author: Arjun Li
Created: 2026-04-15
"""

from __future__ import annotations

# Pagination settings
PAGE_SIZE = 15
MAX_DISPLAY_ITEMS = 100


# Display limits
MAX_PATH_DISPLAY_LENGTH = 50
MAX_PREVIEW_LINES = 30
MAX_LINE_DISPLAY_LENGTH = 60


# Navigation hints (i18n keys)
FOOTER_NAV_HINT = "footer_nav_hint"
FOOTER_PAGE_HINT = "footer_page_hint"
FOOTER_MENU_HINT = "footer_menu_hint"
FOOTER_DETAIL_HINT = "footer_detail_hint"


# UI styles
STYLE_SELECTED = "selected"
STYLE_NORMAL = "normal"
STYLE_TITLE = "title"
STYLE_MUTED = "muted"
STYLE_ACCENT = "accent"


# Menu icons
ICON_SCAN = "🔍"
ICON_INCREMENTAL = "📊"
ICON_MANUAL = "👍️"
ICON_BACKUP = "💾"
ICON_LANGUAGE = "🌐"
ICON_MODE = "📋"
ICON_EXIT = "🚪"
ICON_FILE = "📄"
ICON_DETAIL = "🔎"
ICON_NOTICE = "ℹ️"
ICON_SUCCESS = "✅"
ICON_ERROR = "⚠️"

# Translation mode icons
ICON_MODE_COMMENT = "💬"
ICON_MODE_FULL = "📝"

# Settings menu icons
ICON_SETTINGS = "🔧"
ICON_CHECK = "✓"
ICON_ARROW = "→"
ICON_RESET = "🔄"

# Setup wizard icons
ICON_QUICK = "🌠"
ICON_WIZARD = "🧙"
ICON_FOLDER = "📂"
ICON_CHECKBOX_ON = "✓"
ICON_CHECKBOX_OFF = "○"
ICON_CONFIG = "⚙️"
ICON_API_KEY = "🔑"
