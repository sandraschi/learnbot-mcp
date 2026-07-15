"""Platform bridges - speech-mcp TTS, avatar-mcp, resonite-mcp, etc."""

from __future__ import annotations

import logging

import httpx

from chatbot_mcp.config import get_settings

log = logging.getLogger(__name__)


async def speech_say(text: str, voice: str = "", provider: str = "") -> dict:
    """Send text to speech-mcp for TTS synthesis + playback.

    Calls ``POST /api/v1/tts`` on the configured speech-mcp backend.
    Returns success/failure; does NOT raise on connection error.
    """
    cfg = get_settings()
    url = f"{cfg.speech_mcp_url.rstrip('/')}/api/v1/tts"
    payload = {"text": text[:2000]}
    if voice:
        payload["voice_id"] = voice
    if provider:
        payload["provider"] = provider

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                log.info("Speech OK: provider=%s voice=%s", data.get("provider"), data.get("voice"))
                return {
                    "success": True,
                    "provider": data.get("provider"),
                    "voice": data.get("voice"),
                }
            log.warning("Speech returned HTTP %s: %s", resp.status_code, resp.text[:200])
            return {"success": False, "error": f"HTTP {resp.status_code}"}
    except httpx.ConnectError:
        log.info("Speech-mcp not reachable on %s", cfg.speech_mcp_url)
        return {"success": False, "error": "speech-mcp not reachable"}
    except Exception as e:
        log.warning("Speech call failed: %s", e)
        return {"success": False, "error": str(e)}


async def platform_send(
    conversation_id: str,
    content: str,
    platform: str,
    voice: str = "",
) -> dict:
    """Send content to a specific platform bridge.

    Supported platforms: ``speech``, ``opencode`` (log only), ``discord`` (future).
    """
    if platform == "speech":
        return await speech_say(text=content, voice=voice)
    if platform == "opencode":
        return {
            "success": True,
            "platform": "opencode",
            "message": "Delivered via opencode context",
        }
    if platform in ("discord", "resonite", "avatar"):
        return {
            "success": False,
            "platform": platform,
            "error": f"{platform} bridge not implemented",
        }
    return {"success": False, "error": f"Unknown platform: {platform}"}
