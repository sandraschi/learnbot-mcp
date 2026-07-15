#!/usr/bin/env pwsh
param([switch]$Headless, [switch]$NoFrontend)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSCommandPath
$BackendPort = 11101
$FrontendPort = 11102

# Port zombie clearing
Get-NetTCPConnection -LocalPort $BackendPort -ErrorAction SilentlyContinue |
    ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
Get-NetTCPConnection -LocalPort $FrontendPort -ErrorAction SilentlyContinue |
    ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }

# Start backend (REST API)
$BackendJob = Start-Job -Name "chatbot-backend" -ScriptBlock {
    param($Root)
    Set-Location $Root
    uv run python -m chatbot_mcp.api
} -ArgumentList $Root

# Readiness poll
Write-Host "Waiting for backend on port $BackendPort..."
for ($i = 0; $i -lt 30; $i++) {
    try {
        $r = Invoke-WebRequest -Uri "http://127.0.0.1:$BackendPort/health" -TimeoutSec 2 -UseBasicParsing -ErrorAction SilentlyContinue
        if ($r.StatusCode -eq 200) { Write-Host "Backend ready."; break }
    } catch {}
    Start-Sleep 1
}

# Start frontend
if (-not $NoFrontend) {
    $WebRoot = Join-Path $Root "web_sota"
    Start-Process -NoNewWindow -FilePath "bun" -ArgumentList "run dev" -WorkingDirectory $WebRoot
    Start-Sleep 3
    if (-not $Headless) { Start-Process "http://127.0.0.1:$FrontendPort" }
}

Write-Host "chatbot-mcp running:"
Write-Host "  Backend API: http://127.0.0.1:$BackendPort"
Write-Host "  Frontend:    http://127.0.0.1:$FrontendPort"

# Keep-alive
while ($true) {
    if ($BackendJob.State -in @("Completed", "Failed")) {
        Receive-Job $BackendJob; break
    }
    Start-Sleep 2
}
