"""Learnbot tools — vocabulary quiz, grammar check, reading passage generation."""

from __future__ import annotations

import json
import logging
import random
from datetime import UTC, datetime

from learnbot_mcp.database import get_db
from learnbot_mcp.llm_client import chat_completion

log = logging.getLogger(__name__)

REVIEW_INTERVALS = [1, 3, 7, 14, 30]  # days for spaced repetition


async def ensure_vocab_table():
    """Create the spaced-repetition vocab table if it doesn't exist."""
    async with get_db() as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS vocab_items (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     TEXT NOT NULL,
                source_lang TEXT NOT NULL DEFAULT 'ja',
                target_lang TEXT NOT NULL DEFAULT 'en',
                word        TEXT NOT NULL,
                reading     TEXT DEFAULT '',
                definition  TEXT NOT NULL,
                example     TEXT DEFAULT '',
                interval    INTEGER NOT NULL DEFAULT 0,
                ease        REAL NOT NULL DEFAULT 2.5,
                due_at      TEXT NOT NULL DEFAULT (datetime('now')),
                created_at  TEXT NOT NULL DEFAULT (datetime('now')),
                reviewed_at TEXT,
                review_count INTEGER NOT NULL DEFAULT 0,
                UNIQUE(user_id, word)
            )
        """)
        await db.commit()


async def vocab_quiz(
    user_id: str,
    source_lang: str = "ja",
    target_lang: str = "en",
    count: int = 5,
) -> dict:
    """Generate a vocabulary quiz from items due for review.

    Pulls items from the spaced-repetition table, fills gaps with LLM-generated
    fresh items when not enough are due.

    ## Return Format
    {"success": bool, "quiz": list[{"word": str, "options": list[str], "answer": str}], "count": int}
    """  # noqa: E501
    await ensure_vocab_table()
    async with get_db() as db:
        cur = await db.execute(
            "SELECT word, reading, definition FROM vocab_items WHERE user_id=? AND due_at <= datetime('now') ORDER BY due_at ASC LIMIT ?",  # noqa: E501
            (user_id, count),
        )
        due_items = await cur.fetchall()
    quiz = []
    for item in due_items:
        word = item["word"]
        reading = item["reading"] if item["reading"] else ""
        correct = item["definition"]
        # Generate distractors via LLM
        distractors = await _generate_distractors(word, correct, source_lang, target_lang, count=3)
        options = distractors + [correct]
        random.shuffle(options)
        display = f"{word} ({reading})" if reading else word
        quiz.append({"word": display, "options": options, "answer": correct})
    if len(quiz) < count:
        # Fill remaining with LLM-generated fresh items
        needed = count - len(quiz)
        fresh = await _generate_fresh_quiz(user_id, source_lang, target_lang, needed)
        quiz.extend(fresh)
    return {"success": True, "quiz": quiz, "count": len(quiz), "due": len(due_items)}


async def vocab_submit(user_id: str, word: str, correct: bool) -> dict:
    """Submit a quiz result and update the spaced-repetition schedule."""
    await ensure_vocab_table()
    async with get_db() as db:
        cur = await db.execute(
            "SELECT id, interval, ease, review_count FROM vocab_items WHERE user_id=? AND word=?",
            (user_id, word),
        )
        item = await cur.fetchone()
        if not item:
            return {"success": False, "error": f"Word '{word}' not found for user {user_id}"}
        interval = item["interval"]
        ease = item["ease"]
        review_count = item["review_count"]
        if correct:
            if review_count == 0:
                interval = 1
            else:
                interval = int(interval * ease)
                ease = min(ease + 0.15, 3.0)
        else:
            interval = 0
            ease = max(ease - 0.3, 1.3)
        from datetime import timedelta

        due = (datetime.now(UTC) + timedelta(days=min(interval, 365))).isoformat()
        await db.execute(
            "UPDATE vocab_items SET interval=?, ease=?, due_at=?, reviewed_at=datetime('now'), review_count=? WHERE id=?",  # noqa: E501
            (interval, ease, due, review_count + 1, item["id"]),
        )
        await db.commit()
    return {"success": True, "word": word, "next_review_days": interval, "ease": round(ease, 2)}


async def grammar_check(text: str, source_lang: str = "ja", target_lang: str = "en") -> dict:
    """Check a learner's sentence for grammar errors and return corrections.

    Uses the LLM to analyze the sentence and provide structured feedback.

    ## Return Format
    {"success": bool, "original": str, "corrected": str, "errors": list[dict], "explanation": str}
    """
    prompt = (
        f"Act as a {source_lang} language teacher. Analyze this {target_lang} learner's sentence:\n\n"  # noqa: E501
        f"---\n{text}\n---\n\n"
        "Return a JSON object with:\n"
        "- `corrected`: the corrected version\n"
        "- `errors`: array of {`original`, `corrected`, `rule`} for each error\n"
        "- `explanation`: brief explanation of the grammar rule in simple terms\n"
        "- `level`: estimated JLPT level (N5-N1)\n\n"
        'If there are no errors, return `"corrected": "<same as original>"` and `"errors": []`.'
    )
    try:
        result = await chat_completion(
            messages=[{"role": "user", "content": prompt}],
            system_prompt="You are a professional language teacher. Be precise but encouraging.",
            model="",
        )
        raw = result.get("response", "{}")
        # Strip markdown code fences if present
        raw = raw.replace("```json", "").replace("```", "").strip()
        data = json.loads(raw)
        return {
            "success": True,
            "original": text,
            "corrected": data.get("corrected", text),
            "errors": data.get("errors", []),
            "explanation": data.get("explanation", ""),
            "level": data.get("level", "?"),
        }
    except Exception as e:
        log.warning("Grammar check failed: %s", e)
        return {"success": False, "error": str(e), "original": text}


async def reading_passage(
    level: str = "N4",
    source_lang: str = "ja",
    target_lang: str = "en",
) -> dict:
    """Generate a graded reading passage with comprehension questions.

    ## Return Format
    {"success": bool, "passage": str, "vocabulary": list[dict], "questions": list[dict]}
    """
    prompt = (
        f"Create a {source_lang} reading passage at JLPT {level} level (~100-200 words). "
        f"Also provide {target_lang} translations for 5 key vocabulary items and 3 comprehension questions.\n\n"  # noqa: E501
        "Return JSON with:\n"
        "- `title`: passage title in both languages\n"
        "- `passage`: the {source_lang} text with furigana for hard kanji in parentheses\n"
        "- `vocabulary`: array of {`word`, `reading`, `definition`} for 5 key items\n"
        "- `questions`: array of {`question`, `options` (4), `answer`} in {target_lang}"
    )
    try:
        result = await chat_completion(
            messages=[{"role": "user", "content": prompt}],
            system_prompt="You are a JLPT preparation teacher. Generate accurate, level-appropriate content.",  # noqa: E501
        )
        raw = result.get("response", "{}").replace("```json", "").replace("```", "").strip()
        data = json.loads(raw)
        return {"success": True, **data}
    except Exception as e:
        log.warning("Reading passage failed: %s", e)
        return {"success": False, "error": str(e)}


async def _generate_distractors(
    word: str, correct: str, src: str, tgt: str, count: int = 3
) -> list[str]:
    """Generate plausible wrong answers for a vocabulary item."""
    prompt = (
        f"Generate {count} plausible but incorrect {tgt} translations for the {src} word '{word}'. "
        f"The correct answer is '{correct}'. Return only a JSON array of strings, nothing else."
    )
    try:
        result = await chat_completion(
            messages=[{"role": "user", "content": prompt}],
            system_prompt="You are a language quiz generator.",
        )
        raw = result.get("response", "[]").replace("```json", "").replace("```", "").strip()
        distractors = json.loads(raw)
        if isinstance(distractors, list) and len(distractors) >= count:
            return distractors[:count]
    except Exception:
        pass
    return ["(generation failed)"] * count


async def _generate_fresh_quiz(user_id: str, src: str, tgt: str, count: int) -> list[dict]:
    """Generate new quiz items via LLM and save them to the vocab table."""
    prompt = (
        f"Generate {count} {src}-{tgt} vocabulary items suitable for a learner. "
        "Return a JSON array of objects with `word`, `reading` (if applicable), `definition`, and `example_sentence`."  # noqa: E501
    )
    try:
        result = await chat_completion(
            messages=[{"role": "user", "content": prompt}],
            system_prompt="You are a language teacher creating study materials.",
        )
        raw = result.get("response", "[]").replace("```json", "").replace("```", "").strip()
        items = json.loads(raw)
        if not isinstance(items, list):
            items = []
    except Exception:
        items = []
    quiz = []
    for item in items[:count]:
        word = item.get("word", "?")
        reading = item.get("reading", "")
        definition = item.get("definition", "?")
        example = item.get("example_sentence", "")
        # Save to DB
        async with get_db() as db:
            try:
                await db.execute(
                    "INSERT OR IGNORE INTO vocab_items (user_id, word, reading, definition, example, source_lang, target_lang) VALUES (?,?,?,?,?,?,?)",  # noqa: E501
                    (user_id, word, reading, definition, example, src, tgt),
                )
                await db.commit()
            except Exception:
                pass
        # Generate distractors
        distractors = await _generate_distractors(word, definition, src, tgt, count=3)
        options = distractors + [definition]
        random.shuffle(options)
        display = f"{word} ({reading})" if reading else word
        quiz.append({"word": display, "options": options, "answer": definition})
    return quiz
