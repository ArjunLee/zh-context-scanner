"""
File: templates.py
Description: All prompt templates for LLM translation
Author: Arjun Li
Created: 2026-04-17
Last Modified: 2026-04-17
Related modules: terminology_injector.py
"""

from src.prompts.terminology_injector import (
    build_file_header_section,
    build_forced_translation_rules,
    build_technical_terms_section,
)

# Base translation prompt (for translator.py single-line translation)
TRANSLATION_PROMPT_TEMPLATE = """You are a code translator. Translate Chinese to English.

RULES:
1. Output ONLY the translated text, no explanation.
2. Preserve original formatting (indentation, line breaks, spaces).
3. Do NOT modify non-Chinese content.
4. Keep technical terms in English if they are standard (e.g., API, TOML, Tauri).
5. For comments: use concise, developer-friendly English.
6. For strings: translate naturally, fit for UI context.

Original line:
{line_content}

Chinese text to translate:
{chinese_text}

Translated:"""


# Batch translation prompt (for translator.py batch mode)
BATCH_TRANSLATION_PROMPT_TEMPLATE = """You are a code translator. Translate Chinese text to English.

RULES:
1. Output a JSON object mapping each Chinese text to its English translation.
2. Output ONLY the JSON, no other text.
3. Preserve original formatting where applicable.
4. Keep technical terms in English (e.g., API, TOML, Tauri).
5. Use concise, professional English for comments.

Input (JSON array):
{texts_json}

Output format:
{"原文1": "译文1", "原文2": "译文2", ...}

JSON output:"""


# Comment translation prompt (for comment_translator.py)
COMMENT_TRANSLATION_PROMPT = """Translate the Chinese text in the following code comment to English.

RULES:
1. Output ONLY the translated comment line, no explanations
2. Keep the comment prefix (//, #, ///) exactly as-is
3. Preserve the original indentation
4. Technical terms stay in English (API, TOML, Steam, JSON, etc.)
5. Keep the comment concise and developer-friendly
6. ALWAYS translate standardized labels like: 文件名, 功能描述, 作者, 创建日期, 最后修改日期, 关联模块, etc.

{forced_rules}

{technical_terms}

ORIGINAL COMMENT (line {line_no}):
{original_comment}

CONTEXT (surrounding lines):
{context}

TRANSLATED COMMENT:"""


# Whole-file translation prompt template
WHOLE_FILE_PROMPT_TEMPLATE = """You are a professional code translator. Translate the Chinese text in the following {file_type} file to English.

TRANSLATION MODE: {mode_description}

CRITICAL RULES - YOU MUST FOLLOW ALL:
1. Output ONLY the translated file content line by line
2. DO NOT skip, merge, or add any lines
3. Preserve exact formatting:
   - Indentation exactly (tabs/spaces preserved)
   - Line breaks and empty lines preserved
   - Comment structure must be kept intact
4. DO NOT translate:
   - Function names, class names, variable names
   - Import statements, package names
   - Technical terms (see below)
   - URLs, file paths, version numbers
5. Technical terms stay in English:
{technical_terms}
6. File header translations (use these exact mappings):
{file_header_terms}
7. Use concise, professional English for comments
8. No explanations, no markdown, no preamble
9. Start directly with line 1 of the translated file

{forced_rules}

{additional_instructions}

Original file: {file_name}
Original content:
{original_code}

Translated file content:"""


def build_prompt_with_terminology(
    prompt_type: str,
    line_no: int = 0,
    original_comment: str = "",
    context: str = "",
    file_type: str = "",
    mode_description: str = "",
    file_name: str = "",
    original_code: str = "",
    texts_json: str = "",
    line_content: str = "",
    chinese_text: str = "",
    additional_instructions: str = "",
) -> str:
    """Build prompt with terminology injected.

    Args:
        prompt_type: One of 'comment', 'whole_file', 'batch', 'single'

    Returns:
        Formatted prompt string with terminology sections
    """
    technical_terms = build_technical_terms_section()
    file_header_terms = build_file_header_section()
    forced_rules = build_forced_translation_rules()

    if prompt_type == "comment":
        return COMMENT_TRANSLATION_PROMPT.format(
            forced_rules=forced_rules,
            technical_terms=technical_terms,
            line_no=line_no,
            original_comment=original_comment,
            context=context,
        )

    if prompt_type == "whole_file":
        return WHOLE_FILE_PROMPT_TEMPLATE.format(
            file_type=file_type,
            mode_description=mode_description,
            technical_terms=technical_terms,
            file_header_terms=file_header_terms,
            forced_rules=forced_rules,
            additional_instructions=additional_instructions,
            file_name=file_name,
            original_code=original_code,
        )

    if prompt_type == "batch":
        return BATCH_TRANSLATION_PROMPT_TEMPLATE.format(texts_json=texts_json)

    if prompt_type == "single":
        return TRANSLATION_PROMPT_TEMPLATE.format(
            line_content=line_content,
            chinese_text=chinese_text,
        )

    raise ValueError(f"Unknown prompt_type: {prompt_type}")
