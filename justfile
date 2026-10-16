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
    cd webapp; bunx tsc --noEmit

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
    Set-Location native; npx @tauri-apps/cli build --bundles nsis

# Run CUA-NSIS smoke test
cua-nsis-test:
    uv run python scripts/cua-smoke.py

# Run E2E Playwright tests
e2e:
    cd webapp; npx playwright test

# Bootstrap: install dev deps + pre-commit hook + announce post-commit hook
bootstrap:
    uv sync --group dev
    uv run pre-commit install
    pwsh.exe -NoProfile -Command "Copy-Item '{{justfile_directory()}}\scripts\hooks\post-commit' '{{justfile_directory()}}\.git\hooks\post-commit' -Force; Write-Host 'Pre-commit + announce hooks installed.' -ForegroundColor Green"

# Run CUA webapp test (pre-Tauri: start.ps1 stack + nav walk in browser)
cua-webapp-test:
    powershell.exe -NoProfile -File "{{justfile_directory()}}\scripts\just\cua-webapp-test.ps1"

# Announce pilot -> #fleet-learnbot via local discord-mcp backend (no token in repo).
# Usage: just announce "hello fleet" / just announce-file "reports/announce-draft-abc.md"
# Channel override: set ANNOUNCE_CHANNEL env var (default: fleet-learnbot).
announce MSG:
    pwsh.exe -NoProfile -File "{{justfile_directory()}}\scripts\announce-discord.ps1" -Message '{{MSG}}'

announce-file FILE:
    pwsh.exe -NoProfile -File "{{justfile_directory()}}\scripts\announce-discord.ps1" -MessageFile '{{FILE}}'

# Preview without sending.
announce-dry MSG:
    pwsh.exe -NoProfile -File "{{justfile_directory()}}\scripts\announce-discord.ps1" -Message '{{MSG}}' -DryRun

announce-file-dry FILE:
    pwsh.exe -NoProfile -File "{{justfile_directory()}}\scripts\announce-discord.ps1" -MessageFile '{{FILE}}' -DryRun

# Install post-commit announce hook (one time per clone, best-effort, never fails commits).
install-announce-hook:
    pwsh.exe -NoProfile -Command "Copy-Item '{{justfile_directory()}}\scripts\hooks\post-commit' '{{justfile_directory()}}\.git\hooks\post-commit' -Force; Write-Host 'post-commit hook installed.' -ForegroundColor Green"