# chatbot-mcp recipes
default: serve

# Run the MCP server (stdio)
serve:
    uv run python -m chatbot_mcp

# Run the REST API (for health checks, fleet hub)
serve-rest:
    uv run python -m chatbot_mcp.api

# Run lint
lint:
    uv run ruff check src/

# Run formatter
fmt:
    uv run ruff format src/

# Run tests
test:
    uv run pytest tests/ -q -v

# Sync deps
deps:
    uv add uvicorn starlette
    uv sync
