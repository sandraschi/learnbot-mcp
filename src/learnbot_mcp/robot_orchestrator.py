"""Robot orchestration — maps emotion tags to Boomy/Bumi physical actions."""

from __future__ import annotations

import asyncio
import logging

import httpx

log = logging.getLogger(__name__)

# Emotion tag → robot action sequences
_EMOTION_MOTIONS: dict[str, list[dict]] = {
    "cheerfully": [
        {"tool": "yahboom_tool", "args": {"operation": "forward", "param1": 0.15}, "duration": 0.8},
        {
            "tool": "yahboom_tool",
            "args": {"operation": "backward", "param1": 0.15},
            "duration": 0.8,
        },
        {
            "tool": "yahboom_tool",
            "args": {"operation": "led", "param1": 0, "param2": 255, "param3": 0},
        },
        {"tool": "yahboom_tool", "args": {"operation": "light_effect", "param1": "rainbow"}},
    ],
    "excited": [
        {
            "tool": "yahboom_tool",
            "args": {"operation": "turn_left", "param1": 0.6},
            "duration": 0.5,
        },
        {
            "tool": "yahboom_tool",
            "args": {"operation": "turn_right", "param1": 0.6},
            "duration": 0.5,
        },
        {"tool": "yahboom_tool", "args": {"operation": "light_effect", "param1": "rainbow"}},
    ],
    "laughs": [
        {"tool": "yahboom_tool", "args": {"operation": "forward", "param1": 0.1}, "duration": 0.3},
        {"tool": "yahboom_tool", "args": {"operation": "backward", "param1": 0.1}, "duration": 0.3},
        {"tool": "yahboom_tool", "args": {"operation": "light_effect", "param1": "breathe"}},
    ],
    "greeting": [
        {"tool": "yahboom_tool", "args": {"operation": "forward", "param1": 0.2}, "duration": 1.0},
        {
            "tool": "yahboom_tool",
            "args": {"operation": "camera_move", "param1": "up", "param2": 10},
        },
        {
            "tool": "yahboom_tool",
            "args": {"operation": "camera_move", "param1": "down", "param2": 10},
        },
        {
            "tool": "yahboom_tool",
            "args": {"operation": "led", "param1": 255, "param2": 200, "param3": 0},
        },
    ],
    "sad": [
        {"tool": "yahboom_tool", "args": {"operation": "forward", "param1": 0.05}, "duration": 0.5},
        {
            "tool": "yahboom_tool",
            "args": {"operation": "led", "param1": 50, "param2": 50, "param3": 255},
        },
    ],
    "thoughtful": [
        {
            "tool": "yahboom_tool",
            "args": {"operation": "camera_move", "param1": "up", "param2": 20},
        },
        {
            "tool": "yahboom_tool",
            "args": {"operation": "led", "param1": 255, "param2": 255, "param3": 255},
        },
    ],
    "sympathetically": [
        {"tool": "yahboom_tool", "args": {"operation": "forward", "param1": 0.08}, "duration": 0.6},
        {
            "tool": "yahboom_tool",
            "args": {"operation": "led", "param1": 255, "param2": 180, "param3": 100},
        },
    ],
    "playful": [
        {
            "tool": "yahboom_tool",
            "args": {"operation": "strafe_left", "param1": 0.15},
            "duration": 0.4,
        },
        {
            "tool": "yahboom_tool",
            "args": {"operation": "strafe_right", "param1": 0.15},
            "duration": 0.4,
        },
        {"tool": "yahboom_tool", "args": {"operation": "light_effect", "param1": "breathe"}},
    ],
    "angry": [
        {"tool": "yahboom_tool", "args": {"operation": "forward", "param1": 0.3}, "duration": 0.3},
        {"tool": "yahboom_tool", "args": {"operation": "backward", "param1": 0.3}, "duration": 0.3},
        {
            "tool": "yahboom_tool",
            "args": {"operation": "led", "param1": 255, "param2": 0, "param3": 0},
        },
    ],
    "serious": [
        {
            "tool": "yahboom_tool",
            "args": {"operation": "led", "param1": 100, "param2": 100, "param3": 255},
        },
    ],
    "softly": [
        {"tool": "yahboom_tool", "args": {"operation": "forward", "param1": 0.05}, "duration": 0.5},
        {
            "tool": "yahboom_tool",
            "args": {"operation": "led", "param1": 200, "param2": 200, "param3": 255},
        },
    ],
}

_DEFAULT_EMOTION = "cheerfully"

# Duration to wait between actions in a sequence (seconds)
_ACTION_GAP = 0.3


async def execute_emotion(emotion_tag: str, yahboom_url: str = "http://127.0.0.1:10892") -> dict:
    """Execute a robot motion sequence matching an emotion tag.

    Fires the action sequence asynchronously (non-blocking). Returns immediately
    with the planned sequence; the robot executes in background.
    """
    tag = emotion_tag.lower().strip("[] ")
    sequence = _EMOTION_MOTIONS.get(tag, _EMOTION_MOTIONS.get(_DEFAULT_EMOTION, []))
    if not sequence:
        return {"success": True, "emotion": tag, "actions": 0}

    async def _run():
        async with httpx.AsyncClient(timeout=3.0) as client:
            for step in sequence:
                try:
                    await client.post(
                        f"{yahboom_url}/api/v1/control/tool",
                        json=step,
                    )
                except httpx.ConnectError:
                    log.info("Yahboom not reachable on %s", yahboom_url)
                    return
                except Exception as e:
                    log.warning("Yahboom action failed: %s", e)
                dur = step.get("duration", 0)
                if dur > 0:
                    await asyncio.sleep(dur + _ACTION_GAP)

    asyncio.create_task(_run())
    return {"success": True, "emotion": tag, "actions": len(sequence)}


async def robot_stop_all(yahboom_url: str = "http://127.0.0.1:10892") -> dict:
    """Emergency stop — halt all robot motion."""
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            await client.post(f"{yahboom_url}/api/v1/stop_all")
            await client.post(
                f"{yahboom_url}/api/v1/control/tool",
                json={
                    "tool": "yahboom_tool",
                    "args": {"operation": "stop_all"},
                },
            )
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


# Canonical tag list — all tags the LLM may emit (TTS-only tags have no robot mapping)
_EXTRA_TTS_TAGS = [
    "whispers",
    "sighs",
    "happy",
    "warmly",
    "gently",
    "dramatically",
    "nervously",
    "sarcastically",
    "warm",
    "cold",
    "formal",
    "casual",
]
EMOTION_TAGS = list(_EMOTION_MOTIONS.keys()) + _EXTRA_TTS_TAGS

# Single regex for all tag extraction — import and reuse, don't duplicate
TAG_PATTERN = r"\[(" + "|".join(EMOTION_TAGS) + r")\]"
