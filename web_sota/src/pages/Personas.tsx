import { useEffect, useState } from "react";
import { Plus, Trash2, Bot } from "lucide-react";
import { api } from "../api";

export function Personas() {
  const [personas, setPersonas] = useState<any[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ name: "", display_name: "", backstory: "", voice: "", triggers: "" });
  const [err, setErr] = useState("");

  const load = async () => {
    try { const d = await api.personas.list(); setPersonas(d.personas || []); }
    catch { setErr("Failed to load personas"); }
  };
  useEffect(() => { load(); }, []);

  const create = async () => {
    if (!form.name.trim()) return;
    try {
      let triggers: any = form.triggers ? JSON.parse(form.triggers) : [];
      await api.personas.create({ ...form, proactive_triggers: triggers });
      setShowForm(false);
      setForm({ name: "", display_name: "", backstory: "", voice: "", triggers: "" });
      load();
    } catch (e: any) { setErr(String(e)); }
  };

  const remove = async (name: string) => {
    try { await api.personas.delete(name); load(); }
    catch (e: any) { setErr(String(e)); }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-bold">Personas</h1>
        <button onClick={() => setShowForm(!showForm)} className="flex items-center gap-1 text-sm bg-amber-600 hover:bg-amber-500 px-3 py-1.5 rounded-lg">
          <Plus className="w-4 h-4" /> New
        </button>
      </div>
      {err && <div className="text-red-400 text-sm mb-4">{err}</div>}

      {showForm && (
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 mb-6 space-y-3">
          <input className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-sm" placeholder="Name (unique)" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          <input className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-sm" placeholder="Display name" value={form.display_name} onChange={(e) => setForm({ ...form, display_name: e.target.value })} />
          <textarea className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-sm h-24" placeholder="Backstory / system prompt" value={form.backstory} onChange={(e) => setForm({ ...form, backstory: e.target.value })} />
          <input className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-sm" placeholder="Voice (e.g. heart, sky)" value={form.voice} onChange={(e) => setForm({ ...form, voice: e.target.value })} />
          <input className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-sm" placeholder={'Proactive triggers as JSON array, e.g. [{"schedule":"15m","prompt":"hi"}]'} value={form.triggers} onChange={(e) => setForm({ ...form, triggers: e.target.value })} />
          <button onClick={create} className="bg-amber-600 hover:bg-amber-500 text-sm px-4 py-1.5 rounded-lg">Create</button>
        </div>
      )}

      <div className="space-y-2">
        {personas.map((p: any) => (
          <div key={p.name} className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 flex items-start justify-between">
    <div data-testid="personas-page">
              <div className="flex items-center gap-2">
                <Bot className="w-4 h-4 text-amber-500" />
                <span className="font-medium">{p.display_name || p.name}</span>
                <span className="text-xs text-zinc-600">{p.name}</span>
              </div>
              <div className="text-sm text-zinc-500 mt-1 line-clamp-2">{p.backstory?.slice(0, 200)}</div>
              <div className="text-xs text-zinc-600 mt-1">
                Voice: {p.voice || "none"} &middot; Platforms: {(p.platforms || []).join(", ") || "none"}
                {(p.proactive_triggers || []).length > 0 && <> &middot; Triggers: {p.proactive_triggers.length}</>}
              </div>
            </div>
            <button onClick={() => remove(p.name)} className="text-zinc-600 hover:text-red-400 p-1">
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        ))}
        {personas.length === 0 && <div className="text-center text-zinc-600 py-8 text-sm">No personas yet.</div>}
      </div>
    </div>
  );
}
