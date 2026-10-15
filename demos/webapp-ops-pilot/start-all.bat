@echo off
REM start-all.bat - one double-click for the webapp-ops pilot stack.
REM   speech-mcp   backend :10909  frontend :10908  (voiceover companion)
REM   learnbot-mcp backend :11101  frontend :11102  (tour target)
REM Each repo boots in its own window via its fleet-standard start.ps1.
REM Paths are derived from this file's location, nothing hardcoded.
setlocal
set "PILOT_DIR=%~dp0"
set "LEARNBOT_ROOT=%PILOT_DIR%..\.."
set "SPEECH_ROOT=%PILOT_DIR%..\..\..\speech-mcp"

if not exist "%LEARNBOT_ROOT%\start.ps1" (
    echo [start-all] ERROR: learnbot start.ps1 not found at "%LEARNBOT_ROOT%\start.ps1"
    pause
    exit /b 1
)
if not exist "%SPEECH_ROOT%\start.ps1" (
    echo [start-all] ERROR: speech-mcp not found at "%SPEECH_ROOT%"
    echo [start-all] Clone it next to learnbot-mcp: github.com/sandraschi/speech-mcp
    pause
    exit /b 1
)

echo [start-all] 1/3 starting speech-mcp -Headless ...
start "speech-mcp :10909/:10908" powershell -ExecutionPolicy Bypass -NoExit -File "%SPEECH_ROOT%\start.ps1" -Headless

echo [start-all] 2/3 starting learnbot-mcp -Headless ...
start "learnbot-mcp :11101/:11102" powershell -ExecutionPolicy Bypass -NoExit -File "%LEARNBOT_ROOT%\start.ps1" -Headless

echo [start-all] 3/3 waiting for backends (max ~90s) ...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$deadline=(Get-Date).AddSeconds(90); $ok=@{}; while((Get-Date) -lt $deadline -and $ok.Count -lt 2){ foreach($u in @('http://127.0.0.1:10909/','http://127.0.0.1:11101/health')){ if(-not $ok[$u]){ try{ if((Invoke-WebRequest -Uri $u -TimeoutSec 3 -UseBasicParsing).StatusCode -match '2..'){ $ok[$u]=1; Write-Host \"  up: $u\" } }catch{} } }; if($ok.Count -lt 2){ Start-Sleep 3 } }; if($ok.Count -lt 2){ Write-Host '  NOTE: one backend did not answer in time - check its window.' }"

echo.
echo [start-all] Stack:
echo   learnbot webapp  http://127.0.0.1:11102  ^(backend :11101^)
echo   speech webapp    http://127.0.0.1:10908  ^(backend :10909^)
echo.
start http://127.0.0.1:11102/
echo [start-all] Try in your MCP client:
echo   webapp_ops(operation="diagnose_webapp")
echo   webapp_ops(operation="demo_webapp", preset="demo_60s", speak=true)
echo.
echo [start-all] To stop: close the two launcher windows (Ctrl+C inside each).
pause
