"""Database layer - aiosqlite, schema, CRUD helpers."""

from __future__ import annotations

import asyncio
import json
import logging
from contextlib import asynccontextmanager
from typing import Any

import aiosqlite

from chatbot_mcp.config import get_settings

log = logging.getLogger(__name__)

_db_initialized = False
_init_lock = asyncio.Lock()


def clear_db_init_guard() -> None:
    global _db_initialized
    _db_initialized = False


_db_conn: aiosqlite.Connection | None = None
_db_pool_lock = asyncio.Lock()


@asynccontextmanager
async def get_db():
    yield await _get_pooled_connection()


async def _get_pooled_connection() -> aiosqlite.Connection:
    global _db_conn
    cfg = get_settings()
    import os

    os.makedirs(os.path.dirname(cfg.db_path) or ".", exist_ok=True)
    async with _db_pool_lock:
        if _db_conn is None:
            pending = aiosqlite.connect(cfg.db_path)
            pending.daemon = True
            _db_conn = await pending
            _db_conn.row_factory = aiosqlite.Row
            await _db_conn.execute("PRAGMA journal_mode=WAL")
            await _db_conn.execute("PRAGMA foreign_keys=ON")
        return _db_conn


async def close_db_pool() -> None:
    global _db_conn
    async with _db_pool_lock:
        if _db_conn is not None:
            await _db_conn.close()
            _db_conn = None


SCHEMA = """
CREATE TABLE IF NOT EXISTS personas (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    backstory   TEXT NOT NULL,
    voice       TEXT DEFAULT '',
    avatar_vrm  TEXT DEFAULT '',
    avatar_scale REAL DEFAULT 1.0,
    platforms   TEXT DEFAULT '[]',
    constraints TEXT DEFAULT '[]',
    proactive_triggers TEXT DEFAULT '[]',
    knowledge_base TEXT DEFAULT '',
    languages   TEXT DEFAULT '[]',
    skills      TEXT DEFAULT '[]',
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS conversations (
    id              TEXT PRIMARY KEY,
    persona_name    TEXT NOT NULL REFERENCES personas(name),
    platform        TEXT NOT NULL,
    session_id      TEXT DEFAULT '',
    state           TEXT NOT NULL DEFAULT 'active',
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now')),
    turn_count      INTEGER NOT NULL DEFAULT 0,
    metadata        TEXT DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS turns (
    id              TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL REFERENCES conversations(id),
    role            TEXT NOT NULL,
    content         TEXT NOT NULL,
    timestamp       TEXT NOT NULL DEFAULT (datetime('now')),
    user_id         TEXT DEFAULT '',
    platform        TEXT DEFAULT '',
    safety_verdict  TEXT DEFAULT 'passed',
    metadata        TEXT DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS safety_rules (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    topic       TEXT NOT NULL,
    action      TEXT NOT NULL DEFAULT 'refuse',
    message     TEXT DEFAULT '',
    enabled     INTEGER NOT NULL DEFAULT 1,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_conversations_persona ON conversations(persona_name);
CREATE INDEX IF NOT EXISTS idx_conversations_state ON conversations(state);
CREATE INDEX IF NOT EXISTS idx_turns_conv ON turns(conversation_id);
CREATE INDEX IF NOT EXISTS idx_turns_user ON turns(user_id);
CREATE INDEX IF NOT EXISTS idx_turns_ts ON turns(timestamp);
"""


async def init_db() -> None:
    global _db_initialized
    async with _init_lock:
        if _db_initialized:
            return
        async with get_db() as db:
            await db.executescript(SCHEMA)
            await db.commit()
            log.info("Database initialized")
        # Schema migrations
        for col in ("languages", "skills"):
            try:
                await db.execute(f"ALTER TABLE personas ADD COLUMN {col} TEXT DEFAULT '[]'")
                await db.commit()
                log.info("Migrated personas: added %s", col)
            except aiosqlite.OperationalError:
                pass
        _db_initialized = True


async def upsert_persona(persona: dict[str, Any]) -> bool:
    async with get_db() as db:
        try:
            await db.execute(
                """INSERT INTO personas (name, display_name, backstory, voice, avatar_vrm,
                   avatar_scale, platforms, constraints, proactive_triggers, knowledge_base,
                   languages, skills)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    persona["name"],
                    persona.get("display_name", persona["name"]),
                    persona.get("backstory", ""),
                    persona.get("voice", ""),
                    persona.get("avatar_vrm", ""),
                    persona.get("avatar_scale", 1.0),
                    json.dumps(persona.get("platforms", [])),
                    json.dumps(persona.get("constraints", [])),
                    json.dumps(persona.get("proactive_triggers", [])),
                    persona.get("knowledge_base", ""),
                    json.dumps(persona.get("languages", [])),
                    json.dumps(persona.get("skills", [])),
                ),
            )
            await db.commit()
            return True
        except aiosqlite.IntegrityError:
            await db.execute(
                """UPDATE personas SET display_name=?, backstory=?, voice=?, avatar_vrm=?,
                   avatar_scale=?, platforms=?, constraints=?, proactive_triggers=?,
                   knowledge_base=?, languages=?, skills=?, updated_at=datetime('now') WHERE name=?""",  # noqa: E501
                (
                    persona.get("display_name", persona["name"]),
                    persona.get("backstory", ""),
                    persona.get("voice", ""),
                    persona.get("avatar_vrm", ""),
                    persona.get("avatar_scale", 1.0),
                    json.dumps(persona.get("platforms", [])),
                    json.dumps(persona.get("constraints", [])),
                    json.dumps(persona.get("proactive_triggers", [])),
                    persona.get("knowledge_base", ""),
                    json.dumps(persona.get("languages", [])),
                    json.dumps(persona.get("skills", [])),
                    persona["name"],
                ),
            )
            await db.commit()
            return False


async def list_personas() -> list[dict[str, Any]]:
    async with get_db() as db:
        cur = await db.execute("SELECT * FROM personas ORDER BY name")
        rows = await cur.fetchall()
        return [_row_to_persona(r) for r in rows]


async def get_persona(name: str) -> dict[str, Any] | None:
    async with get_db() as db:
        cur = await db.execute("SELECT * FROM personas WHERE name=?", (name,))
        row = await cur.fetchone()
        return _row_to_persona(row) if row else None


async def delete_persona(name: str) -> bool:
    async with get_db() as db:
        cur = await db.execute("DELETE FROM personas WHERE name=?", (name,))
        await db.commit()
        return cur.rowcount > 0


def _row_to_persona(r: aiosqlite.Row) -> dict[str, Any]:
    def _j(v):
        return json.loads(v) if isinstance(v, str) else v or []

    return {
        "id": r["id"],
        "name": r["name"],
        "display_name": r["display_name"],
        "backstory": r["backstory"],
        "voice": r["voice"],
        "avatar_vrm": r["avatar_vrm"],
        "avatar_scale": r["avatar_scale"],
        "platforms": _j(r["platforms"]),
        "constraints": _j(r["constraints"]),
        "proactive_triggers": _j(r["proactive_triggers"]),
        "knowledge_base": r["knowledge_base"],
        "languages": _j(r["languages"]) if "languages" in r else [],
        "skills": _j(r["skills"]) if "skills" in r else [],
        "created_at": r["created_at"],
        "updated_at": r["updated_at"],
    }
