# Development Setup

## Tools Required

Install all of these before continuing:

```bash
# Windows (winget)
winget install astral-sh.uv
winget install Git.Git
winget install OpenJS.NodeJS
winget install Casey.Just

# Verify
uv --version
git --version
node --version
just --version
```

The webapp uses **bun** (not npm) as its script runner in Quick Start
examples, but `npm`/`vite` work too since `webapp/package.json` only
declares standard `vite` scripts (`dev`, `build`, `preview`) — bun isn't a
hard requirement, just what's used day to day.

## Setup

```bash
git clone https://github.com/sandraschi/learnbot-mcp
cd learnbot-mcp
uv sync

cd webapp
npm install   # or: bun install
```

## Common Tasks

```bash
just serve         # run the MCP server (stdio)
just serve-rest    # run the REST API (:11101) — webapp + /api/* routes
just lint          # ruff check src/
just fmt           # ruff format src/
just test          # pytest tests/ -q -v
just deps          # uv sync
just mcpb-pack      # build dist/learnbot-mcp.mcpb for Claude Desktop
```

Webapp dev server (hot reload, separate from the REST API):

```bash
cd webapp
npm run dev   # :11102, proxies /api to :11101
```

## Tests

```bash
uv run pytest tests/ -q -v
```

Test files: `test_persona.py`, `test_safety.py`, `test_learn_tools.py`,
`test_llm_client.py`, `test_regression.py`, `test_smoke.py`, `test_e2e.py`.

## Native / desktop build (optional)

The repo also ships a Tauri desktop wrapper (`native/`) with a PyInstaller
sidecar for the backend:

```bash
just build-sidecar   # PyInstaller exe via native/build.ps1
just build-native    # Tauri NSIS installer (requires build-sidecar first)
```

This is a separate distribution path from the MCP server / webapp — most
contributors won't need it.

## Code Standards

Python: `ruff` (line length 100, target py312), rule set `E, F, I, N, W,
SIM, UP` — see `pyproject.toml`. Async-first, `aiosqlite` for the database,
FastMCP 3.4+ tool patterns, `pydantic-settings` for config.

Fleet-wide standards live in
[mcp-central-docs/standards](https://github.com/sandraschi/mcp-central-docs/tree/master/standards),
including this repo's README structure requirements
([README_STRUCTURE.md](https://github.com/sandraschi/mcp-central-docs/blob/master/standards/README_STRUCTURE.md)).
