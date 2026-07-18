"""Learnbot tools — vocabulary quiz, grammar check, reading passage generation."""

from __future__ import annotations

import json
import logging
import random
from datetime import UTC, datetime

from learnbot_mcp.database import get_db
from learnbot_mcp.llm_client import chat_completion

log = logging.getLogger(__name__)


def _clean_llm_json(text: str) -> str:
    """Strip markdown fences and surrounding prose from LLM output."""
    cleaned = text.replace("```json", "").replace("```", "").strip()
    return cleaned


def _extract_json_array(text: str) -> list:
    """Extract a JSON array from LLM response text."""
    cleaned = _clean_llm_json(text)
    start = cleaned.find("[")
    end = cleaned.rfind("]")
    if start != -1 and end != -1 and end > start:
        cleaned = cleaned[start : end + 1]
    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, list):
            return parsed
    except (json.JSONDecodeError, ValueError):
        pass
    return []


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
        raw = _clean_llm_json(result.get("response", "{}"))
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
    framework: str = "",
) -> dict:
    """Generate a graded reading passage with comprehension questions.

    Works for any language pair. Pass framework='CEFR', 'JLPT', 'HSK', etc.
    to target a specific standard. For example: level='A1', framework='CEFR',
    source_lang='de' gives beginner German.

    ## Return Format
    {"success": bool, "passage": str, "vocabulary": list[dict], "questions": list[dict]}
    """
    framework_hint = f" ({framework})" if framework else ""
    prompt = (
        f"Create a {source_lang} reading passage at {level}{framework_hint} level"
        f" (~100-200 words). "
        f"Also provide {target_lang} translations for 5 key vocabulary items and 3 comprehension questions.\n\n"  # noqa: E501
        "Return JSON with:\n"
        "- `title`: passage title in both languages\n"
        "- `passage`: the {source_lang} text"
        f"{' with furigana for hard kanji in parentheses' if source_lang == 'ja' else ''}\n"
        "- `vocabulary`: array of {`word`, `reading`, `definition`} for 5 key items\n"
        "- `questions`: array of {`question`, `options` (4), `answer`} in {target_lang}"
    )
    try:
        result = await chat_completion(
            messages=[{"role": "user", "content": prompt}],
            system_prompt="You are a JLPT preparation teacher. Generate accurate, level-appropriate content.",  # noqa: E501
        )
        raw = _clean_llm_json(result.get("response", "{}"))
        data = json.loads(raw)
        return {"success": True, **data}
    except Exception as e:
        log.warning("Reading passage failed: %s", e)
        return {"success": False, "error": str(e)}


async def graded_reader(
    language: str = "de",
    level: str = "A1",
    framework: str = "CEFR",
    target_lang: str = "ar",
    topic: str = "",
) -> dict:
    """Generate a graded reader — a leveled reading text with vocabulary and questions.

    Unlike reading_passage which generates one-off texts, graded_reader produces
    a structured reader suitable for extensive reading practice:
    - Full text at the target level
    - Pre-reading vocabulary with translations
    - While-reading comprehension questions
    - Post-reading discussion prompts

    Optimised for any language pair. Example: language='de', target_lang='ar',
    level='A1' for Arabic speakers learning German.

    ## Return Format
    {"success": bool, "title": str, "text": str, "vocabulary": list,
     "questions": list, "discussion": list}
    """
    framework_hint = f" ({framework})" if framework else ""
    topic_hint = f" about '{topic}'" if topic else ""
    prompt = (
        f"Create a graded reader in {language} at {level}{framework_hint} level{topic_hint}.\n\n"
        "The reader should use controlled vocabulary and grammar appropriate for this level.\n\n"
        "Return JSON with:\n"
        "- `title`: title in {language}\n"
        f"- `text`: ~150-250 word passage in {language}\n"
        f"- `vocabulary`: array of 8-12 {{`word`, `reading` (if needed), `definition` (in {target_lang})}} for key vocabulary\n"  # noqa: E501
        "- `questions`: array of 5 {{`question` (in {language}), `options` (4 strings), `answer` (correct option), `explanation` (in {target_lang})}}\n"  # noqa: E501
        f"- `discussion`: array of 3 open-ended prompts in {target_lang} for deeper reflection\n\n"  # noqa: E501
        f"For {language} at {level} level: keep sentences short, use high-frequency words, "
        "repeat key vocabulary, and avoid complex subordinate clauses."
    )
    try:
        result = await chat_completion(
            messages=[{"role": "user", "content": prompt}],
            system_prompt=(
                f"You are an expert in teaching {language} to {target_lang} speakers. "
                "Create pedagogically sound graded readers following recognised "
                "extensive reading principles."
            ),
        )
        raw = _clean_llm_json(result.get("response", "{}"))
        data = json.loads(raw)
        return {
            "success": True,
            "title": data.get("title", ""),
            "text": data.get("text", ""),
            "vocabulary": data.get("vocabulary", []),
            "questions": data.get("questions", []),
            "discussion": data.get("discussion", []),
            "level": level,
            "framework": framework,
            "language": language,
        }
    except Exception as e:
        log.warning("Graded reader failed: %s", e)
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
        distractors = _extract_json_array(result.get("response", "[]"))
        if isinstance(distractors, list) and len(distractors) >= count:
            return distractors[:count]
    except Exception as e:
        log.warning("Distractor generation failed for '%s': %s", word, e)
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
        items = _extract_json_array(result.get("response", "{}"))
        if not isinstance(items, list):
            items = []
    except Exception as e:
        log.warning("Fresh quiz generation failed: %s", e)
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
            except Exception as e:
                log.warning("Failed to save vocab item '%s': %s", word, e)
        # Generate distractors
        distractors = await _generate_distractors(word, definition, src, tgt, count=3)
        options = distractors + [definition]
        random.shuffle(options)
        display = f"{word} ({reading})" if reading else word
        quiz.append({"word": display, "options": options, "answer": definition})
    return quiz
