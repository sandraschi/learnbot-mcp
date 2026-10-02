"""VR companion status - Phase 1 page shell (Resonite / VRChat / Overte).

Thin health aggregation for the /vr launchpad page. All companions are
optional: every probe degrades to a dialogic hint, never an exception.
Single implementation shared by REST (GET /api/vr/status) and the future
vr_status / vr_summon MCP tools (Phase 2+).
"""

from __future__ import annotations

import logging

import httpx
from starlette.requests import Request
from starlette.responses import JSONResponse

from learnbot_mcp.config import get_settings

log = logging.getLogger(__name__)

# Short timeout: status probes must never stall page load.
_PROBE_TIMEOUT_S = 2.5


async def _probe(url: str) -> tuple[bool, str]:
    """GET <url>/health with a short timeout. Returns (reachable, detail)."""
    target = f"{url.rstrip('/')}/health"
    try:
        async with httpx.AsyncClient(timeout=_PROBE_TIMEOUT_S) as client:
            resp = await client.get(target)
            if resp.status_code < 500:
                return True, f"HTTP {resp.status_code}"
            return False, f"HTTP {resp.status_code}"
    except Exception as e:  # ConnectError, Timeout, DNS - all mean "not running"
        return False, f"{type(e).__name__}"


async def vr_status_payload() -> dict:
    """Aggregate companion status for the /vr page. Never raises."""
    cfg = get_settings()
    companions = {
        "resonite": {
            "url": cfg.resonite_mcp_url,
            "repo": "https://github.com/sandraschi/resonite-mcp",
            "hint": "Start resonite-mcp: cd D:/Dev/repos/resonite-mcp && just serve",
        },
        "vrchat": {
            "url": cfg.vrchat_mcp_url,
            "repo": "https://github.com/sandraschi/vrchat-mcp",
            "hint": "Start vrchat-mcp: cd D:/Dev/repos/vrchat-mcp && just serve",
        },
        "overte": {
            "url": cfg.overte_mcp_url,
            "repo": "https://github.com/sandraschi/overte-mcp",
            "hint": "Start overte-mcp: cd D:/Dev/repos/overte-mcp && ./start.ps1",
        },
    }
    result: dict = {"companions": {}, "can_summon": False, "summon_note": ""}
    for name, meta in companions.items():
        ok, detail = await _probe(meta["url"])
        entry = {
            "reachable": ok,
            "url": meta["url"],
            "detail": detail,
            "repo": meta["repo"],
            "hint": meta["hint"],
        }
        if not ok:
            entry["action"] = (
                f"Action Required: the '{name}-mcp' companion server was not detected "
                f"({detail}). To enable it, install sandraschi/{name}-mcp: {meta['repo']}"
            )
        result["companions"][name] = entry
    result["can_summon"] = False  # Phase 2 wires platform_send; page shell only
    result["summon_note"] = "Summon Miko lands in Phase 2 - this page reports status only."
    return result


async def api_vr_status(request: Request) -> JSONResponse:
    """GET /api/vr/status - companion health for the /vr page."""
    try:
        return JSONResponse(await vr_status_payload())
    except Exception as e:  # belt-and-braces: status must never 500 the page
        log.warning("vr_status failed: %s", e)
        return JSONResponse(
            {"companions": {}, "can_summon": False, "error": str(e)},
            status_code=200,
        )
