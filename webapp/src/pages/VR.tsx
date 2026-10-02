import { useEffect, useState } from "react";
import { Headset, Monitor, Glasses, ChevronDown, ChevronRight, CircleDot } from "lucide-react";
import { api } from "../api";
import { VRMViewer } from "../VRMViewer";

type Companion = {
  reachable: boolean;
  url: string;
  detail: string;
  repo: string;
  hint: string;
  action?: string;
};

type VrStatus = {
  companions: Record<string, Companion>;
  can_summon: boolean;
  summon_note: string;
};

const TRACKS = [
  {
    id: "resonite",
    title: "Resonite — start here",
    badge: "Recommended",
    steps: [
      "Install Steam (free), then install Resonite and create a free Resonite account.",
      "Launch Resonite in desktop mode — no headset required.",
      "Enable ResoniteLink: Dashboard > Session > Settings > Enable ResoniteLink.",
      "Start resonite-mcp (just serve) so the bridge can reach your session.",
      "Join the classroom session from the invite link, keep this page open, and press Summon Miko (Phase 2).",
    ],
  },
  {
    id: "vrchat",
    title: "VRChat — advanced",
    badge: "2FA required",
    steps: [
      "Create a VRChat account and verify your email.",
      "Install VRChat (Steam or Quest) — desktop mode works.",
      "Log vrchat-mcp in via its Settings (username + password, then 2FA code).",
      "Join a private or friends instance — never a public world for lessons.",
      "Keep this page open and press Summon Miko (Phase 4) — greetings arrive as chatbox messages.",
    ],
  },
  {
    id: "overte",
    title: "Overte — self-hosted",
    badge: "Classroom future",
    steps: [
      "Download Overte client + server from overte.org and install both.",
      "Start domain-server.exe, open http://localhost:40100/settings and set a local admin account.",
      "Start Interface, log into your local domain (localhost).",
      "Load scripts/overte-mcp-bridge.js in Interface (Developer > Script Manager > From Disk).",
      "Keep overte-mcp running — spawn/inject flips from simulated to live once the bridge connects.",
    ],
  },
];

const MOCK_SESSIONS = [
  { persona: "Miko-chan", platform: "resonite", user: "Joe Mocky", when: "2h ago" },
  { persona: "Miko-chan (genki)", platform: "overte", user: "Sandra Mockinger", when: "1d ago" },
];

