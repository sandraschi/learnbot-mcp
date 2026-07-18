# Changelog

## [0.6.0] — 2026-07-17

### Changed
- **Japanese reference data (kanji, JMdict, JLPT vocab, Tatoeba examples,
  JLPT questions) moved from games-app HTTP integration to bundled local
  SQLite files.** `kanji_search`, `vocab_lookup`, `jlpt_vocab_by_level`,
  `example_sentences`, `jlpt_quiz` now query `data/kanji.db` and
  `data/jlpt_questions.db` directly via aiosqlite — no running games-app
  required. Eliminates a real port collision: the old defaults
  (`LEARNBOT_GAMES_APP_API_URL`=:11003, `LEARNBOT_GAMES_APP_JLPT_URL`=:11001)
  matched games-app's actual kanji-api/jlpt-api ports, but those exact
  ports are also allocated to unrelated fleet hardware-control servers
  (power-supply-mcp, function-generator-mcp) per WEBAPP_PORTS.md.
- `games_integration.py` rewritten: httpx calls → direct aiosqlite queries
  against the bundled files. Same function signatures and return shapes,
  no caller-side changes needed.
- Removed `LEARNBOT_GAMES_APP_API_URL` / `LEARNBOT_GAMES_APP_JLPT_URL`
  config fields (no longer meaningful).
- `jlpt_vocab_by_level` — previously implemented but never registered as
  an MCP tool — now wired into `server.py`.
- Added REST routes (`/api/kanji/search`, `/api/vocab/lookup`,
  `/api/examples/search`, `/api/jlpt/quiz`) so the webapp can actually
  reach this data — previously zero REST exposure existed for any of it.
- `webapp/src/pages/Japanese.tsx` rewritten: added a real inline
  dictionary/kanji search UI backed by the new local API. The 11
  external games-app game links (kanji-master, flashcards, karuta, etc.)
  stay as optional external links, now honestly labeled as such and with
  a health check pointed at games-app's actual port (:10987, was
  incorrectly checking :11003/:11001 — the visible links and the status
  indicator were checking different things).
- Added `data/ATTRIBUTION.md` — JMdict (EDRDG licence) and Tatoeba
  (CC BY 2.0 FR) attribution.

### Fixed
- `_version.py` was still 0.4.0 despite pyproject.toml/README/AGENTS.md
  already at 0.5.0 — synced.

## [0.5.0] — 2026-07-16

### Added
- `kanji_search`, `vocab_lookup`, `example_sentences`, `jlpt_quiz` — MCP tools
  integrating games-app's kanji DB, JMdict (214K), JLPT vocab (8K), Tatoeba (278K),
  and JLPT practice questions (600). Configurable via LEARNBOT_GAMES_APP_API_URL.
- `graded_reader` — structured graded reader for any language: leveled text,
  pre-reading vocabulary, comprehension questions, discussion prompts.
- `framework` parameter on `lesson_generate` and `reading_passage` — target CEFR,
  HSK, DELF, DELE, Goethe, etc. alongside existing JLPT support.
- Japanese learning page in webapp (`/japanese`) with 11 linked games-app tools.
- `docs/JAPANESE_LEARNING.md` — full-spectrum Japanese learning guide.
- README.md — Table of Contents, Arabic→German persona preset for Austrian
  integration context (Layla, AR/DE bilingual).
- classroom-mcp: `framework` field on students/classes, `syllabus_generate` (AI
  curriculum per framework), `courseware_generate_ai`, `assignment_create_with_lesson`
  (calls learnbot-mcp via LEARNBOT_URL — bridge now wired).

### Changed
- `_version.py` and `pyproject.toml` bumped to 0.5.0.
- Removed duplicate `except` block in `_generate_fresh_quiz`.

## [0.4.1] — 2026-07-16

### Fixed
- JSON extraction from LLM responses — `_generate_fresh_quiz`, `_generate_distractors`,
  `grammar_check`, `reading_passage`, `lesson_generate`, `lesson_differentiate` all
  now handle prose-wrapped JSON (LLM wraps arrays/objects in explanatory text).
  Added shared `_clean_llm_json()` and `_extract_json_array()` helpers.
- `{overdue_count}` variable now resolved in proactive triggers — queries
  `vocab_items` table for `COUNT(*) WHERE due_at <= now` instead of being
  a planned-but-unimplemented feature.
