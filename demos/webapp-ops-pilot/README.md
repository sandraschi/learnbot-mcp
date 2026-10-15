# webapp_ops pilot — self-driving webapp (learnbot-mcp)

Status: PILOT 2026-10-15. Works on learnbot-mcp; not yet a fleet standard.
Fleet pattern draft: `mcp-central-docs/patterns/WEBAPP_OPS_SELF_DRIVING.md`.

The idea: instead of OCR-scraping the sidebar to discover pages (what
`cua-webapp-test` does), the repo ships an **authoritative UI map** and the
MCP server drives its own webapp from it — tours, demos with voiceover,
and self-diagnostics.

## One-click start

Double-click `start-all.bat` (this folder). It boots both stacks in their
own windows via the fleet-standard launchers, waits for health, and opens
the webapp:

| Stack | Backend | Frontend |
|-------|---------|----------|
| speech-mcp (voiceover companion) | :10909 | :10908 |
| learnbot-mcp (tour target) | :11101 | :11102 |

Close the two windows to stop. If `speech-mcp` is missing you get an
error with the clone URL — learnbot still works, voiceover just degrades
to text.

## The four ops

All on the `webapp_ops` MCP tool (read-only; never submits forms):

```
webapp_ops(operation="get_ui_map")
webapp_ops(operation="tour_page", route="/chat")
webapp_ops(operation="demo_webapp", preset="demo_60s", speak=true)
webapp_ops(operation="diagnose_webapp")
```

| Op | What it answers |
|----|-----------------|
| `get_ui_map` | The map itself: 14 routes, nav testids, assert testids, narration, which pages mutate. No backend needed. |
| `tour_page` | One-page receipt: label, testids, narration, frontend `dist` present, backend reachable. Unknown route fails with the known-path list. |
| `demo_webapp` | Walks a preset (`demo_60s`, `onboarding`, `full_walk`). `speak=true` narrates each stop via speech-mcp `POST /api/v1/tts`, degrading to text when absent. |
| `diagnose_webapp` | "Did yesterday break page 9?" Walks all 14, per-page status + backend reachability, snapshot to `last-diagnosis.json` for run-over-run diff. |

REST twins for the frontend: `GET /api/ui-map`, `GET /api/v1/request-log`
(ring buffer — backend-receipt proof that data actually arrived, not just
that `<h1>` rendered).

## Files

| File | Role |
|------|------|
| `ui-map.json` | Hand-derived pilot map (production path: emitted at `bun run build` from the router) |
| `WEBAPP_OPS_DRAFT.md` | Tool signature, speech wiring, safety gates, next steps |
| `start-all.bat` | One-click two-stack launcher |
| `last-diagnosis.json` | Latest `diagnose_webapp` snapshot (regenerated each run) |
| `../../webapp/public/ui-map.json` | Same map, shipped with the build |
| `../../webapp/src/Layout.tsx` | Sidebar links carry `data-testid="nav-<slug>"` (Playwright-clickable) |
| `../../src/learnbot_mcp/webapp_ops.py` | Receipt logic (phase 1: static, no browser) |
| `../../src/learnbot_mcp/server.py` | `webapp_ops` tool registration |
| `../../src/learnbot_mcp/api.py` | `/api/ui-map` + `/api/v1/request-log` + logging middleware |

## What phase 2 adds

Live Playwright driving (screenshots, mp4) behind an honest
`needs_playwright` refusal; request-log delta per page in
`diagnose_webapp`; `tour.ts` narration source next to pages so the map is
generated, not hand-maintained.

## Rollout order

`japanophile-mcp` (cheap, same shape) → `yahboom-mcp` (physical actuators:
read-only tour only, env-flag gates) → `resonite-mcp` (needs `?demo=1`
mock before any drive) → `calibre-mcp` (list-page asserts, paginated
receipts). Full plan in the MCD pattern doc.
