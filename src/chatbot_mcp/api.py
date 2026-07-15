"""Starlette REST API - health, personas, conversations, safety, audit."""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles

from chatbot_mcp._version import __version__
from chatbot_mcp.compliance import disclosure_message, refusal_templates, requires_real_name_auth
from chatbot_mcp.config import get_settings
from chatbot_mcp.platforms import speech_say
from chatbot_mcp.proactive import proactive_tick

# Gemini TTS voices with character descriptions (from speech-mcp)
GEMINI_VOICES = [
    {
        "id": "Leda",
        "gender": "female",
        "desc": "Warm, friendly, youthful — good for cheerful assistants",
    },
    {"id": "Aoede", "gender": "female", "desc": "Soft, melodic — good for storytelling"},
    {
        "id": "Callirrhoe",
        "gender": "female",
        "desc": "Bright, energetic — good for upbeat responses",
    },
    {"id": "Autonoe", "gender": "female", "desc": "Calm, measured — good for thoughtful answers"},
    {"id": "Despina", "gender": "female", "desc": "Smooth, professional — good for business"},
    {"id": "Erinome", "gender": "female", "desc": "Gentle, soothing — good for comfort"},
    {"id": "Laomedeia", "gender": "female", "desc": "Rich, warm — good for narration"},
    {"id": "Iocaste", "gender": "female", "desc": "Clear, authoritative — good for presenting"},
    {
        "id": "Umbriel",
        "gender": "female",
        "desc": "Soft-spoken, intimate — good for close conversation",
    },
    {"id": "Kore", "gender": "neutral", "desc": "Balanced, all-purpose — good for general use"},
    {"id": "Puck", "gender": "neutral", "desc": "Playful, mischievous — good for casual chat"},
    {"id": "Algieba", "gender": "neutral", "desc": "Steady, reliable — safe default"},
    {"id": "Algenib", "gender": "neutral", "desc": "Earnest, honest — good for serious topics"},
    {"id": "Charon", "gender": "male", "desc": "Deep, resonant — good for authority figures"},
    {"id": "Fenrir", "gender": "male", "desc": "Gruff, rough — good for pirates and warriors"},
    {"id": "Orion", "gender": "male", "desc": "Bold, confident — good for heroes"},
    {"id": "Orus", "gender": "male", "desc": "Warm baritone — good for mentors"},
    {"id": "Zephyr", "gender": "male", "desc": "Light, airy — good for friendly banter"},
    {"id": "Enceladus", "gender": "male", "desc": "Deep, booming — good for villains"},
    {"id": "Rasalgethi", "gender": "male", "desc": "Grand, theatrical — good for dramatic effect"},
]

log = logging.getLogger(__name__)
cfg = get_settings()

_START_TIME = datetime.now(UTC)


async def api_health(request: Request) -> JSONResponse:
    from chatbot_mcp.database import get_db

    uptime = (datetime.now(UTC) - _START_TIME).total_seconds()
    try:
        async with get_db() as db:
            cur = await db.execute("SELECT COUNT(*) FROM personas")
            (pc,) = await cur.fetchone()
            cur = await db.execute("SELECT COUNT(*) FROM conversations")
            (cc,) = await cur.fetchone()
            cur = await db.execute("SELECT COUNT(*) FROM safety_rules")
            (rc,) = await cur.fetchone()
    except Exception:
        pc = cc = rc = -1
    return JSONResponse(
        {
            "status": "ok",
            "server": cfg.server_name,
            "version": __version__,
            "uptime_seconds": int(uptime),
            "personas": pc,
            "conversations": cc,
            "safety_rules": rc,
        }
    )


async def api_diagnostics(request: Request) -> JSONResponse:
    uptime = (datetime.now(UTC) - _START_TIME).total_seconds()
    return JSONResponse(
        {
            "status": "ok",
            "server": cfg.server_name,
            "version": __version__,
            "uptime_seconds": int(uptime),
            "port": cfg.backend_port,
        }
    )


async def api_personas_list(request: Request) -> JSONResponse:
    from chatbot_mcp.database import list_personas

    personas = await list_personas()
    return JSONResponse({"personas": personas, "count": len(personas)})


async def api_personas_create(request: Request) -> JSONResponse:
    from chatbot_mcp.database import upsert_persona

    body = await request.json()
    created = await upsert_persona(
        {
            "name": body.get("name", ""),
            "display_name": body.get("display_name", body.get("name", "")),
            "backstory": body.get("backstory", ""),
            "voice": body.get("voice", ""),
            "avatar_vrm": body.get("avatar_vrm", ""),
            "avatar_scale": float(body.get("avatar_scale", 1.0)),
            "platforms": body.get("platforms", []),
            "constraints": body.get("constraints", []),
            "proactive_triggers": body.get("proactive_triggers", []),
            "knowledge_base": body.get("knowledge_base", ""),
        }
    )
    return JSONResponse({"success": True, "created": created})


