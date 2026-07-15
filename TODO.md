# learnbot-mcp — TODO

## P1 — Core experience

- [ ] **Streaming responses** — SSE from Ollama → live text in chat UI
- [ ] **Server auto-start** — NSSM or scheduled task for learnbot-api + speech-mcp + Ollama
- [ ] **LLM model config in webapp** — switch between models via UI
- [ ] **Conversation export** — full .txt/.json download with metadata

## P2 — Learnbot tools

- [ ] `vocab_quiz` — spaced-repetition vocab from conversation context
- [ ] `grammar_check` — LLM corrects learner's sentence, explains grammar
- [ ] `reading_passage` — generate JLPT-graded text + comprehension questions
- [ ] `speaking_drill` — speech-mcp prompts, listens (STT), rates pronunciation

## P3 — Avatar & presence

- [ ] **Resonite web panel** — test mascot.html in Resonite web panel
- [ ] **Resonite full avatar** — `POST /rl/world/import-vrm` with Nekomimi-chan
- [ ] **Blendshape mirroring** — emotion tags → VRM facial expressions
- [ ] **Lip-sync** — Gemini TTS phonemes → mouth blendshapes
- [ ] **Tauri mascot build** — `cd native && cargo tauri build` for always-on-top

## P4 — Platforms

- [ ] Discord bridge — chat with personas via DMs
- [ ] Gemini Live voice — realtime conversation with emotion
- [ ] Gimp-mcp writing practice — render learner text as annotated image
- [ ] FLUX 2 Klein avatar generation — generate persona portraits

## P5 — Polish

- [ ] Playwright E2E tests
- [ ] Settings page wired to backend
- [ ] TypeScript strict mode
- [ ] Framer Motion micro-interactions
