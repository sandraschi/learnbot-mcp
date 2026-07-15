"""FastMCP server - persona management, chat lifecycle, safety, platform bridge."""

from __future__ import annotations

import json
import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from fastmcp.server.lifespan import lifespan
from fastmcp.server.server import FastMCP

from learnbot_mcp._version import __version__
from learnbot_mcp.config import get_settings

_READ_ONLY = {"readonly": True}
_MUTATING: dict = {}
_disclosed_convos: set[str] = set()

log = logging.getLogger(__name__)
cfg = get_settings()

_TURNS_INSERT = "INSERT INTO turns (id, conversation_id, role, content, timestamp, user_id, platform, safety_verdict) VALUES (?,?,?,?,?,?,?,?)"  # noqa: E501
_CONV_ACTIVE = "UPDATE conversations SET turn_count=turn_count+1, updated_at=? WHERE id=?"


@lifespan
async def _lifespan(_server):
    from learnbot_mcp.database import close_db_pool, init_db

    await init_db()
    log.info("learnbot-mcp startup: DB ready")

    from learnbot_mcp.compliance import check_conversation_retention

    retention = await check_conversation_retention()
    if retention.get("deleted", 0) > 0:
        log.info("Retention cleanup on startup: %d conversations", retention["deleted"])

    try:
        yield {}
    finally:
        await close_db_pool()
        log.info("learnbot-mcp shutdown: DB closed")


mcp = FastMCP(
    name=cfg.server_name,
    version=__version__,
    instructions="AI chatbot orchestrator - personas, conversations, safety, platforms",
    lifespan=_lifespan,
)


@mcp.tool(annotations=_MUTATING)
async def persona_create(
    name: str,
    display_name: str,
    backstory: str,
    voice: str = "",
    avatar_vrm: str = "",
    avatar_scale: float = 1.0,
    platforms: str = "",
    constraints: str = "",
    proactive_triggers: str = "",
    knowledge_base: str = "",
    languages: str = "",
    skills: str = "",
) -> dict:
    """Create or update a chatbot persona.

    ## Return Format
    {"success": bool, "name": str, "created": bool}

    ## Examples
    persona_create(name="miko", display_name="Miko-chan", backstory="A friendly assistant...")
    """
    from learnbot_mcp.database import upsert_persona

    persona = {
        "name": name,
        "display_name": display_name,
        "backstory": backstory,
        "voice": voice,
        "avatar_vrm": avatar_vrm,
        "avatar_scale": avatar_scale,
        "platforms": [p.strip() for p in platforms.split(",") if p.strip()] if platforms else [],
        "constraints": json.loads(constraints) if constraints else [],
        "proactive_triggers": json.loads(proactive_triggers) if proactive_triggers else [],
        "knowledge_base": knowledge_base,
        "languages": [lang.strip() for lang in languages.split(",") if lang.strip()]
        if languages
        else [],
        "skills": [sk.strip() for sk in skills.split(",") if sk.strip()] if skills else [],
    }
    created = await upsert_persona(persona)
    log.info("Persona %s: %s", "created" if created else "updated", name)
    return {"success": True, "name": name, "created": created}


@mcp.tool(annotations=_READ_ONLY)
async def persona_get(name: str) -> dict:
    """Get a persona by name.

    ## Return Format
    {"success": bool, "persona": {...} or None}
    """
    from learnbot_mcp.database import get_persona

    p = await get_persona(name)
    return {"success": p is not None, "persona": p}


@mcp.tool(annotations=_READ_ONLY)
async def persona_list() -> dict:
    """List all registered personas.

    ## Return Format
    {"success": bool, "personas": [...], "count": int}
    """
    from learnbot_mcp.database import list_personas

    personas = await list_personas()
    return {"success": True, "personas": personas, "count": len(personas)}


@mcp.tool(annotations=_MUTATING)
async def persona_delete(name: str) -> dict:
    """Delete a persona.

    ## Return Format
    {"success": bool, "deleted": bool}
    """
    from learnbot_mcp.database import delete_persona

    deleted = await delete_persona(name)
    return {"success": deleted, "deleted": deleted}


