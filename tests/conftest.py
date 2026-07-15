"""Test configuration - temp DB for isolation. Not autouse — add ``db`` param to tests that need it."""

from __future__ import annotations

import pytest


@pytest.fixture
async def db(monkeypatch, tmp_path):
    """Use a temp DB. Add ``db`` parameter to test functions that need database access."""
    db_file = str(tmp_path / "test.db")
    monkeypatch.setenv("DB_PATH", db_file)
    import learnbot_mcp.config as cfg

    cfg._settings = None

    from learnbot_mcp.database import clear_db_init_guard, close_db_pool, init_db

    await init_db()
    yield
    await close_db_pool()
    clear_db_init_guard()
