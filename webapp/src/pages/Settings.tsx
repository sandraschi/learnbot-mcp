import { useCallback, useEffect, useState } from "react";
import { ActiveLlmCard } from "../components/ActiveLlmCard";
import { LlmOnboarding } from "../components/LlmOnboarding";
import { LlmProviderCards } from "../components/LlmProviderCards";
import { fetchProviders, loadSelection, type ProviderInfo } from "../lib/llm";

export function Settings() {
  const [providers, setProviders] = useState<ProviderInfo[]>([]);
  const [probing, setProbing] = useState(true);
  const [selected, setSelected] = useState("ollama");

  const refreshProviders = useCallback(async () => {
    try {
      const pv = await fetchProviders();
      setProviders(pv.providers);
    } catch {
      /* keep previous list */
    }
  }, []);

  useEffect(() => {
    (async () => {
      await refreshProviders();
      const prev = loadSelection();
      if (prev.provider) setSelected(prev.provider);
      setProbing(false);
    })();
  }, [refreshProviders]);

  return (
    <div className="max-w-3xl mx-auto space-y-4" data-testid="settings-page">
      <div>
        <h1 className="text-xl font-bold mb-1">Settings</h1>
        <p className="text-sm text-zinc-400">
          AI providers for Chat. Local engines are free; cloud needs a key.
          Keys stay on this machine (server keystore, never shown back).
        </p>
      </div>
      <LlmOnboarding mode="full" />
      <ActiveLlmCard />
      <LlmProviderCards
        providers={providers}
        probing={probing}
        selected={selected}
        onChanged={() => refreshProviders()}
      />
    </div>
  );
}
