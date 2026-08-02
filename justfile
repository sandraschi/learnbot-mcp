set windows-shell := ["powershell.exe", "-NoProfile", "-Command"]

# learnbot-mcp recipes
default: serve

# Run the MCP server (stdio)
serve:
    uv run python -m learnbot_mcp

# Run the REST API (for health checks, fleet hub)
serve-rest:
    uv run python -m learnbot_mcp.api

# Run lint
lint:
    uv run ruff check src/

# Run formatter
fmt:
    uv run ruff format src/

# Run tests
test:
    uv run pytest tests/ -q -v

# CI parity: lint + format check + tests + frontend typecheck
ci:
    uv run ruff check src/
    uv run ruff format src/ --check
    uv run pytest tests/ -q
    cd webapp && bunx tsc --noEmit

# Sync deps
deps:
    uv sync

# Build the MCPB bundle for Claude Desktop
mcpb-pack:
    mcpb pack . dist/learnbot-mcp.mcpb

# Build the PyInstaller backend exe
build-sidecar:
    powershell.exe -NoProfile -File native\build.ps1

# Build the Tauri NSIS desktop installer
build-native: build-sidecar
    Set-Location native
    npx @tauri-apps/cli build --bundles nsis

# Run CUA-NSIS smoke test
cua-nsis-test:
    uv run python scripts/cua-smoke.py

# Run E2E Playwright tests
e2e:
    cd webapp && npx playwright test

# Bootstrap: install dev deps + pre-commit hook
bootstrap:
    uv sync --group dev
    uv run pre-commit install
    Write-Host "Pre-commit hooks installed." -ForegroundColor Green