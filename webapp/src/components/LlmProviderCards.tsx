import { useState } from "react";
import { testProvider, saveProviderKey, clearProviderKey, type ProviderInfo } from "../lib/llm";

type Props = {
  providers: ProviderInfo[];
  probing: boolean;
  selected: string;
  /** Called after any mutation (key save/clear) with the affected id. */
  onChanged: (providerId: string) => Promise<void> | void;
};

/**
 * Canonical fleet provider cards (local free vs cloud paid, status dots,
 * key entry, Test). Ported from arxiv-mcp; zinc styling, no shadcn.
 * No-auto-pick: saving a key never selects a model (user picks in Settings).
 */
export function LlmProviderCards({ providers, probing, selected, onChanged }: Props) {
  const [keyInputs, setKeyInputs] = useState<Record<string, string>>({});
  const [showKeys, setShowKeys] = useState<Record<string, boolean>>({});
  const [cardMsg, setCardMsg] = useState<Record<string, string>>({});

  const localProviders = providers.filter((p) => p.kind === "local");
  const cloudProviders = providers.filter((p) => p.kind === "cloud");

  function statusDot(p: ProviderInfo) {
    if (p.kind === "local") {
      if (probing) return <span className="w-2 h-2 rounded-full bg-zinc-600 animate-pulse" />;
      return <span className="w-2 h-2 rounded-full bg-zinc-600" />;
    }
    return p.configured ? (
      <span className="w-2 h-2 rounded-full bg-green-500" />
    ) : (
      <span className="w-2 h-2 rounded-full bg-amber-500" />
    );
  }

  function statusText(p: ProviderInfo): string {
    if (p.kind === "local") return probing ? "Probing..." : "Local engine";
    return p.configured ? "Key configured" : "Missing key";
  }

  async function saveKey(id: string) {
    const key = keyInputs[id]?.trim();
    if (!key) return;
    setCardMsg((m) => ({ ...m, [id]: "Saving..." }));
    try {
      await saveProviderKey(id, key);
      setKeyInputs((k) => ({ ...k, [id]: "" }));
      await onChanged(id);
      setCardMsg((m) => ({ ...m, [id]: "Key saved." }));
    } catch (e) {
      setCardMsg((m) => ({ ...m, [id]: e instanceof Error ? e.message : String(e) }));
    }
  }

  async function clearKey(id: string) {
    setCardMsg((m) => ({ ...m, [id]: "Clearing..." }));
    try {
      await clearProviderKey(id);
      await onChanged(id);
      setCardMsg((m) => ({ ...m, [id]: "Key cleared." }));
    } catch (e) {
      setCardMsg((m) => ({ ...m, [id]: e instanceof Error ? e.message : String(e) }));
    }
  }

  async function runTest(id: string) {
    setCardMsg((m) => ({ ...m, [id]: "Testing..." }));
    try {
      const typed = keyInputs[id]?.trim() || undefined;
      const t = await testProvider(id, typed);
      if (t.ok) {
        setCardMsg((m2) => ({
          ...m2,
          [id]: `Key valid — ${t.models.length} live model(s).${typed ? " Save key to keep it." : ""}`,
        }));
      } else {
        setCardMsg((m2) => ({ ...m2, [id]: t.note || t.error || "Not reachable — check the endpoint." }));
      }
    } catch (e) {
      setCardMsg((m) => ({ ...m, [id]: e instanceof Error ? e.message : String(e) }));
    }
  }

  return (
    <div className="grid gap-3 md:grid-cols-2">
      {localProviders.length > 0 && (
        <div className="space-y-3">
          <p className="text-xs text-zinc-400 font-medium">Local engines (free)</p>
          {localProviders.map((p) => (
            <div
              key={p.id}
              data-testid={`llm-provider-card-${p.id}`}
              className={`bg-zinc-900 border rounded-xl p-4 space-y-2 ${p.id === selected ? "border-amber-500" : "border-zinc-800"}`}
            >
              <div className="flex items-center gap-2">
                {statusDot(p)}
                <span className="text-sm font-semibold">{p.label}</span>
                <span className="text-[10px] rounded bg-zinc-800 px-1.5 py-0.5 font-medium text-zinc-400">
                  local · free
                </span>
                <span className="text-xs text-zinc-400 ml-auto">{statusText(p)}</span>
              </div>
              {p.id === "ollama" && !probing && (
                <p className="text-xs text-zinc-500 rounded-lg border border-zinc-800 px-2 py-1.5">
                  Needs Ollama running: <code className="font-mono">ollama serve</code> then{" "}
                  <code className="font-mono">ollama pull qwen3:32b</code>. Test below checks reachability.
                </p>
              )}
              <div className="flex gap-2">
                <button
                  data-testid={`llm-test-${p.id}`}
                  onClick={() => void runTest(p.id)}
                  className="text-sm bg-zinc-800 hover:bg-zinc-700 px-3 py-1 rounded-lg"
                >
                  Test
                </button>
                {cardMsg[p.id] && <span className="text-xs text-zinc-400 self-center">{cardMsg[p.id]}</span>}
              </div>
            </div>
          ))}
        </div>
      )}

      {cloudProviders.length > 0 && (
        <div className="space-y-3">
          <p className="text-xs text-zinc-400 font-medium">Cloud (API key)</p>
          {cloudProviders.map((p) => (
            <div
              key={p.id}
              data-testid={`llm-provider-card-${p.id}`}
              className={`bg-zinc-900 border rounded-xl p-4 space-y-2 ${p.id === selected ? "border-amber-500" : "border-zinc-800"}`}
            >
              <div className="flex items-center gap-2">
                {statusDot(p)}
                <span className="text-sm font-semibold">{p.label}</span>
                <span className="text-[10px] rounded bg-zinc-800 px-1.5 py-0.5 font-medium text-zinc-400">
                  cloud · paid
                </span>
                <span className="text-xs text-zinc-400 ml-auto">{statusText(p)}</span>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <input
                  type={showKeys[p.id] ? "text" : "password"}
                  value={keyInputs[p.id] ?? ""}
                  onChange={(e) => setKeyInputs((k) => ({ ...k, [p.id]: e.target.value }))}
                  placeholder={p.configured ? "•••••••• configured" : `Paste ${p.key_env}`}
                  aria-label={`${p.label} API key`}
                  data-testid={`llm-key-${p.id}`}
                  className="flex-1 min-w-40 rounded-lg border border-zinc-700 bg-zinc-800 px-2 py-1 text-xs font-mono"
                />
                <button
                  onClick={() => setShowKeys((s) => ({ ...s, [p.id]: !s[p.id] }))}
                  className="text-sm text-zinc-400 hover:text-zinc-200"
                >
                  {showKeys[p.id] ? "Hide" : "Show"}
                </button>
              </div>
              <div className="flex gap-2">
                <button
                  disabled={!keyInputs[p.id]?.trim()}
                  onClick={() => void saveKey(p.id)}
                  className="text-sm bg-zinc-800 hover:bg-zinc-700 disabled:opacity-50 px-3 py-1 rounded-lg"
                >
                  Save key
                </button>
                {p.configured && (
                  <button
                    onClick={() => void clearKey(p.id)}
                    className="text-sm text-zinc-400 hover:text-zinc-200 px-3 py-1"
                  >
                    Clear
                  </button>
                )}
                <button
                  data-testid={`llm-test-${p.id}`}
                  onClick={() => void runTest(p.id)}
                  className="text-sm text-zinc-400 hover:text-zinc-200 px-3 py-1"
                >
                  Test
                </button>
                {cardMsg[p.id] && <span className="text-xs text-zinc-400 self-center">{cardMsg[p.id]}</span>}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
