"""Tests for learnbot tools — vocab, grammar, reading, lessons."""

from __future__ import annotations

import pytest


class TestVocabQuiz:
    """Vocab quiz — creation, submission, spaced repetition."""

    @pytest.mark.asyncio
    async def test_quiz_empty_user_returns_no_due(self, db):
        """A new user with no vocab items gets 0 due items, quiz fills with fresh."""
        from learnbot_mcp.learn_tools import vocab_quiz

        result = await vocab_quiz(user_id="test-empty", count=3)
        assert result["success"] is True
        assert result["count"] > 0  # fresh items generated
        assert result["due"] == 0  # no items in DB yet

    @pytest.mark.asyncio
    async def test_vocab_submit_missing_word(self, db):
        """Submitting for a nonexistent word returns error, not crash."""
        from learnbot_mcp.learn_tools import vocab_submit

        result = await vocab_submit(user_id="test-sub", word="missing", correct=True)
        assert result["success"] is False
        assert "not found" in result.get("error", "")


class TestGrammarCheck:
    """Grammar check — uses LLM, should not crash even if LLM is down."""

    @pytest.mark.asyncio
    async def test_grammar_check_returns_structure(self):
        from learnbot_mcp.learn_tools import grammar_check

        result = await grammar_check(text="これはペンです。")
        # LLM may be down — should not crash
        assert "success" in result
        assert "original" in result


class TestReading:
    """Reading passage generation."""

    @pytest.mark.asyncio
    async def test_reading_returns_structure(self):
        from learnbot_mcp.learn_tools import reading_passage

        result = await reading_passage(level="N5")
        assert "success" in result


class TestLessons:
    """Lesson depot CRUD — no LLM needed."""

    @pytest.mark.asyncio
    async def test_create_and_get(self, db):
        from learnbot_mcp.lessons import lesson_create, lesson_get

        result = await lesson_create(
            title="Test Lesson",
            description="A test",
            language="ja", level="N5",
            sections=[{"type": "explanation", "content": "Hello", "duration_min": 5}],
            vocab=[{"word": "こんにちは", "reading": "konnichiwa", "definition": "hello"}],
            quiz=[{"question": "What is こんにちは?", "options": ["hello", "goodbye"], "answer": "hello"}],
        )
        assert result["success"] is True
        lid = result["lesson"]["id"]

        got = await lesson_get(lid)
        assert got["success"] is True
        assert got["lesson"]["title"] == "Test Lesson"
        assert len(got["lesson"]["sections"]) == 1
        assert len(got["lesson"]["vocab"]) == 1
        assert len(got["lesson"]["quiz"]) == 1

    @pytest.mark.asyncio
    async def test_list_filters(self, db):
        from learnbot_mcp.lessons import lesson_create, lesson_list

        await lesson_create(title="Ja N5", language="ja", level="N5")
        await lesson_create(title="Ja N4", language="ja", level="N4")
        await lesson_create(title="En N5", language="en", level="N5")

        all_l = await lesson_list()
        assert all_l["count"] >= 3

        ja = await lesson_list(language="ja")
        assert ja["count"] >= 2

        n5 = await lesson_list(level="N5")
        assert n5["count"] >= 2

    @pytest.mark.asyncio
    async def test_delete(self, db):
        from learnbot_mcp.lessons import lesson_create, lesson_delete, lesson_get

        r = await lesson_create(title="Delete Me")
        lid = r["lesson"]["id"]
        await lesson_delete(lid)
        got = await lesson_get(lid)
        assert got["success"] is False

    @pytest.mark.asyncio
    async def test_update(self, db):
        from learnbot_mcp.lessons import lesson_create, lesson_update, lesson_get

        r = await lesson_create(title="Original", level="N5")
        lid = r["lesson"]["id"]

        await lesson_update(lid, title="Updated", level="N4")
        got = await lesson_get(lid)
        assert got["lesson"]["title"] == "Updated"
        assert got["lesson"]["level"] == "N4"
