# learnbot-mcp — TODO

**Updated**: 2026-07-15

## P1 — Core experience

- [ ] **Streaming responses (deferred)** — SSE from Ollama → live text
  ~2 days for marginal UX gain. Revisit if chat latency becomes a top complaint.
  Fire-and-forget TTS + robot motion already mask response time:
  user hears/speaks/feels output while the LLM finishes generating.
- [ ] **Server auto-start** — NSSM for learnbot-api, speech-mcp, Ollama
- [ ] **LLM model config in webapp** — switch models via UI
- [ ] **Conversation export** — full .txt/.json download with metadata
- [ ] **Error audit logging** — all API error responses logged with traceback

## P2 — Learnbot tools (in progress)

- [x] `vocab_quiz` — spaced-repetition vocab from conversation context
- [x] `grammar_check` — LLM corrects learner's sentence, explains grammar
- [x] `reading_passage` — generate JLPT-graded text + comprehension questions
- [x] `lesson_generate` — AI generates full lesson from title
- [x] `lesson_run` — injects lesson into conversation
- [x] `lesson_differentiate` — adapt lesson for different JLPT level
- [ ] `speaking_drill` — speech-mcp prompts, listens (STT), rates pronunciation
- [ ] `writing_practice` — gimp-mcp renders learner text as annotated image

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
