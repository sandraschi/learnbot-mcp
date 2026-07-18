"""Proactive chat - bot-initiated conversations based on scheduled triggers."""

from __future__ import annotations

import logging
import re
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

log = logging.getLogger(__name__)

# Track last-fired per trigger (in-memory, resets on restart)
_last_fired: dict[str, str] = {}


def _parse_cron_hour_min(cron: str) -> tuple[int, int] | None:
    """Parse HH:MM or cron-like '0 8 * * 1-5' into (hour, minute)."""
    m = re.match(r"(\d{1,2}):(\d{2})", cron)
    if m:
        return int(m.group(1)), int(m.group(2))
    parts = cron.strip().split()
    if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
        return int(parts[1]), int(parts[0])
    return None


def _parse_interval(cron: str) -> timedelta | None:
    """Parse interval strings like '15m', '2h', '3600' into timedelta."""
    m = re.match(r"(\d+)\s*(m|min|h|hr)?$", cron.strip().lower())
    if not m:
        return None
    val = int(m.group(1))
    unit = m.group(2) or ""
    if unit in ("h", "hr"):
        return timedelta(hours=val)
    return timedelta(minutes=val)


def _should_fire(cron: str, trigger_key: str) -> bool:
    """Check if a cron/interval trigger should fire now.

    Returns True if the trigger is due and hasn't fired in its window.
    """
    now = datetime.now(UTC)
    last = _last_fired.get(trigger_key)

    # Try interval first (e.g. '15m', '2h')
    interval = _parse_interval(cron)
    if interval:
        if last:
            last_dt = datetime.fromisoformat(last)
            if now - last_dt < interval:
                return False
        _last_fired[trigger_key] = now.isoformat()
        return True

    # Try cron-like (e.g. '0 8 * * 1-5')
    hm = _parse_cron_hour_min(cron)
    if hm:
        target_hour, target_min = hm
        if now.hour != target_hour or now.minute != target_min:
            return False
        today_key = f"{trigger_key}_{now.strftime('%Y%m%d')}"
        if _last_fired.get(today_key):
            return False
        _last_fired[today_key] = now.isoformat()
        # Check day-of-week: '1-5' means Mon-Fri
        parts = cron.strip().split()
        if len(parts) >= 5 and parts[4] != "*":
            try:
                allowed_days = _parse_dow(parts[4])
                if now.weekday() not in allowed_days:
                    return False
            except (ValueError, IndexError):
                pass
        return True

    return False


def _parse_dow(dow_expr: str) -> list[int]:
    """Parse day-of-week expression like '1-5' or '1,3,5' into list of ints (0=Mon)."""
    result: list[int] = []
    for part in dow_expr.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-", 1)
            result.extend(range(int(a), int(b) + 1))
        else:
            result.append(int(part))
    return result


async def proactive_tick() -> dict[str, Any]:
    """Check all personas for due proactive triggers and fire them.

    Call this periodically (e.g. every 5 minutes via Fritz cron or Windows Task Scheduler).

    Returns summary of triggered conversations.
    """
    from learnbot_mcp.database import get_db, get_persona

    triggered: list[dict[str, Any]] = []

    async with get_db() as db:
        cur = await db.execute(
            "SELECT name, proactive_triggers FROM personas WHERE proactive_triggers IS NOT NULL AND proactive_triggers != '[]'"  # noqa: E501
        )
        personas = await cur.fetchall()

    for row in personas:
        name = row["name"]
        triggers_raw = row["proactive_triggers"]
        triggers = triggers_raw
        if isinstance(triggers_raw, str):
            import json

            try:
                triggers = json.loads(triggers_raw)
            except json.JSONDecodeError:
                triggers = []

        for trigger in triggers:
            if isinstance(trigger, str):
                cron = trigger
                prompt = ""
            elif isinstance(trigger, dict):
                cron = trigger.get("schedule", "")
                prompt = trigger.get("prompt", "")
            else:
                continue

            if not cron:
                continue
            trigger_key = f"{name}:{cron}:{prompt[:50]}"

            if not _should_fire(cron, trigger_key):
                continue

            # Fire the trigger: create conversation and send the prompt
            persona = await get_persona(name)
            if not persona:
                log.warning("Proactive trigger: persona '%s' not found", name)
                continue

            conv_id = str(uuid.uuid4())[:12]
            stamp = datetime.now(UTC).isoformat()
            async with get_db() as db_conv:
                await db_conv.execute(
                    "INSERT INTO conversations (id, persona_name, platform, state, created_at, updated_at) VALUES (?,?,'proactive','active',?,?)",  # noqa: E501
                    (conv_id, name, stamp, stamp),
                )
                await db_conv.commit()

            resolved_prompt = prompt
            if "{time_of_day}" in prompt:
                resolved_prompt = prompt.replace(
                    "{time_of_day}",
                    "morning" if datetime.now(UTC).hour < 12 else "afternoon",
                )
            if "{overdue_count}" in resolved_prompt:
                from learnbot_mcp.learn_tools import ensure_vocab_table

                await ensure_vocab_table()
                async with get_db() as db_voc:
                    cur = await db_voc.execute(
                        "SELECT COUNT(*) AS cnt FROM vocab_items WHERE due_at <= datetime('now')"
                    )
                    row = await cur.fetchone()
                    count = row["cnt"] if row else 0
                resolved_prompt = resolved_prompt.replace("{overdue_count}", str(count))

            from learnbot_mcp.server import chat_send

            try:
                result = await chat_send.__wrapped__(
                    conversation_id=conv_id, content=resolved_prompt, user_id="system"
                )
                triggered.append(
                    {
                        "persona": name,
                        "conversation_id": conv_id,
                        "prompt": resolved_prompt[:100],
                        "response_preview": (result.get("response") or "")[:100],
                    }
                )
                log.info(
                    "Proactive: %s -> conv=%s (%s)",
                    name,
                    conv_id,
                    resolved_prompt[:80],
                )
            except Exception as e:
                log.warning("Proactive trigger failed for %s: %s", name, e)

    return {"success": True, "triggered": triggered, "count": len(triggered)}
