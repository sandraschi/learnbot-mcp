# learnbot-mcp - Architecture Specification

**Version**: 0.1.0-draft  
**Status**: draft  
**Ports**: 11101 (backend), 11102 (frontend, future)

## Architecture Overview

```
learnbot-mcp (orchestrator)
    │
    ├── MCP tools: persona CRUD, chat lifecycle, safety config, audit
    ├── Starlette REST: /api/health, /api/chat, /api/personas
    ├── SQLite: personas, conversations, audit log, safety rules
    │
    ├── Outbound (fleet MCP servers):
    │   ├── local-llm-mcp :10832  - LLM inference
    │   ├── speech-mcp :10908    - TTS + STT
    │   ├── avatar-mcp :10792    - avatar lifecycle
    │   ├── resonite-mcp :10978  - Resonite world bridge
    │   └── memops :10732        - memory / RAG
    │
    └── Inbound:
        ├── MCP stdio (Claude Desktop, opencode)
        ├── MCP streamable HTTP /mcp
        └── Starlette REST /api/*
```

## Data Model

### Persona
```yaml
name: "Miko"                    # unique handle
display_name: "Miko-chan"       # shown in chat
backstory: "..."                # full character description / system prompt
voice: "heart"                  # speech-mcp voice ID
avatar_vrm: "miko.vrm"          # path to VRM file
avatar_scale: 1.0               # Resonite avatar scale
platforms: ["resonite", "discord", "web", "tts"]
behavioral_constraints:
  - topic: "politics"
    action: "refuse"
    message: "I am not equipped to discuss politics."
  - topic: "gore"
    action: "refuse"
  - topic: "personal_info"
    action: "redact"            # strip from logs
proactive_triggers:             # bot can start conversations
  - schedule: "0 8 * * 1-5"     # weekday 8am
    prompt: "Good morning! Your TBR pile has {overdue_count} items."
knowledge_base: ""              # optional RAG context source
```

### Conversation
```yaml
id: uuid
persona: "Miko"
platform: "resonite" | "discord" | "web" | "tts"
session_id: "..."              # platform-specific session
state: "active" | "hibernating" | "completed"
created_at: ISO8601
updated_at: ISO8601
turn_count: int
metadata: {}                   # platform-specific
```

### Turn
```yaml
id: uuid
conversation_id: uuid
role: "user" | "assistant" | "system" | "refused"
content: string
timestamp: ISO8601
user_id: str                   # for audit / real-name
platform: str
safety_verdict: "passed" | "blocked" | "redacted"
metadata: {}                   # llm provider, model, latency, etc.
```

## Tools

### Persona Management
- `persona_create(name, display_name, backstory, voice, avatar_vrm, platforms, constraints, proactive_triggers)` → id
- `persona_update(name, ...)` → success
- `persona_delete(name)` → success
- `persona_list()` → personas
- `persona_get(name)` → persona detail
- `persona_duplicate(from_name, to_name)` → new persona id

### Chat Lifecycle
- `chat_start(persona, platform, user_id)` → conversation_id
- `chat_send(conversation_id, content, user_id)` → response
- `chat_hibernate(conversation_id)` → hibernated (save state for later)
- `chat_resume(conversation_id)` → active
- `chat_destroy(conversation_id)` → delete
- `chat_list(state_filter?)` → active conversations
- `chat_proactive_tick()` - check all scheduled triggers, fire those due

### Safety & Compliance
- `safety_rule_create(topic, action, message?)` → id
- `safety_rule_update(id, ...)` → success
- `safety_rule_delete(id)` → success
- `safety_rule_list()` → rules
- `safety_check(content, user_id)` → verdict (runs all enabled rules)
- `audit_query(user_id?, persona?, after?, limit?)` → turns matching query

### Platform Bridge
- `platform_send(conversation_id, content, platform)` → send output to platform
- `platform_status()` → which platforms are connected and healthy

## Safety Architecture

Every incoming message flows through:
```
user message
    │
    ├── Rate limiter (per user, per persona)
    ├── Safety rules (topic match → block/refuse/redact)
    ├── Content filter (regex + LLM classification)
    │
    ├── [if blocked] → log + return refusal
    │
    ├── LLM call (via local-llm-mcp)
    │
    ├── Output safety filter (regenerate if problematic)
    ├── Log turn to audit store
    │
    └── Deliver to platform(s)
```

## Regulatory Compliance

### China (2026 regulations)
- Real-name auth: `user_id` maps to verified identity
- Conversation retention: minimum 30 days, configurable
- Topic blocklist: must refuse specified topics
- Audit export: government request format
- Refusal templates: configurable per topic

### EU AI Act
- Transparency: "You are talking to an AI" disclosure
- Logging: all turns logged for audit
- Opt-out: user can delete all conversation data
- Provider attribution: which LLM model was used per turn

Config via `.env`: `LEARNBOT_REGULATORY_REGIME=china|eu|none`

## Deployment

```yaml
# opencode.json
{
  "mcpServers": {
    "learnbot-mcp": {
      "command": "uv",
      "args": ["run", "--directory", "D:/Dev/repos/learnbot-mcp", "python", "-m", "learnbot_mcp"]
    }
  }
}
```

Ports: 11101 (backend), 11102 (frontend, future)

## Phased Rollout

| Phase | What | Depends on |
|-------|------|-----------|
| P1 - Core | Persona CRUD, chat lifecycle, SQLite, safety rules | Nothing |
| P2 - LLM bridge | Chat delegates to local-llm-mcp, streaming responses | local-llm-mcp running |
| P3 - Platforms | Discord bridge, Resonite bridge, speech-mcp bridge | Platform MCP servers |
| P4 - Compliance | China real-name, audit export, EU transparency | P1 |
| P5 - Proactive | Scheduled triggers, bot-initiated chat | P2 |
| P6 - Webapp | React dashboard, persona editor, live chat | P1 |
| P7 - Tauri | Native desktop wrapper, system tray | P6 |
