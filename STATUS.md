# learnbot-mcp — Status

**Updated**: 2026-07-15

## Current State

| Area | Status | Notes |
|------|--------|-------|
| Core chat | ✅ | Persona CRUD, conversation lifecycle, safety, audit |
| LLM bridge | ✅ | Default: llama3.2:3b via Ollama. Falls back gracefully. |
| Speech TTS | ✅ | Gemini TTS via speech-mcp (Kore/Leda), fallback windows/SAPI5 |
| Emotion tags | ✅ | LLM infers mood, tags → Gemini prosody |
| Compliance | ✅ | China/EU configurable regimes |
| Proactive chat | ✅ | Scheduled triggers |
| REST API | ✅ | 20+ endpoints on port 11101 |
| Webapp (SPA) | ✅ | 8 pages — Dashboard, Chat, Personas, Safety, Compliance, Audit, Voices, Avatar |
| Chat tag | ✅ | Floating widget at /chat-tag.html |
| VRM 3D viewer | ✅ | three.js + @pixiv/three-vrm at /avatar page |
| Desktop mascot | ✅ | Transparent always-on-top at /mascot.html (Tauri config ready) |
| Windows SAPI5 | ✅ | Fallback when speech-mcp down |
| Japanese support | ✅ | Miko-chan bilingual (ja/en), Gemini handles kanji pronunciation |
| Persona skills | ✅ | languages + skills fields in schema (for learnbot tools) |
| Git | ✅ | Initialized, 7 commits |

## Running Services

| Service | Port | Status |
|---------|------|--------|
| learnbot-mcp API | 11101 | — |
| learnbot-mcp webapp | 11101/served | — |
| speech-mcp | 10909 | — |
| Ollama | 11434 | — |

## What's Next

See [TODO.md](TODO.md) for the roadmap. Key priorities: streaming responses, learnbot tools (vocab quiz, grammar check), Resonite integration, Gemini Live voice.
