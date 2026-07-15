# Changelog

## [0.2.0] — 2026-07-15

### Added
- Emotion tags — LLM infers mood from conversation, Gemini TTS speaks with prosody
- Gemini TTS as default (Kore/Leda voice), Windows SAPI5 fallback, speech-mcp secondary fallback
- Voice selector page — 20 Gemini voices with descriptions and test buttons
- VRM 3D viewer — three.js + @pixiv/three-vrm, loads Nekomimi-chan from avatar-mcp
- Avatar page for 3D model viewing
- Transparent desktop mascot (`/mascot.html`) — always-on-top capable, Tauri config ready
- `languages` and `skills` fields on personas — architecture ready for learnbot tools
- REST API: `/api/voices`, `/api/voice/test`, `/api/avatar.vrm`, `/api/avatar/vrm`
- Fleet start entry in mcp-central-docs
- STATUS.md, TODO.md, docs/chatbot-ethics.md

### Changed
- Renamed from chatbot-mcp to learnbot-mcp
- Default TTS provider: gemini (was: windows)
- Default voice: Leda (was: Kore)
- Default LLM model: llama3.2:3b (was: qwen3.5-9b-deepseek-v4-flash)
- Backend API base URL: speech-mcp port corrected to :10909

### Fixed
- `build_history` crash on sqlite3.Row objects (missing .get())
- All `get_db()` calls wrapped in `async with` context managers
- `speech_say` async fire-and-forget using `asyncio.create_task`

## [0.1.0] — 2026-07-15

### Added
- Initial scaffold — persona CRUD, conversation lifecycle, safety guardrails
- 14 MCP tools (persona, chat, safety, audit, platform bridge)
- SQLite persistence (aiosqlite, WAL mode)
- Safety module: rate limiting, topic blocking, PII redaction
- LLM bridge to local-llm-mcp with conversation history
- Speech bridge to speech-mcp (TTS via `platform_send`)
- Starlette REST API (18 endpoints on port 11101)
- React/Vite/Tailwind webapp (5 pages)
- FastMCP 3.4+ stdio transport
- SPEC.md and PRD.md with phased rollout plan