async def api_persona_get(request: Request) -> JSONResponse:
    from chatbot_mcp.database import get_persona

    p = await get_persona(request.path_params["name"])
    if not p:
        return JSONResponse({"error": "not found"}, status_code=404)
    return JSONResponse(p)


async def api_persona_delete(request: Request) -> JSONResponse:
    from chatbot_mcp.database import delete_persona

    deleted = await delete_persona(request.path_params["name"])
    return JSONResponse({"success": deleted})


async def api_conversations_list(request: Request) -> JSONResponse:
    from chatbot_mcp.database import get_db

    state = request.query_params.get("state", "")
    async with get_db() as db_conv:
        if state:
            cur = await db_conv.execute(
                "SELECT * FROM conversations WHERE state=? ORDER BY updated_at DESC", (state,)
            )
        else:
            cur = await db_conv.execute("SELECT * FROM conversations ORDER BY updated_at DESC")
        rows = await cur.fetchall()
    return JSONResponse({"conversations": [dict(r) for r in rows], "count": len(rows)})


async def api_conversations_create(request: Request) -> JSONResponse:
    from chatbot_mcp.database import get_db

    body = await request.json()
    persona = body.get("persona", "")
    platform = body.get("platform", "web")
    user_id = body.get("user_id", "")
    cid = str(uuid.uuid4())[:12]
    stamp = datetime.now(UTC).isoformat()
    async with get_db() as db:
        await db.execute(
            "INSERT INTO conversations (id, persona_name, platform, session_id, state, created_at, updated_at) VALUES (?,?,?,?,'active',?,?)",  # noqa: E501
            (cid, persona, platform, user_id, stamp, stamp),
        )
        await db.commit()
    return JSONResponse({"success": True, "conversation_id": cid, "persona": persona})


async def api_conversations_send(request: Request) -> JSONResponse:
    import traceback as _tb

    from chatbot_mcp.database import get_db, get_persona

    try:
        body = await request.json()
        content = body.get("content", "")
        user_id = body.get("user_id", "")
        cid = request.path_params["id"]
        async with get_db() as db:
            cur = await db.execute("SELECT * FROM conversations WHERE id=?", (cid,))
            conv = await cur.fetchone()
        if not conv:
            return JSONResponse({"error": "Conversation not found"}, status_code=404)
        if conv["state"] != "active":
            return JSONResponse({"error": f"Conversation is {conv['state']}"}, status_code=400)

        from chatbot_mcp.safety import check_safety

        safety = await check_safety(content, user_id)
        turn_id = str(uuid.uuid4())[:12]
        stamp = datetime.now(UTC).isoformat()
        platform = conv["platform"]

        if not safety["passed"]:
            refusal = safety.get("reason", "Content blocked")
            async with get_db() as db:
                await db.execute(
                    "INSERT INTO turns (id, conversation_id, role, content, timestamp, user_id, platform, safety_verdict) VALUES (?,?,'user',?,?,?,?,?)",  # noqa: E501
                    (turn_id, cid, content[:10000], stamp, user_id, platform, "blocked"),
                )  # noqa: E501
                await db.commit()
            return JSONResponse({"response": refusal, "safety_verdict": "blocked"})

        redacted = safety.get("redacted_content", content)
        async with get_db() as db:
            await db.execute(
                "INSERT INTO turns (id, conversation_id, role, content, timestamp, user_id, platform, safety_verdict) VALUES (?,?,'user',?,?,?,?,?)",  # noqa: E501
                (turn_id, cid, redacted[:10000], stamp, user_id, platform, "passed"),
            )  # noqa: E501
            await db.commit()

        persona = await get_persona(conv["persona_name"])
        from chatbot_mcp.llm_client import build_history, chat_completion

        async with get_db() as db_hist:
            cur_hist = await db_hist.execute(
                "SELECT role, content FROM turns WHERE conversation_id=? ORDER BY timestamp ASC",
                (cid,),
            )  # noqa: E501
            history = build_history(await cur_hist.fetchall())
        history.append({"role": "user", "content": (redacted or content)[:4000]})
        system = (persona["backstory"] if persona else "") + (
            "\n\nPrefix your response with ONE bracketed emotion tag matching your feeling. "
            "Examples: [cheerfully] [sympathetically] [excited] [softly] [thoughtful] [playful] [serious] [warmly] [sad] [laughs]"  # noqa: E501
        )
        response_text = ""
        try:
            result = await chat_completion(messages=history, system_prompt=system)
            response_text = result.get("response", "")
        except Exception as e:
            log.warning("LLM call failed: %s", e)
            response_text = f"(LLM call failed: {e})"

        async with get_db() as db:
            await db.execute(
                "INSERT INTO turns (id, conversation_id, role, content, timestamp, platform, safety_verdict) VALUES (?,?,'assistant',?,?,?,?)",  # noqa: E501
                (str(uuid.uuid4())[:12], cid, response_text[:10000], stamp, platform, "passed"),
            )  # noqa: E501
            await db.execute(
                "UPDATE conversations SET turn_count=turn_count+1, updated_at=? WHERE id=?",
                (stamp, cid),
            )  # noqa: E501
            await db.commit()

        # Strip emotion tags from display, use them in TTS
        import re as _re

        _tag_pattern = r"\[(laughs|whispers|sighs|excited|sad|happy|cheerfully|softly|sympathetically|warmly|gently|dramatically|nervously|sarcastically|angry|serious|thoughtful|playful|warm|cold|formal|casual)\]"  # noqa: E501
        _tags = _re.findall(_tag_pattern, response_text)
        _display_text = _re.sub(_tag_pattern, "", response_text).strip()

        if persona and persona.get("voice"):
            import asyncio

            from chatbot_mcp.platforms import speech_say

            _speech = _display_text[:1900]
            if _tags:
                _speech = f"[{_tags[0]}] {_speech}"
            asyncio.create_task(speech_say(text=_speech[:2000], voice=persona["voice"]))

        return JSONResponse({"response": _display_text, "safety_verdict": "passed"})
    except Exception as e:
        _tb.print_exc()
        log.error("chat_send failed: %s", e, exc_info=True)
        return JSONResponse({"error": str(e), "traceback": _tb.format_exc()}, status_code=500)


