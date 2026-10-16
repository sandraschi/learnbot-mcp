#Requires -Version 7.0
<#
.SYNOPSIS
  Post a message to a Discord channel via discord-mcp backend (pilot: fleet-learnbot).
.DESCRIPTION
  Thin wrapper over discord-mcp HTTP: POST /api/v1/channels/{id}/messages
  with {"content": "..."}. No token in repo - relies on local discord-mcp
  backend (default http://127.0.0.1:10756, NSSM service 'discord-mcp').
  Auto-chunks content over 1900 chars on newline boundaries (Discord cap 2000).
.PARAMETER Message
  Inline message text (ASCII, hyphens only - no em dashes).
.PARAMETER MessageFile
  Path to a text file to send instead of -Message.
.PARAMETER ChannelId
  Defaults to #fleet-learnbot.
.PARAMETER BackendUrl
  discord-mcp backend base URL.
.PARAMETER DryRun
  Print chunks without POSTing.
.EXAMPLE
  .\scripts\announce-discord.ps1 -Message "hello fleet" -DryRun
  .\scripts\announce-discord.ps1 -MessageFile reports/announce-draft-abc123.md
#>
[CmdletBinding()]
param(
  [string]$Message = '',
  [string]$MessageFile = '',
  [string]$ChannelId = '1558203571894362129',
  [string]$BackendUrl = 'http://127.0.0.1:10756',
  [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if ([string]::IsNullOrWhiteSpace($ChannelId) -or $ChannelId -eq '1558203571894362129') {
  $envOverride = $env:ANNOUNCE_CHANNEL
  if (-not [string]::IsNullOrWhiteSpace($envOverride)) { $ChannelId = $envOverride }
}

$text = $Message
if ($MessageFile -ne '') {
  if (-not (Test-Path -LiteralPath $MessageFile)) { throw "MessageFile not found: $MessageFile" }
  $text = Get-Content -LiteralPath $MessageFile -Raw -Encoding utf8
}
if ([string]::IsNullOrWhiteSpace($text)) { throw 'Nothing to send: pass -Message or -MessageFile.' }

# ASCII hygiene: normalize em/en dashes, smart quotes.
$text = $text -replace "`u{2014}", '-' -replace "`u{2013}", '-' -replace "`u{201C}", '"' -replace "`u{201D}", '"' -replace "`u{2018}", "'" -replace "`u{2019}", "'"

# Chunk on newlines to stay under Discord 2000 cap (use 1900 for safety).
$chunks = @()
$current = ''
foreach ($line in ($text -split "`r?`n")) {
  $candidate = if ($current -eq '') { $line } else { "$current`n$line" }
  if ($candidate.Length -gt 1900 -and $current -ne '') {
    $chunks += $current
    $current = $line
  } else {
    $current = $candidate
  }
}
if ($current -ne '') { $chunks += $current }

Write-Host "Channel: $ChannelId | Chunks: $($chunks.Count) | Backend: $BackendUrl" -ForegroundColor Cyan
for ($i = 0; $i -lt $chunks.Count; $i++) {
  $preview = $chunks[$i].Substring(0, [Math]::Min(120, $chunks[$i].Length))
  Write-Host "--- chunk $($i + 1)/$($chunks.Count) ($($chunks[$i].Length) chars): $preview..." -ForegroundColor DarkGray
  if ($DryRun) { continue }
  $uri = "$BackendUrl/api/v1/channels/$ChannelId/messages"
  $body = @{ content = $chunks[$i] } | ConvertTo-Json -Depth 2
  try {
    $resp = Invoke-RestMethod -Method Post -Uri $uri -ContentType 'application/json' -Body $body -TimeoutSec 20
    Write-Host "Sent chunk $($i + 1): message_id=$($resp.message_id)" -ForegroundColor Green
  } catch {
    Write-Error "POST failed for chunk $($i + 1): $($_.Exception.Message)"
  }
  if ($i -lt $chunks.Count - 1) { Start-Sleep -Seconds 6 }  # respect per-channel 3/min limit
}
