# Tool Reference

Full MCP tool reference for learnbot-mcp — 35 tools, verified against
`src/learnbot_mcp/server.py` (2026-07-18). If a tool isn't listed here, it
isn't registered.

## Personas

| Tool | Signature | What |
|------|-----------|------|
| `persona_create` | `name, display_name, backstory, voice, languages, skills, ...` | Create or update a chatbot persona |
| `persona_get` | `name` | Get a persona by name |
| `persona_list` | — | List all registered personas |
| `persona_delete` | `name` | Delete a persona |

## Conversations

| Tool | Signature | What |
|------|-----------|------|
| `chat_start` | `persona, user_id, ...` | Start a new conversation with a persona |
| `chat_send` | `conversation_id, content` | Send a message. Runs safety checks, then calls the LLM |
| `chat_hibernate` | `conversation_id` | Pause a conversation; state is preserved for later resume |
| `chat_resume` | `conversation_id` | Resume a hibernated conversation |
| `chat_destroy` | `conversation_id` | Permanently delete a conversation and all its turns |
| `chat_list` | `state_filter` | List conversations, optionally filtered by state (active/hibernating/completed) |
| `chat_proactive_tick` | — | Check all personas for due proactive triggers and fire them |

## Lessons

| Tool | Signature | What |
|------|-----------|------|
| `lesson_create` | `title, language, level, ...` | Create a lesson plan. Optionally generate with AI via `lesson_generate` |
| `lesson_generate` | `title, language, level` | Generate a complete lesson via AI — sections, vocab, quiz — and save it |
| `lesson_differentiate` | `lesson_id, level` | Adapt an existing lesson for a different JLPT level and save as a new lesson |
| `lesson_run` | `lesson_id, conversation_id` | Execute a lesson plan through an active conversation |
| `lesson_get` | `lesson_id` | Get a lesson plan by ID with full content |
| `lesson_list` | `language, level, tag, limit` | List lesson plans with optional filters |
| `lesson_update` | `lesson_id, title, level, language` | Update a lesson plan's title, level, or language |
| `lesson_delete` | `lesson_id` | Delete a lesson plan |

## Language learning (language-agnostic)

All accept `source_lang`/`target_lang` — not Japanese-only.

| Tool | Signature | What |
|------|-----------|------|
| `vocab_quiz` | `user_id, source_lang, count` | Generate a vocabulary quiz from items due for review (SM-2) |
| `vocab_submit` | `user_id, word, correct` | Submit a quiz result and update the spaced-repetition schedule |
| `grammar_check` | `text, source_lang, target_lang` | Check a learner's sentence for grammar errors and return corrections |
| `reading_passage` | `language, level, ...` | Generate a graded reading passage with comprehension questions |
| `graded_reader` | `language, level, target_lang, topic` | Generate a graded reader — leveled text + vocabulary + comprehension + discussion |

## Japanese reference data (bundled locally, no external calls)

| Tool | Signature | What |
|------|-----------|------|
| `kanji_search` | `q, jlpt, limit` | Search kanji by meaning, JLPT level, grade, or category |
| `vocab_lookup` | `search, jlpt, limit` | Look up Japanese vocabulary from JMdict or JLPT-graded lists |
| `jlpt_vocab_by_level` | `jlpt, limit` | Get a JLPT-graded vocabulary list for a specific level (N5–N1) |
| `example_sentences` | `word, limit` | Get example sentences for a Japanese word |
| `jlpt_quiz` | `level, limit` | Get JLPT practice questions for a given level (N5–N1) |

## Safety & audit

| Tool | Signature | What |
|------|-----------|------|
| `safety_rule_create` | `topic, action, message` | Create a safety rule — when a message matches the topic, the action triggers |
| `safety_rule_list` | — | List all safety rules |
| `safety_rule_delete` | `rule_id` | Delete a safety rule by ID |
| `audit_query` | `user_id, persona, ...` | Query the audit log, filtered by user_id, persona name, or time window |

## Platform & meta

| Tool | Signature | What |
|------|-----------|------|
| `platform_send` | `platform, content, ...` | Send content to a platform bridge (speech, discord, resonite) |
| `chatbot_help` | — | Show all available learnbot-mcp tools and usage |

---

Not MCP tools, but part of the same server:
- **REST API** (`learnbot_mcp.api`, port 11101) — serves the webapp, plus `/api/kanji/search`, `/api/vocab/lookup`, `/api/lesson/generate`, `/api/avatar.vrm`, and more. See `src/learnbot_mcp/api.py`.
- **Webapp** (React, port 11102 dev / served from 11101 in prod) — 12 pages: Dashboard, Personas, Chat, Safety, Audit, Compliance, Help, Voices, Avatar, Demos, Lessons, Japanese.
