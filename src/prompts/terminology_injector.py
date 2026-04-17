"""
File: terminology_injector.py
Description: Terminology injection for LLM prompts
Author: Arjun Li
Created: 2026-04-17
Last Modified: 2026-04-17
Related modules: templates.py, models.py
"""

from src.models import get_file_header_translations, get_technical_terms


def build_technical_terms_section() -> str:
    """Build technical terms section for prompt from YAML config."""
    terms = get_technical_terms()
    if not terms:
        return "   - No special technical terms defined"
    return "\n".join(f"   - {term}" for term in terms)


def build_file_header_section() -> str:
    """Build file header translations section for prompt."""
    translations = get_file_header_translations()
    if not translations:
        return "   - No file header translations defined"
    return "\n".join(f"   - {zh} → {en}" for zh, en in translations.items())


def build_forced_translation_rules() -> str:
    """Build forced translation rules section.

    This addresses the issue where LLM might skip translating
    standardized labels like '创建日期'.
    """
    return """FORCED TRANSLATIONS - These Chinese labels MUST be translated to English:
   - 文件名 → File name
   - 功能描述 → Function description / Description
   - 作者 → Author
   - 创建日期 → Created / Creation date
   - 最后修改日期 → Last modified / Last modified date
   - 关联模块 → Related module / Related modules
   - 无 → None / N/A
   - 备注 → Note / Remark

IMPORTANT: Do NOT return the original Chinese text for these labels."""