@mcp.tool(annotations=_MUTATING)
async def chat_start(
    persona: str,
    platform: str = "opencode",
    user_id: str = "",
) -> dict:
    """Start a new conversation with a persona.

    ## Return Format
    {"success": bool, "conversation_id": str, "persona": str}

    ## Examples
    chat_start(persona="miko", platform="resonite", user_id="sandra")
    """
    from learnbot_mcp.database import get_db, get_persona

    existing = await get_persona(persona)
    if not existing:
        return {"success": False, "error": f"Persona '{persona}' not found"}

    conv_id = str(uuid.uuid4())[:12]
    stamp = datetime.now(UTC).isoformat()
    _csql = """INSERT INTO conversations (id, persona_name, platform, session_id, state, created_at, updated_at) VALUES (?,?,?,?,'active',?,?)"""  # noqa: E501
    async with get_db() as db:
        await db.execute(_csql, (conv_id, persona, platform, user_id, stamp, stamp))
        await db.commit()

    log.info("Chat started: conv=%s persona=%s platform=%s", conv_id, persona, platform)
    return {"success": True, "conversation_id": conv_id, "persona": persona}


@mcp.tool(annotations=_MUTATING)
async def chat_send(
    conversation_id: str,
    content: str,
    user_id: str = "",
) -> dict:
    """Send a message in an active conversation. Runs safety checks, then calls LLM.

    ## Return Format
    {"success": bool, "response": str, "safety_verdict": str}

    ## Examples
    chat_send(conversation_id="abc123", content="Hello!")
    """
    from learnbot_mcp.database import get_db, get_persona
    from learnbot_mcp.safety import check_safety

    async with get_db() as db:
        cur = await db.execute("SELECT * FROM conversations WHERE id=?", (conversation_id,))
        conv = await cur.fetchone()

    if not conv:
        return {"success": False, "error": "Conversation not found"}
    if conv["state"] != "active":
        return {"success": False, "error": f"Conversation is {conv['state']}"}

    # Compliance check (regulatory regime)
    from learnbot_mcp.compliance import disclosure_message, requires_real_name_auth

    if requires_real_name_auth() and not user_id:
        return {"success": False, "error": "Real-name authentication required for this deployment."}

    if conversation_id not in _disclosed_convos:
        disc = disclosure_message()
        if disc:
            _disclosed_convos.add(conversation_id)
            return {"success": True, "response": disc, "safety_verdict": "system"}

    # Safety check
    safety = await check_safety(content, user_id)
    turn_id = str(uuid.uuid4())[:12]
    stamp = datetime.now(UTC).isoformat()
    platform = conv["platform"]

    if not safety["passed"]:
        refusal = safety.get("reason", "Content blocked")
        async with get_db() as db:
            await db.execute(
                _TURNS_INSERT,
                (turn_id, conversation_id, content[:10000], stamp, user_id, platform, "passed"),
            )
            await db.execute(_CONV_ACTIVE, (stamp, conversation_id))
            await db.commit()
        return {"success": True, "response": refusal, "safety_verdict": "blocked"}

    redacted_content = safety.get("redacted_content", content)

    # Log user turn
    async with get_db() as db:
        await db.execute(
            _TURNS_INSERT,
            (
                turn_id,
                conversation_id,
                redacted_content[:10000],
                stamp,
                user_id,
                platform,
                "passed",
            ),
        )
        await db.commit()

    # Call LLM with conversation history
    persona = await get_persona(conv["persona_name"])
    system_prompt = persona["backstory"] if persona else "You are a helpful assistant."

    _emo_tag_instr = (
        "\n\nIMPORTANT: Prefix your response with ONE bracketed emotion tag that best matches your feeling. "  # noqa: E501
        "Examples: [cheerfully] [sympathetically] [excited] [softly] [thoughtful] [playful] [serious] [warmly] [sad] [laughs] "  # noqa: E501
        "The tag drives voice tone and robot motion. Do NOT use tags in short answers."
    )
    system_prompt = (system_prompt or "") + _emo_tag_instr

    from learnbot_mcp.llm_client import build_history, chat_completion

    async with get_db() as db:
        cur = await db.execute(
            "SELECT role, content FROM turns WHERE conversation_id=? ORDER BY timestamp ASC",
            (conversation_id,),
        )
        previous_turns = await cur.fetchall()

    history = build_history(previous_turns)
    user_msg = {"role": "user", "content": (redacted_content or content)[:4000]}
    history.append(user_msg)

    try:
        result = await chat_completion(
            messages=history,
            system_prompt=system_prompt[:4000],
        )
        response_text = result["response"]
    except Exception as e:
        log.warning("LLM call failed: %s", e)
        response_text = f"(LLM unavailable: {e})"

    # Log assistant turn
    _aid = str(uuid.uuid4())[:12]
    async with get_db() as db:
        await db.execute(
            "INSERT INTO turns (id, conversation_id, role, content, timestamp, platform, safety_verdict) VALUES (?,?,'assistant',?,?,?,?)",  # noqa: E501
            (_aid, conversation_id, response_text[:10000], stamp, platform, "passed"),
        )
        await db.execute(_CONV_ACTIVE, (stamp, conversation_id))
        await db.commit()

    import re as _re

    # Speak via speech-mcp (fire-and-forget), strip emotion tags for display
    if persona and persona.get("voice"):
        from learnbot_mcp.platforms import speech_say

        _tags = _re.findall(
            r"\[(laughs|whispers|sighs|excited|sad|happy|cheerfully|softly|sympathetically|warmly|gently|dramatically|nervously|sarcastically|angry|serious|thoughtful|playful|warm|cold|formal|casual)\]",
            response_text,
        )
        _speech_text = (response_text or "")[:2000]
        if _tags:
            _speech_text = f"[{_tags[0]}] {_speech_text}"[:2000]
        import asyncio

        asyncio.create_task(speech_say(text=_speech_text, voice=persona["voice"]))

        # Robot emotion expression (fire-and-forget)
        if _tags:
            from learnbot_mcp.robot_orchestrator import execute_emotion

            asyncio.create_task(execute_emotion(emotion_tag=_tags[0]))

    # Strip emotion tags from displayed response
    response_text = _re.sub(
        r"\[(laughs|whispers|sighs|excited|sad|happy|cheerfully|softly|sympathetically|warmly|gently|dramatically|nervously|sarcastically|angry|serious|thoughtful|playful|warm|cold|formal|casual)\]",
        "",
        response_text,
    ).strip()

    return {"success": True, "response": response_text, "safety_verdict": "passed"}


