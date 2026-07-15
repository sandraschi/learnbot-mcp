import { useState } from "react";
import { Info, Shield, BookOpen, FileText, MessageCircle } from "lucide-react";

const tabs = [
  {
    id: "about",
    label: "About",
    icon: Info,
    content: `## chatbot-mcp

An AI chatbot orchestrator — define personas, run conversations with safety guardrails, speak via TTS, and audit every turn.

### Architecture

\`\`\`
chatbot-mcp → Ollama (LLM)
            → speech-mcp / Windows SAPI5 (TTS)
            → SQLite (conversations, audit)
            → React webapp
\`\`\`

### Ports
- Backend API: :11101
- Frontend: :11102 (Vite dev)`,
  },
  {
    id: "personas",
    label: "Personas",
    icon: MessageCircle,
    content: `## Personas

A persona is a chatbot character definition. Create one with a name, backstory, voice, and optional proactive triggers.

### Fields
- **name**: unique identifier
- **display_name**: shown in chat UI
- **backstory**: system prompt that defines personality
- **voice**: TTS voice ID (e.g. "heart", "sky")
- **platforms**: where this persona appears
- **proactive_triggers**: JSON array of scheduled messages

### Example
\`\`\`
persona_create(name="miko", display_name="Miko-chan",
  backstory="You are a cheerful assistant...", voice="heart")
\`\`\``,
  },
  {
    id: "safety",
    label: "Safety",
    icon: Shield,
    content: `## Safety Guardrails

Every message passes through safety checks before reaching the LLM.

### Rules
- **Topic blocking**: refusals for configured topics (politics, gore, etc.)
- **Rate limiting**: max messages per minute per user
- **PII redaction**: emails, phone numbers, credit cards stripped
- **Regulatory compliance**: China real-name auth, EU transparency

### Compliance regimes
Set \`CHATBOT_REGULATORY_REGIME\` in .env:
- \`none\`: no extra restrictions
- \`china\`: real-name auth, topic blocklists, retention
- \`eu\`: AI disclosure, opt-out, full logging`,
  },
  {
    id: "ethics",
    label: "Ethics",
    icon: BookOpen,
    content: `## Ethics

Chatbots can cause harm through addiction pathways, emotional manipulation, and privacy violations.

### Key risks
- **Pseudohuman attachment**: users form real emotional bonds with synthetic entities
- **Active solicitation**: proactive chat can create guilt-based engagement loops
- **Data permanence**: conversations persist, can be leaked or subpoenaed
- **Regulatory gaps**: most of the world has no chatbot-specific laws

See \`docs/chatbot-ethics.md\` for the full discussion including the history of ELIZA to GPT-5, the addiction gradient, vulnerable populations, and regulatory comparison (China vs EU vs unregulated).`,
  },
  {
    id: "api",
    label: "API",
    icon: FileText,
    content: `## REST API

All endpoints on http://127.0.0.1:11101

### Personas
- \`GET /api/personas\` — list all
- \`POST /api/personas\` — create
- \`GET /api/personas/{name}\` — get
- \`DELETE /api/personas/{name}\` — delete

### Conversations
- \`POST /api/conversations\` — start
- \`POST /api/conversations/{id}/send\` — send message
- \`POST /api/conversations/{id}/hibernate\` — pause
- \`POST /api/conversations/{id}/resume\` — resume
- \`DELETE /api/conversations/{id}\` — delete

### Safety & Audit
- \`GET /api/safety/rules\` — list rules
- \`POST /api/safety/rules\` — add rule
- \`DELETE /api/safety/rules/{id}\` — remove
- \`GET /api/audit\` — query audit log

### System
- \`GET /api/health\` — server health
- \`GET /api/compliance\` — compliance config
- \`POST /api/chat/proactive-tick\` — fire due triggers`,
  },
];

export function Help() {
  const [active, setActive] = useState(tabs[0].id);

  const tab = tabs.find((t) => t.id === active);
  return (
    <div data-testid="help-page">
      <h1 className="text-xl font-bold mb-4">Help</h1>
      <div className="flex gap-1 border-b border-zinc-800 mb-4 overflow-x-auto">
        {tabs.map((t) => (
          <button
            key={t.id}
            onClick={() => setActive(t.id)}
            className={`flex items-center gap-1.5 px-4 py-2 text-sm font-medium whitespace-nowrap border-b-2 transition-colors ${
              active === t.id
                ? "border-amber-500 text-amber-500"
                : "border-transparent text-zinc-500 hover:text-zinc-300"
            }`}
          >
            <t.icon className="w-4 h-4" />
            {t.label}
          </button>
        ))}
      </div>
      <div className="prose prose-invert max-w-none">
        {tab ? (
          <div className="text-sm leading-relaxed whitespace-pre-wrap font-mono text-zinc-300">
            {tab.content}
          </div>
        ) : (
          <div className="text-zinc-500">Select a tab.</div>
        )}
      </div>
    </div>
  );
}
