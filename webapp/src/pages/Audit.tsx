import { useEffect, useState } from "react";
import { ScrollText, User, Bot, ShieldAlert } from "lucide-react";
import { api } from "../api";

export function Audit() {
  const [turns, setTurns] = useState<any[]>([]);
  const [filterUser, setFilterUser] = useState("");
  const [filterPersona, setFilterPersona] = useState("");
  const [err, setErr] = useState("");

  const load = async () => {
    try {
      const params: Record<string, string> = { limit: "50" };
      if (filterUser) params.user_id = filterUser;
      if (filterPersona) params.persona = filterPersona;
      const d = await api.audit(params);
      setTurns(d.turns || []);
    } catch { setErr("Failed to load audit log"); }
  };
  useEffect(() => { load(); }, []);

  const icon = (role: string) => {
    if (role === "user") return <User className="w-4 h-4" />;
    if (role === "assistant") return <Bot className="w-4 h-4" />;
    return <ShieldAlert className="w-4 h-4" />;
  };
  const color = (role: string) => {
    if (role === "user") return "border-l-amber-500/30";
    if (role === "refused" || role === "blocked") return "border-l-red-500/30";
    return "border-l-zinc-600";
  };

  return (
    <div data-testid="audit-page">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-bold">Audit Log</h1>
        <button onClick={load} className="text-sm text-zinc-500 hover:text-zinc-300 px-3 py-1.5 rounded-lg border border-zinc-700">
          Refresh
        </button>
      </div>
      {err && <div className="text-red-400 text-sm mb-4">{err}</div>}

      <div className="flex gap-2 mb-4 flex-wrap">
        <input className="bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-1.5 text-sm w-40" placeholder="Filter by user" value={filterUser} onChange={(e) => setFilterUser(e.target.value)} />
        <input className="bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-1.5 text-sm w-40" placeholder="Filter by persona" value={filterPersona} onChange={(e) => setFilterPersona(e.target.value)} />
        <button onClick={load} className="bg-amber-600 hover:bg-amber-500 text-sm px-3 py-1.5 rounded-lg">Search</button>
      </div>

      <div className="space-y-1">
        {turns.map((t: any, i: number) => (
          <div key={t.id || i} className={`border-l-2 ${color(t.role)} pl-3 py-2`}>
            <div className="flex items-center gap-1.5 text-xs text-zinc-500">
              {icon(t.role)}
              <span>{t.role}</span>
              <span>&middot;</span>
              <span>{t.persona_name || "?"}</span>
              <span>&middot;</span>
              <span>{t.timestamp?.slice(0, 16) || "?"}</span>
              {t.safety_verdict !== "passed" && (
                <span className="text-red-400 text-xs">{t.safety_verdict}</span>
              )}
            </div>
            <div className="text-sm mt-0.5 line-clamp-2">{t.content?.slice(0, 300)}</div>
          </div>
        ))}
        {turns.length === 0 && <div className="text-center text-zinc-600 py-8 text-sm">No audit entries found.</div>}
      </div>
    </div>
  );
}