@mcp.tool(annotations=_MUTATING)
async def chat_hibernate(conversation_id: str) -> dict:
    """Pause a conversation. State is preserved for later resume."""
    from learnbot_mcp.database import get_db

    stamp = datetime.now(UTC).isoformat()
    async with get_db() as db:
        cur = await db.execute(
            "UPDATE conversations SET state='hibernating', updated_at=? WHERE id=? AND state='active'",  # noqa: E501
            (stamp, conversation_id),
        )
        await db.commit()
    return {"success": cur.rowcount > 0, "conversation_id": conversation_id}


@mcp.tool(annotations=_MUTATING)
async def chat_resume(conversation_id: str) -> dict:
    """Resume a hibernated conversation."""
    from learnbot_mcp.database import get_db

    stamp = datetime.now(UTC).isoformat()
    async with get_db() as db:
        cur = await db.execute(
            "UPDATE conversations SET state='active', updated_at=? WHERE id=? AND state='hibernating'",  # noqa: E501
            (stamp, conversation_id),
        )
        await db.commit()
    return {"success": cur.rowcount > 0, "conversation_id": conversation_id}


@mcp.tool(annotations=_MUTATING)
async def chat_destroy(conversation_id: str) -> dict:
    """Permanently delete a conversation and all its turns."""
    from learnbot_mcp.database import get_db

    async with get_db() as db:
        await db.execute("DELETE FROM turns WHERE conversation_id=?", (conversation_id,))
        await db.execute("DELETE FROM conversations WHERE id=?", (conversation_id,))
        await db.commit()
    return {"success": True, "conversation_id": conversation_id}


@mcp.tool(annotations=_READ_ONLY)
async def chat_list(state_filter: str = "") -> dict:
    """List conversations, optionally filtered by state (active, hibernating, completed).

    ## Return Format
    {"success": bool, "conversations": [...], "count": int}
    """
    from learnbot_mcp.database import get_db

    async with get_db() as db_cl:
        if state_filter:
            cur = await db_cl.execute(
                "SELECT * FROM conversations WHERE state=? ORDER BY updated_at DESC",
                (state_filter,),
            )
        else:
            cur = await db_cl.execute("SELECT * FROM conversations ORDER BY updated_at DESC")
        rows = await cur.fetchall()
    return {"success": True, "conversations": [dict(r) for r in rows], "count": len(rows)}


