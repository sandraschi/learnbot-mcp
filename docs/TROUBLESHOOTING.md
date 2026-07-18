# Troubleshooting

## Server doesn't appear in Claude Desktop
**Cause**: Config JSON is malformed
**Fix**: Validate at jsonlint.com, check for trailing commas. Confirm the
`--directory` path in your config points at the actual repo location.

## "command not found: uv"
**Cause**: uv not installed or not in PATH
**Fix**: `winget install astral-sh.uv` then restart your terminal.

## Lesson generation / grammar check / reading passage returns an error
**Cause**: These tools call out to an LLM (`local-llm-mcp` or Ollama, via
`LEARNBOT_LLM_BASE_URL`, default `http://127.0.0.1:10832`). If nothing is
listening there, generation fails.
**Fix**: Start `local-llm-mcp` or point `LEARNBOT_LLM_BASE_URL` at a running
Ollama instance (`http://127.0.0.1:11434`) and set `LEARNBOT_LLM_MODEL` to
a model you've pulled.

## LLM responses fail to parse as JSON
**Cause**: Some LLMs wrap JSON output in explanatory prose instead of
returning bare JSON, especially smaller local models.
**Fix**: This is handled internally (`_clean_llm_json()` /
`_extract_json_array()` strip prose wrapping) as of v0.4.1. If you still
hit this, it's likely a new prose pattern the parser doesn't recognize yet
— file it, don't assume the tool itself is broken.

## Avatar page shows no VRM model
**Cause**: `GET /api/avatar.vrm` reads the `avatar_vrm` path from the
active persona. If the persona has none set, it falls back to a hardcoded
path: `D:/Dev/repos/avatar-mcp/models/Nekomimi-chan.vrm`. If that file
doesn't exist on your machine, the endpoint returns a 404 and the viewer
shows nothing.
**Fix**: Either place a `.vrm` file at that fallback path, or set
`avatar_vrm` explicitly when creating/updating the persona
(`persona_create(..., avatar_vrm="C:/path/to/your.vrm")`).

## Japanese page: "games-app not reachable"
**Cause**: The built-in dictionary/kanji search (top of `/japanese`) does
**not** need this — it queries local SQLite files directly. This warning
only affects the 11 linked extra-practice games (kanji-master, flashcards,
karuta, etc.), which live in a separate `games-app` repo/process on port
`10987`.
**Fix**: If you want the extra games, start `games-app` separately. If you
just want the dictionary/kanji/JLPT-quiz tools, ignore this warning — they
already work.

## TTS doesn't speak (no audio)
**Cause**: `platform_send`/proactive speech first tries `speech-mcp`
(`LEARNBOT_SPEECH_MCP_URL`, default `http://127.0.0.1:10909`). If that's
unreachable, it falls back to Windows SAPI5 via PowerShell — this fallback
only works on Windows and only as a last resort (lower voice quality, no
emotion prosody).
**Fix**: Start `speech-mcp` for full quality (Gemini TTS with emotion
prosody). On non-Windows without `speech-mcp`, there's currently no
fallback.

## Port already in use (11101 / 11102)
**Cause**: Another process is already bound to the backend (11101) or
frontend dev (11102) port — possibly a previous unclosed learnbot-mcp
instance.
**Fix**: `netstat -ano | findstr :11101` (Windows) to find the PID, then
stop it, or override `BACKEND_PORT`/`FRONTEND_PORT` in `.env`.

## Tests fail with import errors
**Cause**: Dependencies not synced, or running from the wrong directory.
**Fix**: `uv sync` from the repo root, then `uv run pytest tests/ -q -v`
(not bare `pytest` — the `uv run` prefix ensures the right environment).
