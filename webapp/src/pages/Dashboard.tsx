import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Bot, MessageSquare, Shield, Activity, ShieldCheck, Clock, ArrowRight, Users2, Headset } from "lucide-react";
import { api } from "../api";

function KpiCard({ icon: Icon, label, value, testid }: { icon: React.ElementType; label: string; value: string | number; testid: string }) {
  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4" data-testid={testid}>
      <div className="flex items-center gap-3">
        <div className="p-2 rounded-lg bg-amber-500/10">
          <Icon className="w-5 h-5 text-amber-500" />
        </div>
        <div>
          <div className="text-2xl font-bold">{value}</div>
          <div className="text-sm text-zinc-400">{label}</div>
        </div>
      </div>
    </div>
  );
}

function timeAgo(iso?: string) {
  if (!iso) return "";
  const ms = Date.now() - new Date(iso).getTime();
  if (ms < 0 || Number.isNaN(ms)) return "";
  const mins = Math.floor(ms / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

export function Dashboard() {
  const navigate = useNavigate();
  const [health, setHealth] = useState<any>(null);
  const [err, setErr] = useState("");
  const [restarting, setRestarting] = useState(false);
  const [conversations, setConversations] = useState<any[]>([]);
  const [activeCount, setActiveCount] = useState(0);
  const [compliance, setCompliance] = useState<any>(null);

  const refresh = useCallback(async () => {
    try {
      const h = await api.health();
      setHealth(h);
      setErr("");
      setRestarting(false);
    } catch { /* backoff handles retry */ }
  }, []);

  useEffect(() => {
    let attempts = 0;
    const fn = async () => {
      try {
        const h = await api.health();
        setHealth(h);
        setErr("");
        attempts = 0;
      } catch {
        attempts++;
        const delay = Math.min(1000 * Math.pow(2, attempts), 16000);
        setTimeout(fn, delay);
      }
    };
    fn();
    const interval = setInterval(fn, 10000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    api.conversations.list().then((d) => {
      const all = d.conversations || [];
      setConversations(all.slice(0, 5));
      setActiveCount(all.filter((c: any) => c.state === "active").length);
    }).catch(() => {});
    api.compliance().then(setCompliance).catch(() => {});
  }, [health]);

  useEffect(() => {
    let unlisten: (() => void) | undefined;
    (async () => {
      try {
        const { listen } = await import("@tauri-apps/api/event");
        unlisten = await listen<string>("backend-status", (event) => {
          if (event.payload === "ready") {
            refresh();
          } else if (typeof event.payload === "string" && event.payload.startsWith("error:")) {
            setErr(event.payload);
            setRestarting(false);
          }
        });
      } catch { /* not in Tauri */ }
    })();
    return () => { if (unlisten) unlisten(); };
  }, [refresh]);

  const restartBackend = useCallback(async () => {
    setRestarting(true);
    try {
      const { invoke } = await import("@tauri-apps/api/core");
      await invoke("start_backend");
    } catch { setRestarting(false); }
  }, []);

  if (!health) {
    return (
      <div className="flex items-center justify-center h-64 text-zinc-400">
        <Activity className="w-5 h-5 mr-2 animate-pulse" />
        Connecting...
      </div>
    );
  }

  return (
    <div data-testid="dashboard">
      <div className="flex items-center justify-between bg-gradient-to-br from-amber-500/10 via-zinc-900 to-zinc-900 border border-zinc-800 rounded-2xl p-6 mb-6">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <div
              data-testid="backend-dot"
              className={`w-2.5 h-2.5 rounded-full ${err ? "bg-red-500" : "bg-green-500"} animate-pulse`}
            />
            <span className="text-xs text-zinc-400">{err ? "Offline" : "Connected"}</span>
            {err && (
              <button
                onClick={restartBackend}
                disabled={restarting}
                className="ml-2 px-2 py-1 text-xs bg-amber-500/10 text-amber-500 rounded hover:bg-amber-500/20"
              >
                {restarting ? "Restarting..." : "Restart Backend"}
              </button>
            )}
          </div>
          <div className="text-xs font-semibold tracking-wider text-amber-500/80 uppercase mb-1">
            AI Persona Orchestrator
          </div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Bot className="w-6 h-6 text-amber-500" /> LearnBot MCP
          </h1>
          <p className="text-sm text-zinc-400 mt-2 max-w-xl">
            Runs AI chatbot personas end to end: starts and hibernates conversations, enforces safety
            guardrails on every turn, and hands off responses to speech and other output platforms.
          </p>
          <p className="text-xs text-zinc-400 mt-2">
            {health.server} &middot; v{health.version} &middot; up {Math.floor((health.uptime_seconds ?? 0) / 3600)}h {Math.floor(((health.uptime_seconds ?? 0) % 3600) / 60)}m
          </p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => navigate("/chat")} className="flex items-center gap-1.5 text-sm bg-amber-600 hover:bg-amber-500 px-3 py-2 rounded-lg">
            <MessageSquare className="w-4 h-4" /> New Chat
          </button>
          <button onClick={() => navigate("/personas")} className="flex items-center gap-1.5 text-sm bg-zinc-800 hover:bg-zinc-700 px-3 py-2 rounded-lg">
            <Users2 className="w-4 h-4" /> Personas
          </button>
          <button onClick={() => navigate("/vr")} data-testid="learn-in-vr-cta" className="flex items-center gap-1.5 text-sm bg-zinc-800 hover:bg-zinc-700 px-3 py-2 rounded-lg">
            <Headset className="w-4 h-4" /> Learn in VR
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <KpiCard icon={Bot} label="Personas" value={health.personas ?? "?"} testid="kpi-personas" />
        <KpiCard icon={MessageSquare} label="Active Conversations" value={activeCount} testid="kpi-conversations" />
        <KpiCard icon={Shield} label="Safety Rules" value={health.safety_rules ?? "?"} testid="kpi-safety" />
        <KpiCard icon={ShieldCheck} label="Compliance Regime" value={compliance?.regime ?? "?"} testid="kpi-compliance" />
      </div>

      <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-semibold text-zinc-300 flex items-center gap-2">
            <Clock className="w-4 h-4 text-amber-500" /> Recent Conversations
          </h2>
          <button onClick={() => navigate("/chat")} className="text-xs text-amber-500 hover:text-amber-400 flex items-center gap-1">
            View all <ArrowRight className="w-3 h-3" />
          </button>
        </div>
        {conversations.length === 0 ? (
          <div className="text-sm text-zinc-400 py-6 text-center">No conversations yet. Start one from a persona to see activity here.</div>
        ) : (
          <div className="space-y-2">
            {conversations.map((c) => (
              <div key={c.id} className="flex items-center justify-between text-sm py-2 border-b border-zinc-800 last:border-0">
                <div className="flex items-center gap-2 min-w-0">
                  <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${c.state === "active" ? "bg-green-500" : "bg-zinc-600"}`} />
                  <span className="font-medium truncate">{c.persona_name}</span>
                  <span className="text-zinc-400 shrink-0">&middot; {c.platform}</span>
                </div>
                <span className="text-zinc-400 shrink-0">{timeAgo(c.updated_at)}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
