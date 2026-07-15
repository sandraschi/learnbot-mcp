const BASE = "/api";

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
  safety: {
    list: () => get("/safety/rules"),
    create: (data: Record<string, unknown>) => post("/safety/rules", data),
    delete: (id: number) => del(`/safety/rules/${id}`),
  },
  audit: (params?: Record<string, string>) => {
    const q = params ? "?" + new URLSearchParams(params).toString() : "";
    return get(`/audit${q}`);
  },
};
