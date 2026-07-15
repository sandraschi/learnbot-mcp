"""Tests for safety guardrails."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_rate_limit():
    from chatbot_mcp.safety import _rate_limit

    # Should pass for a new user
    assert _rate_limit("test-user") is True


@pytest.mark.asyncio
async def test_check_topics():
    from chatbot_mcp.safety import _check_topics

    rules = [
        {"topic": "politics", "action": "refuse", "message": "I avoid politics."},
        {"topic": "gore", "action": "refuse", "message": ""},
    ]
    result = _check_topics("What do you think about politics today?", rules)
    assert result["blocked"] is True
    assert result["topic"] == "politics"

    result = _check_topics("The weather is nice today.", rules)
    assert result["blocked"] is False


@pytest.mark.asyncio
async def test_pii_redaction():
    from chatbot_mcp.safety import _check_pii_redaction

    result = _check_pii_redaction("My email is sandra@example.com")
    assert result["redacted"] is True
    assert "[REDACTED email]" in result["content"]

    result = _check_pii_redaction("The weather is nice.")
    assert result["redacted"] is False
    assert result["content"] == "The weather is nice."
