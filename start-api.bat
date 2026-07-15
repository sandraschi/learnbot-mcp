@echo off
cd /d D:\Dev\repos\learnbot-mcp
:C.RUN
C:\Users\sandr\.local\bin\uv.exe run python -m learnbot_mcp.api
timeout /t 5 /nobreak >nul
goto C.RUN
