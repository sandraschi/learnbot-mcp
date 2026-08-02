# Japanese Learning — Full-Spectrum Language Acquisition

**learnbot-mcp** is not a JLPT prep tool. It is a **full-spectrum Japanese learning environment** that covers all four language skills — reading, writing, speaking, and listening — plus kanji acquisition, grammar, and cultural context. The JLPT covers two (reading, listening) with multiple-choice questions only. This system covers all four with active production, feedback loops, and personalized spaced repetition.

## Skills Coverage

| Skill | JLPT N5-N1 | learnbot-mcp |
|-------|-----------|-------------|
| **Reading** | Multiple-choice kanji/vocab/grammar recognition | `reading_passage` (JLPT-graded full texts), `lesson_run` (interactive curriculum), ai-games-collection Kanji Master/table/flashcards |
| **Listening** | Canned audio, multiple-choice | TTS via speech-mcp (20+ Gemini voices with emotion prosody), `japanese-listening.html` game |
| **Speaking** | **Not tested at any level** | Live conversation with Miko-chan (bilingual JA/EN persona), `grammar_check` for corrective feedback, `vocab_quiz` for recall practice |
| **Writing** | **Not tested at any level** | Chat composition (free-form output), `grammar_check` analyses sentences, lesson exercises require constructed responses |

**Key insight**: A learner can pass JLPT N1 with zero speaking or writing ability. learnbot-mcp fills that gap by demanding **production** — the user must construct sentences, hold conversations, and actively recall vocabulary, not just recognise the correct bubble.

## Learning Tools

### Conversation (Speaking + Writing)
The core learning loop is conversation with a bilingual persona (Miko-chan, JA/EN). Every chat turn is a speaking/writing exercise with immediate contextual feedback.

- `chat_start(persona="miko", ...)` — begin a session
- `chat_send(conversation_id, content, ...)` — produce Japanese text, get a natural response
- Emotion tags drive TTS prosody — the persona's voice reflects mood, making conversation feel real
- `grammar_check(text, source_lang="ja")` — analyse a sentence, return corrections, rule explanation, and estimated JLPT level

### Reading (Passages + Lessons)
- `reading_passage(level="N4")` — generate a JLPT-graded text (~100-200 words) with furigana, vocabulary list, and comprehension questions
- `lesson_generate(title="...")` — create a full lesson plan (sections, vocab, quiz)
- `lesson_run(lesson_id, conversation_id)` — inject lesson into a conversation as active curriculum
- `lesson_differentiate(lesson_id, target_level="N5")` — adapt any lesson for a different JLPT level

### Vocabulary (Spaced Repetition)
- `vocab_quiz(user_id, count=5)` — SM-2 spaced repetition quiz, pulls due items + LLM-generated fresh items
- `vocab_submit(user_id, word, correct=True/False)` — submit result, schedule next review
- `vocab_lookup(jlpt="N5")` — browse authentic JLPT-graded vocabulary from JMdict (214K entries)
- `kanji_search(jlpt="N5")` — search jouyou kanji by level, grade, meaning, or category

### Kanji
- ai-games-collection kanji master — reading/meaning drill with spaced repetition, stroke order animation
- kanji table — filterable reference by JLPT level, grade, stroke count, category
- kanji 3D visualiser — spatial exploration of the kanji cosmos

### Listening
- Gemini TTS with emotion prosody — voices speak naturally with context-appropriate tone
- Japanese listening game — Web Speech API `ja-JP` audio with comprehension checks

## Workflow: From Absolute Beginner to Conversational

### Phase 1 — Foundation (kana + basic vocab)
1. Hiragana/Katakana mastery via `games/educational/hiragana-katakana.html`
2. `vocab_quiz` for basic vocabulary with SM-2 spaced repetition
3. Short greetings with Miko-chan (`chat_start(persona="miko")`)

