/**
 * LLM provider client — ported from arxiv-mcp `web_sota/src/lib/llm.ts`.
 *
 * Learnbot adaptation: plain fetch via api.ts (no shadcn, no @/ alias);
 * server settings store dropped (selection is localStorage-only);
 * GPU/loaded/unload/install endpoints don't exist here — ActiveLlmCard
 * covers provider + model selection, cards cover keys + Test.
 */
import { api } from "../api";

export type ProviderKind = "local" | "cloud";
export type ModelSource = "live" | "curated" | "none";

export interface ProviderInfo {
  id: string;
  label: string;
  kind: ProviderKind;
  base_url: string;
  needs_key: boolean;
  key_env: string | null;
  configured: boolean;
}

export interface ModelsResponse {
  provider: string;
  models: string[];
  source: ModelSource;
  note?: string;
  error?: string;
  /** True when names are curated stand-ins (no key) — never a success. */
  key_missing?: boolean;
}

export interface TestResult {
  success: boolean;
  /** True only for a live list. Curated-without-key is ok:false by design. */
  ok: boolean;
  provider: string;
  models: string[];
  source: ModelSource;
  note?: string;
  error?: string;
}

export interface ChatMessage {
  role: "system" | "user" | "assistant";
  content: string;
}

const PROVIDER_KEY = "llm_provider";
const MODEL_KEY = "llm_model";
const ONBOARDED_KEY = "llm_onboarded";
const SELECTION_EVENT = "llm-selection-changed";

export type Selection = { provider: string; model: string };

function storageGet(key: string): string | null {
  try {
    return localStorage.getItem(key);
  } catch {
    return null;
  }
}

function storageSet(key: string, value: string) {
  try {
    localStorage.setItem(key, value);
  } catch {
    /* quota */
  }
}

export function loadSelection(): Selection {
  return {
    provider: storageGet(PROVIDER_KEY) || "ollama",
    model: storageGet(MODEL_KEY) || "",
  };
}

export function saveSelection(provider: string, model: string) {
  storageSet(PROVIDER_KEY, provider);
  storageSet(MODEL_KEY, model);
  // Same-tab broadcast (the "storage" event only fires across tabs).
  try {
    window.dispatchEvent(
      new CustomEvent(SELECTION_EVENT, { detail: { provider, model } }),
    );
  } catch {
    /* non-DOM */
  }
}

/** Live-sync hook: fires when any tab/page saves a new LLM selection. */
export function subscribeSelection(cb: (sel: Selection) => void): () => void {
  const onStorage = (e: StorageEvent) => {
    if (e.key === PROVIDER_KEY || e.key === MODEL_KEY) cb(loadSelection());
  };
  const onCustom = (e: Event) => {
    const d = (e as CustomEvent).detail as Selection | undefined;
    if (d && typeof d.provider === "string" && typeof d.model === "string")
      cb({ provider: d.provider, model: d.model });
  };
  window.addEventListener("storage", onStorage);
  window.addEventListener(SELECTION_EVENT, onCustom);
  return () => {
    window.removeEventListener("storage", onStorage);
    window.removeEventListener(SELECTION_EVENT, onCustom);
  };
}

export function isOnboarded(): boolean {
  return storageGet(ONBOARDED_KEY) === "1";
}

export function markOnboarded() {
  storageSet(ONBOARDED_KEY, "1");
}

export function fetchProviders(): Promise<{ providers: ProviderInfo[] }> {
  return api.llm.providers();
}

export function fetchModels(provider: string): Promise<ModelsResponse> {
  return api.llm.models(provider);
}

/**
 * Validate a provider without saving anything. Pass the card's typed key
 * (if any) — it travels in the POST body only and is never persisted.
 */
export function testProvider(provider: string, apiKey?: string): Promise<TestResult> {
  return api.llm.test({ provider, ...(apiKey ? { api_key: apiKey } : {}) });
}

export function saveProviderKey(provider: string, apiKey: string): Promise<{ success: boolean }> {
  return api.llm.saveKey({ provider, api_key: apiKey });
}

export function clearProviderKey(provider: string): Promise<{ success: boolean }> {
  return api.llm.clearKey(provider);
}

export async function chatComplete(
  provider: string,
  model: string,
  messages: ChatMessage[],
): Promise<string> {
  const d = await api.llm.chat({ provider, model, messages });
  if (d && typeof d === "object" && "content" in (d as object)) return (d as { content: string }).content;
  throw new Error((d as { error?: string })?.error || "LLM chat failed");
}
