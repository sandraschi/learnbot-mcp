$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$ResourceDir = "$PSScriptRoot\resources"
$DevDir = "$PSScriptRoot\binaries"
$Triple = "x86_64-pc-windows-msvc"
New-Item -ItemType Directory -Force -Path $ResourceDir, $DevDir | Out-Null

Write-Host "=== learnbot-mcp Tauri Release Build ===" -ForegroundColor Cyan

# Step 1: Frontend build
Write-Host "-> [1/4] Building frontend..." -ForegroundColor Yellow
$frontend = Join-Path $Root "webapp"
Push-Location $frontend
bun install --silent 2>$null
bun run build
if ($LASTEXITCODE -ne 0) { throw "Frontend build failed" }
Pop-Location

# Step 2: PyInstaller backend
Write-Host "-> [2/4] PyInstaller backend..." -ForegroundColor Yellow
$specFile = "$Root\learnbot-mcp-backend.spec"
if (Test-Path $specFile) {
    $entryFile = "$Root\run_server.py"
    if (-not (Test-Path $entryFile)) { throw "run_server.py not found at $entryFile" }

    Push-Location $Root
    # Install pyinstaller if needed
    $pyiExe = "$Root\.venv\Scripts\pyinstaller.exe"
    if (-not (Test-Path $pyiExe)) {
        uv add --dev pyinstaller | Out-Null
    }
    Remove-Item "$Root\dist\learnbot-mcp-backend.exe" -Force -ErrorAction SilentlyContinue
    & $pyiExe "$specFile" --clean --noconfirm
    if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed" }

    # Smoke test
    $frozenExe = "$Root\dist\learnbot-mcp-backend.exe"
    Write-Host "  Smoke-testing frozen binary..." -ForegroundColor Yellow
    $testPort = 11999
    $env:MCP_PORT = "$testPort"; $env:MCP_HOST = "127.0.0.1"
    $testProc = Start-Process -FilePath $frozenExe -NoNewWindow -PassThru -RedirectStandardError "$Root\dist\pyi-crash.log"
    Start-Sleep -Seconds 5
    if ($testProc.HasExited) {
        $crash = Get-Content "$Root\dist\pyi-crash.log" -Raw
        throw "Frozen binary crashed on launch (exit $($testProc.ExitCode)):`n$crash"
    }
    $testProc.Kill(); $testProc.Dispose()
    Remove-Item "$Root\dist\pyi-crash.log" -Force -ErrorAction SilentlyContinue
    Write-Host "  Frozen binary smoke test PASSED" -ForegroundColor Green
    Pop-Location
} else {
    Write-Host "  WARNING: No spec file at $specFile — skipping PyInstaller" -ForegroundColor DarkYellow
}

# Step 3: Embed backend
Write-Host "-> [3/4] Embedding backend..." -ForegroundColor Yellow
$src = "$Root\dist\learnbot-mcp-backend.exe"
if (Test-Path $src) {
    $sizeMB = (Get-Item $src).Length / 1MB
    if ($sizeMB -lt 5) { throw "Backend exe is only $([math]::Round($sizeMB,1)) MB — broken build" }
    Copy-Item $src "$ResourceDir\learnbot-mcp-backend.exe" -Force
    Copy-Item $src "$DevDir\learnbot-mcp-backend-$Triple.exe" -Force
    Write-Host "  Backend exe: $([math]::Round($sizeMB,1)) MB" -ForegroundColor Green
} else {
    Write-Host "  WARNING: No backend exe at $src — Tauri will run without embedded backend" -ForegroundColor DarkYellow
}

# Bundle .env.example
$envExample = "$Root\.env.example"
if (Test-Path $envExample) {
    Copy-Item $envExample "$ResourceDir\.env.example" -Force
}

# Step 4: Tauri NSIS build
Write-Host "-> [4/4] Tauri NSIS bundle..." -ForegroundColor Yellow
Push-Location $PSScriptRoot
$env:Path = "$env:USERPROFILE\.cargo\bin;$env:Path"
npx @tauri-apps/cli build --bundles nsis
if ($LASTEXITCODE -ne 0) { throw "Tauri build failed" }
Pop-Location

$distDir = Join-Path $Root "dist"
New-Item -ItemType Directory -Force -Path $distDir | Out-Null
$nsisDir = "$PSScriptRoot\target\release\bundle\nsis"
if (Test-Path $nsisDir) { Copy-Item "$nsisDir\*-setup.exe" "$distDir\" -Force }

Write-Host "=== Build complete ===" -ForegroundColor Green
Write-Host "Ship: $nsisDir\*.exe"
