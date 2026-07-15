"""Safety guardrails - topic rules, rate limiting, content filtering."""

from __future__ import annotations

import logging
import re
import time
from collections import defaultdict
from typing import Any

from learnbot_mcp.config import get_settings

log = logging.getLogger(__name__)

_rate_limit_buckets: dict[str, list[float]] = defaultdict(list)


def _rate_limit(user_id: str) -> bool:
    cfg = get_settings()
    now = time.time()
    window = 60.0
    bucket = _rate_limit_buckets[user_id]
    bucket[:] = [t for t in bucket if t > now - window]
    if len(bucket) >= cfg.safety_rate_limit_per_minute:
        return False
    bucket.append(now)
    return True


async def check_safety(content: str, user_id: str) -> dict[str, Any]:
    """Run all safety checks on a message. Returns verdict."""
    get_settings()

    if not _rate_limit(user_id):
        return {
            "passed": False,
            "action": "rate_limited",
            "reason": "Rate limit exceeded",
            "user_id": user_id,
        }

    from learnbot_mcp.database import get_db

    async with get_db() as db:
        cur = await db.execute("SELECT topic, action, message FROM safety_rules WHERE enabled=1")
        rules = await cur.fetchall()

    topic_check = _check_topics(content, rules)
    if topic_check["blocked"]:
        log.info("Safety blocked: topic=%s user=%s", topic_check.get("topic"), user_id)
        return {
            "passed": False,
            "action": topic_check["action"],
            "topic": topic_check.get("topic"),
            "reason": topic_check.get("message", "Content blocked by safety rule"),
            "user_id": user_id,
        }

    pii_check = _check_pii_redaction(content)
    if pii_check["redacted"]:
        log.info("Safety redacted PII for user=%s", user_id)

    return {
        "passed": True,
        "action": "allow",
        "redacted_content": pii_check.get("content"),
        "user_id": user_id,
    }


def _check_topics(content: str, rules) -> dict[str, Any]:
    """Check content against configured topic rules."""
    content_lower = content.lower()
    for rule in rules:
        topic = rule["topic"].lower()
        if topic in content_lower:
            action = rule["action"]
            message = rule.get("message") or f"I cannot discuss {rule['topic']}."
            return {"blocked": True, "action": action, "topic": rule["topic"], "message": message}
    return {"blocked": False}


_PII_PATTERNS: list[tuple[str, str]] = [
    (r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b", "credit_card"),
    (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", "email"),
    (r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b", "phone"),
]


def _check_pii_redaction(content: str) -> dict[str, Any]:
    """Redact common PII patterns from content."""
    redacted = False
    result = content
    for pattern, pii_type in _PII_PATTERNS:
        if re.search(pattern, result):
            result = re.sub(pattern, f"[REDACTED {pii_type}]", result)
            redacted = True
    return {"redacted": redacted, "content": result if redacted else content}
