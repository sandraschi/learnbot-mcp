# learnbot-mcp — Build Log

## 2026-08-02 — v0.6.0 NSIS Build

**Build**: `LearnBot MCP_0.6.0_x64-setup.exe` (36.1 MB)
**Contents**: Rust shell + React frontend + PyInstaller Python backend (33.6 MB)

### Build Steps

| Step | Status | Notes |
|------|--------|-------|
| Frontend build (`bun run build`) | ✅ | 1550 modules, `VITE_API_ORIGIN=http://127.0.0.1:11101` set in build.ps1 |
| PyInstaller backend | ✅ | 33.6 MB, frozen binary smoke test PASSED |
| Tauri Rust compilation | ✅ | Release build |
| NSIS bundling | ✅ | `LearnBot MCP_0.6.0_x64-setup.exe` |
| CUA smoke test | ✅ | **ALL 6/6 PASS** — install → launch → health → 12-page nav (live `/api/*` calls per page) → uninstall |

### Regressions Encountered & Fixed

| Issue | Root Cause | Fix |
|-------|-----------|-----|
| **Installed app UI empty / "Failed to fetch"** | Webview loads embedded dist at `tauri://localhost`; `api.ts` used relative `/api` → hits webview origin, not backend. The 0.5.0 smoke test (6 phases, pre-nav-OCR) never caught it. | `webapp/src/api.ts`: `VITE_API_ORIGIN` env pattern (absolute origin in prod, relative in dev via vite proxy). `native/build.ps1` sets `VITE_API_ORIGIN=http://127.0.0.1:11101` before `bun run build`. Verified: dashboard shows "Connected", per-page API calls 200 in nav click-through. |
| **Vite dev binds IPv6 `::1` only** | `vite.config.ts` had no `host:` → `bun run dev` served on `::1`, so `http://127.0.0.1:11102` refused (ERR_CONNECTION_REFUSED). | Added `host: "127.0.0.1"` to `webapp/vite.config.ts`. Fleet-wide: 47 repos patched same day, documented in TRAPS_AND_PITFALLS.md #8. |
| **CUA smoke nav phase failed silently** | `win.descendants(text=...)` is invalid pywinauto (criteria use `title=`); the exception path skipped the control_type fallback → all 12 "screenshots" were the same page. | `scripts/cua-smoke.py`: `title=` criteria + fallback retained. Verified distinct captures per page (48–191 KB). |
| **tsc gate failures** | `getCurrentWindow().setZoom` moved to Webview class in Tauri 2.11; missing `three` + `vite/client` type declarations. | `useZoom.ts` → `getCurrentWebview()`, added `@types/three` dev dep + `vite-env.d.ts`. `tsc --noEmit` clean. |

### Version Sync

pyproject/CHANGELOG were 0.6.0 but tauri.conf.json, Cargo.toml, glama.json, manifest.json were 0.5.0 — all bumped to 0.6.0 before this build.

---

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
