# Configuration

Verified against `src/learnbot_mcp/config.py` (pydantic-settings, `.env`-backed).

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `BACKEND_PORT` | `11101` | REST API port |
| `FRONTEND_PORT` | `11102` | Webapp dev port |
| `LOG_LEVEL` | `INFO` | Log verbosity |
| `DB_PATH` | `data/chatbot.db` | SQLite database path |
| `LEARNBOT_REGULATORY_REGIME` | `none` | Compliance regime: `china` / `eu` / `none` |
| `LEARNBOT_REAL_NAME_AUTH` | `false` | Require real-name auth (China compliance) |
| `LEARNBOT_RETENTION_DAYS` | `90` | Conversation retention window, in days |
| `CHATBOT_LLM_PROVIDER` | `local-llm-mcp` | LLM backend provider |
| `LEARNBOT_LLM_BASE_URL` | `http://127.0.0.1:10832` | LLM server base URL |
| `LEARNBOT_LLM_MODEL` | *(empty)* | Model name override (e.g. `llama3.2:3b`) |
| `LEARNBOT_LLM_PROVIDER` | `ollama` | LLM provider ID for chat (`ollama`, `lmstudio`, `vllm`, or any cloud ID); Settings page offers all 16 |
| `LEARNBOT_SPEECH_MCP_URL` | `http://127.0.0.1:10909` | speech-mcp TTS/STT bridge URL |
| `LEARNBOT_AVATAR_MCP_URL` | `http://127.0.0.1:10792` | avatar-mcp bridge URL |
| `LEARNBOT_RESONITE_MCP_URL` | `http://127.0.0.1:10979` | resonite-mcp bridge URL (backend — `:10978` is the Vite frontend, no `/health`) |
| `LEARNBOT_VRCHAT_MCP_URL` | `http://127.0.0.1:10712` | vrchat-mcp transport URL (MCP `/mcp`; chatbox via MCP/OSC, not REST) |
| `LEARNBOT_OVERTE_MCP_URL` | `http://127.0.0.1:11110` | overte-mcp bridge URL (domain admin `:40100`) |
| `LEARNBOT_MIKO_AVATAR_PATH` | *(empty)* | Miko's Resonite inventory path for summon avatar-load (empty = skip with hint) |
| `LEARNBOT_MIKO_GLB_URL` | `http://localhost:11110/models/Nekomimi-chan.glb` | Miko GLB for Overte classroom entities |
| `LEARNBOT_MEMOPS_URL` | `http://127.0.0.1:10732` | memops (basic-memory) bridge URL |
| `LEARNBOT_RATE_LIMIT` | `30` | Safety rate limit, messages per minute |
| `LEARNBOT_API_KEY` | *(empty)* | API key for REST endpoints, if enforced |

## Setting Variables

Create a `.env` file in the repo root (see `.env.example`), or set them in
`claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "learnbot-mcp": {
      "command": "uv",
      "args": ["run", "--directory", "D:/Dev/repos/learnbot-mcp", "python", "-m", "learnbot_mcp"],
      "env": {
        "LEARNBOT_LLM_MODEL": "llama3.2:3b",
        "LEARNBOT_REGULATORY_REGIME": "none"
      }
    }
  }
}
```

## LLM providers

Chat supports 16 providers through the backend proxy (`POST /api/llm/chat`,
SSE at `/api/llm/chat/stream`) — the browser never calls vendors directly.
Locals (`ollama`, `lmstudio`, `vllm`) need no key; cloud providers
(OpenAI, Anthropic, DeepSeek, OpenRouter, Meta, Google, Groq, Mistral,
Together, Fireworks, Cohere, xAI, Perplexity) need a key from env
(`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, … — see `llm_providers.py`) or the
Settings page, which stores into `data/llm_keys.json` (0600, gitignored —
env wins). `GET /api/llm/providers` reports configured flags, never keys.
Fleet background: `arxiv-mcp/docs/SPEC-llm-providers.md`.

## Notes

- `LEARNBOT_LLM_BASE_URL` defaults to `local-llm-mcp`'s port (10832), not
  Ollama directly — if you're pointing straight at Ollama, override it to
  `http://127.0.0.1:11434`.
- All six bridge URLs (`speech`, `avatar`, `resonite`, `vrchat`, `overte`,
  `memops`) point to other fleet MCP servers. learnbot-mcp degrades gracefully
  if any of them aren't running — features that need them (TTS, avatar VRM,
  Resonite/Overte/VRChat summon, long-term memory) report dialogic hints,
  they don't hard-fail the whole server. The `/vr` page shows live status.
