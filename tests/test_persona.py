"""Tests for persona CRUD operations."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
async def auto_db():
    from learnbot_mcp.database import clear_db_init_guard, close_db_pool, init_db

    await init_db()
    yield
    await close_db_pool()
    clear_db_init_guard()


@pytest.mark.asyncio
async def test_create_and_get_persona():
    from learnbot_mcp.database import get_persona, list_personas, upsert_persona

    result = await upsert_persona(
        {
            "name": "test-bot",
            "display_name": "Test Bot",
            "backstory": "You are a test assistant.",
        }
    )
    assert result is True

    p = await get_persona("test-bot")
    assert p is not None
    assert p["name"] == "test-bot"
    assert p["backstory"] == "You are a test assistant."

    personas = await list_personas()
    assert any(pp["name"] == "test-bot" for pp in personas)


@pytest.mark.asyncio
async def test_delete_persona():
    from learnbot_mcp.database import delete_persona, get_persona, upsert_persona

    await upsert_persona({"name": "delete-me", "display_name": "Delete Me", "backstory": ""})
    assert await get_persona("delete-me") is not None
    assert await delete_persona("delete-me") is True
    assert await get_persona("delete-me") is None