async def api_conversation_hibernate(request: Request) -> JSONResponse:
    from chatbot_mcp.database import get_db

    stamp = datetime.now(UTC).isoformat()
    async with get_db() as db:
        cur = await db.execute(
            "UPDATE conversations SET state='hibernating', updated_at=? WHERE id=? AND state='active'",  # noqa: E501
            (stamp, request.path_params["id"]),
        )
        await db.commit()
    return JSONResponse({"success": cur.rowcount > 0})


async def api_conversation_resume(request: Request) -> JSONResponse:
    from chatbot_mcp.database import get_db

    stamp = datetime.now(UTC).isoformat()
    async with get_db() as db:
        cur = await db.execute(
            "UPDATE conversations SET state='active', updated_at=? WHERE id=? AND state='hibernating'",  # noqa: E501
            (stamp, request.path_params["id"]),
        )
        await db.commit()
    return JSONResponse({"success": cur.rowcount > 0})


async def api_conversation_delete(request: Request) -> JSONResponse:
    from chatbot_mcp.database import get_db

    cid = request.path_params["id"]
    async with get_db() as db:
        await db.execute("DELETE FROM turns WHERE conversation_id=?", (cid,))
        await db.execute("DELETE FROM conversations WHERE id=?", (cid,))
        await db.commit()
    return JSONResponse({"success": True})


async def api_safety_rules_list(request: Request) -> JSONResponse:
    from chatbot_mcp.database import get_db

    async with get_db() as db_sr:
        cur = await db_sr.execute("SELECT * FROM safety_rules ORDER BY topic")
    rows = await cur.fetchall()
    return JSONResponse({"rules": [dict(r) for r in rows], "count": len(rows)})


async def api_safety_rules_create(request: Request) -> JSONResponse:
    from chatbot_mcp.database import get_db

    body = await request.json()
    async with get_db() as db:
        cur = await db.execute(
            "INSERT INTO safety_rules (topic, action, message) VALUES (?,?,?)",
            (body.get("topic", ""), body.get("action", "refuse"), body.get("message", "")),
        )
        await db.commit()
    return JSONResponse({"success": True, "id": cur.lastrowid})


async def api_safety_rule_delete(request: Request) -> JSONResponse:
    from chatbot_mcp.database import get_db

    async with get_db() as db:
        cur = await db.execute(
            "DELETE FROM safety_rules WHERE id=?", (int(request.path_params["id"]),)
        )
        await db.commit()
    return JSONResponse({"success": cur.rowcount > 0})


async def api_compliance(request: Request) -> JSONResponse:
    cfg = get_settings()
    return JSONResponse(
        {
            "regime": cfg.regulatory_regime,
            "real_name_auth": requires_real_name_auth(),
            "retention_days": cfg.conversation_retention_days,
            "disclosure": disclosure_message(),
            "refusal_templates": refusal_templates(),
        }
    )


async def api_voices(request: Request) -> JSONResponse:
    """List available Gemini TTS voices with test-playback endpoint hint."""
    return JSONResponse({"voices": GEMINI_VOICES, "count": len(GEMINI_VOICES)})


