"""
Safety Guidelines for LLM Prompts

This module provides safety guidelines to be included in all system prompts
to ensure safe and responsible AI-generated content.
"""

from app.core.i18n import t


def get_safety_guidelines() -> str:
    """
    Get safety guidelines text (multilingual)

    Returns:
        Safety guidelines text in the current language
    """
    return t('prompts.safety_guidelines')
