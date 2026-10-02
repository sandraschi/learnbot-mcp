"""VR companion status + Miko summon - Phase 2 (Resonite live, VRChat/Overte Phase 4).

Thin orchestration for the /vr launchpad page. All companions are
optional: every probe degrades to a dialogic hint, never an exception.
Single implementation shared by REST (GET /api/vr/status, POST /api/vr/summon)
and MCP (vr_status, vr_summon tools in server.py).

Phase 2 summon (Resonite): session probe -> Happy expression best-effort ->
spoken JP greeting via speech-mcp -> audit turn. Avatar VRM loading lands in
Phase 3 (needs Miko's Resonite inventory path); VRChat/Overte in Phase 4.
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


async def _resonite_post(path: str, payload: dict) -> tuple[bool, str]:
    """POST to resonite-mcp backend. Returns (ok, detail). Never raises."""
    cfg = get_settings()
    target = f"{cfg.resonite_mcp_url.rstrip('/')}{path}"
    try:
        async with httpx.AsyncClient(timeout=_PROBE_TIMEOUT_S) as client:
            resp = await client.post(target, json=payload)
            if resp.status_code < 400:
                return True, f"HTTP {resp.status_code}"
            try:
                detail = resp.json().get("detail", resp.text[:160])
            except Exception:
                detail = resp.text[:160]
            return False, f"HTTP {resp.status_code}: {detail}"
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


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

    Phase 2 supports platform="resonite". vrchat/overte return a
    "lands in Phase 4" receipt instead of failing. Never raises.
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

    if platform != "resonite":
        receipts.append(
            {
                "step": platform,
                "ok": False,
                "detail": f"{platform} summon lands in Phase 4 - Resonite only for now.",
            }
        )
    else:
        linked, link_detail = await resonite_session_linked()
        receipts.append({"step": "session", "ok": linked, "detail": link_detail})
        if linked:
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
