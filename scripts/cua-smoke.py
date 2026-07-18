"""CUA-NSIS smoke test — SPA nav click-through with OCR page verification.

Phases:
  1. Kill stale processes
  2. Install NSIS silently
  3. Launch app + wait for window
  4. Backend health check
  5. Nav click-through: Dashboard, Chat, Personas, Safety, Compliance,
     Audit, Demos, Japanese, Lessons, Avatar, Voices, Help
  6. Screenshot each page + OCR for errors
  7. Uninstall
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

CUA_SMOKE_VERSION = "1.2.0"

SCRIPT_DIR = Path(__file__).parent
CONFIG_PATH = SCRIPT_DIR / "cua-nsis-config.json"
with open(CONFIG_PATH) as f:
    CFG = json.load(f)

NSIS_DIR = Path(__file__).parent.parent / "native" / "target" / "release" / "bundle" / "nsis"
PRODUCT = CFG["product_name"]
BACKEND_PORT = CFG["backend_port"]
HEALTH_PATH = CFG["backend_health_path"]
BACKEND_TIMEOUT = CFG.get("backend_timeout", 30)
INSTALL_TIMEOUT = CFG.get("install_timeout", 60)
UNINSTALL_GLOBS = CFG.get("uninstall_globs", [f"{PRODUCT}*"])

# Sidebar nav items in order — matches Layout.tsx
NAV_ITEMS = [
    "Dashboard",
    "Chat",
    "Personas",
    "Safety",
    "Compliance",
    "Audit",
    "Demos",
    "Japanese",
    "Lessons",
    "Avatar",
    "Voices",
    "Help",
]

FAIL_KEYWORDS = [
    "404", "not found", "error", "timeout", "internal server error",
    "bad gateway", "failed to fetch", "cannot connect", "connection refused",
    "blank", "loading...", "unreachable",
]

_logs: list[str] = []
_phases: list[tuple[str, bool]] = []


def _log(phase: str, msg: str):
    line = f"[{phase}] {msg}"
    print(line)
    _logs.append(line)


def _fail(phase: str, msg: str) -> bool:
    line = f"[{phase}] FAIL: {msg}"
    print(line)
    _logs.append(line)
    return False


def _get_nsis_path() -> Path | None:
    for d in (NSIS_DIR, Path(__file__).parent.parent / "dist"):
        matches = list(d.glob(CFG["nsis_glob"]))
        if matches:
            return max(matches, key=lambda p: p.stat().st_mtime)
    return None


def _find_uninstaller() -> str | None:
    for pattern in UNINSTALL_GLOBS:
        for pf in (os.environ.get("LOCALAPPDATA", ""), os.environ.get("PROGRAMFILES", "")):
            for root, dirs, _ in os.walk(pf):
                for d in dirs:
                    if d.lower().startswith(pattern.lower().replace("*", "").lower()):
                        u = os.path.join(root, d, "uninstall.exe")
                        if os.path.exists(u):
                            return u
    return None


def _release_mouse():
    try:
        import ctypes
        for flag in (0x0004, 0x0010, 0x0040):
            ctypes.windll.user32.mouse_event(flag, 0, 0, 0, 0)
    except Exception:
        pass


def _run_phase(name: str, fn, critical: bool = False):
    try:
        ok = fn()
    except Exception as e:
        _log(name, f"EXCEPTION: {e}")
        ok = False
    _phases.append((name, ok))
    _release_mouse()
    if not ok and critical:
        _log(name, "CRITICAL — aborting")
        return False
    return True


# ── Phase implementations ──


def phase_kill_stale() -> bool:
    _log("1-kill", "Killing stale processes...")
    for cmd in [
        ['taskkill', '/F', '/IM', 'learnbot-mcp-backend.exe', '/T'],
        ['taskkill', '/F', '/IM', 'learnbot-mcp-native.exe', '/T'],
    ]:
        subprocess.run(cmd, capture_output=True, timeout=10)
    time.sleep(2)
    return True


def phase_install() -> bool:
    _log("2-install", "Installing NSIS...")
    nsis_path = _get_nsis_path()
    if not nsis_path:
        return _fail("2-install", "No installer found")
    _log("2-install", f"Using: {nsis_path}")
    try:
        r = subprocess.run([str(nsis_path), "/S"], capture_output=True, timeout=INSTALL_TIMEOUT)
        if r.returncode != 0:
            return _fail("2-install", f"Exit code {r.returncode}")
    except subprocess.TimeoutExpired:
        return _fail("2-install", f"Timed out after {INSTALL_TIMEOUT}s")
    _log("2-install", "Installation completed")
    return True


def phase_launch() -> bool:
    _log("3-launch", "Launching app...")
    search_dirs = [os.environ.get("LOCALAPPDATA", ""), os.environ.get("PROGRAMFILES", "")]
    exe = "learnbot-mcp-native.exe"
    found = None
    for sd in search_dirs:
        for root, dirs, files in os.walk(sd):
            if exe in files:
                found = os.path.join(root, exe)
                break
        if found:
            break
    if not found:
        fallback = Path(__file__).parent.parent / "native" / "target" / "release" / exe
        if fallback.exists():
            found = str(fallback)
    if not found:
        return _fail("3-launch", "Could not find binary")
    subprocess.Popen([found], shell=True)
    _log("3-launch", f"Launched: {found}")
    return True


def phase_backend_health() -> bool:
    _log("4-health", f"Waiting for backend on port {BACKEND_PORT}...")
    import httpx
    deadline = time.time() + BACKEND_TIMEOUT
    while time.time() < deadline:
        try:
            resp = httpx.get(f"http://127.0.0.1:{BACKEND_PORT}{HEALTH_PATH}", timeout=3)
            if resp.status_code == 200:
                _log("4-health", "Backend health OK")
                return True
        except Exception:
            pass
        time.sleep(2)
    return _fail("4-health", f"Backend not reachable after {BACKEND_TIMEOUT}s")


def phase_nav_clickthrough() -> bool:
    """Click each sidebar nav item, screenshot each page, OCR for errors."""
    import pywinauto
    import pytesseract
    from PIL import Image

    _log("5-nav", "Waiting for app window...")
    try:
        win = pywinauto.Desktop(backend="uia").window(title_re=CFG["window_title"])
        win.wait("visible", timeout=30)
        win.set_focus()
        time.sleep(2)
    except Exception as e:
        return _fail("5-nav", f"Window not found: {e}")

    # Maximize for consistent click coordinates
    win.maximize()
    time.sleep(1)

    output_dir = Path(__file__).parent.parent / "docs" / "screenshots"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Try to find nav links by text — they're <a> elements inside the sidebar
    nav_failures = []
    for item in NAV_ITEMS:
        _log("5-nav", f"Navigating to {item}...")
        try:
            # Find the link element by its accessible text
            link = win.descendants(text=item)
            if link:
                link[0].click_input()
            else:
                # Fallback: try finding by control type and name
                elements = win.descendants(control_type="Hyperlink")
                el = [e for e in elements if item.lower() in (e.window_text() or "").lower()]
                if el:
                    el[0].click_input()
                else:
                    nav_failures.append((item, "no link found by text or control_type"))
                    _log("5-nav", f"  WARN: no link found for '{item}', taking screenshot anyway")
        except Exception as e:
            nav_failures.append((item, str(e)))
            _log("5-nav", f"  WARN: click failed for '{item}': {e}")

        time.sleep(2)

        # Screenshot the current page
        try:
            img = win.capture_as_image()
            safe_name = item.lower().replace(" ", "-").replace("/", "-")
            path = output_dir / f"cua-{safe_name}.png"
            img.save(str(path))
            _log("5-nav", f"  Screenshot: {path} ({img.size[0]}x{img.size[1]})")
        except Exception as e:
            nav_failures.append((item, f"screenshot failed: {e}"))
            continue

        # OCR: check for error keywords
        try:
            text = pytesseract.image_to_string(img, lang="eng")
            detected = [kw for kw in FAIL_KEYWORDS if kw.lower() in text.lower()]
            if detected:
                nav_failures.append((item, f"OCR detected error keywords: {detected}"))
                _log("5-nav", f"  OCR WARN: {detected}")
        except Exception as e:
            _log("5-nav", f"  OCR skipped: {e}")

        # 1-second pause so the user can see the page before the next nav click
        time.sleep(1)

    # Close the app window for clean uninstall
    try:
        win.close()
        time.sleep(2)
    except Exception:
        pass

    _release_mouse()

    if nav_failures:
        for item, reason in nav_failures:
            _log("5-nav", f"  ISSUE: {item} — {reason}")
        return False

    _log("5-nav", f"All {len(NAV_ITEMS)} pages navigated and captured")
    return True


def phase_uninstall() -> bool:
    _log("6-uninstall", "Uninstalling...")
    uninstaller = _find_uninstaller()
    if not uninstaller:
        return _fail("6-uninstall", "Uninstaller not found")
    try:
        r = subprocess.run([uninstaller, "/S"], capture_output=True, timeout=60)
        if r.returncode != 0:
            return _fail("6-uninstall", f"Exit code {r.returncode}")
    except subprocess.TimeoutExpired:
        return _fail("6-uninstall", "Timed out")
    _log("6-uninstall", "Uninstall completed")
    return True


# ── Main ──


def main():
    print(f"=== CUA-NSIS Smoke Test v{CUA_SMOKE_VERSION} ===")
    print(f"Product: {PRODUCT}")
    print(f"Nav pages: {len(NAV_ITEMS)}")

    phases = [
        ("1-kill-stale", phase_kill_stale, False),
        ("2-install", phase_install, True),
        ("3-launch", phase_launch, False),
        ("4-backend-health", phase_backend_health, False),
        ("5-nav-clickthrough", phase_nav_clickthrough, False),
        ("6-uninstall", phase_uninstall, False),
    ]

    for name, fn, critical in phases:
        if not _run_phase(name, fn, critical):
            if critical:
                break

    print()
    print("=== Results ===")
    all_pass = True
    for name, ok in _phases:
        status = "PASS" if ok else "FAIL"
        print(f"  {name}: {status}")
        if not ok:
            all_pass = False

    if all_pass:
        print(f"=== ALL {len(_phases)}/{len(_phases)} PASS ===")
    else:
        print(f"=== {sum(1 for _, ok in _phases if ok)}/{len(_phases)} PASS ===")

    _release_mouse()
    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
