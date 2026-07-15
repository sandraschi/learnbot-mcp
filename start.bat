@echo off
cd /d "%~dp0"
echo Starting learnbot-mcp REST API on port 11101...
echo Webapp: http://127.0.0.1:11101/
echo Floating chat: http://127.0.0.1:11101/chat-tag.html
echo.
start http://127.0.0.1:11101/chat-tag.html
powershell -ExecutionPolicy Bypass -File "%~dp0start.ps1"
