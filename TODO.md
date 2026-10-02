# learnbot-mcp — TODO

**Updated**: 2026-10-02

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
  (PARTIAL 2026-10-02: summon sets `LEARNBOT_MIKO_AVATAR_PATH` avatar-load when
  linked; ResoniteLink has no VRM import, inventory times out upstream — manual
  drag-drop + inventory path is the current flow, see ONBOARDING_VR)
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

## P7 — Learn in VR (shipped 2026-10-02, Phases 0–6)

- [x] `/vr` page shell + Dashboard quick-action + 3-companion status
- [x] Resonite summon (session probe + optional avatar-load + Happy + TTS + audit)
- [x] Voice ranking A/B (Gemini Leda JP default; samples in `docs/audio/`)
- [x] Overte summon (greeting-sign spawn, live/simulated) + Track C onboarding
- [x] Classroom loop (`vr_lesson_step`, katakana grading) + `vr_classroom_ensure`
- [x] VRChat handoff last (chatbox chunks + 2FA/Secure Boot checklist) + polish gate
- [ ] Ear check: Sandra confirms Leda samples in `docs/audio/`
- [ ] VR screenshot: `cua-webapp-test` pass with `/vr` in nav walk
- [ ] Companion-side: vrchat-mcp README ports (10795/10796 stale → 10712)
- [ ] Local-first voice: run VoiceStudio sidecar (`:3900`) + JP quality check
- [ ] General `docs/ONBOARDING.md` (VR doc shipped; repo-wide doc still missing)
