# AGENTS.md - learnbot-mcp

## Identity

- **Name**: learnbot-mcp
- **Purpose**: AI chatbot orchestrator — persona management, conversation lifecycle, safety guardrails, multi-platform output, language learning (any language)
- **Owner**: Sandra Schipal, Vienna
- **Ports**: Backend 11101, Frontend 11102
- **Version**: 0.5.0

## Architecture

```
learnbot-mcp (orchestrator)
  ├── Persona CRUD (create, read, list, delete)
  ├── Conversation lifecycle (start, send, hibernate, resume, destroy)
  ├── Safety rules (topic-based blocking, rate limiting, PII redaction)
  ├── Learning tools — vocab (SM-2), grammar check, graded reader, lessons
  ├── Audit log (all turns with user_id, verdict, platform)
  ├── Japanese reference data (kanji/JMdict/JLPT/Tatoeba — bundled locally, data/kanji.db)
  │
  └── Delegates to fleet MCP servers:
      ├── Ollama (default :11434) - LLM inference
      ├── speech-mcp (:10908) - TTS/STT
      ├── avatar-mcp (:10792) - avatar lifecycle
      └── classroom-mcp (:11105) - admin layer (courses, students)
```

## Tools

- `persona_*` — CRUD with languages, skills, voice, proactive triggers
- `chat_*` — start, send, hibernate, resume, destroy, list
- `lesson_*` — create, generate (AI), differentiate, run, get, list, update, delete
- `vocab_quiz` / `vocab_submit` — SM-2 spaced repetition
- `grammar_check` — sentence correction with JLPT/CEFR level
- `reading_passage` / `graded_reader` — leveled reading with questions
- `kanji_search`, `vocab_lookup`, `jlpt_vocab_by_level`, `example_sentences`, `jlpt_quiz` — Japanese reference data (bundled locally)
- `safety_rule_*`, `audit_query`, `platform_send`, `chat_proactive_tick`

All learning tools accept `source_lang`/`target_lang`/`level`/`framework` — language-agnostic.

## Key Files

| File | Purpose |
|------|---------|
| `src/learnbot_mcp/server.py` | MCP tool registrations |
| `src/learnbot_mcp/learn_tools.py` | Vocab, grammar, reading, graded reader |
| `src/learnbot_mcp/lessons.py` | Lesson CRUD + AI generation |
| `src/learnbot_mcp/games_integration.py` | games-app API wrappers |
| `src/learnbot_mcp/config.py` | Settings (pydantic-settings) |
| `docs/JAPANESE_LEARNING.md` | Japanese learning guide |
| `SPEC.md` | Architecture specification |

## Code Rules

- Python 3.12+, async-first, aiosqlite for DB
- FastMCP 3.4+ tool patterns
- pydantic-settings for config
- All learning tools are language-agnostic (source_lang/target_lang params)
- LLM calls Ollama or local-llm-mcp
