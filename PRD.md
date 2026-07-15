# learnbot-mcp - PRD

**Status**: Draft  
**Date**: 2026-07-15  
**Owner**: Sandra Schipal

## Problem

Running a chatbot today means stitching together an LLM, a TTS engine, an avatar renderer, a memory system, and safety guardrails - every time. There is no single MCP server that owns the **chatbot domain**: persona management, conversation lifecycle, multi-platform output, and regulatory compliance.

## Product Vision

One MCP server that lets you define a chatbot persona once, then spawn it across Resonite (as a visible avatar), Discord, web chat, or TTS phone call - with built-in safety guardrails and regulatory compliance.

## Scope

### In scope (learnbot-mcp owns)

- **Persona definition**: YAML/JSON schema - name, backstory, voice, avatar, behavioral constraints, knowledge base
- **Conversation lifecycle**: spawn, run, hibernate, destroy - state persisted to SQLite
- **Safety guardrails**: content filter, topic denial, rate limiting, conversation logging for audit
- **Multi-platform output**: Resonite (visible avatar + gestures), Discord, web chat, TTS call
- **Regulatory compliance**: configurable - China real-name auth, conversation retention, refusal templates; EU AI Act; or unconstrained
- **Proactive chat**: bot can initiate conversation based on triggers (time, event, context)

### Out of scope (delegates to fleet infra)

- **LLM inference**: delegates to `local-llm-mcp` or cloud providers
- **TTS/STT**: delegates to `speech-mcp`
- **Avatar rendering/VRM**: delegates to `avatar-mcp`
- **Resonite world state**: delegates to `resonite-mcp`
- **Long-term memory / RAG**: delegates to `advanced-memory-mcp`

## User Stories

1. As Sandra, I define a chatbot persona (name, voice, backstory) and spawn it as a visible avatar in my Resonite home.
2. As Sandra, the same persona can chat via Discord DMs without losing context.
3. As Sandra, all conversations are logged with timestamps and can be audited.
4. As Sandra, the bot refuses topics I configure (gore, politics, etc.) with configurable refusal messages.
5. As Sandra, the bot can proactively start a conversation ("Good morning, your TBR pile has 3 items due").
6. As a fleet user, I deploy learnbot-mcp in China-compliant mode - real-name auth, 30-day retention, topic blocklist.

## Success Metrics

- Persona definition created and modified via MCP tools
- Chatbot instance spawns and persists across server restarts
- Conversation flows across platforms (Resonite → same persona on Discord)
- Audit log captures every turn with requestor identity
- Safety rules block configured topics with logged refusal
