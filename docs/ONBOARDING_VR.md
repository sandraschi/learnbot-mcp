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

### Track B — VRChat (advanced, Phase 4)

Create + verify a VRChat account, log vrchat-mcp in (Settings: username,
password, then 2FA code), join a **private/friends instance**, summon from the
VR page (chatbox delivery, ≤144 chars per message). Fleet ports for vrchat-mcp
are currently unclaimed (config 0/0, README claims 10795/10796) — resolved in
Phase 4 before this track goes live.

### Track C — Overte self-hosted (Phase 4, classroom future)

Install Overte client + server, start `domain-server.exe`, set a local admin
at `http://localhost:40100/settings`, load `scripts/overte-mcp-bridge.js` in
Interface. Miko arrives as a GLB entity (VRM must be converted first —
Overte cannot load VRM directly).

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
  even for list — avatar VRM loading waits for Phase 3, voice + expression
  work without it.
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
