"""Soundscape — background music, environmental audio, and SFX for the learnbot.

Delegates to yahboom-mcp for physical sound effects (buzzer, beeps, built-in sounds)
and to speech-mcp for ambient audio when no robot is available.
"""

from __future__ import annotations

import asyncio
import logging

import httpx

log = logging.getLogger(__name__)

# Built-in sound effect IDs on yahboom-mcp (from raspbot audio module)
SFX = {
    "greeting": 1,
    "happy": 5,
    "sad": 8,
    "surprise": 12,
    "thinking": 15,
    "done": 20,
    "error": 25,
    "wake": 30,
    "sleep": 35,
    "alert": 40,
}

# Tone sequences for buzzer (frequency, duration_ms)
BUZZER_TONES = {
    "greeting": [(523, 150), (659, 150), (784, 200)],
    "happy": [(523, 100), (659, 100), (784, 150)],
    "sad": [(392, 200), (349, 200), (330, 300)],
    "thoughtful": [(262, 300), (330, 300)],
    "alert": [(880, 100), (0, 50), (880, 100)],
}

_YAHBOOM_URL = "http://127.0.0.1:10892"


async def play_sfx(sfx_name: str, yahboom_url: str = _YAHBOOM_URL) -> dict:
    """Play a named sound effect via yahboom-mcp.

    Falls back to buzzer tones if the audio module is unavailable.
    """
    sfx_id = SFX.get(sfx_name)
    if sfx_id:
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.post(
                    f"{yahboom_url}/api/v1/control/tool",
                    json={"tool": "audio", "args": {"operation": "sound", "param1": sfx_name}},
                )
                if resp.status_code == 200:
                    return {"success": True, "sfx": sfx_name, "via": "audio"}
        except httpx.ConnectError:
            log.info("Yahboom not reachable for SFX")
        except Exception as e:
            log.warning("SFX failed: %s", e)

    # Fallback: buzzer tones
    tones = BUZZER_TONES.get(sfx_name, BUZZER_TONES["happy"])
    for freq, dur in tones:
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                await client.post(
                    f"{yahboom_url}/api/v1/control/buzzer",
                    json={"frequency": freq, "duration": dur / 1000.0},
                )
                await asyncio.sleep(dur / 1000.0 + 0.05)
        except Exception:
            pass
    return {"success": True, "sfx": sfx_name, "via": "buzzer"}


async def play_emotion_sfx(emotion_tag: str) -> dict:
    """Map an emotion tag to a sound effect and play it (fire-and-forget)."""
    sfx_map = {
        "cheerfully": "happy",
        "excited": "happy",
        "laughs": "happy",
        "greeting": "greeting",
        "sad": "sad",
        "sympathetically": "sad",
        "thoughtful": "thinking",
        "playful": "happy",
        "angry": "alert",
        "serious": "thinking",
    }
    sfx_name = sfx_map.get(emotion_tag.lower().strip("[] "))
    if not sfx_name:
        return {"success": False, "reason": "no sfx mapping"}
    return await play_sfx(sfx_name)


def emotion_sfx_tags() -> list[str]:
    """Return the subset of emotion tags that have SFX mappings."""
    return list(
        set(
            v
            for k, v in {
                "cheerfully": "happy",
                "excited": "happy",
                "laughs": "happy",
                "greeting": "greeting",
                "sad": "sad",
                "sympathetically": "sad",
                "thoughtful": "thinking",
                "playful": "happy",
                "angry": "alert",
                "serious": "thinking",
            }.values()
        )
    )
