# learnbot-mcp — TODO

**Updated**: 2026-07-15

## P1 — Core experience

- [ ] **Streaming responses** — SSE from Ollama → live text in chat UI
- [ ] **Server auto-start** — NSSM for learnbot-api, speech-mcp, Ollama
- [ ] **LLM model config in webapp** — switch models via UI
- [ ] **Conversation export** — full .txt/.json download with metadata
- [ ] **Error audit logging** — all API error responses logged with traceback

## P2 — Learnbot tools

- [ ] `vocab_quiz` — spaced-repetition vocab from conversation context
- [ ] `grammar_check` — LLM corrects learner's sentence, explains grammar
- [ ] `reading_passage` — generate JLPT-graded text + comprehension questions
- [ ] `speaking_drill` — speech-mcp prompts, listens (STT), rates pronunciation

## P3 — Avatar & presence

- [ ] **Resonite web panel** — test mascot.html in Resonite web panel
- [ ] **Resonite full avatar** — `POST /rl/world/import-vrm` with Nekomimi-chan
- [ ] **Blendshape mirroring** — emotion tags → VRM facial expressions via three-vrm
- [ ] **Lip-sync** — Gemini TTS phonemes → mouth blendshapes
- [ ] **Tauri mascot build** — `cd native && cargo tauri build` for always-on-top desktop

## P4 — Platforms

- [ ] Discord bridge — chat with personas via DMs
- [ ] Gemini Live voice — realtime conversation with emotion
- [ ] Gimp-mcp writing practice — render learner text as annotated image
- [ ] FLUX 2 Klein avatar generation — generate persona portraits via comfyops-mcp

## P5 — Robot

- [ ] **Emotion→Boomy mapping** — ✅ DONE (12 emotions mapped to motion/LED/camera)
- [ ] **Bumi physical control** — re-evaluate when bumi-mcp gets real hardware support
- [ ] **Talkbot demo bridge** — connect learnbot persona to Boomy talkbot demo
- [ ] **Follow-me mode** — emotion triggers Boomy to follow or retreat

## P6 — Polish

- [ ] Playwright E2E tests
- [ ] Settings page wired to backend
- [ ] TypeScript strict mode
- [ ] Framer Motion micro-interactions
- [ ] Pagination on audit log
