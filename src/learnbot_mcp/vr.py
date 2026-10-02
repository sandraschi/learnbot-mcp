"""VR companion status + Miko summon - Phase 2 (Resonite live, VRChat/Overte Phase 4).

Thin orchestration for the /vr launchpad page. All companions are
optional: every probe degrades to a dialogic hint, never an exception.
Single implementation shared by REST (GET /api/vr/status, POST /api/vr/summon)
and MCP (vr_status, vr_summon tools in server.py).

Summon (Resonite, live since Phase 2): session probe -> optional avatar load
(LEARNBOT_MIKO_AVATAR_PATH, empty = skipped with hint) -> Happy expression
best-effort -> spoken JP greeting via speech-mcp -> audit turn.
Voice ranking, locked Phase 3 A/B (2026-10-02): gemini/Leda JP proven
(4.3 s sample in docs/audio), kokoro EN-only (gloss fallback), qwen needs
clone ref audio, VoiceStudio pending sidecar. Ear confirmation is Sandra's.
VRChat/Overte summon lands in Phase 4/6.
"""

from __future__ import annotations

import logging

import httpx
from starlette.requests import Request
from starlette.responses import JSONResponse

from learnbot_mcp.config import get_settings

log = logging.getLogger(__name__)

# Short timeout: status probes must never stall page load.
_PROBE_TIMEOUT_S = 2.5


async def _probe(url: str) -> tuple[bool, str]:
    """GET <url>/health with a short timeout. Returns (reachable, detail)."""
    target = f"{url.rstrip('/')}/health"
    try:
        async with httpx.AsyncClient(timeout=_PROBE_TIMEOUT_S) as client:
            resp = await client.get(target)
            if resp.status_code < 500:
                return True, f"HTTP {resp.status_code}"
            return False, f"HTTP {resp.status_code}"
    except Exception as e:  # ConnectError, Timeout, DNS - all mean "not running"
        return False, f"{type(e).__name__}"


async def vr_status_payload() -> dict:
    """Aggregate companion status for the /vr page. Never raises."""
    cfg = get_settings()
    companions = {
        "resonite": {
            "url": cfg.resonite_mcp_url,
            "repo": "https://github.com/sandraschi/resonite-mcp",
            "hint": "Start resonite-mcp: cd D:/Dev/repos/resonite-mcp && just serve",
        },
        "vrchat": {
            "url": cfg.vrchat_mcp_url,
            "repo": "https://github.com/sandraschi/vrchat-mcp",
            "hint": "Start vrchat-mcp: cd D:/Dev/repos/vrchat-mcp && just serve",
        },
        "overte": {
            "url": cfg.overte_mcp_url,
            "repo": "https://github.com/sandraschi/overte-mcp",
            "hint": "Start overte-mcp: cd D:/Dev/repos/overte-mcp && ./start.ps1",
        },
    }
    result: dict = {"companions": {}, "can_summon": False, "summon_note": ""}
    for name, meta in companions.items():
        ok, detail = await _probe(meta["url"])
        entry = {
            "reachable": ok,
            "url": meta["url"],
            "detail": detail,
            "repo": meta["repo"],
            "hint": meta["hint"],
        }
        if not ok:
            entry["action"] = (
                f"Action Required: the '{name}-mcp' companion server was not detected "
                f"({detail}). To enable it, install sandraschi/{name}-mcp: {meta['repo']}"
            )
        result["companions"][name] = entry
    resonite_ok = result["companions"].get("resonite", {}).get("reachable", False)
    result["can_summon"] = resonite_ok
    result["summon_note"] = (
        "Resonite summon is live."
        if resonite_ok
        else "Start resonite-mcp and link Resonite to enable summon."
    )
    return result


async def api_vr_status(request: Request) -> JSONResponse:
    """GET /api/vr/status - companion health for the /vr page."""
    try:
        return JSONResponse(await vr_status_payload())
    except Exception as e:  # belt-and-braces: status must never 500 the page
        log.warning("vr_status failed: %s", e)
        return JSONResponse(
            {"companions": {}, "can_summon": False, "error": str(e)},
            status_code=200,
        )


# --- Phase 2: Miko summon (Resonite) --------------------------------------

MIKO_SCRIPTS: dict[str, dict[str, str]] = {
    "classic": {
        "persona": "miko",
        "ja": "こんにちは！ミコです。一緒に日本語を練習しましょう！",
        "romaji": "Konnichiwa! Miko desu. Issho ni nihongo o renshuu shimashou!",
        "en": "Hello! I'm Miko. Let's practice Japanese together!",
    },
    "genki": {
        "persona": "miko-vr",
        "ja": "やっほー！ミコだよ！たのしく日本語をれんしゅうしよう！",
        "romaji": "Yahhoo! Miko da yo! Tanoshiku nihongo o renshuu shiyou!",
        "en": "Hiii! I'm Miko! Let's have fun practicing Japanese!",
    },
}


