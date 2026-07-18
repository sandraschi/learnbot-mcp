"""Lesson depot — structured lesson plans with CRUD and runner."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Any

from learnbot_mcp.database import get_db
from learnbot_mcp.llm_client import chat_completion

log = logging.getLogger(__name__)


def _clean_llm_json(text: str) -> str:
    """Strip markdown fences from LLM output."""
    return text.replace("```json", "").replace("```", "").strip()


_LESSON_SCHEMA = """
CREATE TABLE IF NOT EXISTS lessons (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    title           TEXT NOT NULL,
    description     TEXT DEFAULT '',
    language        TEXT NOT NULL DEFAULT 'ja',
    level           TEXT NOT NULL DEFAULT 'N4',
    author          TEXT DEFAULT '',
    sections        TEXT NOT NULL DEFAULT '[]',
    vocab           TEXT NOT NULL DEFAULT '[]',
    quiz            TEXT NOT NULL DEFAULT '[]',
    duration_min    INTEGER DEFAULT 15,
    tags            TEXT DEFAULT '[]',
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


async def ensure_lessons_table():
    async with get_db() as db:
        await db.executescript(_LESSON_SCHEMA)
        await db.commit()


async def lesson_create(
    title: str,
    description: str = "",
    language: str = "ja",
    level: str = "N4",
    author: str = "",
    sections: list[dict] | None = None,
    vocab: list[dict] | None = None,
    quiz: list[dict] | None = None,
    duration_min: int = 15,
    tags: list[str] | None = None,
) -> dict:
    """Create a new lesson plan.

    Sections are structured content blocks: {"type": "explanation|dialogue|exercise|quiz",
    "content": str, "duration_min": int}.
    Vocab items: {"word": str, "reading": str, "definition": str}.
    Quiz items: {"question": str, "options": list[str], "answer": str}.
    """
    await ensure_lessons_table()
    async with get_db() as db:
        cur = await db.execute(
            """INSERT INTO lessons (title, description, language, level, author, sections, vocab, quiz, duration_min, tags)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",  # noqa: E501
            (
                title,
                description,
                language,
                level,
                author,
                json.dumps(sections or []),
                json.dumps(vocab or []),
                json.dumps(quiz or []),
                duration_min,
                json.dumps(tags or []),
            ),
        )
        await db.commit()
        lesson_id = cur.lastrowid
    log.info("Lesson created: %s (#%s)", title, lesson_id)
    return await lesson_get(lesson_id)


async def lesson_get(lesson_id: int) -> dict:
    """Get a lesson by ID."""
    await ensure_lessons_table()
    async with get_db() as db:
        cur = await db.execute("SELECT * FROM lessons WHERE id=?", (lesson_id,))
        row = await cur.fetchone()
        if not row:
            return {"success": False, "error": "Lesson not found"}
        return {"success": True, "lesson": _row_to_lesson(row)}


async def lesson_list(language: str = "", level: str = "", tag: str = "", limit: int = 50) -> dict:
    """List lessons with optional filters."""
    await ensure_lessons_table()
    conditions = []
    params: list[Any] = []
    if language:
        conditions.append("language=?")
        params.append(language)
    if level:
        conditions.append("level=?")
        params.append(level)
    if tag:
        conditions.append("tags LIKE ?")
        params.append(f"%{tag}%")
    where = " WHERE " + " AND ".join(conditions) if conditions else ""
    params.append(limit)
    async with get_db() as db:
        cur = await db.execute(
            f"SELECT * FROM lessons {where} ORDER BY updated_at DESC LIMIT ?",
            params,
        )
        rows = await cur.fetchall()
    return {"success": True, "lessons": [_row_to_lesson(r) for r in rows], "count": len(rows)}


async def lesson_update(lesson_id: int, **kwargs) -> dict:
    """Update lesson fields. Pass only the fields to change."""
    await ensure_lessons_table()
    allowed = {
        "title",
        "description",
        "language",
        "level",
        "author",
        "sections",
        "vocab",
        "quiz",
        "duration_min",
        "tags",
    }  # noqa: E501
    sets = []
    params: list[Any] = []
    for key, value in kwargs.items():
        if key in allowed:
            sets.append(f"{key}=?")
            if isinstance(value, (list, dict)):
                params.append(json.dumps(value))
            else:
                params.append(value)
    if not sets:
        return lesson_get(lesson_id)
    sets.append("updated_at=datetime('now')")
    params.append(lesson_id)
    async with get_db() as db:
        await db.execute(f"UPDATE lessons SET {', '.join(sets)} WHERE id=?", params)
        await db.commit()
    return await lesson_get(lesson_id)


async def lesson_delete(lesson_id: int) -> dict:
    """Delete a lesson."""
    await ensure_lessons_table()
    async with get_db() as db:
        cur = await db.execute("DELETE FROM lessons WHERE id=?", (lesson_id,))
        await db.commit()
    return {"success": cur.rowcount > 0, "deleted": cur.rowcount > 0}


async def lesson_generate(
    title: str,
    language: str = "ja",
    level: str = "N4",
    framework: str = "",
    duration_min: int = 15,
) -> dict:
    """Generate a complete lesson plan via LLM and save it."""
    framework_hint = ""
    if framework:
        framework_hint = f" ({framework} framework)"
    prompt = (
        f"Create a {language} lesson plan at {level}{framework_hint} level"
        f" lasting approximately {duration_min} minutes. "
        f"Title: '{title}'.\n\n"
        "Return a JSON object with:\n"
        "- `description`: 1-2 sentence summary\n"
        "- `sections`: array of {`type`: 'explanation'|'dialogue'|'exercise'|'quiz', `content`: str, `duration_min`: int}\n"  # noqa: E501
        "- `vocab`: array of {`word`: str, `reading`: str, `definition`: str} (5-8 items)\n"
        "- `quiz`: array of {`question`: str, `options`: [4 strings], `answer`: str} (3 questions)\n"  # noqa: E501
        "- `tags`: array of topic strings\n\n"
        "The lesson should follow a natural progression: introduce concept → show example → practice → quiz."  # noqa: E501
    )
    try:
        result = await chat_completion(
            messages=[{"role": "user", "content": prompt}],
            system_prompt="You are an expert language curriculum designer. Create engaging, pedagogically sound lessons.",  # noqa: E501
        )
        raw = _clean_llm_json(result.get("response", "{}"))
        data = json.loads(raw)
        return await lesson_create(
            title=title,
            description=data.get("description", ""),
            language=language,
            level=level,
            sections=data.get("sections", []),
            vocab=data.get("vocab", []),
            quiz=data.get("quiz", []),
            duration_min=duration_min,
            tags=data.get("tags", []),
        )
    except Exception as e:
        log.warning("Lesson generation failed: %s", e)
        return {"success": False, "error": str(e), "title": title}


async def lesson_differentiate(
    lesson_id: int,
    target_level: str,
    language: str = "ja",
    duration_min: int | None = None,
) -> dict:
    """Adapt an existing lesson for a different proficiency level.

    Reads the source lesson, sends it to the LLM to rework explanations,
    vocabulary, and quiz for the target JLPT level, and saves as a new lesson.
    The original is unchanged.
    """
    result = await lesson_get(lesson_id)
    if not result.get("success"):
        return result
    src = result["lesson"]
    new_duration = duration_min or src.get("duration_min", 15)
    sections_text = json.dumps(src.get("sections", []), ensure_ascii=False, indent=2)
    vocab_text = json.dumps(src.get("vocab", []), ensure_ascii=False, indent=2)
    quiz_text = json.dumps(src.get("quiz", []), ensure_ascii=False, indent=2)

    prompt = (
        f"Adapt this {src['level']} lesson to JLPT {target_level} (language: {language}).\n"
        f"Original title: '{src['title']}'\n"
        f"Target duration: ~{new_duration} min\n\n"
        "Keep the same topic and structure, but adjust for the new level:\n"
        "- Simpler vocab and grammar for lower levels; more advanced for higher\n"
        "- Adjust explanation depth (more scaffolding for lower, concise for higher)\n"
        "- Rewrite dialogue/exercises to match target proficiency\n"
        "- Adjust quiz difficulty\n\n"
        f"### Existing Sections\n{sections_text}\n\n"
        f"### Existing Vocabulary\n{vocab_text}\n\n"
        f"### Existing Quiz\n{quiz_text}\n\n"
        "Return ONLY a JSON object with:\n"
        "- `description`: 1-2 sentence summary of the *adapted* lesson\n"
        "- `sections`: array of {type, content, duration_min}\n"
        "- `vocab`: array of {word, reading, definition} (5-8 items)\n"
        "- `quiz`: array of {question, options: [4 strings], answer} (3 questions)\n"
        "- `tags`: array of topic strings\n"
        "Do not include markdown fences in the response."
    )
    try:
        result_llm = await chat_completion(
            messages=[{"role": "user", "content": prompt}],
            system_prompt=(
                "You are an expert language curriculum designer. Adapt lessons "
                "precisely to JLPT levels. Adjust vocabulary, grammar complexity, "
                "and explanation depth without changing the core topic."
            ),
        )
        raw = _clean_llm_json(result_llm.get("response", "{}"))
        data = json.loads(raw)
        adapted_title = f"{src['title']} ({target_level})"
        return await lesson_create(
            title=adapted_title,
            description=data.get("description", src.get("description", "")),
            language=language,
            level=target_level,
            author=f"adapted from {src.get('author', '?')}",
            sections=data.get("sections", src.get("sections", [])),
            vocab=data.get("vocab", src.get("vocab", [])),
            quiz=data.get("quiz", src.get("quiz", [])),
            duration_min=new_duration,
            tags=data.get("tags", src.get("tags", [])),
        )
    except Exception as e:
        log.warning("Lesson differentiation failed for #%s → %s: %s", lesson_id, target_level, e)
        return {
            "success": False,
            "error": str(e),
            "source_lesson_id": lesson_id,
            "target_level": target_level,
        }


async def lesson_run(lesson_id: int, conversation_id: str) -> dict:
    """Execute a lesson through an active conversation.

    Sends each section of the lesson as consecutive assistant messages,
    waiting for the user to respond between interactive sections.
    """
    result = await lesson_get(lesson_id)
    if not result.get("success"):
        return result
    lesson = result["lesson"]
    # Post lesson intro as system message
    from learnbot_mcp.database import get_db as _db

    stamp = datetime.now(UTC).isoformat()
    async with _db() as db:
        cur = await db.execute("SELECT state FROM conversations WHERE id=?", (conversation_id,))
        conv = await cur.fetchone()
        if not conv or conv["state"] != "active":
            return {"success": False, "error": "Conversation not active"}
        # Inject lesson intro
        intro = f"Starting lesson: **{lesson['title']}** ({lesson['level']}, ~{lesson['duration_min']}min)\n\n{lesson.get('description', '')}"  # noqa: E501
        await db.execute(
            "INSERT INTO turns (id, conversation_id, role, content, timestamp, platform, safety_verdict) VALUES (?,?,'assistant',?,?,?,?)",  # noqa: E501
            (str(lesson_id), conversation_id, intro, stamp, "lesson", "passed"),
        )
        await db.execute(
            "UPDATE conversations SET turn_count=turn_count+1, updated_at=? WHERE id=?",
            (stamp, conversation_id),
        )  # noqa: E501
        await db.commit()
    # Build a lesson prompt for the LLM
    sections_text = "\n\n".join(
        f"[{s.get('type', 'section').upper()}] {s['content']}" for s in lesson.get("sections", [])
    )
    vocab_text = "\n".join(
        f"  {v.get('word', '?')} ({v.get('reading', '')}) = {v.get('definition', '')}"
        for v in lesson.get("vocab", [])
    )
    quiz_text = (
        "\n".join(f"  Q: {q.get('question', '?')}" for q in lesson.get("quiz", []))
        if lesson.get("quiz")
        else "No quiz."
    )
    lesson_prompt = (
        f"## Lesson: {lesson['title']}\n"
        f"**Level**: {lesson['level']} | **Duration**: {lesson['duration_min']}min\n\n"
        f"### Sections\n{sections_text}\n\n"
        f"### Vocabulary\n{vocab_text}\n\n"
        f"### Quiz\n{quiz_text}\n\n"
        "Guide the student through this lesson. Teach each section interactively, "
        "ask questions, check understanding, and quiz at the end. Be encouraging."
    )

    # Persist as the conversation's active lesson so chat_send merges it into
    # the system prompt on every subsequent turn, until a new lesson_run
    # replaces it or the conversation ends.
    import json as _json

    async with _db() as db:
        await db.execute(
            "UPDATE conversations SET metadata=? WHERE id=?",
            (
                _json.dumps({"active_lesson_id": lesson_id, "lesson_prompt": lesson_prompt}),
                conversation_id,
            ),
        )
        await db.commit()

    return {
        "success": True,
        "lesson_id": lesson_id,
        "lesson_title": lesson["title"],
        "conversation_id": conversation_id,
        "sections": len(lesson.get("sections", [])),
        "vocab_count": len(lesson.get("vocab", [])),
        "lesson_prompt": lesson_prompt,
    }


def _row_to_lesson(r) -> dict:
    def _j(v):
        return json.loads(v) if isinstance(v, str) else v or []

    return {
        "id": r["id"],
        "title": r["title"],
        "description": r["description"],
        "language": r["language"],
        "level": r["level"],
        "author": r["author"],
        "sections": _j(r["sections"]),
        "vocab": _j(r["vocab"]),
        "quiz": _j(r["quiz"]),
        "duration_min": r["duration_min"],
        "tags": _j(r["tags"]),
        "created_at": r["created_at"],
        "updated_at": r["updated_at"],
    }
