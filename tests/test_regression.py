"""Regression tests — guards against bugs found during handoff (2026-07-16).

See HANDOFF_TODO.md for context on each fix.
"""

from __future__ import annotations

import ast
import json

import pytest


class TestNoDuplicateToolRegistration:
    """Regression guard: all @mcp.tool() decorated functions have unique names."""

    def _get_tool_names(self) -> list[str]:
        with open("src/learnbot_mcp/server.py", encoding="utf-8") as f:
            tree = ast.parse(f.read())
        names: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for deco in node.decorator_list:
                    if (
                        (isinstance(deco, ast.Call) and getattr(deco.func, "attr", None) == "tool")
                        or isinstance(deco, ast.Attribute)
                        and deco.attr == "tool"
                    ):
                        names.append(node.name)
        return names

    def test_no_duplicate_tool_names(self):
        names = self._get_tool_names()
        duplicates = [n for n in names if names.count(n) > 1]
        assert not duplicates, f"Duplicate tool registrations: {set(duplicates)}"
        assert len(names) >= 20, f"Expected >=20 tools, got {len(names)}"


class TestLessonRoundTrip:
    """chat_start -> lesson_create -> lesson_run -> chat_send system prompt."""

    @pytest.mark.asyncio
    async def test_lesson_metadata_injected_into_chat_send(self, db):
        from learnbot_mcp.database import get_db, upsert_persona

        await upsert_persona(
            {
                "name": "regression-test",
                "display_name": "Regression Test",
                "backstory": "You are a test assistant.",
                "voice": "",
                "platforms": [],
                "constraints": [],
                "proactive_triggers": [],
                "knowledge_base": "",
                "languages": ["en"],
                "skills": [],
            }
        )

        from learnbot_mcp.server import chat_start

        start = await chat_start(persona="regression-test", platform="test", user_id="tester")
        assert start["success"] is True
        cid = start["conversation_id"]

        from learnbot_mcp.lessons import lesson_create, lesson_run

        lesson = await lesson_create(
            title="Regression Lesson",
            description="Test lesson for regression guard",
            language="ja",
            level="N5",
            sections=[{"type": "explanation", "content": "Test content", "duration_min": 5}],
            vocab=[{"word": "test", "reading": "test", "definition": "test"}],
            quiz=[{"question": "Q?", "options": ["A", "B"], "answer": "A"}],
        )
        assert lesson["success"] is True
        lid = lesson["lesson"]["id"]

        run = await lesson_run(lesson_id=lid, conversation_id=cid)
        assert run["success"] is True
        assert run["lesson_prompt"] is not None
        assert "Regression Lesson" in run["lesson_prompt"]

        async with get_db() as db_c:
            cur = await db_c.execute("SELECT metadata FROM conversations WHERE id=?", (cid,))
            row = await cur.fetchone()
        assert row is not None
        meta = json.loads(row["metadata"]) if isinstance(row["metadata"], str) else row["metadata"]
        assert meta["active_lesson_id"] == lid
        assert "Regression Lesson" in meta["lesson_prompt"]


class TestVocabQuizDueItem:
    """vocab_quiz returns due items from the DB, not just fresh LLM items."""

    @pytest.mark.asyncio
    async def test_due_item_appears_in_quiz(self, db):
        from learnbot_mcp.database import get_db
        from learnbot_mcp.learn_tools import ensure_vocab_table, vocab_quiz

        await ensure_vocab_table()
        async with get_db() as db_v:
            await db_v.execute(
                "INSERT INTO vocab_items (user_id, word, reading, definition, source_lang, target_lang, due_at) VALUES (?,?,?,?,?,?,datetime('now', '-1 day'))",  # noqa: E501
                ("regression-user", "猫", "ねこ", "cat", "ja", "en"),
            )
            await db_v.commit()

        result = await vocab_quiz(user_id="regression-user", count=5)
        assert result["success"] is True
        assert result["due"] >= 1
        found = any("猫" in q["word"] for q in result["quiz"])
        assert found, "Due item 猫 should appear in quiz output"


class TestGenerateDistractors:
    """_generate_distractors returns non-crash output with the right shape."""

    @pytest.mark.asyncio
    async def test_distractors_return_list(self):
        from learnbot_mcp.learn_tools import _generate_distractors

        result = await _generate_distractors("猫", "cat", "ja", "en", count=3)
        assert isinstance(result, list)
        assert len(result) == 3
        # The correct answer should NOT be in the distractor list
        assert "cat" not in result, "Correct answer leaked into distractors"