async def _companion_post(base_url: str, path: str, payload: dict) -> tuple[bool, str]:
    """POST to a companion backend. Returns (ok, detail). Never raises."""
    target = f"{base_url.rstrip('/')}{path}"
    try:
        async with httpx.AsyncClient(timeout=_PROBE_TIMEOUT_S) as client:
            resp = await client.post(target, json=payload)
            if resp.status_code < 400:
                try:
                    body = resp.json()
                    src = body.get("source", "")
                    src_note = f" source={src}" if src else ""
                except Exception:
                    src_note = ""
                return True, f"HTTP {resp.status_code}{src_note}"
            try:
                detail = resp.json().get("detail", resp.text[:160])
            except Exception:
                detail = resp.text[:160]
            return False, f"HTTP {resp.status_code}: {detail}"
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


async def _resonite_post(path: str, payload: dict) -> tuple[bool, str]:
    """POST to resonite-mcp backend. Returns (ok, detail). Never raises."""
    return await _companion_post(get_settings().resonite_mcp_url, path, payload)


def _chatbox_chunks(text: str, limit: int = 144) -> list[str]:
    """Split text into OSC chatbox-sized chunks on word boundaries."""
    words, chunks, cur = text.split(), [], ""
    for w in words:
        nxt = f"{cur} {w}".strip()
        if len(nxt) > limit and cur:
            chunks.append(cur)
            cur = w
        else:
            cur = nxt
    if cur:
        chunks.append(cur)
    return chunks


async def overte_domain_live() -> tuple[bool, str]:
    """True when the Overte domain-server answers :40100 via overte-mcp."""
    cfg = get_settings()
    target = f"{cfg.overte_mcp_url.rstrip('/')}/api/overte/status"
    try:
        async with httpx.AsyncClient(timeout=_PROBE_TIMEOUT_S) as client:
            resp = await client.get(target)
            if resp.status_code == 200:
                return True, "domain-server answered via overte-mcp"
            return False, f"HTTP {resp.status_code}"
    except Exception as e:
        return False, f"{type(e).__name__}: overte-mcp not detected"


async def overte_spawn_greeting(text: str) -> tuple[bool, str]:
    """Spawn a temporary Text entity with the greeting. Surfaces live/simulated."""
    cfg = get_settings()
    return await _companion_post(
        cfg.overte_mcp_url,
        "/api/overte/spawn",
        {
            "type": "Text",
            "name": "Miko greeting",
            "position": [0.0, 1.5, 0.0],
            "permanent": False,
            "extra_properties": {"text": text},
        },
    )


async def resonite_session_linked() -> tuple[bool, str]:
    """True when a Resonite client is linked (session endpoint answers)."""
    cfg = get_settings()
    target = f"{cfg.resonite_mcp_url.rstrip('/')}/api/resonite/session/status"
    try:
        async with httpx.AsyncClient(timeout=_PROBE_TIMEOUT_S) as client:
            resp = await client.get(target)
            if resp.status_code == 200:
                return True, "session endpoint answered"
            if resp.status_code == 503:
                return False, "resonite-mcp is up but no Resonite client is linked"
            return False, f"HTTP {resp.status_code}"
    except Exception as e:
        return False, f"{type(e).__name__}: resonite-mcp not detected"


