# Installing learnbot-mcp

## Prerequisites

Install these if you don't have them already:

| Tool | Purpose | Install |
|------|---------|---------|
| Claude Desktop | Required host | [download](https://claude.ai/download) |
| Git | Clone repo | `winget install Git.Git` |
| Python + uv | Run server | `winget install astral-sh.uv` |
| Node.js | webapp + mcpb CLI (Option B, or webapp dev) | `winget install OpenJS.NodeJS` |

> Windows: all installs via [winget](https://learn.microsoft.com/en-us/windows/package-manager/winget/)
> macOS: use `brew install` equivalents
> Linux: use your distro package manager

**LLM backend required for AI features.** `lesson_generate`,
`grammar_check`, and `reading_passage` call out to an LLM. Either run
[local-llm-mcp](https://github.com/sandraschi/local-llm-mcp) (default) or
point `LEARNBOT_LLM_BASE_URL` at your own Ollama/cloud endpoint — see
[docs/CONFIGURATION.md](docs/CONFIGURATION.md). The dictionary/kanji/JLPT
tools (`kanji_search`, `vocab_lookup`, `jlpt_quiz`, etc.) are local SQLite
lookups and need no LLM at all.

## Option A — Drag and Drop (.mcpb)

1. Go to [Releases](https://github.com/sandraschi/learnbot-mcp/releases/latest)
2. Download `learnbot-mcp-{version}.mcpb`
3. Open Claude Desktop → drag the file onto the window
   *Or*: Settings → MCP Servers → Install from file

> **Not yet verified from this pass**: whether a `.mcpb` release is
> currently published for this repo. The build recipe exists
> (`just mcpb-pack` → `dist/learnbot-mcp.mcpb`) but nobody has confirmed a
> GitHub Release is live. If the Releases page is empty, use Option C below
> — it's what's actually been tested day to day.

## Option B — mcpb CLI

```bash
# Requires Node.js (see Prerequisites)
npx @anthropic-ai/mcpb install https://github.com/sandraschi/learnbot-mcp
```

## Option C — Manual Configuration (recommended today)

1. Clone: `git clone https://github.com/sandraschi/learnbot-mcp`
2. Install deps: `cd learnbot-mcp && uv sync`
3. Add to Claude Desktop config:

```json
{
  "mcpServers": {
    "learnbot-mcp": {
      "command": "uv",
      "args": ["run", "--directory", "C:\\path\\to\\learnbot-mcp", "python", "-m", "learnbot_mcp"]
    }
  }
}
```

Config file location:
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`

4. Restart Claude Desktop

## Option D — Developer Mode

For contributing, running the webapp, or running from source with live
reload. See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md).

```bash
uv sync
uv run python -m learnbot_mcp.api   # REST API + webapp, :11101

cd webapp
npm install
npm run dev                          # webapp dev server, :11102
```

Or double-click `start.bat`.

## Verify Installation

After installing, open Claude Desktop and type:
> "List the personas registered in learnbot-mcp."

You should see a tool call to `persona_list` and a (possibly empty) list
of personas back.

To check the webapp side, open `http://127.0.0.1:11101/` after starting
the REST API — you should land on the Dashboard with a sidebar linking to
Personas, Chat, Avatar, Lessons, Japanese, and more.

## Troubleshooting

See [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) for common issues.
