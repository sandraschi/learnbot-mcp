"""Platform bridges - speech-mcp TTS (default Gemini, fallback Windows SAPI5)."""

from __future__ import annotations

import asyncio
import logging

import httpx

from chatbot_mcp.config import get_settings

log = logging.getLogger(__name__)


async def _call_speech_mcp(payload: dict) -> dict:
    """Call speech-mcp's POST /api/v1/tts. Returns response dict or None on failure."""
    cfg = get_settings()
    url = f"{cfg.speech_mcp_url.rstrip('/')}/api/v1/tts"
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
            return None
    except httpx.ConnectError:
        log.info("Speech-mcp unreachable")
        return None
    except Exception as e:
        log.warning("Speech-mcp error: %s", e)
        return None


async def _sapi5_fallback(text: str) -> dict:
    """Windows SAPI5 via PowerShell — last resort when speech-mcp is down."""
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
        log.info("Windows SAPI5 dispatched")
        return {"success": True, "provider": "windows-sapi5", "voice": "default"}
    except Exception as e:
        log.warning("SAPI5 failed: %s", e)
        return {"success": False, "error": str(e)}


async def speech_say(text: str, voice: str = "Leda", provider: str = "gemini") -> dict:
    """Speak text aloud. Tries Gemini via speech-mcp, falls back to Windows SAPI5.

    Speech-mcp provider chain: gemini → windows (if gemini key missing) → SAPI5 (if speech-mcp down).
    """  # noqa: E501
    payload: dict = {"text": text[:2000], "voice_id": voice, "provider": provider}

    # Try 1: Gemini via speech-mcp
    result = await _call_speech_mcp(payload)
    if result:
        return result

    # Try 2: Windows via speech-mcp (Gemini key missing or provider errored)
    if provider != "windows":
        log.info("Falling back to speech-mcp with provider=windows")
        payload["provider"] = "windows"
        result = await _call_speech_mcp(payload)
        if result:
            return result

    # Try 3: Windows SAPI5 (speech-mcp entirely unreachable)
    return await _sapi5_fallback(text)


async def platform_send(
    conversation_id: str,
    content: str,
    platform: str,
    voice: str = "",
) -> dict:
    """Send content to a specific platform bridge."""
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