async def vr_summon(
    platform: str = "resonite",
    variant: str = "genki",
    user_id: str = "",
) -> dict:
    """Summon Miko: greeting script + delivery receipts + audit turn.

    Live for platform="resonite" and "overte". vrchat returns a
    "lands in Phase 6" receipt instead of failing. Never raises.
    """
    from learnbot_mcp.compliance import disclosure_message
    from learnbot_mcp.database import get_db
    from learnbot_mcp.platforms import speech_say

    script = MIKO_SCRIPTS.get(variant, MIKO_SCRIPTS["genki"])
    persona_name = script["persona"]
    from learnbot_mcp.database import get_persona, upsert_persona

    persona = await get_persona(persona_name)
    if persona is None:
        # Joe-fresh install has zero personas - seed the summoned Miko so the
        # audit conversation (FK personas(name)) can be logged. Full backstory
        # stays editable via persona_create / Personas page.
        # Old DB files may predate the languages/skills migration - ensure it.
        async with get_db() as _db:
            for _col in ("languages", "skills"):
                try:
                    await _db.execute(f"ALTER TABLE personas ADD COLUMN {_col} TEXT DEFAULT '[]'")
                    await _db.commit()
                except Exception:
                    pass
        seed_backstory = (
            "Miko-chan, a calm and friendly Japanese tutor. Speaks polite desu/masu "
            "Japanese with romaji and English glosses. Continues the learner's active lesson."
            if variant == "classic"
            else "Miko-chan (genki VR variant): a bright, energetic Japanese tutor for "
            "first-timers in VR. Short simple sentences, furigana-first, lots of "
            "listening repetition and encouragement."
        )
        await upsert_persona(
            {
                "name": persona_name,
                "display_name": "Miko-chan" if variant == "classic" else "Miko-chan (genki)",
                "backstory": seed_backstory,
                "voice": "Leda",
                "avatar_vrm": "",
                "avatar_scale": 1.0,
                "platforms": ["resonite"],
                "constraints": [],
                "proactive_triggers": [],
                "knowledge_base": "",
                "languages": ["ja", "en"],
                "skills": [],
            }
        )
    persona = await get_persona(persona_name)
    receipts: list[dict] = []
    chunks: list[str] = []

    if platform == "overte":
        live, live_detail = await overte_domain_live()
        receipts.append({"step": "domain", "ok": live, "detail": live_detail})
        if live:
            ok, detail = await overte_spawn_greeting(f"{script['ja']} [{script['romaji']}]")
            receipts.append({"step": "greeting-sign", "ok": ok, "detail": detail})
        else:
            receipts.append(
                {
                    "step": "greeting-sign",
                    "ok": False,
                    "detail": "Skipped: start domain-server.exe, load overte-mcp-bridge.js in Interface, then retry.",
                }
            )
    elif platform == "vrchat":
        # Phase 6 (last): vrchat-mcp exposes chatbox via MCP manage_input
        # (OSC /chatbox/input), NOT via plain REST - learnbot cannot POST a
        # message itself. So summon = service probe + auth checklist +
        # 144-char chunks the user (or a future MCP client) delivers.
        up, up_detail = await _probe(get_settings().vrchat_mcp_url)
        receipts.append({"step": "service", "ok": up, "detail": up_detail})
        full = f"{script['ja']} [{script['romaji']}] {script['en']}"
        chunks = _chatbox_chunks(full)
        receipts.append(
            {
                "step": "auth-checklist",
                "ok": False,
                "detail": "In vrchat-mcp: log in (username + password + 2FA code), join a "
                "private/friends instance, then send the chunks below in order via "
                "manage_input chatbox. EAC needs Secure Boot + Memory Integrity "
                "(see ONBOARDING_VR Track B).",
            }
        )
        receipts.append(
            {
                "step": "chatbox-chunks",
                "ok": True,
                "detail": f"{len(chunks)} chunk(s), each <=144 chars.",
            }
        )
    else:
        linked, link_detail = await resonite_session_linked()
        receipts.append({"step": "session", "ok": linked, "detail": link_detail})
        if linked:
            from learnbot_mcp.config import get_settings as _get_cfg

            avatar_path = _get_cfg().miko_avatar_path.strip()
            if avatar_path:
                ok, detail = await _resonite_post(
                    "/api/resonite/avatar/load", {"avatar_path": avatar_path}
                )
                receipts.append({"step": "avatar", "ok": ok, "detail": detail})
            else:
                receipts.append(
                    {
                        "step": "avatar",
                        "ok": False,
                        "detail": "Skipped: set LEARNBOT_MIKO_AVATAR_PATH to Miko's Resonite inventory path "
                        "(import D:/Dev/repos/avatar-mcp/models/Nekomimi-chan.vrm to inventory once, "
                        "then use its inventory path). Web preview stays on the /vr page.",
                    }
                )
            ok, detail = await _resonite_post(
                "/api/resonite/avatar/set_parameter",
                {"parameter": "Happy", "value": 0.8},
            )
            receipts.append({"step": "expression", "ok": ok, "detail": detail})
        else:
            receipts.append(
                {
                    "step": "expression",
                    "ok": False,
                    "detail": "Skipped: enable ResoniteLink (Dashboard > Session > Settings), then retry.",
                }
            )

    # Spoken greeting on Joe's speakers - works even with no world linked.
    tts = await speech_say(text=script["ja"], voice="Leda", provider="gemini")
    receipts.append(
        {
            "step": "voice",
            "ok": bool(tts.get("success")),
            "detail": f"provider={tts.get('provider')} voice={tts.get('voice')}",
        }
    )

    # Audit turn on a dedicated summon conversation (platform=resonite/vrchat/overte).
    import uuid as _uuid
    from datetime import UTC as _UTC
    from datetime import datetime as _dt

    conv_id = str(_uuid.uuid4())[:12]
    stamp = _dt.now(_UTC).isoformat()
    display = persona["display_name"] if persona else persona_name
    greeting_line = f"{script['ja']} [{script['romaji']}] {script['en']}"
    try:
        async with get_db() as db:
            await db.execute(
                "INSERT INTO conversations (id, persona_name, platform, session_id, state, created_at, updated_at) VALUES (?,?,?,?,'active',?,?)",  # noqa: E501
                (conv_id, persona_name, platform, user_id, stamp, stamp),
            )
            await db.execute(
                "INSERT INTO turns (id, conversation_id, role, content, timestamp, platform, safety_verdict) VALUES (?,?,'assistant',?,?,?,?)",  # noqa: E501
                (_uuid.uuid4().hex[:12], conv_id, greeting_line[:10000], stamp, platform, "passed"),
            )
            await db.commit()
        turns_note = "audit turn logged"
    except Exception as e:
        log.warning("vr_summon audit failed: %s", e)
        turns_note = f"audit turn NOT logged: {e}"

    disclosure = disclosure_message()
    return {
        "success": True,
        "platform": platform,
        "persona": persona_name,
        "display_name": display,
        "persona_seeded": persona is not None,
        "greeting_ja": script["ja"],
        "greeting_romaji": script["romaji"],
        "greeting_en": script["en"],
        "receipts": receipts,
        "chunks": chunks,
        "conversation_id": conv_id,
        "audit": turns_note,
        "disclosure": disclosure,
    }


