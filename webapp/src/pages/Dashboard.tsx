import { useCallback, useEffect, useState } from "react";
import { Bot, MessageSquare, Shield, Activity } from "lucide-react";
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
          <div className="text-sm text-zinc-500">{label}</div>
        </div>
      </div>
    </div>
  );
}

export function Dashboard() {
  const [health, setHealth] = useState<any>(null);
  const [err, setErr] = useState("");
  const [restarting, setRestarting] = useState(false);

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
      <div className="flex items-center justify-center h-64 text-zinc-500">
        <Activity className="w-5 h-5 mr-2 animate-pulse" />
        Connecting...
      </div>
    );
  }

  return (
    <div data-testid="dashboard">
      <div className="flex items-center gap-2 mb-6">
        <div
          data-testid="backend-dot"
          className={`w-2.5 h-2.5 rounded-full ${err ? "bg-red-500" : health ? "bg-green-500" : "bg-gray-500"} animate-pulse`}
        />
        <span className="text-xs text-zinc-500">
          {err ? "Offline" : health ? "Connected" : "Connecting..."}
        </span>
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
      <h1 className="text-xl font-bold mb-6">Dashboard</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard icon={Bot} label="Personas" value={health.personas ?? "?"} testid="kpi-personas" />
        <KpiCard icon={MessageSquare} label="Conversations" value={health.conversations ?? "?"} testid="kpi-conversations" />
        <KpiCard icon={Shield} label="Safety Rules" value={health.safety_rules ?? "?"} testid="kpi-safety" />
        <KpiCard icon={Activity} label="Uptime" value={`${Math.floor((health.uptime_seconds ?? 0) / 3600)}h`} testid="kpi-uptime" />
      </div>
      <div className="mt-4 text-sm text-zinc-600">
        learnbot-mcp v{health.version} &middot; {err && <span className="text-red-400">{err}</span>}
      </div>
    </div>
  );
}
