# AGENTS.md - learnbot-mcp

## Identity

- **Name**: learnbot-mcp
- **Purpose**: AI chatbot orchestrator - persona management, conversation lifecycle, safety guardrails, multi-platform output (Resonite, Discord, web, TTS)
- **Owner**: Sandra Schipal, Vienna
- **Ports**: Backend 11101, Frontend 11102

## Architecture

```
learnbot-mcp (orchestrator)
  ├── Persona CRUD (create, read, list, delete)
  ├── Conversation lifecycle (start, send, hibernate, resume, destroy)
  ├── Safety rules (topic-based blocking, rate limiting, PII redaction)
  ├── Audit log (all turns with user_id, verdict, platform)
  │
  └── Delegates to fleet MCP servers:
      ├── local-llm-mcp (:10832) - LLM inference
      ├── speech-mcp (:10908) - TTS/STT
      ├── avatar-mcp (:10792) - avatar lifecycle
      ├── resonite-mcp (:10978) - Resonite world bridge
      └── memops (:10732) - memory / RAG
```

## Key Files

| File | Purpose |
|------|---------|
| `src/learnbot_mcp/server.py` | MCP tool registrations |
| `src/learnbot_mcp/database.py` | Schema + CRUD (aiosqlite) |
| `src/learnbot_mcp/safety.py` | Safety guardrails |
| `src/learnbot_mcp/config.py` | Settings (pydantic-settings) |
| `SPEC.md` | Architecture specification |
| `PRD.md` | Product requirements |

## Tools

- `persona_create`, `persona_get`, `persona_list`, `persona_delete`
- `chat_start`, `chat_send`, `chat_hibernate`, `chat_resume`, `chat_destroy`, `chat_list`
- `safety_rule_create`, `safety_rule_list`, `safety_rule_delete`
- `audit_query`

## Code Rules

- Python 3.12+, async-first, aiosqlite for DB
- FastMCP 3.4+ tool patterns
- pydantic-settings for config
- All safety checks log to audit before acting
- LLM calls delegate to fleet servers (no direct inference)
