# Onboarding — Learn in VR (learnbot-mcp)

First-time setup for the `/vr` page: from zero to Miko greeting you in Japanese
in a Resonite world. Desktop-first; no headset required.

## 1. What this is for

- Who: Joe Greybeardy — smart adult, Windows PC, zero VR background, no headset.
- Goal: open learnbot's Dashboard, press **Learn in VR**, follow the Resonite
  track, press **Summon Miko**, and hear
  こんにちは！ミコです。一緒に日本語を練習しましょう！
  with romaji + English gloss on screen.
- Non-goals (Phase 2): VRChat/Overte summon (Phase 4), custom classroom worlds
  (Phase 5), headset QA (later, optional).

## 2. Cost and accounts

| Item | Cost | Account | Card |
|---|---|---|---|
| Steam client | Free | Steam account | No |
| Resonite | Free (demo suffices for desktop join) | Resonite account (free) | No |
| resonite-mcp (fleet bridge) | Free, local | None | No |
| VoiceStudio sidecar (local JP TTS) | Free, local (~2.3 GB model download) | None | No |
| Gemini cloud TTS fallback | Pay-per-use | Google API key (optional) | Only if you enable it |
| Headset (Quest / Pico) | Not required | — | No |

Core path costs €0 and needs no credit card. Cloud TTS is an optional fallback.

## 3. Prerequisites outside this repo

1. **learnbot-mcp running**: `cd D:/Dev/repos/learnbot-mcp` then `./start.ps1`
   (backend :11101, frontend :11102).
2. **speech-mcp running** (voice): `cd D:/Dev/repos/speech-mcp`, `just serve`
   (backend :10909). Without it, summon still works but the voice receipt fails.
3. **Steam + Resonite installed** (Track A steps 1-2 below).
4. **resonite-mcp running** (bridge): `cd D:/Dev/repos/resonite-mcp`, `just serve`
   (backend :10979 — note: the learnbot default `LEARNBOT_RESONITE_MCP_URL`
   already points at :10979; if you overrode it to :10978 (frontend), fix it).

## 4. First-timer setup steps

### Track A — Resonite desktop (DEFAULT, Joe path)

1. Install Steam (free), then install **Resonite** from the Steam store.
2. Create a free Resonite account and run through the intro tutorial once.
3. Launch Resonite in **desktop mode** (no headset needed). Force it with the
   Steam launch option `-Screen` if it ever tries VR.
4. In Resonite: open the Dash (`Esc`), go to **Session > Settings**, enable
   **ResoniteLink**. This is the step everything depends on — no link, no Miko.
5. Start resonite-mcp (`just serve`), then open learnbot's **VR page**.
   The Resonite card should flip green (Connected).
6. Pick your Miko (**Classic** = same persona as Chat; **Genki VR** =
   listening-first for first-timers), press **Summon Miko**.
7. You hear the greeting on your speakers; the script + delivery receipts show
   on the page. Press **Continue in Chat** to keep practicing as text.
8. (Optional, in-world avatar): import `D:/Dev/repos/avatar-mcp/models/Nekomimi-chan.vrm`
   into your Resonite inventory once via drag-drop, note its inventory path, and set
   `LEARNBOT_MIKO_AVATAR_PATH` to it before restarting learnbot. Until then the
   `avatar` receipt honestly reports skipped — voice + expression still work.
8. Classroom shortcut (later, Phase 5): a Resonite shortcut/Steam launch option
   like `-Join <session-URI>` boots straight into the Miko classroom session —
   no navigation needed. `-SkipIntroTutorial` and `-ForceLANOnly` are useful
   classroom extras (see Resonite wiki: Command line arguments).

### Windowed mode / second monitor

Resonite (FrooxEngine, not Unity) has **no command-line switch for windowed
mode or monitor selection** — there is no `-screen-fullscreen`-style flag;
`-Screen` only forces desktop-vs-VR mode. Practical setup:

- Start Resonite (it opens fullscreen on the primary monitor), then press
  **Win+Shift+Left/Right Arrow** to throw the window to the second monitor.
- Resize freely once moved — plain Windows window behavior from there.
- Keep learnbot's VR page (browser) on the main monitor, Resonite on the
  second. No config file to edit, no relaunch needed.

### Track B — VRChat (advanced, LAST)

Heaviest track: account + 2FA + anti-cheat + trust ranks. Do Resonite first.

1. Create a VRChat account, verify your email, and merge it to a full
   VRChat account (not Steam-only) so API login works.
