"""Test configuration - temp DB for isolation."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
async def auto_db(monkeypatch, tmp_path):
    """Use a temp DB to avoid cross-contamination between tests."""
    db_file = str(tmp_path / "test.db")
    monkeypatch.setenv("DB_PATH", db_file)
    # Force settings re-read
    import chatbot_mcp.config as cfg

    cfg._settings = None

    from chatbot_mcp.database import clear_db_init_guard, close_db_pool, init_db

    await init_db()
    yield
    await close_db_pool()
    clear_db_init_guard()