async def api_voice_test(request: Request) -> JSONResponse:
    """Test a voice by saying a sample phrase."""
    body = await request.json()
    voice_id = body.get("voice_id", "Leda")
    text = body.get("text", "Hello! This is a voice test. How do I sound?")
    result = await speech_say(text=text, voice=voice_id)
    return JSONResponse(result)


async def api_proactive_tick(request: Request) -> JSONResponse:
    result = await proactive_tick()
    return JSONResponse(result)


async def api_audit_query(request: Request) -> JSONResponse:
    from chatbot_mcp.database import get_db

    try:
        user_id = request.query_params.get("user_id", "")
        persona = request.query_params.get("persona", "")
        after = request.query_params.get("after", "")
        limit = int(request.query_params.get("limit", 50))
        conditions = []
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
        where = " WHERE " + " AND ".join(conditions) if conditions else ""
        q = f"""SELECT t.id, t.conversation_id, t.role, t.content, t.timestamp, t.user_id,
                       t.platform, t.safety_verdict, c.persona_name
                FROM turns t JOIN conversations c ON c.id=t.conversation_id
                {where} ORDER BY t.timestamp DESC LIMIT ?"""
        params.append(limit)
        async with get_db() as db_aud:
            cur = await db_aud.execute(q, params)
            rows = await cur.fetchall()
        return JSONResponse({"turns": [dict(r) for r in rows], "count": len(rows)})
    except Exception as e:
        import traceback

        tb = traceback.format_exc()
        log.error("Audit query failed: %s\n%s", e, tb)
        return JSONResponse({"error": str(e), "detail": tb}, status_code=500)


def _spa_fallback(request: Request) -> HTMLResponse:
    dist = Path(__file__).resolve().parents[2] / "web_sota" / "dist"
    index = dist / "index.html"
    if index.is_file():
        return HTMLResponse(index.read_text(encoding="utf-8"))
    return HTMLResponse(
        "<h1>Frontend not built. Run: cd web_sota && bun run build</h1>", status_code=503
    )


def build_app() -> Starlette:
    dist = Path(__file__).resolve().parents[2] / "web_sota" / "dist"
    _routes = [
        Route("/health", api_health),
        Route("/api/health", api_health),
        Route("/api/v1/diagnostics", api_diagnostics),
        Route("/api/personas", api_personas_list),
        Route("/api/personas", api_personas_create, methods=["POST"]),
        Route("/api/personas/{name}", api_persona_get),
        Route("/api/personas/{name}", api_persona_delete, methods=["DELETE"]),
        Route("/api/conversations", api_conversations_list),
        Route("/api/conversations", api_conversations_create, methods=["POST"]),
        Route("/api/conversations/{id}/send", api_conversations_send, methods=["POST"]),
        Route("/api/conversations/{id}/hibernate", api_conversation_hibernate, methods=["POST"]),
        Route("/api/conversations/{id}/resume", api_conversation_resume, methods=["POST"]),
        Route("/api/conversations/{id}", api_conversation_delete, methods=["DELETE"]),
        Route("/api/safety/rules", api_safety_rules_list),
        Route("/api/safety/rules", api_safety_rules_create, methods=["POST"]),
        Route("/api/safety/rules/{id}", api_safety_rule_delete, methods=["DELETE"]),
        Route("/api/compliance", api_compliance),
        Route("/api/voices", api_voices),
        Route("/api/voice/test", api_voice_test, methods=["POST"]),
        Route("/api/chat/proactive-tick", api_proactive_tick, methods=["POST"]),
        Route("/api/audit", api_audit_query),
    ]
    if dist.is_dir() and (dist / "index.html").is_file():
        _routes.append(Mount("/assets", StaticFiles(directory=str(dist / "assets")), name="assets"))
        _routes.append(Route("/{path:path}", _spa_fallback))
    app = Starlette(routes=_routes)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["tauri://localhost", "http://tauri.localhost", "https://tauri.localhost"],
        allow_origin_regex=r"https?://(?:[a-zA-Z0-9-]+\.ts\.net|.*?\.tail-[a-f0-9]+\.ts\.net|tauri\.localhost|localhost|127\.0\.0\.1|192\.168\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3}\.\d{1,3}|100\.\d{1,3}\.\d{1,3}\.\d{1,3})(?::\d+)?$|^tauri://localhost$",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    return app


def run_rest() -> None:
    import uvicorn

    app = build_app()
    log.info("chatbot-mcp REST API on port %s", cfg.backend_port)
    uvicorn.run(app, host="0.0.0.0", port=cfg.backend_port, log_level="info")


if __name__ == "__main__":
    run_rest()