@mcp.tool(annotations=_MUTATING)
async def safety_rule_create(topic: str, action: str = "refuse", message: str = "") -> dict:
    """Create a safety rule. When a message matches the topic, the action is triggered.

    ## Return Format
    {"success": bool, "id": int}
    """
    from learnbot_mcp.database import get_db

    async with get_db() as db:
        cur = await db.execute(
            "INSERT INTO safety_rules (topic, action, message) VALUES (?,?,?)",
            (topic, action, message),
        )
        await db.commit()
    return {"success": True, "id": cur.lastrowid}


@mcp.tool(annotations=_READ_ONLY)
async def safety_rule_list() -> dict:
    """List all safety rules."""
    from learnbot_mcp.database import get_db

    async with get_db() as db_sr:
        cur = await db_sr.execute("SELECT * FROM safety_rules ORDER BY topic")
        rows = await cur.fetchall()
    return {"success": True, "rules": [dict(r) for r in rows], "count": len(rows)}


@mcp.tool(annotations=_MUTATING)
async def safety_rule_delete(rule_id: int) -> dict:
    """Delete a safety rule by ID."""
    from learnbot_mcp.database import get_db

    async with get_db() as db:
        cur = await db.execute("DELETE FROM safety_rules WHERE id=?", (rule_id,))
        await db.commit()
    return {"success": cur.rowcount > 0}


@mcp.tool(annotations=_READ_ONLY)
async def audit_query(
    user_id: str = "", persona: str = "", after: str = "", limit: int = 50
) -> dict:
    """Query the audit log. Filter by user_id, persona name, or time window.

    ## Return Format
    {"success": bool, "turns": [...], "count": int}
    """
    from learnbot_mcp.database import get_db

    conditions: list[str] = []
    params: list[Any] = []
    if user_id:
        conditions.append("t.user_id=?")
        params.append(user_id)
    if persona:
        conditions.append("c.persona_name=?")
        params.append(persona)
    if after:
        conditions.append("t.timestamp>=?")
        params.append(after)

    where = (" WHERE " + " AND ".join(conditions)) if conditions else ""
    query = f"""SELECT t.id, t.conversation_id, t.role, t.content, t.timestamp, t.user_id,
                       t.platform, t.safety_verdict, c.persona_name
                FROM turns t JOIN conversations c ON c.id=t.conversation_id
                {where} ORDER BY t.timestamp DESC LIMIT ?"""
    params.append(limit)
    async with get_db() as db_aud:
        cur = await db_aud.execute(query, params)
        rows = await cur.fetchall()
    return {"success": True, "turns": [dict(r) for r in rows], "count": len(rows)}


@mcp.tool(annotations=_READ_ONLY)
async def chatbot_help() -> dict:
    """Show all available learnbot-mcp tools and usage."""
    return {
        "success": True,
        "tools": [
            "persona_create, persona_get, persona_list, persona_delete",
            "chat_start, chat_send, chat_hibernate, chat_resume, chat_destroy, chat_list",
            "safety_rule_create, safety_rule_list, safety_rule_delete",
            "audit_query, platform_send",
        ],
        "message": "See SPEC.md for full documentation.",
    }


@mcp.tool(annotations=_MUTATING)
async def platform_send(
    conversation_id: str,
    content: str,
    platform: str,
    voice: str = "",
) -> dict:
    """Send content to a specific platform bridge (speech, discord, resonite).

    ## Return Format
    {"success": bool, "platform": str, ...}

    ## Examples
    platform_send(conversation_id="abc123", content="Hello!", platform="speech", voice="heart")
    """
    from learnbot_mcp.platforms import platform_send as _send

    return await _send(
        conversation_id=conversation_id, content=content, platform=platform, voice=voice
    )


@mcp.tool(annotations=_MUTATING)
async def chat_proactive_tick() -> dict:
    """Check all personas for due proactive triggers and fire them.

    Call this periodically (e.g. every 5 min via cron).  Returns list of
    triggered conversations.

    ## Return Format
    {"success": bool, "triggered": [...], "count": int}
    """
    from learnbot_mcp.proactive import proactive_tick

    return await proactive_tick()


def main():
    from learnbot_mcp.server import mcp

    mcp.run(transport="stdio")
