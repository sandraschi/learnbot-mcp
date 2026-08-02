"""Japanese reference data — kanji, JMdict, JLPT vocab, Tatoeba examples, JLPT questions.

Was ai-games-collection integration over HTTP (kanji-api :11003, jlpt-api :11001).
Now queries local bundled snapshots directly — no running ai-games-collection
required, no port dependency (11001/11003 also collide with unrelated
fleet hardware-control servers per WEBAPP_PORTS.md; local queries sidestep
that entirely). See data/ATTRIBUTION.md for data sources and licensing.

Data files: data/kanji.db (kanji, jmdict, jlpt_vocabulary, examples tables),
data/jlpt_questions.db (questions, question_options tables). Both are
read-only snapshots of ai-games-collection's data — re-copy from ai-games-collection/data/ to
refresh; do not write to these files from learnbot-mcp.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import aiosqlite

log = logging.getLogger(__name__)

_DATA_DIR = Path(__file__).resolve().parents[2] / "data"
KANJI_DB_PATH = _DATA_DIR / "kanji.db"
JLPT_DB_PATH = _DATA_DIR / "jlpt_questions.db"


def _parse_json(value: str | None) -> list:
    if not value:
        return []
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return []


def _missing_db(path: Path) -> dict:
    return {
        "success": False,
        "error": f"{path.name} not found at {path}. Copy it from ai-games-collection/data/ "
        f"— see data/ATTRIBUTION.md.",
    }


def _connect_ro(path: Path) -> aiosqlite.Connection:
    """Return an unstarted aiosqlite Connection for a read-only local file.

    Caller must enter this exactly once via `async with _connect_ro(path) as conn:`.
    Do NOT `await` this function and then also `async with` the result —
    aiosqlite.Connection.__aenter__ awaits itself to start its background
    thread, and starting that thread twice raises
    RuntimeError("threads can only be started once").
    """
    uri = "file:" + path.as_posix() + "?mode=ro"
    return aiosqlite.connect(uri, uri=True)


async def kanji_search(
    query: str = "",
    jlpt: str = "",
    grade: str = "",
    category: str = "",
    limit: int = 20,
) -> dict:
    """Search kanji by meaning, JLPT level, grade, or category.

    Sources from bundled kanji.db (jouyou + jinmeiyou, 13K+ characters).
    Returns: {"success": bool, "kanji": list, "count": int}
    """
    if not KANJI_DB_PATH.exists():
        return _missing_db(KANJI_DB_PATH)

    where = []
    params: list = []
    if query:
        where.append("(kanji LIKE ? OR meanings LIKE ?)")
        params.extend([f"%{query}%", f"%{query}%"])
    if jlpt:
        where.append("jlpt = ?")
        params.append(jlpt)
    if grade:
        where.append("grade = ?")
        params.append(grade)
    if category:
        where.append("categories LIKE ?")
        params.append(f"%{category}%")
    where_sql = " AND ".join(where) if where else "1=1"

    try:
        async with _connect_ro(KANJI_DB_PATH) as conn:
            conn.row_factory = aiosqlite.Row
            cur = await conn.execute(
                f"""
                SELECT kanji, onyomi, kunyomi, meanings, jlpt, grade, strokes,
                       categories, frequency, radical, is_jouyou, is_jinmeiyou
                FROM kanji
                WHERE {where_sql}
                ORDER BY frequency ASC, strokes ASC
                LIMIT ?
                """,
                (*params, limit),
            )
            rows = await cur.fetchall()
    except aiosqlite.Error as e:
        log.warning("kanji_search query failed: %s", e)
        return {"success": False, "error": str(e)}

    items = [
        {
            "kanji": r["kanji"],
            "onyomi": _parse_json(r["onyomi"]),
            "kunyomi": _parse_json(r["kunyomi"]),
            "meanings": _parse_json(r["meanings"]),
            "jlpt": r["jlpt"],
            "grade": r["grade"],
            "strokes": r["strokes"],
            "categories": _parse_json(r["categories"]),
            "frequency": r["frequency"],
            "radical": r["radical"],
            "is_jouyou": bool(r["is_jouyou"]),
            "is_jinmeiyou": bool(r["is_jinmeiyou"]),
        }
        for r in rows
    ]
    return {"success": True, "kanji": items, "count": len(items)}


async def vocab_lookup(search: str = "", jlpt: str = "", limit: int = 20) -> dict:
    """Look up Japanese vocabulary from JMdict or JLPT-graded lists.

    search= queries the official JMdict dictionary (214K+ entries).
    jlpt= queries the JLPT-graded vocabulary list (8K+ entries) instead.
    Sources from bundled kanji.db.

    Returns: {"success": bool, "vocab": list, "count": int}
    """
    if not KANJI_DB_PATH.exists():
        return _missing_db(KANJI_DB_PATH)
    if not search and not jlpt:
        return {"success": False, "error": "Provide search term or jlpt level"}

    try:
        async with _connect_ro(KANJI_DB_PATH) as conn:
            conn.row_factory = aiosqlite.Row
            if search:
                like = f"%{search}%"
                cur = await conn.execute(
                    """
                    SELECT id, expression, reading, translation, tags
                    FROM jmdict
                    WHERE expression != '？？？'
                      AND (expression LIKE ? OR reading LIKE ? OR translation LIKE ?)
                    ORDER BY length(expression) ASC, expression ASC
                    LIMIT ?
                    """,
                    (like, like, like, limit),
                )
                rows = await cur.fetchall()
                items = [
                    {
                        "expression": r["expression"],
                        "reading": r["reading"],
                        "translation": r["translation"],
                        "tags": r["tags"],
                    }
                    for r in rows
                ]
            else:
                cur = await conn.execute(
                    """
                    SELECT expression, reading, meaning, jlpt_level
                    FROM jlpt_vocabulary
                    WHERE jlpt_level = ?
                    ORDER BY RANDOM()
                    LIMIT ?
                    """,
                    (jlpt, limit),
                )
                rows = await cur.fetchall()
                items = [
                    {
                        "japanese": r["expression"],
                        "reading": r["reading"],
                        "meaning": r["meaning"],
                        "jlpt_level": r["jlpt_level"],
                    }
                    for r in rows
                ]
    except aiosqlite.Error as e:
        log.warning("vocab_lookup query failed: %s", e)
        return {"success": False, "error": str(e)}

    return {"success": True, "vocab": items, "count": len(items)}


async def example_sentences(word: str, limit: int = 5) -> dict:
    """Get example sentences for a Japanese word or expression.

    Sources from bundled kanji.db's Tatoeba sentence table (278K+ pairs,
    CC BY 2.0 FR — see data/ATTRIBUTION.md).

    Returns: {"success": bool, "examples": list, "count": int}
    """
    if not KANJI_DB_PATH.exists():
        return _missing_db(KANJI_DB_PATH)
    if not word:
        return {"success": False, "error": "No word provided"}

    try:
        async with _connect_ro(KANJI_DB_PATH) as conn:
            conn.row_factory = aiosqlite.Row
            cur = await conn.execute(
                """
                SELECT japanese, english
                FROM examples
                WHERE japanese LIKE ? OR words LIKE ?
                LIMIT ?
                """,
                (f"%{word}%", f'%"{word}"%', limit),
            )
            rows = await cur.fetchall()
    except aiosqlite.Error as e:
        log.warning("example_sentences query failed: %s", e)
        return {"success": False, "error": str(e)}

    items = [{"japanese": r["japanese"], "english": r["english"]} for r in rows]
    return {"success": True, "examples": items, "count": len(items)}


async def jlpt_quiz(level: str = "N5", limit: int = 5) -> dict:
    """Get JLPT practice questions for a given level (N5-N1).

    Sources from bundled jlpt_questions.db (600 questions, 12 test sets per level).

    Returns: {"success": bool, "questions": list, "count": int}
    """
    if not JLPT_DB_PATH.exists():
        return _missing_db(JLPT_DB_PATH)

    try:
        async with _connect_ro(JLPT_DB_PATH) as conn:
            conn.row_factory = aiosqlite.Row
            cur = await conn.execute(
                """
                SELECT id, level, question_type, question_text, correct_answer
                FROM questions
                WHERE level = ?
                ORDER BY RANDOM()
                LIMIT ?
                """,
                (level, limit),
            )
            rows = await cur.fetchall()
            items = []
            for r in rows:
                opt_cur = await conn.execute(
                    "SELECT option_letter, option_text, explanation "
                    "FROM question_options WHERE question_id = ?",
                    (r["id"],),
                )
                opts = await opt_cur.fetchall()
                items.append(
                    {
                        "id": r["id"],
                        "level": r["level"],
                        "type": r["question_type"],
                        "question": r["question_text"],
                        "correct": r["correct_answer"],
                        "options": {o["option_letter"]: o["option_text"] for o in opts},
                        "explanations": {o["option_letter"]: o["explanation"] for o in opts},
                    }
                )
    except aiosqlite.Error as e:
        log.warning("jlpt_quiz query failed: %s", e)
        return {"success": False, "error": str(e)}

    return {"success": True, "questions": items, "count": len(items)}


async def jlpt_vocab_by_level(jlpt: str = "N5", limit: int = 20) -> dict:
    """Get JLPT-graded vocabulary list for a specific level (N5-N1).

    Sources from bundled kanji.db's jlpt_vocabulary table (8K+ entries).
    Same underlying query as vocab_lookup(jlpt=...) — kept as a separate
    tool for callers that only ever want level-graded lists, not free-text
    search.

    Returns: {"success": bool, "vocab": list, "count": int}
    """
    return await vocab_lookup(jlpt=jlpt, limit=limit)
