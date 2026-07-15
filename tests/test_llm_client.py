"""Tests for LLM client."""

from __future__ import annotations

from learnbot_mcp.llm_client import build_history


def test_build_history_empty():
    assert build_history([]) == []


def test_build_history_filters_roles():
    turns = [
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "hi"},
        {"role": "system", "content": "you are a bot"},  # should be filtered
    ]
    msgs = build_history(turns)
    assert len(msgs) == 2
    assert all(m["role"] in ("user", "assistant") for m in msgs)


def test_build_history_respects_max():
    turns = [{"role": "user", "content": f"msg {i}"} for i in range(50)]
    msgs = build_history(turns, max_turns=10)
    assert len(msgs) <= 10
    assert "msg 40" in msgs[0]["content"]
