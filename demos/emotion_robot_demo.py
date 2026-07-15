"""
Emotion + Robot Demo — tests emotion tag extraction, robot orchestrator mapping,
and the full emotion→TTS→robot chain without hardware.

Run: uv run python demos/emotion_robot_demo.py
"""

import asyncio
import re


EMOTION_TAGS = [
    "cheerfully",
    "excited",
    "laughs",
    "greeting",
    "sad",
    "thoughtful",
    "sympathetically",
    "playful",
    "angry",
    "serious",
    "softly",
]

TAG_PATTERN = r"\[(laughs|whispers|sighs|excited|sad|happy|cheerfully|softly|sympathetically|warmly|gently|dramatically|nervously|sarcastically|angry|serious|thoughtful|playful|warm|cold|formal|casual)\]"


async def main():
    from learnbot_mcp.robot_orchestrator import _EMOTION_MOTIONS, execute_emotion

    print("=== Emotion + Robot Demo ===\n")

    # 1. Verify all emotion tags have robot sequences
    print("Emotion → Robot mappings:")
    for tag in EMOTION_TAGS:
        seq = _EMOTION_MOTIONS.get(tag, [])
        action_count = len(seq)
        action_desc = ", ".join(s["args"]["operation"] for s in seq[:3])
        if len(seq) > 3:
            action_desc += f" +{len(seq)-3} more"
        print(f"  [{tag}] {action_count} actions: {action_desc}")

    # 2. Test tag extraction from sample LLM responses
    sample_responses = [
        "[cheerfully] Good morning! Ready to learn some Japanese?",
        "[sympathetically] I understand, grammar can be difficult. Let's practice together.",
        "[excited] You got 100% on the quiz! Amazing!",
        "[laughs] That pun was terrible! But I love it.",
        "[greeting] Welcome back! I was hoping you'd visit today.",
        "Short answer without a tag.",  # no tag — should not crash
    ]

    print("\nTag extraction from responses:")
    for resp in sample_responses:
        tags = re.findall(TAG_PATTERN, resp)
        display = re.sub(TAG_PATTERN, "", resp).strip()
        has_tag = tags[0] if tags else "(none)"
        print(f"  Tag: [{has_tag}] -> \"{display[:60]}\"")

    # 3. Test execute_emotion (will log "not reachable" since yahboom is likely offline)
    print("\nRobot execute_emotion (offline — should log, not crash):")
    for tag in ["cheerfully", "angry", "nonexistent"]:
        result = await execute_emotion(emotion_tag=tag)
        print(f"  [{tag}] success={result['success']}, actions={result.get('actions', 0)}")

    print("\n=== Emotion + Robot Demo Complete ===")


if __name__ == "__main__":
    asyncio.run(main())
