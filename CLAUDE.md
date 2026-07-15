## Session Context (LearnBot MCP)

You have access to a chatbot orchestrator with persona management, conversation lifecycle, safety guardrails, and multi-platform output (speech, opencode).

**Before starting work:**
1. Check personas: persona_list()
2. Review safety rules: safety_rule_list()
3. Check server health: GET /api/health on :11101

**Key tools:**
- persona_create/delete - manage chatbot personas
- chat_start/send - run conversations with safety checks
- safety_rule_create - add topic blocking
- audit_query - review all conversation turns
- platform_send - dispatch to speech, future platforms
