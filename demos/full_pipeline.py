"""
Full Pipeline Demo — creates a persona, starts a conversation, sends messages,
demonstrates safety, compliance, emotion tags, and TTS.

Run: uv run python demos/full_pipeline.py
"""

import asyncio
import json


async def main():
    from learnbot_mcp.database import init_db, upsert_persona, get_persona, list_personas, get_db

    await init_db()
    print("=== Pipeline Demo ===\n")

    # 1. Create a demo persona
    await upsert_persona({
        "name": "demo-sensei",
        "display_name": "Demo Sensei",
        "backstory": "You are a patient Japanese language teacher. You speak both Japanese and English. When the user writes in Japanese, respond in Japanese.",
        "voice": "Callirrhoe",
        "languages": ["ja", "en"],
        "skills": ["vocab_quiz", "grammar_check"],
        "platforms": ["demo"],
    })
    p = await get_persona("demo-sensei")
    assert p is not None
    print(f"Persona: {p['display_name']} (voice={p['voice']}, languages={p['languages']})")

    # 2. Start a conversation
    import uuid
    from datetime import UTC, datetime

    conv_id = str(uuid.uuid4())[:12]
    stamp = datetime.now(UTC).isoformat()
    async with get_db() as db:
        await db.execute(
            "INSERT INTO conversations (id, persona_name, platform, state, created_at, updated_at) VALUES (?,?,'demo','active',?,?)",
            (conv_id, "demo-sensei", stamp, stamp),
        )
        await db.commit()
    print(f"Conversation: {conv_id}")

    # 3. Send messages through the full safety + LLM pipeline
    from learnbot_mcp.server import chat_send

    messages = [
        ("user", "Hello sensei!"),
        ("user", "今日はどんな天気ですか？"),
    ]

    for role, content in messages:
        print(f"\n[{role}] {content}")
        result = await chat_send.__wrapped__(
            conversation_id=conv_id,
            content=content,
            user_id="demo-user",
        )
        print(f"[assistant] {result.get('response', '')[:200]}")
        print(f"[safety] {result.get('safety_verdict', '?')}")

    # 4. Check audit log
    from learnbot_mcp.database import get_db as _db2

    async with _db2() as db:
        cur = await db.execute(
            "SELECT role, content, safety_verdict FROM turns WHERE conversation_id=? ORDER BY timestamp ASC",
            (conv_id,),
        )
        turns = await cur.fetchall()
    print(f"\nAudit log: {len(turns)} turns")
    for t in turns:
        print(f"  [{t['role']}] verdict={t['safety_verdict']}")

    # 5. List personas
    all_p = await list_personas()
    print(f"\nTotal personas: {len(all_p)}")

    print("\n=== Pipeline Demo Complete ===")


if __name__ == "__main__":
    asyncio.run(main())
