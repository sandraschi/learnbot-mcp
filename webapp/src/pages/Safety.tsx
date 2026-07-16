import { useEffect, useState } from "react";
import { Plus, Trash2, ShieldAlert } from "lucide-react";
import { api } from "../api";

export function Safety() {
  const [rules, setRules] = useState<any[]>([]);
  const [topic, setTopic] = useState("");
  const [message, setMessage] = useState("");
  const [err, setErr] = useState("");

  const load = async () => {
    try { const d = await api.safety.list(); setRules(d.rules || []); }
    catch { setErr("Failed to load rules"); }
  };
  useEffect(() => { load(); }, []);

  const add = async () => {
    if (!topic.trim()) return;
    try {
      await api.safety.create({ topic: topic.trim(), action: "refuse", message });
      setTopic("");
      setMessage("");
      load();
    } catch (e: any) { setErr(String(e)); }
  };

  const remove = async (id: number) => {
    try { await api.safety.delete(id); load(); }
    catch (e: any) { setErr(String(e)); }
  };

  return (
    <div>
      <h1 className="text-xl font-bold mb-6">Safety Rules</h1>
      {err && <div className="text-red-400 text-sm mb-4">{err}</div>}

      <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 mb-6 space-y-3">
        <input className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-sm" placeholder="Topic to block (e.g. politics, gore)" value={topic} onChange={(e) => setTopic(e.target.value)} />
        <input className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-sm" placeholder="Refusal message (optional)" value={message} onChange={(e) => setMessage(e.target.value)} />
        <button onClick={add} disabled={!topic.trim()} className="flex items-center gap-1 text-sm bg-amber-600 hover:bg-amber-500 px-3 py-1.5 rounded-lg disabled:opacity-50">
          <Plus className="w-4 h-4" /> Add Rule
        </button>
      </div>

      <div className="space-y-2">
        {rules.map((r: any) => (
          <div key={r.id} className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 flex items-start justify-between">
            <div className="flex items-start gap-3">
              <ShieldAlert className="w-5 h-5 text-amber-500 mt-0.5 shrink-0" />
    <div data-testid="safety-page">
                <div className="font-medium text-sm">{r.topic}</div>
                <div className="text-xs text-zinc-500">Action: {r.action}</div>
                {r.message && <div className="text-xs text-zinc-600 mt-1">{r.message}</div>}
              </div>
            </div>
            <button onClick={() => remove(r.id)} className="text-zinc-600 hover:text-red-400 p-1">
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        ))}
        {rules.length === 0 && <div className="text-center text-zinc-600 py-8 text-sm">No safety rules configured.</div>}
      </div>
    </div>
  );
}