export function VR() {
  const [status, setStatus] = useState<VrStatus | null>(null);
  const [openTrack, setOpenTrack] = useState("resonite");
  const [miko, setMiko] = useState<"classic" | "genki">("genki");
  const [headsetOpen, setHeadsetOpen] = useState(false);
  const [summoning, setSummoning] = useState(false);
  const [summon, setSummon] = useState<any | null>(null);
  const [level, setLevel] = useState("N5");
  const [step, setStep] = useState<any | null>(null);
  const [stepBusy, setStepBusy] = useState(false);
  const [score, setScore] = useState({ asked: 0, correct: 0 });
  const [room, setRoom] = useState<any | null>(null);

  useEffect(() => {
    api.vr.status().then(setStatus).catch(() => {});
  }, []);

  const companions = status?.companions ?? {};
  const anyReachable = Object.values(companions).some((c) => c.reachable);

  const fetchStep = async (answer = "", questionId = 0) => {
    setStepBusy(true);
    try {
      const r = await fetch("/api/vr/lesson-step", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ level, answer, question_id: questionId }),
      });
      const d = await r.json();
      if (d.success && d.graded?.ok && d.graded.correct !== undefined) {
        setScore((s) => ({
          asked: s.asked + 1,
          correct: s.correct + (d.graded.correct ? 1 : 0),
        }));
      }
      setStep(d);
    } catch {
      setStep({ success: false, error: "Lesson step failed - is the backend running?" });
    }
    setStepBusy(false);
  };

  const ensureRoom = async () => {
    try {
      const r = await fetch("/api/vr/classroom-ensure", { method: "POST" });
      setRoom(await r.json());
    } catch {
      setRoom({ success: false, error: "Classroom request failed." });
    }
  };
  const doSummon = async () => {
    setSummoning(true);
    setSummon(null);
    try {
      const r = await api.vr.summon({ platform: openTrack, variant: miko });
      setSummon(r);
      api.vr.status().then(setStatus).catch(() => {});
    } catch {
      setSummon({ success: false, error: "Summon request failed - is the learnbot backend running?" });
    }
    setSummoning(false);
  };

  return (
    <div data-testid="vr-page" className="max-w-3xl mx-auto">
      <h1 className="text-xl font-bold mb-2 flex items-center gap-2">
        <Headset className="w-5 h-5 text-amber-500" /> Learn in VR
      </h1>
      <p className="text-sm text-zinc-400 mb-6">
        Step into a world where Miko-chan welcomes you in Japanese and quizzes you on
        your lesson. Desktop first — no headset required.
      </p>

      {!anyReachable && (
        <button
          data-testid="onboarding-cue"
          onClick={() => document.getElementById("vr-setup")?.scrollIntoView({ behavior: "smooth" })}
          className="w-full mb-6 px-4 py-3 text-sm font-semibold bg-red-600 hover:bg-red-500 rounded-xl"
        >
          Complete VR onboarding — connect Resonite
        </button>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-6">
        {TRACKS.map((t) => {
          const c = companions[t.id];
          const dot = !status ? "bg-zinc-600" : c?.reachable ? "bg-green-500" : "bg-zinc-600";
          return (
            <button
              key={t.id}
              onClick={() => setOpenTrack(t.id)}
              className={`text-left bg-zinc-900 border rounded-xl p-4 transition-colors ${
                openTrack === t.id ? "border-amber-500" : "border-zinc-800 hover:border-zinc-600"
              }`}
            >
              <div className="flex items-center gap-2 mb-1">
                <span className={`w-2 h-2 rounded-full ${dot}`} />
                <span className="text-sm font-semibold">{t.title}</span>
              </div>
              <div className="text-xs text-zinc-400">{t.badge}</div>
              <div className="text-xs text-zinc-500 mt-1">
                {!status ? "Probing..." : c?.reachable ? `Connected (${c.detail})` : "Not running"}
              </div>
            </button>
          );
        })}
      </div>

      {!status && (
        <div className="text-sm text-zinc-400 mb-6">Probing companions...</div>
      )}
      {status &&
        Object.entries(companions).map(
          ([name, c]) =>
            !c.reachable && (
              <div key={name} className="text-xs text-zinc-400 bg-zinc-900 border border-zinc-800 rounded-xl p-3 mb-2">
                <span className="font-medium text-zinc-300">{name}-mcp:</span> {c.action}{" "}
                <span className="text-zinc-500">{c.hint}</span>
              </div>
            )
        )}

      <div id="vr-setup" className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 mb-6">
        <h2 className="text-sm font-semibold text-zinc-300 mb-3">Setup steps — {TRACKS.find((t) => t.id === openTrack)?.title}</h2>
        <ol className="list-decimal list-inside space-y-1.5 text-sm text-zinc-400">
          {TRACKS.find((t) => t.id === openTrack)?.steps.map((s, i) => (
            <li key={i}>{s}</li>
          ))}
        </ol>
      </div>

      <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 mb-6">
        <h2 className="text-sm font-semibold text-zinc-300 mb-1">Which Miko greets you?</h2>
        <p className="text-xs text-zinc-500 mb-3">Both use the same voice pipeline. Pick the style you want.</p>
        <div className="space-y-2">
          <label className="flex items-start gap-2 text-sm cursor-pointer">
            <input type="radio" name="miko" checked={miko === "classic"} onChange={() => setMiko("classic")} className="mt-1 accent-amber-500" />
            <span>
              <span className="font-medium">Miko Classic</span>
              <span className="text-zinc-400"> — same persona as Chat. Calm desu/masu, continues your active lesson.</span>
            </span>
          </label>
          <label className="flex items-start gap-2 text-sm cursor-pointer">
            <input type="radio" name="miko" checked={miko === "genki"} onChange={() => setMiko("genki")} className="mt-1 accent-amber-500" />
            <span>
              <span className="font-medium">Miko Genki VR</span>
              <span className="text-zinc-400"> — listening-first variant. Shorter sentences, furigana-first, replay button.</span>
            </span>
          </label>
        </div>
        <div className="mt-3 text-sm bg-zinc-800 border border-zinc-700 rounded-lg p-3">
          <div className="font-medium">こんにちは！ミコです。一緒に日本語を練習しましょう！</div>
          <div className="text-xs text-zinc-400 mt-1">Konnichiwa! Miko desu. Issho ni nihongo o renshuu shimashou!</div>
          <div className="text-xs text-zinc-500 mt-1">Hello! I&apos;m Miko. Let&apos;s practice Japanese together!</div>
        </div>
        <button
          data-testid="vr-summon-miko"
          onClick={doSummon}
          disabled={summoning || openTrack === "vrchat"}
          title={openTrack === "vrchat" ? "VRChat summon lands in Phase 6 (last)" : undefined}
          className="mt-3 w-full px-4 py-2 text-sm bg-amber-600 hover:bg-amber-500 disabled:bg-zinc-800 disabled:text-zinc-500 rounded-lg disabled:cursor-not-allowed"
        >
          {summoning ? "Summoning Miko..." : "Summon Miko"}
        </button>
        {openTrack === "vrchat" && (
          <p className="text-xs text-zinc-500 mt-2">VRChat summon lands in Phase 6 (last) — Resonite and Overte summon are live.</p>
        )}
        {summon && (
          <div className="mt-3 text-sm bg-zinc-800 border border-zinc-700 rounded-lg p-3 space-y-2">
            {summon.success ? (
              <>
                <div className="font-medium">{summon.greeting_ja}</div>
                <div className="text-xs text-zinc-400">{summon.greeting_romaji}</div>
                <div className="text-xs text-zinc-500">{summon.greeting_en}</div>
                <div className="text-xs space-y-1 pt-1">
                  {summon.receipts?.map((r: any, i: number) => (
                    <div key={i} className={r.ok ? "text-green-400" : "text-zinc-400"}>
                      {r.ok ? "✓" : "·"} {r.step}: {r.detail}
                    </div>
                  ))}
                </div>
                <div className="text-xs text-zinc-500">
                  Audit: {summon.audit} ·{" "}
                  <a href={`/chat?conv=${summon.conversation_id}`} className="text-amber-500 hover:text-amber-400">
                    Continue in Chat
                  </a>
                </div>
              </>
            ) : (
              <div className="text-red-400 text-xs">Summon failed: {summon.error}</div>
            )}
          </div>
        )}
      </div>

      <div data-testid="vr-practice" className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 mb-6">
        <div className="flex items-center justify-between mb-1">
          <h2 className="text-sm font-semibold text-zinc-300">Practice step — classroom loop</h2>
          <span className="text-xs text-zinc-500">Score {score.correct}/{score.asked}</span>
        </div>
        <p className="text-xs text-zinc-500 mb-3">
          Bundled JLPT items, fully local. Miko reads each question aloud. Answer here or in Chat.
        </p>
        <div className="flex items-center gap-2 mb-3">
          <select
            value={level}
            onChange={(e) => setLevel(e.target.value)}
            className="text-sm bg-zinc-800 border border-zinc-700 rounded-lg px-2 py-1"
          >
            {["N5", "N4", "N3", "N2", "N1"].map((l) => (
              <option key={l} value={l}>{l}</option>
            ))}
          </select>
          <button
            onClick={() => fetchStep()}
            disabled={stepBusy}
            className="text-sm bg-zinc-800 hover:bg-zinc-700 disabled:opacity-50 px-3 py-1 rounded-lg"
          >
            {stepBusy ? "..." : step ? "Next question" : "Start"}
          </button>
          <button
            onClick={ensureRoom}
            title="Spawn the persistent classroom (Overte domain + bridge required)"
            className="text-sm bg-zinc-800 hover:bg-zinc-700 px-3 py-1 rounded-lg"
          >
            Prepare classroom
          </button>
        </div>
        {step && !step.success && (
          <div className="text-xs text-red-400">{step.error}</div>
        )}
        {step?.graded?.ok && (
          <div className={`text-sm mb-2 ${step.graded.correct ? "text-green-400" : "text-amber-400"}`}>
            {step.graded.correct ? "せいかい！ " : "おしい！ "}
            <span className="text-xs text-zinc-400">
              ({step.graded.given} → {step.graded.expected}) {step.graded.explanation}
            </span>
          </div>
        )}
        {step?.item && (
          <div className="text-sm bg-zinc-800 border border-zinc-700 rounded-lg p-3">
            <div className="font-medium mb-2">{step.item.question}</div>
            <div className="grid grid-cols-1 gap-1">
              {Object.entries(step.item.options as Record<string, string>).map(([k, v]) => (
                <button
                  key={k}
                  onClick={() => fetchStep(k, step.item.id)}
                  disabled={stepBusy}
                  className="text-left text-sm bg-zinc-900 hover:bg-zinc-700 border border-zinc-700 rounded-lg px-3 py-1.5 disabled:opacity-50"
                >
                  <span className="font-mono text-amber-500 mr-2">{k}</span>{v as string}
                </button>
              ))}
            </div>
          </div>
        )}
        {room && (
          <div className="text-xs text-zinc-400 mt-2 space-y-1">
            {room.success ? (
              room.receipts?.map((r: any, i: number) => (
                <div key={i} className={r.ok ? "text-green-400" : ""}>· {r.step}: {r.detail}</div>
              ))
            ) : (
              <div className="text-red-400">Classroom failed: {room.error}</div>
            )}
          </div>
        )}
      </div>

      <div data-testid="vr-in-viewer" className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 mb-6">
        <h2 className="text-sm font-semibold text-zinc-300 mb-1">Preview in viewer</h2>
        <p className="text-xs text-zinc-500 mb-3">Flat preview — the real Miko is in-world. No WebXR in v1.</p>
        <div className="flex justify-center">
          <VRMViewer size={240} persona="miko" expression="neutral" talking={false} lookAtMouse={false} autoRotate={true} />
        </div>
      </div>

      <div className="mb-6">
        <button
          onClick={() => setHeadsetOpen(!headsetOpen)}
          className="flex items-center gap-2 text-sm text-zinc-300 hover:text-zinc-100"
        >
          {headsetOpen ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
          <Glasses className="w-4 h-4 text-amber-500" />
          Headset (Meta / Pico) — later, optional
        </button>
        {headsetOpen && (
          <div data-testid="vr-headset-path" className="mt-2 text-sm text-zinc-400 bg-zinc-900 border border-zinc-800 rounded-xl p-4 space-y-2">
            <p className="flex items-center gap-2"><Monitor className="w-4 h-4" /> Desktop stays the default. Headset only changes input and comfort:</p>
            <ul className="list-disc list-inside space-y-1 text-xs">
              <li>Quest: standalone via SideQuest APK, or Quest Link / Air Link for full PC features.</li>
              <li>Pico 4: Pico Store app, or SteamVR mode for creation tools.</li>
              <li>Controllers replace mouse/keyboard; keep WiFi stable and take breaks.</li>
              <li>No headset QA in v1 — desktop screenshots gate this page.</li>
            </ul>
          </div>
        )}
      </div>

      <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 mb-6">
        <div data-testid="mock-data-banner" className="text-xs text-rose-400 border border-dashed border-rose-500 rounded-lg p-2 mb-3">
          [MOCK] Sample sessions below — they clear automatically once a real VR session succeeds. Live session history lands with Phase 2.
        </div>
        <h2 className="text-sm font-semibold text-zinc-300 mb-2">Recent VR sessions</h2>
        <div className="space-y-2">
          {MOCK_SESSIONS.map((s, i) => (
            <div key={i} className="flex items-center justify-between text-sm py-2 border border-dashed border-rose-500/50 rounded-lg px-3">
              <div className="flex items-center gap-2 min-w-0">
                <CircleDot className="w-3 h-3 text-rose-400 shrink-0" />
                <span className="font-medium truncate">{s.persona}</span>
                <span className="text-zinc-400 shrink-0">· {s.platform} · {s.user} [MOCK]</span>
                <span data-testid="mock-badge" className="text-[10px] px-1.5 py-0.5 rounded bg-rose-500/10 text-rose-400 border border-rose-500/50">MOCK</span>
              </div>
              <span className="text-zinc-400 shrink-0 text-xs">{s.when}</span>
            </div>
          ))}
        </div>
      </div>

      <p className="text-xs text-zinc-500 mb-8">
        You are talking to an AI, not a person. VR turns are logged like any chat turn
        (see Audit). If a world gets uncomfortable — motion sickness, noise, strangers —
        switch to desktop mode, take a break, or continue in Chat. Mute, block, and
        report tools are in-world; lesson content stays here.
      </p>
    </div>
  );
}
