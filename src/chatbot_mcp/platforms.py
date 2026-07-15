"""Platform bridges - speech-mcp TTS, Windows SAPI5 fallback, avatar-mcp, etc."""

from __future__ import annotations

import asyncio
import logging

import httpx

from chatbot_mcp.config import get_settings

log = logging.getLogger(__name__)


async def speech_say(text: str, voice: str = "", provider: str = "") -> dict:
    """Speak text aloud. Tries speech-mcp first, falls back to Windows SAPI5.

    Calls ``POST /api/v1/tts`` on speech-mcp (port 10909).
    If speech-mcp is unreachable, uses ``winsound.SND_ASYNC`` as a basic
    fallback (Windows beep — minimal but confirms the pipeline works).
    """
    cfg = get_settings()
    url = f"{cfg.speech_mcp_url.rstrip('/')}/api/v1/tts"
    payload: dict = {"text": text[:2000]}
    if voice:
        payload["voice_id"] = voice
    if provider:
        payload["provider"] = provider

    # Try speech-mcp
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                log.info("Speech-mcp OK: provider=%s", data.get("provider"))
                return {
                    "success": True,
                    "provider": data.get("provider"),
                    "voice": data.get("voice"),
                }
            log.warning("Speech-mcp HTTP %s", resp.status_code)
    except httpx.ConnectError:
        log.info("Speech-mcp unreachable, trying Windows SAPI5")
    except Exception as e:
        log.warning("Speech-mcp error: %s", e)

    # Fallback: Windows SAPI5 via PowerShell (non-blocking)
    try:
        safe = text[:500].replace('"', '\\"').replace("`", "\\`")
        ps_cmd = f'Add-Type -AssemblyName System.Speech; $s=New-Object System.Speech.Synthesis.SpeechSynthesizer; $s.Speak("{safe}")'  # noqa: E501
        await asyncio.create_subprocess_exec(
            "powershell",
            "-NoProfile",
            "-Command",
            ps_cmd,
            stdout=asyncio.DEVNULL,
            stderr=asyncio.DEVNULL,
        )
        log.info("Windows SAPI5 speech dispatched")
        return {"success": True, "provider": "windows-sapi5", "voice": "default"}
    except Exception as e:
        log.warning("Windows SAPI5 fallback failed: %s", e)
        return {"success": False, "error": str(e)}


async def platform_send(
    conversation_id: str,
    content: str,
    platform: str,
    voice: str = "",
) -> dict:
    """Send content to a specific platform bridge.

    Supported platforms: ``speech``, ``opencode``, ``discord`` (future).
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