### Phase 2 — Structured Lessons
1. `lesson_generate(title="te-form grammar")` — generate a lesson
2. `lesson_run(lesson_id, conversation_id)` — inject into chat, Miko-chan teaches it
3. `grammar_check` on sentences the user constructs during the lesson

### Phase 3 — Reading + Listening
1. `reading_passage(level="N4")` — graded text + comprehension questions
2. ai-games-collection JLPT practice tests per level
3. Listening practice with TTS + Japanese listening game

### Phase 4 — Active Production
1. Free conversation with Miko-chan on any topic
2. `grammar_check` for corrective feedback on complex sentences
3. `vocab_quiz` for long-term retention via spaced repetition
4. `lesson_differentiate` to push to higher JLPT levels

## Compared to JLPT

| Aspect | JLPT | learnbot-mcp |
|--------|------|-------------|
| Speaking | Never tested | Core interaction mode |
| Writing | Never tested | Chat composition + grammar analysis |
| Listening | Pre-recorded audio, multiple-choice | Natural TTS with emotion prosody |
| Reading | Multiple-choice comprehension | Full texts with furigana, interactive lessons |
| Vocabulary | Recognition only | Active recall via SM-2 + conversation |
| Grammar | Recognition only | Production + corrective feedback |
| Feedback | Score report | Immediate per-sentence analysis |
| Personalisation | None | SM-2 spaced repetition, adaptive JLPT levels |
| Cost | ~$80/attempt | Free (Ollama local LLM) |

## Data Sources (bundled locally, see data/ATTRIBUTION.md)

| Source | Entries | Used for |
|--------|---------|----------|
| JMdict/EDICT2 | 214K | Dictionary lookups, example generation |
| JLPT vocabulary | 8K | Level-graded word lists (710 N5 + 666 N4 + 2103 N3 + ...) |
| Jouyou kanji | 13K | Kanji search, readings, meanings, stroke order |
| Tatoeba sentences | 278K | Example sentences per word |
| JLPT practice questions | 600 | N5-N1 format practice |

## MCP Tools Quick Reference

```
# Start a learning session
lesson_generate(title="basic keigo", level="N4")
lesson_run(lesson_id=1, conversation_id="abc")
chat_send(conversation_id="abc", content="I don't understand when to use です vs ます")

# Check a sentence
grammar_check(text="私は昨日に映画を見た", source_lang="ja")

# Practice vocab
vocab_quiz(user_id="sandra", count=5)
vocab_submit(user_id="sandra", word="映画", correct=True)

# Browse data
kanji_search(jlpt="N5", limit=10)
vocab_lookup(search="食べる")
example_sentences(word="食べる")

# JLPT practice
jlpt_quiz(level="N4", limit=5)

# Reading practice
reading_passage(level="N4")
```

## Configuration

Requires Ollama running locally (default model `llama3.2:3b`) for LLM-based tools
(chat, grammar_check, lesson_generate, reading_passage).

Dictionary, kanji, and JLPT tools (`kanji_search`, `vocab_lookup`,
`jlpt_vocab_by_level`, `example_sentences`, `jlpt_quiz`) need no external
service — they query `data/kanji.db` and `data/jlpt_questions.db` directly,
bundled snapshots of ai-games-collection's reference data (JMdict, jouyou kanji, JLPT
vocab, Tatoeba sentences). See [data/ATTRIBUTION.md](../data/ATTRIBUTION.md)
for sources and licensing, and re-copy from `ai-games-collection/data/` if you want to
refresh the snapshot.

The webapp's Japanese page also links out to ai-games-collection's own interactive
practice games (kanji flashcards, JLPT test format, karuta, etc.) — those
are optional and require ai-games-collection running separately on :10987; they are
not needed for any of the tools above.

## See Also

- [README.md](../README.md) — Quick start
- [SPEC.md](../SPEC.md) — Architecture
- [DISTANCE_LEARNING.md](DISTANCE_LEARNING.md) — Classroom + teaching agent architecture
- [chatbot-ethics.md](chatbot-ethics.md) — Ethics of AI language tutors
