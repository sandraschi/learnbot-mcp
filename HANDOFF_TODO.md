# learnbot-mcp — Handoff Notes for DeepSeek

**Updated**: 2026-07-16 (second pass). Original handoff below was worked
through almost completely — see "Closed since last handoff" first, it's
short. New findings are in "Open now."

## Closed since last handoff (verified, don't redo)

Everything in the original handoff got fixed, and fixed well:

- Duplicate `lesson_get`/`lesson_delete`/`lesson_run` registration — gone,
  guarded now by `test_regression.py::TestNoDuplicateToolRegistration`
  (AST-based, walks `server.py` for `@mcp.tool()` decorators, asserts no
  name appears twice). Read it — it's a good pattern, reusable elsewhere.
- `lesson_run` → `chat_send` wiring — confirmed working via
  `TestLessonRoundTrip`, which actually asserts on the `conversations.metadata`
  DB row rather than just checking the function returns something.
- `vocab_quiz` `Row.get()` crash, `_generate_distractors` missing f-string —
  both fixed and both have dedicated regression tests now
  (`TestVocabQuizDueItem`, `TestGenerateDistractors`).
- `{overdue_count}` in `proactive.py` — now a real `COUNT(*) WHERE due_at
  <= now` query against `vocab_items`.
- STATUS.md port (11104 → 11101), TODO.md's contradictory checkboxes,
  version drift — all fixed.
- LLM JSON-extraction bugs found along the way (prose-wrapped JSON from
  `_generate_fresh_quiz`, `grammar_check`, `reading_passage`,
  `lesson_generate`, `lesson_differentiate`) — fixed with shared
  `_clean_llm_json()` / `_extract_json_array()` helpers. Good call
  centralizing that instead of patching each call site separately.

Net: 0.3.0 → 0.4.0 → 0.4.1 → 0.5.0 in one stretch, with real fixes and real
tests, not just version bumps. This handoff-doc pattern (write what's known,
let the next session work off it) is producing good results — keep doing it.

## New since last handoff

`games_integration.py` — connects to games-app's kanji-api/jlpt-api for real
JMdict/JLPT/Tatoeba data (kanji search, vocab lookup, example sentences,
JLPT quiz questions) instead of LLM-hallucinated vocab. Good addition —
verified 4 of 5 functions are wired as MCP tools and use real data with
sane connection-error handling.

`lesson_differentiate` — adapts an existing lesson to a different JLPT
level, saves as a new lesson, leaves the original untouched. Reviewed:
clean, goes through `_row_to_lesson()` so no `Row.get()` risk.

`framework` parameter on `lesson_generate`/`reading_passage` — CEFR, HSK,
DELF, DELE, Goethe, not just JLPT. This generalizes the whole tool past
Japanese-only, which matters given classroom-mcp now has multi-language
students/classes.

classroom-mcp's `assignment_create_with_lesson` — calls learnbot-mcp's
lesson_generate to back an assignment with real content. **Was broken by
two independent bugs, both fixed just now:**
- `classroom-mcp/config.py`'s `LEARNBOT_URL` default was `11104`, but
  learnbot-mcp actually runs on `11101` (same port-drift class of bug as
  the STATUS.md one above — one repo's port convention changed, the other
  repo's hardcoded reference to it didn't follow). Fixed.
- The call hit `/api/lessons/generate` (plural); the real route is
  `/api/lesson/generate` (singular). Fixed.
- **Fixed**: the call used to swallow all failures (`except Exception:
  pass`, non-200 treated same as connection error) and report `success:
  True` with `lesson_id: 0` regardless. Now returns `success: False` with
  a specific error, and doesn't create the assignment at all if lesson
  generation fails — the tool's contract is "assignment WITH lesson," so
  a bare assignment isn't a partial success.

## Open now

- **`jlpt_vocab_by_level` in `games_integration.py` has no `@mcp.tool()`
  wrapper.** Its four siblings (`kanji_search`, `vocab_lookup`,
  `example_sentences`, `jlpt_quiz`) are all registered in `server.py`;
  this one isn't. Dead code until it's wired in — quick fix, same pattern
  as the other four.
- **Cross-repo URL/port hardcoding is now a recurring bug class**, not a
  one-off: STATUS.md's port, and now classroom-mcp's `LEARNBOT_URL`
  default, both drifted after the other side changed. Worth considering
  a single source of truth for service ports (mcp-central-docs'
  `WEBAPP_PORTS.md` already exists — worth actually reading defaults from
  there, or at minimum cross-checking new hardcoded URLs against it before
  they ship) rather than catching each instance by hand.
- **Test coverage still hasn't reached `robot_orchestrator.py`,
  `soundscape.py`, `proactive.py`, or `compliance.py`.** `learn_tools.py`
  now has `test_learn_tools.py` and the regression suite covers the specific
  bugs found — good — but these four modules are still zero-coverage.
  Mechanical, same as before: pick one, write a happy-path + one edge case.
- **No `lesson_end` tool** — an active lesson (set via `lesson_run`)
  persists in a conversation's metadata until another `lesson_run`
  overwrites it or the conversation ends. Fine for now, but if a lesson
  needs to be paused/exited mid-conversation there's no way to do that.

## Architecture idea (still not a mandate)

Same note as last time: `classroom-mcp` splitting off and delegating back
via `LEARNBOT_URL` proved the split pattern works — and also just proved
its main risk (the two repos' assumptions about each other's ports/routes
silently diverging). If a third repo ever depends on either of these,
that risk compounds. Worth deciding whether inter-repo URLs get resolved
from a shared config source before that happens, rather than after.

## Process note

Second handoff in a row where nothing got silently reverted or redone —
the fixes and the regression tests survived intact and were built on
rather than duplicated. Whatever the coordination between sessions looks
like right now, it's working. Keep writing to this file before ending a
session, even briefly.
