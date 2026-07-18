"""PyInstaller entry point — dual transport for Tauri.

Detects MCP_PORT env var (set by Tauri backend.rs).
When set: starts HTTP/uvicorn server on 127.0.0.1:{port}.
When unset: runs stdio MCP server (for Claude Desktop).
"""
import os
import sys

sys.path.insert(0, "src")

port = os.environ.get("MCP_PORT") or os.environ.get("PORT")
if port:
    host = os.environ.get("MCP_HOST", "127.0.0.1")
    os.environ.setdefault("BACKEND_PORT", port)
    os.environ.setdefault("LEARNBOT_TAURI", "1")
    from learnbot_mcp.api import run_rest

    run_rest()
else:
    from learnbot_mcp.server import main

    main()
