import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  fetchModels,
  fetchProviders,
  isOnboarded,
  loadSelection,
  markOnboarded,
  saveProviderKey,
  saveSelection,
  type ProviderInfo,
} from "../lib/llm";

type Props = {
  /** banner: render only when setup is incomplete. full: always render status + setup. */
  mode: "banner" | "full";
};

type LocalState = { id: string; label: string; models: string[] };

/**
 * LLM onboarding — ported from arxiv-mcp. State derived client-side
 * (no /api/llm/onboarding endpoint here): locals detected via model fetch,
 * clouds via configured flags. Saving a key never auto-picks a model.
 */
export function LlmOnboarding({ mode }: Props) {
  const navigate = useNavigate();
  const [locals, setLocals] = useState<LocalState[]>([]);
  const [clouds, setClouds] = useState<ProviderInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState(mode === "full");
  const [choice, setChoice] = useState("");
  const [keyInput, setKeyInput] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(isOnboarded());

  useEffect(() => {
    (async () => {
      try {
        const pv = await fetchProviders();
        const list = pv.providers;
        setClouds(list.filter((p) => p.kind === "cloud"));
        const found: LocalState[] = [];
        for (const p of list.filter((x) => x.kind === "local")) {
          try {
            const m = await fetchModels(p.id);
            if (m.models.length > 0) found.push({ id: p.id, label: p.label, models: m.models });
          } catch {
            /* engine down */
          }
        }
        setLocals(found);
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  useEffect(() => {
    if (mode === "full") setExpanded(true);
  }, [mode]);

  if (loading || error) return null;

  const cloudsConfigured = clouds.filter((c) => c.configured).map((c) => c.id);
  const ready = locals.length > 0 || cloudsConfigured.length > 0;
  if (mode === "banner" && (ready || done)) return null;

  const needsKey = choice.startsWith("cloud:");
  const chosenCloud = needsKey ? choice.slice("cloud:".length) : "";

  async function save() {
    if (!choice) return;
    setSaving(true);
    setError(null);
    try {
      const id = choice.includes(":") ? choice.split(":")[1] : choice;
      if (needsKey && keyInput.trim()) await saveProviderKey(id, keyInput.trim());
      const prev = loadSelection();
      const model = prev.provider === id && prev.model ? prev.model : "";
      saveSelection(id, model);
      markOnboarded();
      setDone(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setSaving(false);
    }
  }

  return (
    <div
      data-testid="llm-onboarding"
      className={`border rounded-xl p-4 ${ready ? "border-zinc-800 bg-zinc-900" : "border-red-500/50 bg-red-500/5"}`}
    >
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-sm font-semibold">{ready ? "AI provider ready" : "Set up AI to enable chat"}</p>
          <p className="text-xs text-zinc-400 mt-0.5 max-w-2xl">
            {ready
              ? "A local engine or cloud key is configured. Change providers anytime in Settings."
              : "No local engine detected and no cloud key saved. Pick a path below — chat stays disabled until one works."}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {mode === "banner" && !ready && !expanded && (
            <button
              data-testid="onboarding-cue"
              onClick={() => setExpanded(true)}
              className="bg-red-600 hover:bg-red-500 text-white text-sm px-4 py-2 rounded-lg font-semibold"
            >
              Set up AI
            </button>
          )}
          {mode === "banner" && (
            <button onClick={() => navigate("/settings")} className="text-sm text-zinc-400 hover:text-zinc-200">
              Settings
            </button>
          )}
        </div>
      </div>

      {(expanded || mode === "full") && !done && (
        <div className="mt-4 space-y-2" data-testid="onboarding-paths">
          {locals.map((p) => (
            <label
              key={p.id}
              className={`flex items-center gap-2 rounded-lg border px-3 py-2 text-sm cursor-pointer ${choice === `local:${p.id}` ? "border-amber-500" : "border-zinc-800"}`}
            >
              <input type="radio" name="llm-path" checked={choice === `local:${p.id}`} onChange={() => setChoice(`local:${p.id}`)} />
              <span className="w-2 h-2 rounded-full bg-green-500" />
              <span className="font-medium">{p.label}</span>
              <span className="text-zinc-400 text-xs">detected · free · {p.models.length} models</span>
            </label>
          ))}

          {clouds.map((p) => (
            <label
              key={p.id}
              className={`flex flex-wrap items-center gap-2 rounded-lg border px-3 py-2 text-sm cursor-pointer ${choice === `cloud:${p.id}` ? "border-amber-500" : "border-zinc-800"}`}
            >
              <input type="radio" name="llm-path" checked={choice === `cloud:${p.id}`} onChange={() => setChoice(`cloud:${p.id}`)} />
              <span className={`w-2 h-2 rounded-full ${p.configured ? "bg-green-500" : "bg-amber-500"}`} />
              <span className="font-medium">{p.label}</span>
              <span className="text-zinc-400 text-xs">{p.configured ? "key configured" : `needs ${p.key_env} — cheapest instant path`}</span>
              {choice === `cloud:${p.id}` && !p.configured && (
                <input
                  type="password"
                  value={keyInput}
                  onChange={(e) => setKeyInput(e.target.value)}
                  placeholder={`Paste ${p.key_env}`}
                  aria-label={`${p.label} API key`}
                  data-testid={`llm-key-${p.id}`}
                  className="w-full rounded-lg border border-zinc-700 bg-zinc-800 px-2 py-1 font-mono text-xs mt-1"
                />
              )}
            </label>
          ))}

          {locals.length === 0 && (
            <p className="text-xs text-zinc-400 rounded-lg border border-zinc-800 px-3 py-2">
              No local engine running. Free path: install Ollama (
              <code className="font-mono">winget install -e --id Ollama.Ollama</code>
              , then <code className="font-mono">ollama pull qwen3:32b</code>)
              and come back — or paste a cloud key above.
            </p>
          )}

          {error && <p className="text-xs text-red-400">{error}</p>}

          <div className="flex gap-2 pt-1">
            <button
              onClick={() => void save()}
              disabled={saving || !choice || (needsKey && !keyInput && !clouds.find((c) => c.id === chosenCloud)?.configured)}
              data-testid="onboarding-save"
              className="text-sm bg-amber-600 hover:bg-amber-500 disabled:opacity-50 px-3 py-1 rounded-lg"
            >
              {saving ? "Saving..." : "Use this setup"}
            </button>
          </div>
        </div>
      )}

      {done && mode === "full" && (
        <p className="text-xs text-green-400 mt-3">Saved. Chat is enabled with your selection.</p>
      )}
    </div>
  );
}
