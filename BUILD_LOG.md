# learnbot-mcp — Build Log

## 2026-07-16 — v0.5.0 NSIS Build

**Build**: `LearnBot MCP_0.5.0_x64-setup.exe` (28.4 MB)
**Contents**: Rust shell + React frontend + PyInstaller Python backend (26.2 MB)

### Build Steps

| Step | Status | Notes |
|------|--------|-------|
| Frontend build (bun run build) | ✅ | 7.5s, 1549 modules |
| PyInstaller backend | ✅ | 26.2 MB, `noarchive=True`, fastmcp metadata patched |
| Tauri Rust compilation | ✅ | Release build, cargo crates cached |
| NSIS bundling | ✅ | makensis ran, single setup exe |
| CUA smoke test (6 phases) | ✅ | All PASS — install → launch → health → screenshot → uninstall |

### Regressions Encountered & Fixed

| Issue | Root Cause | Fix |
|-------|-----------|-----|
| Rust binary crashed with exit -1 | `free_port()` used complex PowerShell with `\`` backticks; killed self via `taskkill /IM learnbot-mcp-native.exe` | Replaced with simple `taskkill` for backend only; removed self-kill |
| Icon.ico caused RC2176 error | Auto-generated PNG-based ICO was malformed for Windows Resource Compiler | Deleted icon.ico, only use icon.png |
| `webviewInstallMode: skip` requires WebView2 | Win10 22H2+ has it preinstalled | Confirmed working: WebView2 150.0.4078.65 |
| Backend port collision in dev | Backend was already running on :11101 from `uv run python -m learnbot_mcp.api` | Expected in dev; production install on clean machine has no collision |

### Next Build

Before next NSIS build, check:
- [ ] PyInstaller spec SKIP list still matches current deps
- [ ] `run_server.py` `MCP_PORT` env var is set correctly in `backend.rs`
- [ ] The `beforeBuildCommand` runs `build.ps1` for the full pipeline
