# learnbot-mcp

AI chatbot orchestrator — define personas, run conversations with safety guardrails, speak via TTS, log everything.

```json
// opencode.json
{
  "mcpServers": {
    "learnbot-mcp": {
      "command": "uv",
      "args": ["run", "--directory", "D:/Dev/repos/learnbot-mcp", "python", "-m", "learnbot_mcp"]
    }
  }
}
```

## Quick start

```bash
uv sync              # install deps
uv run python -m learnbot_mcp.api   # REST API on :11101
cd web_sota && bun run dev          # webapp on :11102
```

Or double-click `start.bat`.

## What it does

| Tool | What |
|------|------|
| `persona_create` | Define chatbot personality, voice, backstory |
| `chat_start/send` | Run conversations with safety checks + LLM |
| `platform_send` | Speak via TTS (speech-mcp or Windows SAPI5) |
| `safety_rule_*` | Topic blocking, rate limiting, PII redaction |
| `audit_query` | Full conversation log with verdicts |
| `chat_proactive_tick` | Bot initiates conversations on schedule |

## Architecture

```
learnbot-mcp → local-llm-mcp / Ollama (LLM)
            → speech-mcp / Windows SAPI5 (TTS)
            → SQLite (conversations, personas, audit)
            → React webapp (6 pages)
```

## Ethics & Safety

This server includes configurable regulatory compliance (China/EU/none),
topic-based content filtering, rate limiting, and full audit logging.
See [docs/chatbot-ethics.md](docs/chatbot-ethics.md) for a discussion of
addiction pathways, pseudohuman dynamics, and regulatory context.

## Docs

- [PRD.md](PRD.md) — Product requirements
- [SPEC.md](SPEC.md) — Architecture specification
- [docs/chatbot-ethics.md](docs/chatbot-ethics.md) — Ethics, addiction, regulation
- [AGENTS.md](AGENTS.md) — Coding agent guide
- [CHANGELOG.md](CHANGELOG.md) — Release history
