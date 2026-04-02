"""
LLM Integration Tests.
"""

import pytest


def test_system_prompt_exists():
    """Verify the system prompt contains key philosophies."""
    from backend.core.llm import SYSTEM_PROMPT
    assert "Live better with what you have" in SYSTEM_PROMPT
    assert "Never suggest purchases" in SYSTEM_PROMPT


def test_vision_prompt_exists():
    """Verify the vision prompt is defined."""
    from backend.core.vision import VISION_PROMPT
    assert "living space" in VISION_PROMPT.lower()
    assert "safety" in VISION_PROMPT.lower()
