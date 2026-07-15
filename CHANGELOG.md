# Changelog

## [0.1.0] - 2026-07-15

### Added
- Initial scaffold - persona CRUD, conversation lifecycle, safety guardrails
- 14 MCP tools (persona, chat, safety, audit, platform bridge)
- SQLite persistence (aiosqlite, WAL mode)
- Safety module: rate limiting, topic blocking, PII redaction
- LLM bridge to local-llm-mcp with conversation history
- Speech bridge to speech-mcp (TTS via `platform_send`)
- Starlette REST API (18 endpoints on port 11101)
- React/Vite/Tailwind webapp (5 pages on port 11102)
- FastMCP 3.4+ stdio transport
- SPEC.md and PRD.md with phased rollout plan