2. **Anti-cheat gate (the BIOS one)**: VRChat's EAC build requires **Secure
   Boot enabled in BIOS/UEFI** and **Memory Integrity (HVCI) on** in Windows
   Security > Device security > Core isolation. Check first: `msinfo32` >
   BIOS Mode must read UEFI (Legacy = convert with MBR2GPT first), and
   registry `HKLM:\...\SecureBoot\State\UEFISecureBootEnabled` should be 1.
   Caveats: Secure Boot complicates Linux dual-boot; HVCI broke some Vive
   Bluetooth drivers. If either is a problem, stay on Resonite/Overte.
3. Install VRChat (Steam or Quest) — desktop mode works, no headset needed.
4. In **vrchat-mcp** Settings: store username + password, complete the 2FA
   code handshake (`auth_2fa`, Email or TOTP). learnbot never holds these.
5. Join a **private or friends instance** — never a public world for lessons.
6. On learnbot's VR page (VRChat track), press **Summon Miko**: you get the
   greeting + numbered chatbox chunks (≤144 chars each). Send them in order
   via vrchat-mcp `manage_input chatbox` (MCP, not REST — learnbot cannot
   POST chat itself). Voice + audit turn work regardless.
7. Avatars: switching needs a valid avatar ID your account can access —
   arbitrary anime avatars are NOT promised. Presence + voice + text is v1.

### Track C — Overte self-hosted (Phase 4 live, classroom future)

No anti-cheat, no accounts on someone else's server, no Secure Boot drama —
you host the domain yourself:

1. Download the Overte client + `domain-server.exe` from overte.org and
   install both.
2. Start `domain-server.exe`. Open `http://localhost:40100/settings` and set a
   local admin account (default `admin/admin` — change it, local-only anyway).
3. Start Interface, log into your local domain (`localhost`).
4. In Interface: Developer > Script Manager > From Disk, load
   `D:/Dev/repos/overte-mcp/scripts/overte-mcp-bridge.js`. Until this runs,
   overte-mcp reports `simulated` — the VR page shows it amber, never green.
5. Start overte-mcp (`cd D:/Dev/repos/overte-mcp`, `./start.ps1`, backend
   :11110). The Overte card flips green when the domain answers.
6. Pick your Miko, press **Summon Miko**: learnbot spawns a temporary
   greeting-sign Text entity in-world (`permanent=False`), speaks the line,
   and logs the audit turn. Check Entities in overte-mcp to see it tracked.
7. Classroom preview (Phase 5): the same spawn with `permanent=True` plus a
   welcome script becomes the persistent Miko classroom on your domain.

## 5. Pitfalls

- **ResoniteLink off** (the Joe cliff): summon receipts show
  `session ok:false` + `expression Skipped`. Fix is always the same checkbox
  (Dash > Session > Settings). The page says so; do not reinstall anything.
- **Probing :10978 instead of :10979**: :10978 is the Vite frontend (no
  `/health`). Point `LEARNBOT_RESONITE_MCP_URL` at backend :10979.
- **Resonite fullscreen swallows the guide**: move it with Win+Shift+Arrow
  (see above) instead of fighting Alt+Tab.
- **First VoiceStudio synthesis slow**: ~2.3 GB model download inside the
  first request timeout — pre-install the OmniVoice model via its catalogue.
- **Resonite inventory flaky**: upstream inventory requests currently time out
  even for list — so Miko's avatar step is optional (`LEARNBOT_MIKO_AVATAR_PATH`,
  empty by default). Voice + expression work without it. Never set the path to
  a VRM file and expect ResoniteLink to import it — ResoniteLink has no VRM/GLB
  import; the VRM goes into inventory via manual drag-drop.
- **Old learnbot DB**: summon self-heals the personas languages/skills
  migration and seeds the Miko persona automatically. Nothing to do.
- **VRChat 2FA**: codes expire fast; approve in vrchat-mcp Settings, not here.

## 6. Sanity check

1. `/api/vr/status` returns all three companions with `reachable` flags and no
   `error` field.
2. Resonite track: Dash > Session > Settings shows ResoniteLink enabled;
   resonite-mcp session status answers.
3. Press Summon Miko (Genki): you **hear** Japanese within ~10 s, the page
   shows `voice ok:true`, and Audit lists the greeting turn.
4. `/chat?conv=<id>` (Continue in Chat) opens the summon conversation.

## 7. Declared doubles

- `/vr` Recent sessions shows **Joe Mocky / Sandra Mockinger [MOCK]** rows with
  a mock-data banner until the first real summon succeeds (no live history
  endpoint yet — Phase 2 shipped summon + audit, history query is Phase 5).
- `voice` receipt `provider=windows-sapi5` means speech-mcp was unreachable
  and Windows spoke instead (flat voice, EN-biased) — start speech-mcp.
- `session`/`expression` receipts `ok:false` are expected with no linked
  Resonite client — hints, not errors.
- No WebXR in v1: the viewer card is a flat VRM preview; the real Miko is
  in-world.
