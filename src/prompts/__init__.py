"""
File: __init__.py
Description: Unified prompt module for LLM translation
Author: Arjun Li
Created: 2026-04-17
Last Modified: 2026-04-17
Related modules: translator.py, comment_translator.py, whole_file_translator.py
"""

from src.prompts.templates import (
    BATCH_TRANSLATION_PROMPT_TEMPLATE,
    COMMENT_TRANSLATION_PROMPT,
    TRANSLATION_PROMPT_TEMPLATE,
    WHOLE_FILE_PROMPT_TEMPLATE,
    build_prompt_with_terminology,
)
from src.prompts.terminology_injector import (
    build_file_header_section,
    build_forced_translation_rules,
    build_technical_terms_section,
)

__all__ = [
    "COMMENT_TRANSLATION_PROMPT",
    "BATCH_TRANSLATION_PROMPT_TEMPLATE",
    "TRANSLATION_PROMPT_TEMPLATE",
    "WHOLE_FILE_PROMPT_TEMPLATE",
    "build_prompt_with_terminology",
    "build_technical_terms_section",
    "build_file_header_section",
    "build_forced_translation_rules",
]
