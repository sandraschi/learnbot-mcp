@echo off
cd /d D:\Dev\repos\chatbot-mcp
:C.RUN
C:\Users\sandr\.local\bin\uv.exe run python -m chatbot_mcp.api
timeout /t 5 /nobreak >nul
goto C.RUN
