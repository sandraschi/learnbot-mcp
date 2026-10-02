import { useCallback, useEffect, useState } from "react";
import {
  fetchModels,
  fetchProviders,
  loadSelection,
  type ProviderInfo,
  saveSelection,
} from "../lib/llm";

/**
 * Active LLM card — ported from arxiv-mcp (additive adoption).
 * Learnbot scope: provider + model selection into localStorage.
 * No endpoint override, no GPU/kick telemetry (no backend for those).
 * RULE: never auto-pick — a still-valid choice survives, else empty.
 */
export function ActiveLlmCard() {
  const [providers, setProviders] = useState<ProviderInfo[]>([]);
  const [selected, setSelected] = useState("ollama");
  const [model, setModel] = useState("");
  const [models, setModels] = useState<string[]>([]);
  const [modelsSource, setModelsSource] = useState("");
  const [probing, setProbing] = useState(true);
  const [saveMsg, setSaveMsg] = useState<string | null>(null);

  const reloadModels = useCallback(async (id: string) => {
    try {
      const m = await fetchModels(id);
      setModels(m.models);
      setModelsSource(m.source);
      setModel((cur) => (cur && m.models.includes(cur) ? cur : ""));
    } catch {
      setModels([]);
      setModelsSource("none");
    }
  }, []);

  useEffect(() => {
    (async () => {
      try {
        const pv = await fetchProviders();
        setProviders(pv.providers);
        const prev = loadSelection();
        setSelected(prev.provider || "ollama");
        if (prev.model) setModel(prev.model);
        void reloadModels(prev.provider || "ollama");
      } catch {
        /* backend down: card stays in probing-failed state */
      } finally {
        setProbing(false);
      }
    })();
  }, [reloadModels]);

  useEffect(() => {
    if (selected) void reloadModels(selected);
  }, [selected, reloadModels]);

  function save() {
    saveSelection(selected, model);
    setSaveMsg(model ? `Saved: ${selected} / ${model}. Chat uses this next.` : `Saved provider ${selected}. Pick a model above.`);
  }

  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 space-y-3">
      <p className="text-xs text-zinc-400">Active LLM (used by Chat)</p>
      {probing && (
        <p className="text-xs text-zinc-400 animate-pulse" data-testid="llm-loading">
          Loading providers...
        </p>
      )}
      <div className="flex flex-wrap items-center gap-2">
        <label className="text-xs text-zinc-400" htmlFor="llm-provider">Provider</label>
        <select
          id="llm-provider"
          data-testid="llm-provider-select"
          value={selected}
          disabled={probing}
          onChange={(e) => { setSelected(e.target.value); setSaveMsg(null); }}
          className="rounded-lg border border-zinc-700 bg-zinc-800 px-2 py-1 text-sm"
        >
          {providers.map((p) => (
            <option key={p.id} value={p.id}>{p.label} ({p.kind})</option>
          ))}
        </select>
        <label className="text-xs text-zinc-400" htmlFor="llm-model">Model</label>
        {models.length > 0 ? (
          <select
            id="llm-model"
            data-testid="llm-model-select"
            value={model}
            disabled={probing}
            onChange={(e) => setModel(e.target.value)}
            className="rounded-lg border border-zinc-700 bg-zinc-800 px-2 py-1 text-sm font-mono"
          >
            <option value="">— pick —</option>
            {models.map((m) => (<option key={m} value={m}>{m}</option>))}
          </select>
        ) : (
          <input
            id="llm-model"
            data-testid="llm-model-select"
            value={model}
            disabled={probing}
            onChange={(e) => setModel(e.target.value)}
            placeholder="model id"
            aria-label="Model name"
            className="rounded-lg border border-zinc-700 bg-zinc-800 px-2 py-1 text-sm font-mono w-44"
          />
        )}
        {modelsSource && <span className="text-xs text-zinc-500">source: {modelsSource}</span>}
      </div>
      <div className="flex items-center gap-2">
        <button
          data-testid="settings-llm-save"
          onClick={save}
          disabled={probing}
          className="text-sm bg-amber-600 hover:bg-amber-500 disabled:opacity-50 px-3 py-1 rounded-lg"
        >
          Save
        </button>
        {saveMsg && <span className="text-xs text-zinc-400">{saveMsg}</span>}
      </div>
    </div>
  );
}
