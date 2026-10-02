const origin = (import.meta.env.VITE_API_ORIGIN as string | undefined)?.replace(/\/$/, "") ?? "";
const BASE = `${origin}/api`;

async function get(path: string) {
  const r = await fetch(`${BASE}${path}`);
  if (!r.ok) throw new Error(`GET ${path} ${r.status}`);
  return r.json();
}

async function post(path: string, body?: unknown) {
  const r = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!r.ok) {
    const text = await r.text();
    throw new Error(`POST ${path} ${r.status}: ${text}`);
  }
  return r.json();
}

async function del(path: string) {
  const r = await fetch(`${BASE}${path}`, { method: "DELETE" });
  if (!r.ok) throw new Error(`DELETE ${path} ${r.status}`);
  return r.json();
}

export const api = {
  health: () => get("/health"),
  personas: {
    list: () => get("/personas"),
    create: (data: Record<string, unknown>) => post("/personas", data),
    get: (name: string) => get(`/personas/${encodeURIComponent(name)}`),
    delete: (name: string) => del(`/personas/${encodeURIComponent(name)}`),
  },
  conversations: {
    list: (state?: string) => get(`/conversations${state ? `?state=${state}` : ""}`),
    create: (data: Record<string, unknown>) => post("/conversations", data),
    send: (id: string, content: string, userId?: string) =>
      post(`/conversations/${id}/send`, { content, user_id: userId || "" }),
    hibernate: (id: string) => post(`/conversations/${id}/hibernate`),
    resume: (id: string) => post(`/conversations/${id}/resume`),
    delete: (id: string) => del(`/conversations/${id}`),
  },
  compliance: () => get("/compliance"),
  lessons: {
    list: (params?: Record<string, string>) => {
      const q = params ? "?" + new URLSearchParams(params).toString() : "";
      return get(`/lessons${q}`);
    },
  },
  safety: {
    list: () => get("/safety/rules"),
    create: (data: Record<string, unknown>) => post("/safety/rules", data),
    delete: (id: number) => del(`/safety/rules/${id}`),
  },
  audit: (params?: Record<string, string>) => {
    const q = params ? "?" + new URLSearchParams(params).toString() : "";
    return get(`/audit${q}`);
  },
  vr: {
    status: () => get("/vr/status"),
    summon: (body: { platform: string; variant: string }) =>
      post("/vr/summon", body),
  },
  llm: {
    providers: () => get("/llm/providers"),
    models: (provider: string) => get(`/llm/models?provider=${encodeURIComponent(provider)}`),
    test: (body: { provider: string; api_key?: string }) => post("/llm/test", body),
    saveKey: (body: { provider: string; api_key: string }) => post("/llm/keys", body),
    clearKey: (provider: string) => del(`/llm/keys/${encodeURIComponent(provider)}`),
    chat: (body: { provider: string; model: string; messages: unknown[] }) =>
      post("/llm/chat", body),
  },
};
