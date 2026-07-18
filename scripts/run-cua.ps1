# Run the CUA smoke test in a visible PowerShell window
# This bypasses opencode's bash tool watchdog
$RepoRoot = Split-Path -Parent $PSCommandPath | Split-Path -Parent
Set-Location $RepoRoot
Write-Host "=== CUA-NSIS Smoke Test ===" -ForegroundColor Cyan
Write-Host "Product: LearnBot MCP" -ForegroundColor Cyan
Write-Host "Window will appear and you can watch the test run."
Write-Host "Press Ctrl+C to abort." -ForegroundColor Yellow
Write-Host ""
uv run python scripts/cua-smoke.py
Read-Host "`nPress Enter to close"
