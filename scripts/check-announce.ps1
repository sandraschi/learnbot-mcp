#Requires -Version 7.0
<#
.SYNOPSIS
  post-commit helper: detect major changes, draft an announce note, never auto-send.
.DESCRIPTION
  Called by .git/hooks/post-commit (best-effort, never fails the commit).
  Major = commit subject matches ^feat[(...)]?[!]?: AND touches a watched path
  (src/learnbot_mcp/, docs/TOOLS.md, webapp/public/ui-map.json, pyproject.toml).
  On major: writes reports/announce-draft-<sha>.md and prints the exact
  `just announce` command. No network, no send - human (or agent) reviews first.
#>
[CmdletBinding()]
param()

$ErrorActionPreference = 'Continue'  # never fail a commit

try {
  $repoRoot = Split-Path -Parent $PSScriptRoot
  Push-Location -LiteralPath $repoRoot

  $sha = (& git rev-parse --short HEAD 2>$null).Trim()
  $subject = (& git log -1 --pretty=%s 2>$null).Trim()
  $files = @(& git diff-tree --no-commit-id --name-only -r HEAD 2>$null)

  if ([string]::IsNullOrWhiteSpace($subject)) { Pop-Location; exit 0 }

  $isFeat = $subject -match '^feat(\(.+\))?!?:'
  $watch = @('src/learnbot_mcp/', 'docs/TOOLS.md', 'webapp/public/ui-map.json', 'pyproject.toml')
  $touchesWatch = $false
  foreach ($f in $files) {
    foreach ($w in $watch) {
      if ($f -eq $w -or $f.StartsWith($w)) { $touchesWatch = $true; break }
    }
    if ($touchesWatch) { break }
  }

  if (-not ($isFeat -and $touchesWatch)) { Pop-Location; exit 0 }

  $reportsDir = Join-Path $repoRoot 'reports'
  New-Item -ItemType Directory -Path $reportsDir -Force | Out-Null
  $draftPath = Join-Path $reportsDir "announce-draft-$sha.md"

  $touched = ($files | Select-Object -First 12) -join "`n- "
  $draft = @"
**learnbot-mcp update: $subject**

Commit: $sha
Major paths touched:
- $touched

TODO (edit before sending):
- 1-2 lines: what changed, why it matters
- Tool/route names + verification (ruff/tsc/pytest/diagnose counts)
- Phase/limits (pilot vs standard, what refuses honestly)

Channel: #fleet-learnbot (1558203571894362129)
"@
  Set-Content -LiteralPath $draftPath -Value $draft -Encoding utf8

  Write-Host ''
  Write-Host '[announce] Major change detected - draft written, NOT sent.' -ForegroundColor Yellow
  Write-Host "[announce] Edit: $draftPath" -ForegroundColor Yellow
  Write-Host '[announce] Preview:' -ForegroundColor Yellow
  Write-Host "  just announce-file-dry `"reports/announce-draft-$sha.md`"" -ForegroundColor Cyan
  Write-Host '[announce] Send (after editing):' -ForegroundColor Yellow
  Write-Host "  just announce-file `"reports/announce-draft-$sha.md`"" -ForegroundColor Green
  Write-Host ''
  Pop-Location
  exit 0
} catch {
  Write-Host "[announce] check skipped: $($_.Exception.Message)" -ForegroundColor DarkGray
  exit 0
}