async def api_vr_summon(request: Request) -> JSONResponse:
    """POST /api/vr/summon {platform, variant, user_id} - summon Miko."""
    try:
        body = await request.json()
    except Exception:
        body = {}
    try:
        return JSONResponse(
            await vr_summon(
                platform=str(body.get("platform", "resonite")),
                variant=str(body.get("variant", "genki")),
                user_id=str(body.get("user_id", "")),
            )
        )
    except Exception as e:
        log.warning("vr_summon failed: %s", e)
        return JSONResponse({"success": False, "error": str(e)}, status_code=200)


# --- Phase 5: classroom loop + classroom world ----------------------------


async def _jlpt_question_by_id(question_id: int) -> dict | None:
    """Fetch one bundled JLPT question + options by id. Local only, never raises."""
    import aiosqlite

    from learnbot_mcp.games_integration import JLPT_DB_PATH

    if not JLPT_DB_PATH.exists():
        return None
    try:
        async with aiosqlite.connect(f"file:{JLPT_DB_PATH}?mode=ro", uri=True) as conn:
            conn.row_factory = aiosqlite.Row
            cur = await conn.execute(
                "SELECT id, level, question_type, question_text, correct_answer FROM questions WHERE id=?",
                (question_id,),
            )
            row = await cur.fetchone()
            if not row:
                return None
            opt_cur = await conn.execute(
                "SELECT option_letter, option_text, explanation FROM question_options WHERE question_id=?",
                (row["id"],),
            )
            opts = await opt_cur.fetchall()
            return {
                "id": row["id"],
                "level": row["level"],
                "type": row["question_type"],
                "question": row["question_text"],
                "correct": row["correct_answer"],
                "options": {o["option_letter"]: o["option_text"] for o in opts},
                "explanations": {o["option_letter"]: o["explanation"] for o in opts},
            }
    except Exception as e:
        log.warning("jlpt by-id failed: %s", e)
        return None


