# webapp_ops pilot draft - learnbot-mcp

Status: DRAFT 2026-10-15. Pilot scope only, not a fleet standard yet.
Question it answers: can the MCP server drive its own webapp from an authoritative map instead of OCR-scraping the sidebar?

## Why this pilot repo

- `learnbot-mcp` is the fleet reference impl for `cua-webapp-test` (9/9 pass).
- Real map available: 14 routes in `webapp/src/main.tsx`, nav labels in `Layout.tsx`, `page_testid` on every page (verified 2026-10-15 via grep).
- Gap found by pilot: sidebar `NavLink`s have NO `data-testid="nav-*" yet - CUA test finds them by UIA title, Playwright cannot. One-line fix per entry, required before `tour_page` is stable.
- `speech-mcp` companion already exists in learnbot AGENTS.md (`:10908/:10909`, `read_aloud` + `spoken_status_readout` tools). Voiceover is a soft crossconnect, not a new protocol.

## Portmanteau shape (proposed)

```python
@mcp.tool(annotations={"readonly": True})
async def webapp_ops(
    operation: str,            # get_ui_map | tour_page | demo_webapp | diagnose_webapp
    route: str = "/",          # tour_page: one path from ui-map.json
    preset: str = "demo_60s",  # demo_webapp: tour_presets key
    speak: bool = False,       # voiceover via speech-mcp read_aloud, degrade to text
    headless: bool = True,     # Playwright headless; headed only for live presentation
) -> dict: ...
```

- `get_ui_map` - returns `demos/webapp-ops-pilot/ui-map.json`. No browser, no ports, always works. This alone replaces sidebar OCR discovery.
- `tour_page` - Playwright: goto route, wait for `page_testid` + `assert` testids, screenshot to `cua-reports/webapp-ops-<label>.png`, return narration text. Read-only.
- `demo_webapp` - walks `tour_presets[preset]`, records Playwright video, optionally calls speech-mcp `read_aloud(narrate)` per stop. Returns video path + per-page receipts.
- `diagnose_webapp` - YOUR self-diagnostic use case: walks ALL routes, records per-page {http, testid_found, api_receipts, ms}, diffs against last run. Answers "did yesterday's edits bork page 9?"

Playwright, not CUA, for all four. CUA stays for NSIS installer cert only.

## speech-mcp wiring (1-hop, soft)

- learnbot documents only `speech-mcp` as companion (FLEET_CROSSCONNECT_STANDARD Rule 2).
- `speak=false` default: zero dependency, works standalone (Rule 1).
- `speak=true`: HTTP POST narration to speech-mcp `read_aloud`, or MCP bridge if configured. Missing/unreachable -> return `{"spoken": null, "needs_companion": "speech-mcp https://github.com/sandraschi/speech-mcp"}` dialogic error (Rule 3). Never fatal.
- No wake-word, no mic, no fleet-agent routing in the pilot. Voice Bus ingress stays untouched.

## Safety gates (AGENT_ACTION_GATES.md)

- Map + tour are `readOnlyHint=True`. Demo with `preset` containing `mutating:true` pages MUST either skip interaction (screenshot + narrate only) or require `?demo=1` mock flag. No `confirm=true` gate - model can set that itself.
- `diagnose_webapp` never submits forms, never deletes. It GETs routes and reads `GET /api/v1/request-log` delta as backend-receipt proof (same pattern as cua-smoke v8).
- Log every driven run (who/what/when/preset).

## Generation, not hand-maintenance

Pilot `ui-map.json` was hand-derived from `Layout.tsx` + `main.tsx` to prove the shape. Production path: emit it at `bun run build` from the router (route path + label + page testid), narration lives in one `tour.ts` next to pages. Stale map = build artifact stale, caught by `diagnose_webapp` diff, not by a human remembering to edit JSON.

## Next steps to make the pilot real

1. Add `data-testid="nav-<label>"` to the 14 NavLinks in `Layout.tsx` (5 min, unlocks Playwright clicks).
2. Implement `webapp_ops` with `get_ui_map` + `tour_page` only (no video, no speech yet), prove 14/14 screenshots equal CUA nav walk.
3. Add `diagnose_webapp` with request-log delta, run before/after one webapp edit to prove it catches breakage.
4. Add `speak=true` last, against local speech-mcp `:10909`.
