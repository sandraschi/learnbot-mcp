# learnbot-mcp — Status

**Updated**: 2026-07-15

## Current State

| Area | Status | Notes |
|------|--------|-------|
| Core chat | ✅ | Persona CRUD, conversation lifecycle, safety, audit |
| LLM bridge | ✅ | Default: llama3.2:3b via Ollama. Falls back to any OpenAI-compatible endpoint. |
| Speech TTS | ✅ | Gemini TTS via speech-mcp (Leda voice), fallback windows/SAPI5 |
| Emotion tags | ✅ | LLM infers mood, tags drive Gemini voice prosody + robot motion |
| Robot orchestrator | ✅ | Emotion tags → Boomy (yahboom-mcp) motion, LEDs, camera gestures |
| Compliance | ✅ | China/EU configurable regimes (real-name auth, retention, refusal templates) |
| Proactive chat | ✅ | Scheduled triggers (interval, cron, time-of-day) |
| REST API | ✅ | 20+ endpoints on port 11104 |
| Webapp (SPA) | ✅ | 9 pages — Dashboard, Chat, Personas, Safety, Compliance, Audit, Voices, Avatar, Help |
| Chat tag | ✅ | Floating widget at /chat-tag.html |
| VRM 3D viewer | ✅ | three.js + @pixiv/three-vrm, Nekomimi-chan + AnimeGirl2 from depot |
| Desktop mascot | ✅ | Transparent always-on-top page at /mascot.html, Tauri config ready |
| godot-mcp VRM pipeline | ✅ | godot_import_vrm tool, V-Sekai addon, mcp_bridge.gd command |
| VRM depot | ✅ | ~/.avatarmcp/models/ shared across avatar-mcp, resonite-mcp, vrchat-mcp, godot-mcp |
| Windows SAPI5 | ✅ | Fallback TTS when speech-mcp unavailable |
| Japanese support | ✅ | Miko-chan bilingual (ja/en), Gemini handles kanji pronunciation natively |
| Persona languages/skills | ✅ | Schema fields for learnbot tools |
| Git | ✅ | 9+ commits |

## Architecture

```
learnbot-mcp (orchestrator)
  ├── LLM → Ollama (llama3.2:3b)
  ├── TTS → speech-mcp → Gemini / Windows SAPI5
  ├── Robot → yahboom-mcp (Boomy: motion, LEDs, camera, patrol)
  ├── Avatar → avatar-mcp (VRM depot) / godot-mcp (3D viewer) / resonite-mcp (world)
  ├── Voice → speech-mcp → Gemini TTS (Kore/Leda/Callirrhoe)
  ├── Safety → topic rules, rate limits, PII redaction, compliance regime
  └── Learning → persona skills field (vocab_quiz, grammar_check, reading_passage — planned)
```

## Running Services

| Service | Port | Notes |
|---------|------|-------|
| learnbot-mcp API | 11104 | Full REST + SPA serving |
| speech-mcp | 10909 | Gemini TTS + Windows fallback |
| Ollama | 11434 | llama3.2:3b default |
| yahboom-mcp | 10892 | Robot control (when Boomy is online) |
| avatar-mcp | 10792 | VRM model depot |
| godot-mcp | 10993 | VRM 3D viewer pipeline |

## What's Next

See [TODO.md](TODO.md) for full roadmap. Key near-term: streaming responses,
learnbot tools (vocab quiz, grammar check), Resonite web panel for mascot,
Gemini Live voice for realtime conversation.