async def vr_lesson_step(
    user_id: str = "",
    level: str = "N5",
    answer: str = "",
    question_id: int = 0,
    speak: bool = True,
) -> dict:
    """One classroom loop step. No answer -> present next item (spoken by Miko).
    With answer + question_id -> grade it, explain, and present the next item.
    Fully local (bundled JLPT db + speech-mcp). Never raises.
    """
    from learnbot_mcp.games_integration import jlpt_quiz
    from learnbot_mcp.platforms import speech_say

    result: dict = {"success": True, "level": level, "graded": None}
    if answer and question_id:
        prev = await _jlpt_question_by_id(question_id)
        if prev is None:
            result["graded"] = {"ok": False, "detail": "Question not found - fetch a fresh item."}
        else:
            keys = list(prev["options"].keys())  # DB order = display order, never sort
            raw = (answer or "").strip()
            # Accept the shown key (katakana アイウエ) or 1-4 / A-D position.
            if len(raw) == 1 and ("A" <= raw.upper() <= "D" or "1" <= raw <= "4"):
                idx = (ord(raw.upper()) - ord("A")) if raw.upper() > "9" else (int(raw) - 1)
                given = keys[idx] if 0 <= idx < len(keys) else raw
            else:
                given = raw[:1]
            correct = (prev["correct"] or "").strip().upper()[:1]
            hit = given == correct and given != ""
            result["graded"] = {
                "ok": True,
                "correct": hit,
                "given": given,
                "expected": correct,
                "explanation": prev["explanations"].get(correct, ""),
                "say": "せいかい！すごい！" if hit else "おしい！つぎ、がんばろう！",
            }
            if speak:
                await speech_say(text=result["graded"]["say"], voice="Leda", provider="gemini")

    nxt = await jlpt_quiz(level=level, limit=1)
    questions = (nxt.get("questions") or []) if nxt.get("success") else []
    if not questions:
        result["success"] = False
        result["error"] = "No quiz items available (bundled JLPT db missing?)"
        return result
    q = questions[0]
    result["item"] = {
        "id": q["id"],
        "level": q["level"],
        "type": q["type"],
        "question": q["question"],
        "options": q["options"],
    }
    if speak:
        opts_spoken = " ".join(f"{k}. {v}" for k, v in q["options"].items())
        tts = await speech_say(
            text=f"{q['question']} {opts_spoken}", voice="Leda", provider="gemini"
        )
        result["spoken"] = {"ok": bool(tts.get("success")), "provider": tts.get("provider")}
    return result


async def api_vr_lesson_step(request: Request) -> JSONResponse:
    """POST /api/vr/lesson-step {user_id, level, answer, question_id} - classroom loop."""
    try:
        body = await request.json()
    except Exception:
        body = {}
    try:
        return JSONResponse(
            await vr_lesson_step(
                user_id=str(body.get("user_id", "")),
                level=str(body.get("level", "N5")),
                answer=str(body.get("answer", "")),
                question_id=int(body.get("question_id", 0) or 0),
            )
        )
    except Exception as e:
        log.warning("vr_lesson_step failed: %s", e)
        return JSONResponse({"success": False, "error": str(e)}, status_code=200)


async def vr_classroom_ensure() -> dict:
    """Spin up the persistent Miko classroom (Overte first, Resonite best-effort).

    Overte: permanent greeting-sign Text + Miko GLB Model on the domain
    (needs domain + bridge; otherwise honest down receipts).
    Resonite: session probe only - hosted classroom session stays manual
    until inventory is reliable. Never raises.
    """
    cfg = get_settings()
    receipts: list[dict] = []
    live, live_detail = await overte_domain_live()
    receipts.append({"step": "overte-domain", "ok": live, "detail": live_detail})
    if live:
        ok, detail = await _companion_post(
            cfg.overte_mcp_url,
            "/api/overte/spawn",
            {
                "type": "Text",
                "name": "Miko classroom sign",
                "position": [0.0, 2.0, -2.0],
                "permanent": True,
                "extra_properties": {
                    "text": "ミコのきょうしつへようこそ！ Miko's classroom - Nihongo practice here!"
                },
            },
        )
        receipts.append({"step": "classroom-sign", "ok": ok, "detail": detail})
        ok, detail = await _companion_post(
            cfg.overte_mcp_url,
            "/api/overte/spawn",
            {
                "type": "Model",
                "name": "Miko",
                "position": [1.5, 0.0, -2.0],
                "model_url": cfg.miko_glb_url,
                "permanent": True,
            },
        )
        receipts.append({"step": "classroom-miko", "ok": ok, "detail": detail})
    else:
        receipts.append(
            {
                "step": "classroom-sign",
                "ok": False,
                "detail": "Skipped: start your Overte domain + bridge first (ONBOARDING_VR Track C).",
            }
        )
    linked, link_detail = await resonite_session_linked()
    receipts.append(
        {
            "step": "resonite-classroom",
            "ok": linked,
            "detail": "Resonite linked - host the classroom session manually for now."
            if linked
            else f"Resonite classroom stays manual: {link_detail}",
        }
    )
    return {"success": True, "receipts": receipts}


async def api_vr_classroom_ensure(request: Request) -> JSONResponse:
    """POST /api/vr/classroom-ensure - spin up the persistent classroom."""
    try:
        return JSONResponse(await vr_classroom_ensure())
    except Exception as e:
        log.warning("vr_classroom_ensure failed: %s", e)
        return JSONResponse({"success": False, "error": str(e)}, status_code=200)