- STATUS.md port corrected from 11104 to 11101.
- `_version.py` and `pyproject.toml` version bumped to 0.4.0.
- TODO.md P2 checkboxes fixed for completed items.

### Added
- 4 regression tests: duplicate tool registration guard, lesson round-trip,
  due vocab item appears in quiz, distractor correctness guard.

## [0.4.0] — 2026-07-15

### Added
- Lesson depot — create, generate, list, update, delete, run lesson plans
- AI lesson generator — full curriculum from a title (sections, vocab, quiz questions)
- Lesson runner — injects lesson into conversation flow
- Vocab quiz with spaced repetition (SM-2 algorithm)
- Grammar check tool (LLM-based sentence correction)
- Reading passage generator (JLPT-graded)
- Lesson management page in webapp (generate, view, delete)
- Demo runner page (5 clickable demos + Run All)
- Soundscape module (emotion → SFX via yahboom-mcp audio + buzzer)
- 23 smoke tests + 4 lesson CRUD tests
- Centralized emotion tags (TAG_PATTERN constant, imported everywhere)

### Fixed
- `_re` NameError crash on voiceless personas (hoisted import)
- Per-conversation disclosure tracking (global set → per-conversation set)
- `item.get()` crash on `sqlite3.Row` in vocab_quiz
- Missing `f` prefix on f-string in `_generate_distractors` (LLM received literal `{correct}`)
- `lesson_update` MCP tool missing from server.py registration

### Changed
- Emotion tag regex consolidated into `robot_orchestrator.TAG_PATTERN` (single source of truth)
- Version bumped to 0.4.0

## [0.3.0] — 2026-07-15
- Robot orchestrator — emotion tags mapped to Boomy (yahboom-mcp) motion, LED, camera sequences
- 12 emotion→action mappings with fire-and-forget async execution
- `robot_stop_all()` emergency stop function
- godot-mcp integration: `godot_import_vrm` tool + V-Sekai addon registry entry
- GDScript bridge `_cmd_import_vrm` command for VRM loading in Godot 4
- `godot_list_vrm` tool to browse the shared avatar depot
- VRM depot at `~/.avatarmcp/models/` (shared across avatar-mcp, resonite-mcp, vrchat-mcp)
- STATUS.md and TODO.md documentation

### Changed
- Emotion tag system prompt expanded: tags now drive both voice + robot motion
- Emotion tag regex pattern covers all 12 robot-mapped emotions

## [0.2.0] — 2026-07-15

### Added
- Emotion tags — LLM infers mood from conversation, Gemini TTS speaks with prosody
- Gemini TTS as default (Kore/Leda voice), Windows SAPI5 fallback, speech-mcp secondary fallback
- Voice selector page — 20 Gemini voices with descriptions and test buttons
- VRM 3D viewer — three.js + @pixiv/three-vrm, loads Nekomimi-chan from avatar-mcp
- Avatar page for 3D model viewing
- Transparent desktop mascot (`/mascot.html`) — always-on-top capable, Tauri config ready
- `languages` and `skills` fields on personas — architecture ready for learnbot tools
- REST API: `/api/voices`, `/api/voice/test`, `/api/avatar.vrm`, `/api/avatar/vrm`
- Fleet start entry in mcp-central-docs
- STATUS.md, TODO.md, docs/chatbot-ethics.md

### Changed
- Renamed from chatbot-mcp to learnbot-mcp
- Default TTS provider: gemini (was: windows)
- Default voice: Leda (was: Kore)
- Default LLM model: llama3.2:3b (was: qwen3.5-9b-deepseek-v4-flash)
- Backend API base URL: speech-mcp port corrected to :10909

### Fixed
- `build_history` crash on sqlite3.Row objects (missing .get())
- All `get_db()` calls wrapped in `async with` context managers
- `speech_say` async fire-and-forget using `asyncio.create_task`

## [0.1.0] — 2026-07-15

### Added
- Initial scaffold — persona CRUD, conversation lifecycle, safety guardrails
- 14 MCP tools (persona, chat, safety, audit, platform bridge)
- SQLite persistence (aiosqlite, WAL mode)
- Safety module: rate limiting, topic blocking, PII redaction
- LLM bridge to local-llm-mcp with conversation history
- Speech bridge to speech-mcp (TTS via `platform_send`)
- Starlette REST API (18 endpoints on port 11101)
- React/Vite/Tailwind webapp (5 pages)
- FastMCP 3.4+ stdio transport
- SPEC.md and PRD.md with phased rollout plan
