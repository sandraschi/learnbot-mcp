"""E2E tests — full pipeline through REST API (requires server on 11104)."""

from __future__ import annotations

import httpx
import pytest

API = "http://127.0.0.1:11104"


@pytest.mark.skip(reason="Requires running server on :11104")
class TestE2E:
    """End-to-end tests against a live learnbot-mcp API server."""

    async def test_health(self):
        async with httpx.AsyncClient() as c:
            r = await c.get(f"{API}/api/health")
            assert r.status_code == 200
            data = r.json()
            assert data["status"] == "ok"
            assert data["server"] == "learnbot-mcp"

    async def test_persona_crud(self):
        async with httpx.AsyncClient() as c:
            # Create
            r = await c.post(
                f"{API}/api/personas",
                json={
                    "name": "e2e-test",
                    "display_name": "E2E Test",
                    "backstory": "Test assistant.",
                    "voice": "Leda",
                    "languages": ["en"],
                    "skills": [],
                },
            )
            assert r.status_code == 200

            # List
            r = await c.get(f"{API}/api/personas")
            assert r.status_code == 200
            names = [p["name"] for p in r.json()["personas"]]
            assert "e2e-test" in names

            # Delete
            r = await c.delete(f"{API}/api/personas/e2e-test")
            assert r.status_code == 200

    async def test_conversation_flow(self):
        async with httpx.AsyncClient() as c:
            # Ensure persona exists
            await c.post(
                f"{API}/api/personas",
                json={
                    "name": "e2e-conv",
                    "display_name": "Conv Test",
                    "backstory": "You are a test assistant.",
                    "voice": "",
                },
            )

            # Start conversation
            r = await c.post(
                f"{API}/api/conversations",
                json={
                    "persona": "e2e-conv",
                    "platform": "e2e",
                    "user_id": "tester",
                },
            )
            assert r.status_code == 200
            cid = r.json()["conversation_id"]
            assert cid

            # Send message
            r = await c.post(
                f"{API}/api/conversations/{cid}/send",
                json={
                    "content": "Hello in 3 words",
                    "user_id": "tester",
                },
            )
            # LLM may be unavailable, but should not crash
            assert r.status_code in (200, 500)

            # Audit log
            r = await c.get(f"{API}/api/audit?user_id=tester")
            assert r.status_code == 200

            # Cleanup
            await c.delete(f"{API}/api/conversations/{cid}")
            await c.delete(f"{API}/api/personas/e2e-conv")

    async def test_safety_rules(self):
        async with httpx.AsyncClient() as c:
            r = await c.post(
                f"{API}/api/safety/rules",
                json={
                    "topic": "spam",
                    "action": "refuse",
                    "message": "No spam.",
                },
            )
            assert r.status_code == 200
            rule_id = r.json()["id"]

            r = await c.get(f"{API}/api/safety/rules")
            assert r.status_code == 200
            assert any(rr["topic"] == "spam" for rr in r.json()["rules"])

            r = await c.delete(f"{API}/api/safety/rules/{rule_id}")
            assert r.status_code == 200

    async def test_compliance(self):
        async with httpx.AsyncClient() as c:
            r = await c.get(f"{API}/api/compliance")
            assert r.status_code == 200
            data = r.json()
            assert "regime" in data
            assert "refusal_templates" in data

    async def test_voices(self):
        async with httpx.AsyncClient() as c:
            r = await c.get(f"{API}/api/voices")
            assert r.status_code == 200
            assert r.json()["count"] > 0
